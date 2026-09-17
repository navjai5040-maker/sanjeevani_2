from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from services.api.repositories.followups import follow_up_repository

router = APIRouter(prefix='/api/v1/followups', tags=['follow-ups'])


@router.get('')
def list_followups(patient_id: str | None = Query(None)):
    return follow_up_repository.list(patient_id)


@router.get('/{follow_up_id}')
def get_followup(follow_up_id: str):
    follow_up = follow_up_repository.get(follow_up_id)
    if follow_up is None:
        raise HTTPException(status_code=404, detail='Follow-up not found')
    return follow_up


@router.post('/{follow_up_id}/complete')
def complete_followup(follow_up_id: str):
    follow_up = follow_up_repository.get(follow_up_id)
    if follow_up is None:
        raise HTTPException(status_code=404, detail='Follow-up not found')
    if follow_up.status == 'completed':
        raise HTTPException(status_code=409, detail='Follow-up is already completed')
    return follow_up_repository.add(follow_up.model_copy(update={
        'status': 'completed',
        'completed_at': datetime.now(timezone.utc),
    }))
