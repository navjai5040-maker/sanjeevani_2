from __future__ import annotations

from services.api.domain.models import FollowUp
from services.api.persistence import postgres_store


class FollowUpRepository:
    def __init__(self, follow_ups: list[FollowUp]) -> None:
        self._items = {item.follow_up_id: item for item in follow_ups}

    def list(self, patient_id: str | None = None) -> list[FollowUp]:
        items = list(self._items.values())
        return [item for item in items if patient_id is None or item.patient_id == patient_id]

    def get(self, follow_up_id: str) -> FollowUp | None:
        return self._items.get(follow_up_id)

    def add(self, follow_up: FollowUp) -> FollowUp:
        self._items[follow_up.follow_up_id] = follow_up
        return follow_up

    def reset_demo(self) -> None:
        if postgres_store:
            return
        self._items = {
            item.follow_up_id: item
            for item in [
                FollowUp(follow_up_id='fu-ravi-demo', patient_id='pat-ravi', due_date='2026-09-16T09:00:00Z', reason='Blood-pressure follow-up', priority='high', status='due', next_action='Contact patient and review progress'),
                FollowUp(follow_up_id='fu-sita-demo', patient_id='pat-sita', due_date='2026-09-14T09:00:00Z', reason='Maternal follow-up', priority='high', status='overdue', next_action='Contact patient and reschedule review'),
                FollowUp(follow_up_id='fu-aman-demo', patient_id='pat-aman', due_date='2026-09-22T09:00:00Z', reason='Child-health review', priority='medium', status='upcoming', next_action='Confirm child-health review'),
            ]
        }


follow_up_repository = FollowUpRepository([])
follow_up_repository.reset_demo()
