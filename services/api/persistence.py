from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from services.api.domain.models import (
    Appointment,
    CareRequest,
    FacilityState,
    Referral,
    ReferralEvent,
)

load_dotenv()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS care_requests (
    request_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    requester_id TEXT NOT NULL,
    symptoms TEXT NOT NULL,
    duration TEXT NOT NULL,
    urgency_indicators JSONB NOT NULL,
    location TEXT NOT NULL,
    preferred_language TEXT NOT NULL,
    status TEXT NOT NULL,
    required_service TEXT,
    urgency TEXT,
    notes TEXT
);
CREATE TABLE IF NOT EXISTS facilities (
    facility_id TEXT PRIMARY KEY,
    facility_name TEXT NOT NULL,
    district TEXT NOT NULL,
    facility_type TEXT NOT NULL,
    services JSONB NOT NULL,
    queue_minutes INTEGER NOT NULL,
    specialist_availability JSONB NOT NULL,
    diagnostics JSONB NOT NULL,
    medicines JSONB NOT NULL,
    operational_status TEXT NOT NULL,
    travel_minutes INTEGER NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    readiness INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    facility_id TEXT NOT NULL REFERENCES facilities(facility_id),
    provider_id TEXT NOT NULL,
    service TEXT NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    estimated_wait_minutes INTEGER NOT NULL,
    UNIQUE (facility_id, starts_at) DEFERRABLE INITIALLY IMMEDIATE
);
CREATE TABLE IF NOT EXISTS referrals (
    referral_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    destination TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS referral_events (
    referral_id TEXT NOT NULL REFERENCES referrals(referral_id),
    state TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    description TEXT NOT NULL,
    PRIMARY KEY (referral_id, state)
);
"""


def _json(value: list[str]) -> str:
    return json.dumps(value)


def _parse(value: Any) -> list[str]:
    return value if isinstance(value, list) else json.loads(value)


class PostgresStore:
    def __init__(self, url: str) -> None:
        self.engine = create_engine(url, pool_pre_ping=True)

    def initialize(self) -> None:
        statements = [statement.strip() for statement in SCHEMA_SQL.split(';') if statement.strip()]
        with self.engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement))

    def execute(self, statement: str, values: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.engine.begin() as connection:
            result = connection.execute(text(statement), values or {})
            return [dict(row._mapping) for row in result]


def persistence_enabled() -> bool:
    return os.getenv('PERSISTENCE_BACKEND', 'memory').lower() == 'postgres'


def build_store() -> PostgresStore | None:
    if not persistence_enabled():
        return None
    url = os.getenv('DATABASE_URL')
    if not url:
        raise RuntimeError('DATABASE_URL is required when PERSISTENCE_BACKEND=postgres')
    return PostgresStore(url)


postgres_store = build_store()


def care_request_from_row(row: dict[str, Any]) -> CareRequest:
    return CareRequest(
        request_id=row['request_id'],
        patient_id=row['patient_id'],
        requester_id=row['requester_id'],
        symptoms=row['symptoms'],
        duration=row['duration'],
        urgency_indicators=_parse(row['urgency_indicators']),
        location=row['location'],
        preferred_language=row['preferred_language'],
        status=row['status'],
        required_service=row['required_service'],
        urgency=row['urgency'],
        notes=row['notes'],
    )


def facility_from_row(row: dict[str, Any]) -> FacilityState:
    return FacilityState(
        facility_id=row['facility_id'],
        facility_name=row['facility_name'],
        district=row['district'],
        facility_type=row['facility_type'],
        services=_parse(row['services']),
        queue_minutes=row['queue_minutes'],
        specialist_availability=_parse(row['specialist_availability']),
        diagnostics=_parse(row['diagnostics']),
        medicines=_parse(row['medicines']),
        operational_status=row['operational_status'],
        travel_minutes=row['travel_minutes'],
        latitude=row['latitude'],
        longitude=row['longitude'],
        readiness=row['readiness'],
    )


def appointment_from_row(row: dict[str, Any]) -> Appointment:
    return Appointment(
        appointment_id=row['appointment_id'],
        patient_id=row['patient_id'],
        facility_id=row['facility_id'],
        provider_id=row['provider_id'],
        service=row['service'],
        starts_at=row['starts_at'],
        status=row['status'],
        estimated_wait_minutes=row['estimated_wait_minutes'],
    )


def referral_from_row(row: dict[str, Any]) -> Referral:
    return Referral(
        referral_id=row['referral_id'],
        patient_id=row['patient_id'],
        destination=row['destination'],
        state=row['state'],
        created_at=row['created_at'],
    )


def event_from_row(row: dict[str, Any]) -> ReferralEvent:
    return ReferralEvent(
        referral_id=row['referral_id'],
        state=row['state'],
        timestamp=row['timestamp'],
        description=row['description'],
    )
