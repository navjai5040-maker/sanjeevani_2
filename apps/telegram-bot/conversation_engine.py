from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class Intent(str, Enum):
    FIND_CARE = "FIND_CARE"
    TRIAGE_HELP = "TRIAGE_HELP"
    FACILITY_SEARCH = "FACILITY_SEARCH"
    APPOINTMENT_LOOKUP = "APPOINTMENT_LOOKUP"
    APPOINTMENT_BOOK = "APPOINTMENT_BOOK"
    REFERRAL_STATUS = "REFERRAL_STATUS"
    FOLLOWUP_STATUS = "FOLLOWUP_STATUS"
    FOLLOWUP_COMPLETE = "FOLLOWUP_COMPLETE"
    FACILITY_INFORMATION = "FACILITY_INFORMATION"
    FACILITY_COMPARISON = "FACILITY_COMPARISON"
    CARE_REQUEST_STATUS = "CARE_REQUEST_STATUS"
    HELP = "HELP"
    CANCEL = "CANCEL"
    GREETING = "GREETING"
    UNKNOWN = "UNKNOWN"


@dataclass
class Entities:
    symptoms: str | None = None
    duration: str | None = None
    location: str | None = None
    patient_name: str | None = None
    patient_id: str | None = None
    care_type: str | None = None
    specialty: str | None = None
    diagnostic_service: str | None = None
    date: str | None = None
    time: str | None = None
    language: str | None = None
    referral_id: str | None = None
    appointment_context: str | None = None


@dataclass
class Understanding:
    intent: Intent
    entities: Entities = field(default_factory=Entities)
    missing: list[str] = field(default_factory=list)


PATIENTS = {
    "ravi": ("Ravi", "pat-ravi"),
    "ravi meena": ("Ravi Meena", "pat-ravi"),
    "sita": ("Sita", "pat-sita"),
    "aman": ("Aman", "pat-aman"),
    "meera": ("Meera", "pat-meera"),
}


