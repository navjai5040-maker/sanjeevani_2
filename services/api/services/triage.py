from __future__ import annotations

from typing import Protocol

from services.api.domain.models import CareRequest, TriageResult


class TriageService(Protocol):
    def assess(self, request: CareRequest) -> TriageResult:
        ...


class RuleBasedTriageService:
    def assess(self, request: CareRequest) -> TriageResult:
        indicators = {indicator.lower() for indicator in request.urgency_indicators}
        if request.urgency == 'EMERGENCY' or indicators.intersection({'severe breathing difficulty', 'unconscious', 'heavy bleeding'}):
            return TriageResult(
                request_id=request.request_id,
                level='emergency',
                rationale=['Emergency indicator requires immediate escalation'],
                requires_emergency_escalation=True,
            )
        if request.urgency == 'URGENT' or indicators.intersection({'chest pain', 'high fever', 'severe pain'}):
            return TriageResult(
                request_id=request.request_id,
                level='urgent',
                rationale=['Urgency indicator requires prompt clinical review'],
            )
        return TriageResult(
            request_id=request.request_id,
            level='routine',
            rationale=['No configured emergency or urgent indicator was provided'],
        )


class FutureMLTriageService:
    def assess(self, request: CareRequest) -> TriageResult:
        """Placeholder to be replaced by validated ML-based triage."""
        return RuleBasedTriageService().assess(request)
