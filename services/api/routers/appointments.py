from datetime import datetime

from fastapi import APIRouter, Query

from services.api.domain.models import AppointmentCreate, AppointmentTransition
from services.api.services.appointments import book_appointment, get_appointment, get_slots, list_appointments, transition_appointment

router = APIRouter(prefix='/api/v1/appointments', tags=['appointments'])


@router.get('/slots')
def available_slots(
    facility_id: str = Query(...),
    service: str = Query(...),
    date: datetime | None = Query(None),
):
    return get_slots(facility_id, service, date)


@router.post('', status_code=201)
def create_appointment(payload: AppointmentCreate):
    return book_appointment(payload)


@router.get('')
def appointments(facility_id: str | None = Query(None)):
    return list_appointments(facility_id)


@router.get('/{appointment_id}')
def appointment(appointment_id: str):
    return get_appointment(appointment_id)


@router.post('/{appointment_id}/transition')
def transition(appointment_id: str, payload: AppointmentTransition):
    return transition_appointment(appointment_id, payload)
