from __future__ import annotations

import json

from services.api.domain.models import FacilityState
from services.api.persistence import facility_from_row, postgres_store


class FacilityRepository:
    def __init__(self, facilities: list[FacilityState]) -> None:
        self._items = {facility.facility_id: facility for facility in facilities}

    def list(self) -> list[FacilityState]:
        if postgres_store:
            return [facility_from_row(row) for row in postgres_store.execute('SELECT * FROM facilities ORDER BY facility_name')]
        return list(self._items.values())

    def get(self, facility_id: str) -> FacilityState | None:
        if postgres_store:
            rows = postgres_store.execute(
                'SELECT * FROM facilities WHERE facility_id = :facility_id',
                {'facility_id': facility_id},
            )
            return facility_from_row(rows[0]) if rows else None
        return self._items.get(facility_id)

    def seed(self) -> None:
        if not postgres_store:
            return
        for facility in self._items.values():
            postgres_store.execute(
                """
                INSERT INTO facilities (
                    facility_id, facility_name, district, facility_type, services,
                    queue_minutes, specialist_availability, diagnostics, medicines,
                    operational_status, travel_minutes, latitude, longitude, readiness
                ) VALUES (
                    :facility_id, :facility_name, :district, :facility_type, CAST(:services AS JSONB),
                    :queue_minutes, CAST(:specialists AS JSONB), CAST(:diagnostics AS JSONB), CAST(:medicines AS JSONB),
                    :operational_status, :travel_minutes, :latitude, :longitude, :readiness
                )
                ON CONFLICT (facility_id) DO UPDATE SET
                    facility_name = EXCLUDED.facility_name,
                    queue_minutes = EXCLUDED.queue_minutes,
                    readiness = EXCLUDED.readiness
                """,
                {
                    **facility.model_dump(),
                    'services': json.dumps(facility.services),
                    'specialists': json.dumps(facility.specialist_availability),
                    'diagnostics': json.dumps(facility.diagnostics),
                    'medicines': json.dumps(facility.medicines),
                },
            )


facility_repository = FacilityRepository(
    [
        FacilityState(
            facility_id='fac-udaipur-dh',
            facility_name='District Hospital, Udaipur',
            district='Udaipur',
            facility_type='District Hospital',
            services=['general medicine', 'cardiology', 'emergency care'],
            queue_minutes=28,
            specialist_availability=['cardiology'],
            diagnostics=['ECG', 'laboratory'],
            medicines=['antibiotics', 'antihypertensives'],
            travel_minutes=45,
            latitude=24.5854,
            longitude=73.7125,
            readiness=92,
        ),
        FacilityState(
            facility_id='fac-banswara-chc',
            facility_name='CHC, Banswara',
            district='Banswara',
            facility_type='CHC',
            services=['general medicine', 'maternal care'],
            queue_minutes=14,
            specialist_availability=['general medicine'],
            diagnostics=['X-Ray'],
            medicines=['basic care', 'iron supplements'],
            travel_minutes=20,
            latitude=23.5461,
            longitude=74.4338,
            readiness=81,
        ),
        FacilityState(
            facility_id='fac-ghatol-phc',
            facility_name='PHC, Ghatol',
            district='Banswara',
            facility_type='PHC',
            services=['general medicine', 'maternal care'],
            queue_minutes=8,
            specialist_availability=[],
            diagnostics=['basic laboratory'],
            medicines=['basic care', 'iron supplements'],
            travel_minutes=10,
            latitude=23.4182,
            longitude=74.2631,
            readiness=73,
        ),
    ]
)
