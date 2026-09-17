from __future__ import annotations

import json
from uuid import uuid4

from services.api.domain.models import CareRequest
from services.api.persistence import postgres_store, care_request_from_row


class CareRequestRepository:
    def __init__(self) -> None:
        self._items: dict[str, CareRequest] = {}

    def create(self, request: CareRequest) -> CareRequest:
        request_id = request.request_id or f'req-{uuid4().hex[:10]}'
        stored = request.model_copy(update={'request_id': request_id})
        if postgres_store:
            postgres_store.execute(
                """
                INSERT INTO care_requests (
                    request_id, patient_id, requester_id, symptoms, duration,
                    urgency_indicators, location, preferred_language, status,
                    required_service, urgency, notes
                ) VALUES (
                    :request_id, :patient_id, :requester_id, :symptoms, :duration,
                    CAST(:urgency_indicators AS JSONB), :location, :preferred_language, :status,
                    :required_service, :urgency, :notes
                )
                ON CONFLICT (request_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    symptoms = EXCLUDED.symptoms
                """,
                {**stored.model_dump(), 'urgency_indicators': json.dumps(stored.urgency_indicators)},
            )
            return stored
        self._items[request_id] = stored
        return stored

    def get(self, request_id: str) -> CareRequest | None:
        if postgres_store:
            rows = postgres_store.execute(
                'SELECT * FROM care_requests WHERE request_id = :request_id',
                {'request_id': request_id},
            )
            return care_request_from_row(rows[0]) if rows else None
        return self._items.get(request_id)

    def list(self, patient_id: str | None = None) -> list[CareRequest]:
        if postgres_store:
            rows = postgres_store.execute(
                'SELECT * FROM care_requests ORDER BY request_id',
            )
            items = [care_request_from_row(row) for row in rows]
        else:
            items = list(self._items.values())
        return [item for item in items if patient_id is None or item.patient_id == patient_id]

    def reset_demo(self) -> None:
        if not postgres_store:
            self._items.clear()


care_request_repository = CareRequestRepository()
