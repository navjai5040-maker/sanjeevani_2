from __future__ import annotations

from services.api.domain.models import CareMatch, CareRequest, FacilityState


def _contains(values: list[str], requested: str) -> list[str]:
    needle = requested.lower()
    return [value for value in values if needle in value.lower() or value.lower() in needle]


class CareMatchingService:
    def match(self, request: CareRequest, facilities: list[FacilityState]) -> list[CareMatch]:
        requested = request.requested_service
        matches: list[CareMatch] = []

        for facility in facilities:
            if facility.operational_status == 'closed':
                continue

            services = _contains(facility.services, requested)
            specialists = _contains(facility.specialist_availability, requested)
            diagnostics = _contains(facility.diagnostics, requested)
            medicines = _contains(facility.medicines, requested)
            capable = bool(services or specialists or diagnostics or medicines)
            if not capable:
                continue

            score = 45.0
            explanation = ['Facility has a capability relevant to the care request']
            indicators = ['capability_match']
            if services:
                score += 20
                indicators.append('service_available')
                explanation.append('Requested service is available')
            if specialists:
                score += 20
                indicators.append('specialist_available')
                explanation.append('Relevant specialist coverage is available')
            if diagnostics:
                score += 10
                indicators.append('diagnostic_available')
                explanation.append('Supporting diagnostics are available')
            if medicines:
                score += 5
                indicators.append('medicine_available')
                explanation.append('Related medicines or supplies are available')

            score += facility.readiness / 10
            score -= facility.queue_minutes / 8
            score -= facility.travel_minutes / 25
            matches.append(
                CareMatch(
                    facility_id=facility.facility_id,
                    facility_name=facility.facility_name,
                    matched_services=services,
                    specialists=specialists,
                    diagnostics=diagnostics,
                    medicines=medicines,
                    suitability_indicators=indicators,
                    explanation=explanation,
                    match_score=round(max(0, min(score, 100)), 2),
                    queue_minutes=facility.queue_minutes,
                    travel_minutes=facility.travel_minutes,
                    readiness=facility.readiness,
                    reason=explanation,
                )
            )

        return sorted(matches, key=lambda item: item.match_score, reverse=True)
