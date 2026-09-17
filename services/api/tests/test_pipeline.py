from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from services.api.domain.models import AppointmentCreate, CareRequest, ReferralCreate
from services.api.repositories.followups import follow_up_repository
from services.api.repositories.patients import patient_repository
from services.api.repositories.facilities import facility_repository
from services.api.services.appointments import book_appointment, get_slots
from services.api.services.care_matching import CareMatchingService
from services.api.services.referrals import create_referral
from services.api.services.triage import RuleBasedTriageService


def request(**overrides):
    values = {
        'patient_id': 'pat-1',
        'requester_id': 'asha-1',
        'symptoms': 'chest pain',
        'duration': '2 hours',
        'urgency_indicators': [],
        'location': 'Ghatol',
        'preferred_language': 'hi',
    }
    values.update(overrides)
    return CareRequest(**values)


def test_care_request_validates_required_fields():
    assert request().patient_id == 'pat-1'


def test_care_request_rejects_short_symptoms():
    with pytest.raises(ValidationError):
        request(symptoms='x')


@pytest.mark.parametrize(
    ('indicators', 'expected'),
    [([], 'routine'), (['chest pain'], 'urgent'), (['unconscious'], 'emergency')],
)
def test_rule_based_triage(indicators, expected):
    result = RuleBasedTriageService().assess(request(urgency_indicators=indicators))
    assert result.level == expected


def test_matching_excludes_incapable_facilities_and_explains_rank():
    matches = CareMatchingService().match(request(symptoms='cardiology'), facility_repository.list())
    assert matches
    assert all(match.matched_services or match.specialists or match.diagnostics or match.medicines for match in matches)
    assert matches[0].explanation


def test_queue_affects_matching_score():
    low_queue = request(symptoms='general medicine')
    matches = CareMatchingService().match(low_queue, facility_repository.list())
    assert matches[0].queue_minutes <= matches[-1].queue_minutes or matches[0].readiness > matches[-1].readiness


def test_slot_availability_and_booking():
    facility_id = facility_repository.list()[0].facility_id
    starts_at = datetime.now(timezone.utc) + timedelta(days=1, hours=1)
    slots = get_slots(facility_id, 'general medicine', starts_at)
    appointment = book_appointment(
        AppointmentCreate(
            patient_id='pat-1',
            facility_id=facility_id,
            provider_id=slots[0].provider_id,
            service='general medicine',
            starts_at=starts_at.replace(hour=9),
        )
    )
    assert appointment.status == 'booked'
    with pytest.raises(HTTPException):
        book_appointment(
            AppointmentCreate(
                patient_id='pat-2',
                facility_id=facility_id,
                provider_id=slots[0].provider_id,
                service='general medicine',
                starts_at=starts_at.replace(hour=9),
            )
        )


def test_referral_integration_uses_selected_destination():
    facility = facility_repository.list()[0]
    referral = create_referral(ReferralCreate(patient_id='pat-1', destination=facility.facility_name))
    assert referral.destination == facility.facility_name
    assert referral.state == 'created'


def test_shared_patient_registry_and_follow_up_lifecycle():
    patient = patient_repository.get('pat-ravi')
    assert patient is not None
    follow_up = follow_up_repository.list('pat-ravi')[0]
    assert follow_up.patient_id == patient.id
    assert follow_up.status in {'due', 'upcoming', 'overdue', 'pending', 'missed'}