class ConversationEngine:
    """Stable boundary for deterministic understanding and a future optional LLM."""

    def understand(self, message: str) -> Understanding:
        entities = self.extract_entities(message)
        intent = self.classify(message, entities)
        missing: list[str] = []
        if intent in {Intent.FIND_CARE, Intent.TRIAGE_HELP, Intent.FACILITY_SEARCH}:
            if not entities.symptoms and not entities.care_type and not entities.diagnostic_service and not entities.specialty:
                missing.append("symptoms or care type")
            if not entities.duration:
                missing.append("duration")
            if not entities.location:
                missing.append("location")
        return Understanding(intent=intent, entities=entities, missing=missing)

    def classify(self, message: str, entities: Entities | None = None) -> Intent:
        text = self._normalize(message)
        entities = entities or self.extract_entities(message)
        if not text:
            return Intent.UNKNOWN
        if self._has(text, "cancel", "stop", "never mind", " छोड़"):
            return Intent.CANCEL
        if self._has(text, "follow-up complete", "followup complete", "completed my follow", "follow-up done"):
            return Intent.FOLLOWUP_COMPLETE
        if self._has(text, "follow-up", "followup", "what is due", "anything due", "follow-up kab", "kab hai"):
            return Intent.FOLLOWUP_STATUS
        if self._has(text, "referral", "referred", "hospital accepted", "kahan tak pahucha", "pahucha", "next kya karna"):
            return Intent.REFERRAL_STATUS
        if self._has(text, "koi aur option", "another option", "alternative", "why is the first", "why this facility"):
            return Intent.FACILITY_COMPARISON
        if self._has(text, "appointment", "doctor tomorrow", "see a doctor", "book a doctor", "book ravi", "kal appointment"):
            if self._has(text, "need", "book", "make", "want", "tomorrow", "today", "chahiye", "kal"):
                return Intent.APPOINTMENT_BOOK
            return Intent.APPOINTMENT_LOOKUP
        if self._has(text, "facility information", "hospital information", "opening", "facility details", "specialist ke liye"):
            return Intent.FACILITY_INFORMATION
        if self._has(text, "x-ray", "xray", "diagnostic", "where should i go", "which hospital", "which facility", "kahan milega", "kaunsa hospital"):
            return Intent.FACILITY_SEARCH
        if self._has(text, "help", "what can you do", "menu"):
            return Intent.HELP
        if self._has(text, "request status", "care request", "what happened with my request"):
            return Intent.CARE_REQUEST_STATUS
        if entities.symptoms or entities.care_type or entities.specialty or self._has(text, "doctor", "care", "treatment"):
            return Intent.FIND_CARE
        if self._has(text, "hello", "hi", "namaste", "good morning", "good evening"):
            return Intent.GREETING
        return Intent.UNKNOWN

    def extract_entities(self, message: str) -> Entities:
        text = message.strip()
        normalized = self._normalize(text)
        entities = Entities(language=self.detect_language(text))

        for key, (name, patient_id) in PATIENTS.items():
            if re.search(rf"\b{re.escape(key)}\b", normalized):
                entities.patient_name = name
                entities.patient_id = patient_id
                break

        location = re.search(r"\b(?:near|from|in|at)\s+([A-Za-z][A-Za-z -]{1,40}?)(?:\s+and|\s+I\b|,|\.|$)", text, re.IGNORECASE)
        if location:
            entities.location = location.group(1).strip()
        else:
            hindi_location = re.search(r"\b(?:mein|me|se)\s+([A-Za-z][A-Za-z -]{1,30}?)(?:\s+hai|\s+hain|\s+and|,|\.|$)", text, re.IGNORECASE)
            if hindi_location:
                entities.location = hindi_location.group(1).strip()
            else:
                near_location = re.search(r"\b([A-Za-z][A-Za-z -]{1,30}?)\s+ke paas\b", text, re.IGNORECASE)
                if near_location:
                    entities.location = near_location.group(1).strip()
        if not entities.location and re.search(r"\bghatol\b", normalized):
            entities.location = "Ghatol"

        duration = re.search(
            r"\b(?:for|since)\s+((?:the\s+)?(?:last\s+)?(?:\d+|one|two|three|four|five|six|a few)\s+(?:minutes?|hours?|days?|weeks?|months?|years?)|this morning|today|yesterday|subah se)",
            text,
            re.IGNORECASE,
        )
        if duration:
            entities.duration = duration.group(1).strip()
        elif "few months" in normalized:
            entities.duration = "a few months"
        elif "subah se" in normalized:
            entities.duration = "since this morning"

        if "x-ray" in normalized or "xray" in normalized:
            entities.diagnostic_service = "X-ray"
            entities.care_type = "diagnostic service"
        for specialty in ("cardiology", "diabetes", "diabetic", "general doctor", "pediatrician"):
            if specialty in normalized:
                entities.specialty = specialty
                entities.care_type = specialty
                break
        if not entities.specialty and "chest pain" in normalized:
            entities.specialty = "cardiology"
            entities.care_type = "cardiology"

        symptom_terms = (
            "chest pain",
            "high fever",
            "severe pain",
            "severe breathing difficulty",
            "unconscious",
            "heavy bleeding",
            "cough",
        )
        for symptom in symptom_terms:
            if symptom in normalized:
                entities.symptoms = symptom
                break
        if not entities.symptoms and entities.care_type and entities.care_type not in {"diagnostic service"}:
            entities.symptoms = entities.care_type

        if "tomorrow" in normalized or "kal" in normalized:
            entities.date = "tomorrow"
        elif "today" in normalized:
            entities.date = "today"
        time = re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", normalized)
        if time:
            entities.time = time.group(1)
        return entities

    @staticmethod
    def detect_language(message: str) -> str:
        normalized = message.lower()
        if any(word in normalized for word in ("mujhe", "chahiye", "kal", "seene", "dard", "hai", "namaste")):
            return "hi"
        return "en"

    @staticmethod
    def _normalize(message: str) -> str:
        return re.sub(r"\s+", " ", message.strip().lower())

    @staticmethod
    def _has(text: str, *phrases: str) -> bool:
        return any(phrase in text for phrase in phrases)
