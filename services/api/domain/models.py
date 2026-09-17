from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

ReferralState = Literal[
    'created',
    'destination_identified',
    'accepted',
    'scheduled',
    'arrived',
    'care_completed',
    'closed',
    'follow_up',
]


class Patient(BaseModel):
    id: str
    name: str
    age: int
    sex: Optional[str] = None
    village: str
    preferred_language: Literal['en', 'hi'] = 'en'
    demo_contact: Optional[str] = None
    risk_level: Literal['low', 'medium', 'high'] = 'low'


class CareRequest(BaseModel):
    request_id: str = ''
    patient_id: str
    requester_id: str
    symptoms: str = Field(min_length=2, max_length=2000)
    duration: str = Field(min_length=1, max_length=120)
    urgency_indicators: list[str] = Field(default_factory=list)
    location: str = Field(min_length=2, max_length=200)
    preferred_language: Literal['en', 'hi'] = 'en'
    status: Literal['open', 'triaged', 'matched', 'scheduled', 'referred', 'closed'] = 'open'
    required_service: Optional[str] = Field(default=None, min_length=2, max_length=120)
    urgency: Optional[Literal['ROUTINE', 'URGENT', 'EMERGENCY']] = None
    notes: Optional[str] = None

    @property
    def requested_service(self) -> str:
        return self.required_service or self.symptoms


class FacilityState(BaseModel):
    facility_id: str
    facility_name: str
    district: str = ''
    facility_type: Literal['PHC', 'CHC', 'Rural Hospital', 'District Hospital'] = 'PHC'
    services: list[str] = Field(default_factory=list)
    queue_minutes: int = 0
    specialist_availability: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    medicines: list[str] = Field(default_factory=list)
    operational_status: Literal['open', 'limited', 'closed'] = 'open'
    travel_minutes: int = 0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    readiness: int = Field(default=70, ge=0, le=100)


class CareMatch(BaseModel):
    facility_id: str
    facility_name: str
    match_score: float
    matched_services: list[str] = Field(default_factory=list)
    specialists: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    medicines: list[str] = Field(default_factory=list)
    suitability_indicators: list[str] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)
    queue_minutes: int
    travel_minutes: int
    readiness: int
    reason: list[str] = Field(default_factory=list)


class TriageResult(BaseModel):
    request_id: str
    level: Literal['routine', 'urgent', 'emergency']
    rationale: list[str]
    requires_emergency_escalation: bool = False


class AppointmentSlot(BaseModel):
    slot_id: str
    facility_id: str
    provider_id: str
    service: str
    starts_at: datetime
    estimated_wait_minutes: int = Field(ge=0)
    status: Literal['available', 'booked', 'cancelled', 'completed'] = 'available'


class AppointmentCreate(BaseModel):
    patient_id: str
    facility_id: str
    provider_id: str
    service: str = Field(min_length=2, max_length=120)
    starts_at: datetime


class Appointment(BaseModel):
    appointment_id: str
    patient_id: str
    facility_id: str
    provider_id: str
    service: str
    starts_at: datetime
    status: Literal['available', 'booked', 'cancelled', 'completed'] = 'booked'
    estimated_wait_minutes: int = Field(ge=0)


class AppointmentTransition(BaseModel):
    status: Literal['cancelled', 'completed']


class Referral(BaseModel):
    referral_id: str
    patient_id: str
    destination: str
    state: ReferralState = 'created'
    created_at: datetime


class ReferralEvent(BaseModel):
    referral_id: str
    state: ReferralState
    timestamp: datetime
    description: str


class ReferralCreate(BaseModel):
    patient_id: str
    destination: str


class ReferralTransition(BaseModel):
    state: ReferralState
    description: str


class FollowUp(BaseModel):
    follow_up_id: str
    patient_id: str
    referral_id: Optional[str] = None
    due_date: datetime
    reason: str = 'Care follow-up'
    priority: Literal['low', 'medium', 'high'] = 'medium'
    status: Literal['upcoming', 'pending', 'due', 'overdue', 'missed', 'completed'] = 'upcoming'
    next_action: str
    completed_at: Optional[datetime] = None
