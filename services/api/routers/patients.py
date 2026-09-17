from fastapi import APIRouter, HTTPException, Query

from services.api.repositories.patients import patient_repository

router = APIRouter(prefix='/api/v1/patients', tags=['patients'])


@router.get('')
def list_patients(query: str | None = Query(None, min_length=1)):
    return patient_repository.list(query)


@router.get('/{patient_id}')
def get_patient(patient_id: str):
    patient = patient_repository.get(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail='Patient not found')
    return patient
