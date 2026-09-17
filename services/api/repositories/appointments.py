from __future__ import annotations

from services.api.domain.models import Appointment
from services.api.persistence import appointment_from_row, postgres_store


class AppointmentRepository:
    def __init__(self) -> None:
        self._items: dict[str, Appointment] = {}

    def add(self, appointment: Appointment) -> Appointment:
        if postgres_store:
            postgres_store.execute(
                """
                INSERT INTO appointments (
                    appointment_id, patient_id, facility_id, provider_id, service,
                    starts_at, status, estimated_wait_minutes
                ) VALUES (
                    :appointment_id, :patient_id, :facility_id, :provider_id, :service,
                    :starts_at, :status, :estimated_wait_minutes
                )
                """,
                appointment.model_dump(),
            )
            return appointment
        self._items[appointment.appointment_id] = appointment
        return appointment

    def get(self, appointment_id: str) -> Appointment | None:
        if postgres_store:
            rows = postgres_store.execute(
                'SELECT * FROM appointments WHERE appointment_id = :appointment_id',
                {'appointment_id': appointment_id},
            )
            return appointment_from_row(rows[0]) if rows else None
        return self._items.get(appointment_id)

    def all(self) -> list[Appointment]:
        if postgres_store:
            return [appointment_from_row(row) for row in postgres_store.execute('SELECT * FROM appointments')]
        return list(self._items.values())

    def reset_demo(self) -> None:
        if postgres_store:
            return
        self._items.clear()


appointment_repository = AppointmentRepository()
