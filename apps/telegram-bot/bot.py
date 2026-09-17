from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from conversation_engine import ConversationEngine, Entities, Intent


MENU = (
    "1. Find Care\n"
    "2. My Appointment\n"
    "3. My Referral\n"
    "4. Follow-up\n"
    "5. Facility Information\n"
    "6. Help"
)


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        body = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                return json.loads(response.read().decode())
        except Exception as exc:
            raise ApiError(f"Unable to reach SANJEEVANI API: {exc}") from exc

    def create_care_request(self, patient_id: str, symptoms: str, duration: str, location: str, required_service: str | None = None) -> dict[str, Any]:
        payload = {
            "patient_id": patient_id,
            "requester_id": f"telegram-{patient_id}",
            "symptoms": symptoms,
            "duration": duration,
            "urgency_indicators": [symptoms] if symptoms else [],
            "location": location,
            "preferred_language": "en",
        }
        if required_service:
            payload["required_service"] = required_service
        return self.request("POST", "/api/v1/care-requests", payload)

    def triage(self, request: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/api/v1/triage", request)

    def matches(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        params = urllib.parse.urlencode({
            "patient_id": request["patient_id"],
            "requester_id": request["requester_id"],
            "symptoms": request["symptoms"],
            "duration": request["duration"],
            "location": request["location"],
            "preferred_language": request.get("preferred_language", "en"),
            "required_service": request.get("required_service", ""),
        })
        return self.request("GET", f"/api/v1/facilities/matches?{params}")

    def facilities(self) -> list[dict[str, Any]]:
        return self.request("GET", "/api/v1/facilities")

    def referrals(self, patient_id: str) -> list[dict[str, Any]]:
        return [item for item in self.request("GET", "/api/v1/referrals") if item["patient_id"] == patient_id]

    def create_referral(self, patient_id: str, destination: str) -> dict[str, Any]:
        return self.request("POST", "/api/v1/referrals", {"patient_id": patient_id, "destination": destination})

    def referral_events(self, referral_id: str) -> list[dict[str, Any]]:
        return self.request("GET", f"/api/v1/referrals/{referral_id}/events")

    def appointments(self, patient_id: str) -> list[dict[str, Any]]:
        return [item for item in self.request("GET", "/api/v1/appointments") if item["patient_id"] == patient_id]

    def slots(self, facility_id: str, service: str, date: datetime) -> list[dict[str, Any]]:
        query = urllib.parse.urlencode({"facility_id": facility_id, "service": service, "date": date.isoformat()})
        return self.request("GET", f"/api/v1/appointments/slots?{query}")

    def book_appointment(self, patient_id: str, slot: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/api/v1/appointments", {
            "patient_id": patient_id,
            "facility_id": slot["facility_id"],
            "provider_id": slot["provider_id"],
            "service": slot["service"],
            "starts_at": slot["starts_at"],
        })

    def followups(self, patient_id: str) -> list[dict[str, Any]]:
        return self.request("GET", f"/api/v1/followups?patient_id={urllib.parse.quote(patient_id)}")

    def complete_followup(self, follow_up_id: str) -> dict[str, Any]:
        return self.request("POST", f"/api/v1/followups/{follow_up_id}/complete")


class MockApiClient(ApiClient):
    def __init__(self) -> None:
        super().__init__("mock://sanjeevani")
        self._referral = {
            "referral_id": "ref-telegram-demo",
            "patient_id": "pat-ravi",
            "destination": "District Hospital, Udaipur",
            "state": "created",
        }
        self._followup = {
            "follow_up_id": "fu-ravi-demo",
            "patient_id": "pat-ravi",
            "due_date": "2026-09-16T09:00:00Z",
            "reason": "Blood-pressure follow-up",
            "priority": "high",
            "status": "due",
            "next_action": "Contact patient and review progress",
        }
        self._appointments: list[dict[str, Any]] = []

    def create_care_request(self, patient_id: str, symptoms: str, duration: str, location: str, required_service: str | None = None) -> dict[str, Any]:
        return {
            "request_id": "req-telegram-demo",
            "patient_id": patient_id,
            "requester_id": f"telegram-{patient_id}",
            "symptoms": symptoms,
            "duration": duration,
            "urgency_indicators": [symptoms] if symptoms else [],
            "location": location,
            "preferred_language": "en",
            "required_service": required_service,
        }

    def triage(self, request: dict[str, Any]) -> dict[str, Any]:
        symptom = request["symptoms"].lower()
        emergency = symptom in {"severe breathing difficulty", "unconscious", "heavy bleeding"}
        urgent = symptom in {"chest pain", "high fever", "severe pain"}
        return {
            "request_id": request["request_id"],
            "level": "emergency" if emergency else "urgent" if urgent else "routine",
            "rationale": (
                ["Emergency indicator requires immediate escalation"]
                if emergency
                else ["Urgency indicator requires prompt clinical review"]
                if urgent
                else ["Routine care guidance"]
            ),
            "requires_emergency_escalation": emergency,
        }

    def matches(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        return [{
            "facility_id": "fac-udaipur-dh",
            "facility_name": "District Hospital, Udaipur",
            "match_score": 94,
            "specialists": ["cardiology"],
            "diagnostics": ["ECG", "laboratory"],
            "explanation": ["Required service and specialist are available", "Readiness is acceptable"],
            "queue_minutes": 28,
            "travel_minutes": 45,
            "readiness": 92,
        }]

    def facilities(self) -> list[dict[str, Any]]:
        return [{"facility_name": "District Hospital, Udaipur", "readiness": 92, "queue_minutes": 28}]

    def referrals(self, patient_id: str) -> list[dict[str, Any]]:
        return [self._referral] if patient_id == "pat-ravi" else []

    def create_referral(self, patient_id: str, destination: str) -> dict[str, Any]:
        self._referral["patient_id"] = patient_id
        self._referral["destination"] = destination
        return self._referral

    def referral_events(self, referral_id: str) -> list[dict[str, Any]]:
        return [{"state": self._referral["state"], "description": "Referral created", "timestamp": datetime.now(timezone.utc).isoformat()}]

    def appointments(self, patient_id: str) -> list[dict[str, Any]]:
        return [item for item in self._appointments if item["patient_id"] == patient_id]

    def slots(self, facility_id: str, service: str, date: datetime) -> list[dict[str, Any]]:
        return [
            {
                "slot_id": f"{facility_id}-0900",
                "facility_id": facility_id,
                "provider_id": "provider-1",
                "service": service,
                "starts_at": date.replace(hour=9, minute=0, second=0, microsecond=0).isoformat(),
                "estimated_wait_minutes": 28,
                "status": "available",
            },
            {
                "slot_id": f"{facility_id}-1100",
                "facility_id": facility_id,
                "provider_id": "provider-2",
                "service": service,
                "starts_at": date.replace(hour=11, minute=0, second=0, microsecond=0).isoformat(),
                "estimated_wait_minutes": 28,
                "status": "available",
            },
        ]

    def book_appointment(self, patient_id: str, slot: dict[str, Any]) -> dict[str, Any]:
        appointment = {
            "appointment_id": "appt-telegram-demo",
            "patient_id": patient_id,
            "facility_id": slot["facility_id"],
            "provider_id": slot["provider_id"],
            "service": slot["service"],
            "starts_at": slot["starts_at"],
            "status": "booked",
            "estimated_wait_minutes": slot.get("estimated_wait_minutes", 0),
        }
        self._appointments.append(appointment)
        return appointment

    def followups(self, patient_id: str) -> list[dict[str, Any]]:
        return [self._followup] if patient_id == "pat-ravi" else []

    def complete_followup(self, follow_up_id: str) -> dict[str, Any]:
        if follow_up_id != self._followup["follow_up_id"]:
            raise ApiError("Follow-up not found")
        self._followup["status"] = "completed"
        self._followup["completed_at"] = datetime.now(timezone.utc).isoformat()
        return self._followup


@dataclass
class ChatState:
    step: str = "menu"
    patient_id: str = "pat-ravi"
    request: dict[str, Any] | None = None
    matches: list[dict[str, Any]] = field(default_factory=list)
    current_intent: Intent = Intent.UNKNOWN
    pending_questions: list[str] = field(default_factory=list)
    entities: Entities = field(default_factory=Entities)
    selected_facility: dict[str, Any] | None = None
    language: str = "en"
    natural_find_care: bool = False
    pending_action: str | None = None
    selected_slot: dict[str, Any] | None = None
    appointment_slots: list[dict[str, Any]] = field(default_factory=list)
    pending_followup_id: str | None = None


class ConversationBot:
    def __init__(self, api: ApiClient) -> None:
        self.api = api
        self.chats: dict[str, ChatState] = {}
        self.engine = ConversationEngine()

    def state(self, chat_id: str) -> ChatState:
        return self.chats.setdefault(chat_id, ChatState())

    def handle(self, chat_id: str, text: str) -> str:
        state = self.state(chat_id)
        message = text.strip()
        if message in {"/start", "/menu", "0"}:
            state.step = "menu"
            return "SANJEEVANI demo access\n\nCare coordination, not diagnosis.\n\n" + MENU
        try:
            understanding = self.engine.understand(message)
            actionable_intents = {
                Intent.REFERRAL_STATUS,
                Intent.FOLLOWUP_STATUS,
                Intent.FOLLOWUP_COMPLETE,
                Intent.FACILITY_COMPARISON,
                Intent.FACILITY_SEARCH,
                Intent.FACILITY_INFORMATION,
                Intent.APPOINTMENT_LOOKUP,
                Intent.APPOINTMENT_BOOK,
            }
            if state.pending_action and understanding.intent in actionable_intents:
                state.pending_action = None
                state.selected_slot = None
                state.pending_followup_id = None
                state.step = "menu"
            if state.pending_followup_id and message.lower() in {"yes", "y", "confirm", "complete"}:
                return self.confirm_followup_completion(state, message)
            if state.pending_action == "appointment_confirmation":
                return self.confirm_appointment(state, message)
            if state.pending_action == "appointment_slot":
                return self.select_appointment_slot(state, message)
            if state.pending_action == "appointment_service":
                return self.continue_appointment_service(state, message)
            if state.pending_action == "appointment_date":
                return self.continue_appointment_date(state, message)
            if state.step == "menu" and understanding.intent not in {Intent.UNKNOWN, Intent.GREETING, Intent.HELP}:
                return self.handle_natural_intent(state, message, understanding)
            if state.step == "menu" and understanding.intent == Intent.GREETING:
                return "Namaste. I can help find care, check appointments, track referrals, or review follow-ups.\n\n" + MENU
            if state.step == "menu":
                return self.menu(state, message)
            if state.natural_find_care and state.step in {"symptoms", "duration", "location"}:
                return self.continue_natural_find_care(state, message, understanding.entities)
            if state.step == "symptoms":
                state.request = self.api.create_care_request(state.patient_id, message, "today", "Ghatol")
                triage = self.api.triage(state.request)
                state.matches = self.api.matches(state.request)
                response = self.triage_text(triage)
                if triage.get("requires_emergency_escalation"):
                    state.step = "menu"
                    return response
                state.step = "match"
                return response + "\n\nSuitable facilities:\n" + self.match_text(state.matches)
            if state.step == "match":
                selected = state.matches[0] if state.matches else None
                if selected:
                    if message.lower() in {"referral", "create referral", "2"}:
                        referral = self.api.create_referral(state.patient_id, selected["facility_name"])
                        state.step = "menu"
                        return f"Referral created for {referral['destination']}.\nStatus: {referral['state']}\n\n" + MENU
                    return f"Why this facility?\n{selected['facility_name']}\n" + "\n".join(f"- {item}" for item in selected.get("explanation", [])) + "\n\nReply 'referral' to create a referral, or /menu for more actions."
                state.step = "menu"
                return "No suitable facility was found.\n\n" + MENU
            if state.step == "followup":
                followups = self.api.followups(state.patient_id)
                item = next((item for item in followups if item["status"] != "completed"), None)
                if item and message.lower() in {"complete", "done", "1"}:
                    completed = self.api.complete_followup(item["follow_up_id"])
                    state.step = "menu"
                    return f"Follow-up marked completed at {completed.get('completed_at', 'now')}.\n\n" + MENU
                return self.followup_text(followups) + "\nReply 'complete' to finish the open follow-up."
            return "Please choose an option.\n\n" + MENU
        except ApiError as exc:
            state.step = "menu"
            return f"{exc}\n\nPlease try again later. This bot does not provide a diagnosis."

    def menu(self, state: ChatState, message: str) -> str:
        if message in {"1", "find care", "Find Care"}:
            state.step = "symptoms"
            return "What care concern should we coordinate? For example: chest pain\n\nDecision-support guidance - not a diagnosis."
        if message in {"2", "my appointment", "My Appointment"}:
            appointments = self.api.appointments(state.patient_id)
            return self.appointment_text(appointments) + "\n\n" + MENU
        if message in {"3", "my referral", "My Referral"}:
            referrals = self.api.referrals(state.patient_id)
            return self.referral_text(referrals) + "\n\n" + MENU
        if message in {"4", "follow-up", "Follow-up"}:
            state.step = "followup"
            return self.followup_text(self.api.followups(state.patient_id)) + "\nReply 'complete' to finish the open follow-up."
        if message in {"5", "facility information", "Facility Information"}:
            return self.facility_text(self.api.facilities()) + "\n\n" + MENU
        if message in {"6", "help", "Help"}:
            return "Reply with a menu number. Find Care collects only the concern, duration, and location.\n\n" + MENU
        return "Please choose a menu option.\n\n" + MENU

    def handle_natural_intent(self, state: ChatState, message: str, understanding: Any) -> str:
        state.current_intent = understanding.intent
        for field_name, value in vars(understanding.entities).items():
            if value:
                setattr(state.entities, field_name, value)
        state.language = understanding.entities.language or "en"
        if understanding.entities.patient_id:
            state.patient_id = understanding.entities.patient_id
        if understanding.intent in {Intent.APPOINTMENT_LOOKUP, Intent.APPOINTMENT_BOOK}:
            return self.start_appointment_flow(state, understanding.entities, understanding.intent == Intent.APPOINTMENT_BOOK)
        if understanding.intent == Intent.FACILITY_COMPARISON:
            return self.handle_facility_comparison(state, message)
        if understanding.intent in {Intent.FIND_CARE, Intent.TRIAGE_HELP, Intent.FACILITY_SEARCH}:
            state.natural_find_care = True
            state.step = "symptoms"
            return self.continue_natural_find_care(state, message, understanding.entities)
        if understanding.intent == Intent.REFERRAL_STATUS:
            return self.handle_referral_status(state)
        if understanding.intent in {Intent.FOLLOWUP_STATUS, Intent.FOLLOWUP_COMPLETE}:
            return self.handle_followup_status(state, message, understanding.intent == Intent.FOLLOWUP_COMPLETE)
        if understanding.intent == Intent.CANCEL:
            state.step = "menu"
            state.natural_find_care = False
            return "Okay, I stopped that request.\n\n" + MENU
        return self.menu(state, self.intent_menu_value(understanding.intent))

    def start_appointment_flow(self, state: ChatState, entities: Entities, booking: bool) -> str:
        service = entities.specialty or entities.care_type or entities.diagnostic_service
        if not service and state.request:
            service = state.request.get("symptoms")
        if not service:
            state.pending_action = "appointment_service"
            state.current_intent = Intent.APPOINTMENT_BOOK if booking else Intent.APPOINTMENT_LOOKUP
            return "What service or type of doctor do you need?"
        date = self.appointment_date(entities.date)
        if date is None:
            state.pending_action = "appointment_date"
            state.entities.care_type = service
            return "Which date would you prefer? For example, tomorrow."
        return self.load_appointment_slots(state, service, date, booking)

    def continue_appointment_service(self, state: ChatState, message: str) -> str:
        extracted = self.engine.extract_entities(message)
        service = extracted.specialty or extracted.care_type or extracted.diagnostic_service or message.strip()
        state.entities.specialty = extracted.specialty
        state.entities.care_type = service
        state.pending_action = "appointment_date"
        return "Which date would you prefer? For example, tomorrow."

    def continue_appointment_date(self, state: ChatState, message: str) -> str:
        extracted = self.engine.extract_entities(message)
        date = self.appointment_date(extracted.date)
        if date is None:
            return "Please provide a date such as today or tomorrow."
        state.entities.date = extracted.date
        service = state.entities.specialty or state.entities.care_type or state.entities.diagnostic_service
        if not service:
            state.pending_action = "appointment_service"
            return "What service or type of doctor do you need?"
        return self.load_appointment_slots(state, service, date, True)

    def load_appointment_slots(self, state: ChatState, service: str, date: datetime, booking: bool) -> str:
        facility = state.selected_facility
        if facility is None and state.matches:
            facility = state.matches[0]
        if facility is None:
            request = self.api.create_care_request(state.patient_id, service, "today", state.entities.location or "Ghatol")
            state.request = request
            state.matches = self.api.matches(request)
            facility = state.matches[0] if state.matches else None
        if facility is None:
            state.pending_action = None
            return "I could not find a matching facility for that service."
        state.selected_facility = facility
        facility_id = facility.get("facility_id")
        state.appointment_slots = [
            slot for slot in self.api.slots(facility_id, service, date)
            if slot.get("status", "available") == "available"
        ]
        if not state.appointment_slots:
            state.pending_action = None
            return "There are no available slots for that date. Please try another date."
        state.pending_action = "appointment_slot" if booking else None
        state.current_intent = Intent.APPOINTMENT_BOOK if booking else Intent.APPOINTMENT_LOOKUP
        return self.appointment_slots_text(state.appointment_slots, facility.get("facility_name", facility_id), date, booking)

    def select_appointment_slot(self, state: ChatState, message: str) -> str:
        if message.lower() in {"cancel", "stop", "never mind", "go back"}:
            state.pending_action = None
            state.selected_slot = None
            return "Okay, I cancelled the appointment request.\n\n" + MENU
        try:
            index = int(message) - 1
        except ValueError:
            return "Please reply with the number of the slot you want, or say cancel."
        if index < 0 or index >= len(state.appointment_slots):
            return "Please choose one of the listed slot numbers."
        state.selected_slot = state.appointment_slots[index]
        state.pending_action = "appointment_confirmation"
        patient = state.entities.patient_name or state.patient_id
        facility = state.selected_facility.get("facility_name", "the selected facility") if state.selected_facility else "the selected facility"
        return (
            f"You are booking {patient}'s {state.selected_slot['service']} appointment at {facility} "
            f"for {self.format_slot_time(state.selected_slot['starts_at'])}.\n\n"
            "Confirm booking? Reply yes or no."
        )

    def confirm_appointment(self, state: ChatState, message: str) -> str:
        if message.lower() in {"no", "cancel", "stop", "never mind"}:
            state.pending_action = None
            state.selected_slot = None
            return "Okay, I did not book the appointment.\n\n" + MENU
        if message.lower() not in {"yes", "y", "confirm", "book it"}:
            return "Please reply yes to confirm the booking, or no to cancel."
        if state.selected_slot is None:
            state.pending_action = None
            return "The selected slot is no longer available. Please start the appointment search again."
        appointment = self.api.book_appointment(state.patient_id, state.selected_slot)
        state.pending_action = None
        state.selected_slot = None
        return (
            f"Appointment booked for {self.entities_patient_name(state)} at "
            f"{appointment.get('facility_id', 'the facility')} on "
            f"{self.format_slot_time(appointment['starts_at'])}.\n"
            f"Status: {appointment['status']}\n\n{MENU}"
        )

    @staticmethod
    def appointment_date(value: str | None) -> datetime | None:
        if value == "tomorrow":
            return datetime.now(timezone.utc) + timedelta(days=1)
        if value == "today":
            return datetime.now(timezone.utc)
        return None

    def handle_facility_comparison(self, state: ChatState, message: str) -> str:
        if not state.matches and state.request:
            state.matches = self.api.matches(state.request)
        if not state.matches:
            return "I need a care request first so I can compare suitable facilities."
        if "why" in message.lower() or "better" in message.lower():
            first = state.matches[0]
            reasons = first.get("explanation") or first.get("reason") or []
            return f"{first['facility_name']} is ranked first because:\n" + "\n".join(f"• {reason}" for reason in reasons)
        if len(state.matches) < 2:
            return f"I found one suitable option: {state.matches[0]['facility_name']}."
        return "Another suitable option is:\n" + "\n".join(
            f"{index}. {item['facility_name']} · readiness {item.get('readiness', 0)}% · queue {item.get('queue_minutes', 0)} min"
            for index, item in enumerate(state.matches[1:], 2)
        )

    def patient_label(self, state: ChatState) -> str:
        if state.entities.patient_name:
            return state.entities.patient_name
        if state.patient_id == "pat-ravi":
            return "Ravi"
        if state.patient_id == "pat-sita":
            return "Sita"
        if state.patient_id == "pat-aman":
            return "Aman"
        if state.patient_id == "pat-meera":
            return "Meera"
        return "this patient"

    def handle_referral_status(self, state: ChatState) -> str:
        referrals = self.api.referrals(state.patient_id)
        patient_name = self.patient_label(state)
        if not referrals:
            return f"I did not find an active referral for {patient_name}."
        referral = referrals[0]
        events = self.api.referral_events(referral["referral_id"])
        states = [event["state"] for event in events]
        steps = "\n".join(f"- {item}" for item in states)
        status = referral.get("state", "created")
        if status == "scheduled":
            next_step = "Next step: attend the scheduled hospital visit."
        elif status == "accepted":
            next_step = "Next step: confirm the scheduled visit."
        elif status == "closed":
            next_step = "Next step: follow-up has been generated in the system."
        elif status == "follow_up":
            next_step = "Next step: complete the generated follow-up when it is due."
        else:
            next_step = "Next step: continue with the referral journey and watch for the next update."
        return (
            f"{patient_name}'s referral:\n"
            f"Destination: {referral['destination']}\n"
            f"Status: {status}\n\n"
            f"Journey:\n{steps}\n\n{next_step}"
        )

    def handle_followup_status(self, state: ChatState, message: str, require_confirmation: bool) -> str:
        followups = self.api.followups(state.patient_id)
        patient_name = self.patient_label(state)
        if not followups:
            return f"I did not find any follow-up records for {patient_name}."
        item = next((item for item in followups if item.get("referral_id") and item.get("status") != "completed"), None)
        item = item or next((item for item in followups if item.get("status") != "completed"), None) or followups[0]
        if require_confirmation or message.lower() in {"complete", "done", "mark completed", "i completed my follow-up"}:
            state.pending_followup_id = item["follow_up_id"]
            return (
                f"Mark {patient_name}'s follow-up '{item['reason']}' as completed?\n"
                "Reply yes or no."
            )
        return (
            f"{patient_name} has one follow-up:\n"
            f"Reason: {item['reason']}\n"
            f"Status: {item['status']}\n"
            f"Priority: {item['priority']}\n"
            f"Next action: {item['next_action']}"
        )

    def confirm_followup_completion(self, state: ChatState, message: str) -> str:
        if message.lower() in {"no", "cancel", "stop", "never mind"}:
            state.pending_followup_id = None
            return "Okay, I did not mark the follow-up as completed."
        if state.pending_followup_id is None:
            return "There is no pending follow-up to complete."
        completed = self.api.complete_followup(state.pending_followup_id)
        state.pending_followup_id = None
        return (
            f"Follow-up marked completed at {completed.get('completed_at', 'now')}.\n\n"
            + MENU
        )

    @staticmethod
    def appointment_slots_text(slots: list[dict[str, Any]], facility_name: str, date: datetime, booking: bool) -> str:
        lines = [f"Available options at {facility_name} for {date:%Y-%m-%d}:"]
        lines.extend(f"{index}. {ConversationBot.format_slot_time(slot['starts_at'])}" for index, slot in enumerate(slots, 1))
        if booking:
            lines.append("Reply with a slot number to continue.")
        return "\n".join(lines)

    @staticmethod
    def format_slot_time(value: str) -> str:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d at %I:%M %p")

    def entities_patient_name(self, state: ChatState) -> str:
        return state.entities.patient_name or state.patient_id

    def continue_natural_find_care(self, state: ChatState, message: str, entities: Entities) -> str:
        extracted = self.engine.extract_entities(message)
        for field_name in ("symptoms", "duration", "location", "patient_id", "patient_name", "care_type", "specialty", "diagnostic_service", "date", "time"):
            value = getattr(extracted, field_name)
            if value:
                setattr(state.entities, field_name, value)
        if state.entities.patient_id:
            state.patient_id = state.entities.patient_id
        if state.entities.symptoms in {"unconscious", "heavy bleeding", "severe breathing difficulty"}:
            request = self.api.create_care_request(
                state.patient_id,
                state.entities.symptoms,
                state.entities.duration or "now",
                state.entities.location or "Ghatol",
            )
            state.request = request
            triage = self.api.triage(request)
            state.step = "menu"
            state.natural_find_care = False
            return self.triage_text(triage)
        if not state.entities.symptoms and not state.entities.care_type and not state.entities.diagnostic_service:
            state.step = "symptoms"
            return "What is the main health concern?"
        if state.current_intent == Intent.FACILITY_SEARCH and state.entities.diagnostic_service and not state.entities.duration:
            state.entities.duration = "today"
        if not state.entities.duration:
            state.step = "duration"
            return "I can help coordinate this. How long has this problem been present?"
        if not state.entities.location:
            state.step = "location"
            return "Where are you currently located?"
        state.step = "menu"
        state.natural_find_care = False
        request = self.api.create_care_request(
            state.patient_id,
            state.entities.symptoms or state.entities.care_type or state.entities.diagnostic_service or "care",
            state.entities.duration,
            state.entities.location,
            state.entities.specialty or state.entities.care_type or state.entities.diagnostic_service,
        )
        state.request = request
        triage = self.api.triage(request)
        state.matches = self.api.matches(request)
        response = self.triage_text(triage)
        if triage.get("requires_emergency_escalation"):
            return response
        return response + "\n\nSuitable facilities:\n" + self.match_text(state.matches)

    @staticmethod
    def intent_menu_value(intent: Intent) -> str:
        return {
            Intent.APPOINTMENT_LOOKUP: "2",
            Intent.APPOINTMENT_BOOK: "2",
            Intent.REFERRAL_STATUS: "3",
            Intent.FOLLOWUP_STATUS: "4",
            Intent.FOLLOWUP_COMPLETE: "4",
            Intent.FACILITY_INFORMATION: "5",
            Intent.HELP: "6",
        }.get(intent, "6")

    @staticmethod
    def triage_text(triage: dict[str, Any]) -> str:
        level = str(triage.get("level", "routine")).upper()
        text = f"Triage guidance: {level}\n" + "\n".join(f"- {item}" for item in triage.get("rationale", []))
        if triage.get("requires_emergency_escalation"):
            text += "\n\nPlease contact immediate human/emergency care."
        return text + "\n\nDecision-support guidance - not a diagnosis."

    @staticmethod
    def match_text(matches: list[dict[str, Any]]) -> str:
        return "\n".join(f"{index}. {item['facility_name']} | readiness {item.get('readiness', 0)}% | queue {item.get('queue_minutes', 0)} min" for index, item in enumerate(matches, 1))

    @staticmethod
    def referral_text(referrals: list[dict[str, Any]]) -> str:
        if not referrals:
            return "No referral found for the demo patient."
        referral = referrals[0]
        return f"Referral: {referral['destination']}\nStatus: {referral['state']}\nTimeline: Created → Accepted → Scheduled → Arrived → Care completed → Follow-up"

    @staticmethod
    def appointment_text(appointments: list[dict[str, Any]]) -> str:
        if not appointments:
            return "No appointment is currently booked."
        appointment = appointments[0]
        return f"Appointment: {appointment['service']} at {appointment['facility_id']}\nTime: {appointment['starts_at']}\nStatus: {appointment['status']}"

    @staticmethod
    def followup_text(followups: list[dict[str, Any]]) -> str:
        if not followups:
            return "No follow-up is currently recorded."
        return "\n".join(f"Follow-up: {item['reason']} · {item['status']} · {item['next_action']}" for item in followups)

    @staticmethod
    def facility_text(facilities: list[dict[str, Any]]) -> str:
        return "\n".join(f"{item.get('facility_name', 'Facility')} · readiness {item.get('readiness', 'demo')} · simulated state" for item in facilities)


def run_script(bot: ConversationBot, lines: list[str]) -> None:
    for line in lines:
        print(f"> {line}\n{bot.handle('demo-chat', line)}\n")


def run_telegram_polling(bot: ConversationBot, token: str) -> None:
    offset = 0
    print("Telegram polling started. Press Ctrl+C to stop.")
    while True:
        query = urllib.parse.urlencode({"timeout": 25, "offset": offset})
        try:
            with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getUpdates?{query}", timeout=35) as response:
                updates = json.loads(response.read().decode()).get("result", [])
            for update in updates:
                offset = max(offset, int(update["update_id"]) + 1)
                message = update.get("message", {})
                chat = message.get("chat", {})
                text = message.get("text")
                if not text or "id" not in chat:
                    continue
                reply = bot.handle(str(chat["id"]), text)
                payload = urllib.parse.urlencode({"chat_id": chat["id"], "text": reply}).encode()
                request = urllib.request.Request(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data=payload,
                    method="POST",
                )
                urllib.request.urlopen(request, timeout=10).read()
        except KeyboardInterrupt:
            print("Telegram polling stopped.")
            return
        except Exception as exc:
            print(f"Telegram transport error: {exc}", file=sys.stderr)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="SANJEEVANI Telegram conversational access")
    parser.add_argument("--mock", action="store_true", help="run without a Telegram token or backend")
    parser.add_argument("--script", nargs="*", help="run a local conversation script")
    args = parser.parse_args()
    mock = args.mock or os.getenv("TELEGRAM_BOT_MODE", "mock").lower() == "mock"
    api = MockApiClient() if mock else ApiClient(os.getenv("SANJEEVANI_API_BASE_URL", "http://127.0.0.1:8000"))
    bot = ConversationBot(api)
    if args.script is not None:
        run_script(bot, args.script)
        return
    if mock:
        print("Mock mode. Example: python bot.py --mock --script /start 1 'chest pain' 1")
        return
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is required when TELEGRAM_BOT_MODE=real")
    run_telegram_polling(bot, token)


if __name__ == "__main__":
    main()
