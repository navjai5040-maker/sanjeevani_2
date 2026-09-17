from __future__ import annotations

from services.api.domain.models import Patient


class PatientRepository:
    def __init__(self, patients: list[Patient]) -> None:
        self._items = {patient.id: patient for patient in patients}

    def list(self, query: str | None = None) -> list[Patient]:
        patients = list(self._items.values())
        if query:
            needle = query.casefold()
            patients = [patient for patient in patients if needle in patient.name.casefold() or needle in patient.village.casefold()]
        return patients

    def get(self, patient_id: str) -> Patient | None:
        return self._items.get(patient_id)


patient_repository = PatientRepository([
    Patient(id='pat-ravi', name='Ravi Meena', age=42, sex='male', village='Ghatol', preferred_language='hi', demo_contact='demo-ravi', risk_level='medium'),
    Patient(id='pat-sita', name='Sita Devi', age=29, sex='female', village='Banswara', preferred_language='hi', demo_contact='demo-sita', risk_level='high'),
    Patient(id='pat-aman', name='Aman Khan', age=8, sex='male', village='Ghatol', preferred_language='hi', demo_contact='demo-aman', risk_level='low'),
    Patient(id='pat-meera', name='Meera Sharma', age=34, sex='female', village='Dungarpur', preferred_language='en', demo_contact='demo-meera', risk_level='high'),
])
