from __future__ import annotations

from fastapi import APIRouter

from services.api.domain.models import ReferralCreate, ReferralTransition
from services.api.services.referrals import (
    REFERRAL_STATES,
    create_referral,
    get_referral,
    list_referrals,
    referral_events,
    transition_referral,
)

router = APIRouter(prefix='/api/v1/referrals', tags=['referrals'])


@router.get('/states')
def referral_states() -> dict[str, list[str]]:
    return {'states': list(REFERRAL_STATES)}


@router.post('', status_code=201)
def create(payload: ReferralCreate):
    return create_referral(payload)


@router.get('')
def list_all():
    return list_referrals()


@router.get('/{referral_id}')
def get(referral_id: str):
    return get_referral(referral_id)


@router.get('/{referral_id}/events')
def events(referral_id: str):
    return referral_events(referral_id)


@router.post('/{referral_id}/transition')
def transition(referral_id: str, payload: ReferralTransition):
    return transition_referral(referral_id, payload)
