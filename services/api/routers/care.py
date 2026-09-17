from __future__ import annotations

from fastapi import APIRouter

from services.api.domain.models import CareRequest
from services.api.repositories.facilities import facility_repository
from services.api.services.care_matching import CareMatchingService
from services.api.services.triage import RuleBasedTriageService

router = APIRouter(prefix='/api/v1', tags=['care'])


@router.post('/triage')
def triage(request: CareRequest):
    return RuleBasedTriageService().assess(request)


@router.post('/care-matching')
def care_matching(request: CareRequest):
    return CareMatchingService().match(request, facility_repository.list())
