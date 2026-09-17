from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from services.api.domain.models import Appointment, AppointmentCreate, AppointmentSlot, AppointmentTransition
from services.api.repositories.appointments import appointment_repository
from services.api.repositories.facilities import facility_repository
from services.api.persistence import postgres_store


def get_slots(facility_id: str, service: str, date: datetime | None = None) -> list[AppointmentSlot]:
    facility = facility_repository.get(facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail='Facility not found')
    day = date or datetime.now(timezone.utc)
    slots = []
    for index in range(3):
        starts_at = day.replace(hour=9 + index * 2, minute=0, second=0, microsecond=0)
        slots.append(
            AppointmentSlot(
                slot_id=f'{facility_id}-{starts_at:%Y%m%d%H%M}',
                facility_id=facility_id,
                provider_id=f'provider-{index + 1}',
                service=service,
                starts_at=starts_at,
                estimated_wait_minutes=facility.queue_minutes,
            )
        )
    booked = {(item.facility_id, item.starts_at) for item in appointment_repository.all() if item.status == 'booked'}
    return [slot.model_copy(update={'status': 'booked'}) if (slot.facility_id, slot.starts_at) in booked else slot for slot in slots]


def book_appointment(payload: AppointmentCreate) -> Appointment:
    facility = facility_repository.get(payload.facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail='Facility not found')
    if payload.starts_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail='Appointment time must be in the future')
    if any(item.facility_id == payload.facility_id and item.starts_at == payload.starts_at and item.status == 'booked' for item in appointment_repository.all()):
        raise HTTPException(status_code=409, detail='Appointment slot is already booked')
    appointment = Appointment(
        appointment_id=f'appt-{uuid4().hex[:10]}',
        patient_id=payload.patient_id,
        facility_id=payload.facility_id,
        provider_id=payload.provider_id,
        service=payload.service,
        starts_at=payload.starts_at,
        estimated_wait_minutes=facility.queue_minutes,
    )
    return appointment_repository.add(appointment)


def get_appointment(appointment_id: str) -> Appointment:
    appointment = appointment_repository.get(appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail='Appointment not found')
    return appointment


def list_appointments(facility_id: str | None = None) -> list[Appointment]:
    appointments = appointment_repository.all()
    if facility_id is None:
        return appointments
    return [item for item in appointments if item.facility_id == facility_id]


def transition_appointment(appointment_id: str, payload: AppointmentTransition) -> Appointment:
    appointment = get_appointment(appointment_id)
    if appointment.status != 'booked' or payload.status not in ('cancelled', 'completed'):
        raise HTTPException(
            status_code=409,
            detail=f'Invalid appointment transition from {appointment.status} to {payload.status}',
        )
    updated = appointment.model_copy(update={'status': payload.status})
    if postgres_store:
        postgres_store.execute(
            'UPDATE appointments SET status = :status WHERE appointment_id = :appointment_id',
            {'status': payload.status, 'appointment_id': appointment_id},
        )
    else:
        appointment_repository.add(updated)
    return updated
