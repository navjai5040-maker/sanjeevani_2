from fastapi import APIRouter

from services.api.persistence import postgres_store
from services.api.repositories.appointments import appointment_repository
from services.api.repositories.care_requests import care_request_repository
from services.api.repositories.followups import follow_up_repository
from services.api.services.referrals import reset_demo_state

router = APIRouter(prefix='/api/v1/demo', tags=['demo'])


@router.post('/reset')
def reset_demo() -> dict[str, str]:
    if postgres_store:
        return {'status': 'skipped', 'message': 'Demo reset is available only in in-memory mode.'}
    reset_demo_state()
    appointment_repository.reset_demo()
    care_request_repository.reset_demo()
    follow_up_repository.reset_demo()
    return {'status': 'reset', 'message': 'In-memory referral and appointment demo state reset.'}
