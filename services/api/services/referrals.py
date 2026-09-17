from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from services.api.domain.models import Referral, ReferralCreate, ReferralEvent, ReferralTransition
from services.api.persistence import event_from_row, postgres_store, referral_from_row
from services.api.repositories.followups import follow_up_repository


REFERRAL_STATES = (
    'created',
    'destination_identified',
    'accepted',
    'scheduled',
    'arrived',
    'care_completed',
    'closed',
    'follow_up',
)

_referrals: dict[str, Referral] = {}
_events: dict[str, list[ReferralEvent]] = {}


def create_referral(payload: ReferralCreate) -> Referral:
    referral_id = f'ref-{uuid4().hex[:10]}'
    referral = Referral(
        referral_id=referral_id,
        patient_id=payload.patient_id,
        destination=payload.destination,
        state='created',
        created_at=datetime.now(timezone.utc),
    )
    if postgres_store:
        postgres_store.execute(
            """
            INSERT INTO referrals (referral_id, patient_id, destination, state, created_at)
            VALUES (:referral_id, :patient_id, :destination, :state, :created_at)
            """,
            referral.model_dump(),
        )
        postgres_store.execute(
            """
            INSERT INTO referral_events (referral_id, state, timestamp, description)
            VALUES (:referral_id, :state, :timestamp, :description)
            """,
            {
                'referral_id': referral.referral_id,
                'state': referral.state,
                'timestamp': referral.created_at,
                'description': 'Referral created',
            },
        )
        return referral
    _referrals[referral_id] = referral
    _events[referral_id] = [
        ReferralEvent(
            referral_id=referral_id,
            state='created',
            timestamp=referral.created_at,
            description='Referral created',
        )
    ]
    return referral


def list_referrals() -> list[Referral]:
    if postgres_store:
        return [referral_from_row(row) for row in postgres_store.execute('SELECT * FROM referrals ORDER BY created_at DESC')]
    return list(_referrals.values())


def get_referral(referral_id: str) -> Referral:
    if postgres_store:
        rows = postgres_store.execute(
            'SELECT * FROM referrals WHERE referral_id = :referral_id',
            {'referral_id': referral_id},
        )
        if rows:
            return referral_from_row(rows[0])
        raise HTTPException(status_code=404, detail='Referral not found')
    referral = _referrals.get(referral_id)
    if referral is None:
        raise HTTPException(status_code=404, detail='Referral not found')
    return referral


def transition_referral(referral_id: str, payload: ReferralTransition) -> Referral:
    referral = get_referral(referral_id)
    current_index = REFERRAL_STATES.index(referral.state)
    requested_index = REFERRAL_STATES.index(payload.state)

    if requested_index != current_index + 1:
        raise HTTPException(
            status_code=409,
            detail=f'Invalid referral transition from {referral.state} to {payload.state}',
        )

    updated = referral.model_copy(update={'state': payload.state})
    if postgres_store:
        postgres_store.execute(
            'UPDATE referrals SET state = :state WHERE referral_id = :referral_id',
            {'state': payload.state, 'referral_id': referral_id},
        )
        postgres_store.execute(
            """
            INSERT INTO referral_events (referral_id, state, timestamp, description)
            VALUES (:referral_id, :state, :timestamp, :description)
            """,
            {
                'referral_id': referral_id,
                'state': payload.state,
                'timestamp': datetime.now(timezone.utc),
                'description': payload.description,
            },
        )
        return updated
    _referrals[referral_id] = updated
    _events[referral_id].append(
        ReferralEvent(
            referral_id=referral_id,
            state=payload.state,
            timestamp=datetime.now(timezone.utc),
            description=payload.description,
        )
    )
    if payload.state == 'closed' and not any(item.referral_id == referral_id for item in follow_up_repository.list()):
        from services.api.domain.models import FollowUp
        follow_up_repository.add(FollowUp(
            follow_up_id=f'fu-{referral_id}',
            patient_id=referral.patient_id,
            referral_id=referral_id,
            due_date=datetime.now(timezone.utc),
            reason='Post-referral follow-up',
            priority='high',
            status='due',
            next_action='Contact patient and confirm care completion',
        ))
    return updated


def referral_events(referral_id: str) -> list[ReferralEvent]:
    get_referral(referral_id)
    if postgres_store:
        return [
            event_from_row(row)
            for row in postgres_store.execute(
                'SELECT * FROM referral_events WHERE referral_id = :referral_id ORDER BY timestamp',
                {'referral_id': referral_id},
            )
        ]
    return _events[referral_id]


def reset_demo_state() -> None:
    if postgres_store:
        return
    _referrals.clear()
    _events.clear()
