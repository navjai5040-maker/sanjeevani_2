from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from services.api.domain.models import CareRequest
from services.api.repositories.facilities import facility_repository
from services.api.services.care_matching import CareMatchingService

router = APIRouter(prefix='/api/v1/facilities', tags=['facilities'])


@router.get('')
def list_facilities():
    return facility_repository.list()


@router.get('/matches')
def facility_matches(
    patient_id: str = Query(...),
    requester_id: str = Query(...),
    symptoms: str = Query(...),
    duration: str = Query(...),
    location: str = Query(...),
    preferred_language: Literal['en', 'hi'] = Query('en'),
    required_service: str | None = Query(None),
):
    request = CareRequest(
        patient_id=patient_id,
        requester_id=requester_id,
        symptoms=symptoms,
        duration=duration,
        location=location,
        preferred_language=preferred_language,
        required_service=required_service,
    )
    return CareMatchingService().match(request, facility_repository.list())


@router.get('/{facility_id}')
def get_facility(facility_id: str):
    facility = facility_repository.get(facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail='Facility not found')
    return facility


@router.get('/{facility_id}/state')
def get_facility_state(facility_id: str):
    facility = facility_repository.get(facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail='Facility not found')
    return facility
