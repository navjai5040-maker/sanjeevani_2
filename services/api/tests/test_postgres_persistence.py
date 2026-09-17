import os
from datetime import datetime, timezone

import pytest

from services.api.domain.models import Referral
from services.api.persistence import PostgresStore


pytestmark = pytest.mark.skipif(
    os.getenv('PERSISTENCE_BACKEND', '').lower() != 'postgres',
    reason='PostgreSQL integration tests require PERSISTENCE_BACKEND=postgres',
)


def test_referral_survives_a_new_store_instance():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        pytest.fail('DATABASE_URL is required for the PostgreSQL integration test')

    first_store = PostgresStore(database_url)
    first_store.initialize()
    referral = Referral(
        referral_id='ref-persistence-test',
        patient_id='pat-persistence-test',
        destination='District Hospital, Udaipur',
        created_at=datetime.now(timezone.utc),
    )
    first_store.execute(
        """
        INSERT INTO referrals (referral_id, patient_id, destination, state, created_at)
        VALUES (:referral_id, :patient_id, :destination, :state, :created_at)
        ON CONFLICT (referral_id) DO UPDATE SET destination = EXCLUDED.destination
        """,
        referral.model_dump(),
    )

    second_store = PostgresStore(database_url)
    rows = second_store.execute(
        'SELECT referral_id, destination FROM referrals WHERE referral_id = :referral_id',
        {'referral_id': referral.referral_id},
    )
    assert rows == [{'referral_id': referral.referral_id, 'destination': referral.destination}]
    second_store.execute(
        'DELETE FROM referrals WHERE referral_id = :referral_id',
        {'referral_id': referral.referral_id},
    )
