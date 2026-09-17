from fastapi import APIRouter, HTTPException

from services.api.domain.models import CareRequest
from services.api.repositories.care_requests import care_request_repository
from services.api.repositories.patients import patient_repository

router = APIRouter(prefix='/api/v1/care-requests', tags=['care requests'])


@router.post('', status_code=201)
def create_care_request(request: CareRequest):
    if patient_repository.get(request.patient_id) is None:
        raise HTTPException(status_code=404, detail='Patient not found')
    return care_request_repository.create(request)


@router.get('')
def list_care_requests(patient_id: str | None = None):
    return care_request_repository.list(patient_id)


@router.get('/{request_id}')
def get_care_request(request_id: str):
    request = care_request_repository.get(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail='Care request not found')
    return request
