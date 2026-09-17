from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from services.api.app.main import app


client = TestClient(app)


def test_golden_continuity_lifecycle_and_failure_cases():
    client.post('/api/v1/demo/reset')
    patient = client.get('/api/v1/patients/pat-ravi')
    assert patient.status_code == 200
    assert client.get('/api/v1/patients/not-found').status_code == 404

    request = client.post('/api/v1/care-requests', json={
        'patient_id': 'pat-ravi',
        'requester_id': 'asha-demo',
        'symptoms': 'cardiology review',
        'duration': '2 days',
        'urgency_indicators': ['chest pain'],
        'location': 'Ghatol',
        'preferred_language': 'hi',
    })
    assert request.status_code == 201
    referral = client.post('/api/v1/referrals', json={
        'patient_id': 'pat-ravi',
        'destination': 'District Hospital, Udaipur',
    }).json()
    referral_id = referral['referral_id']
    assert client.post(f'/api/v1/referrals/{referral_id}/transition', json={
        'state': 'scheduled',
        'description': 'invalid skip',
    }).status_code == 409
    for state in ['destination_identified', 'accepted', 'scheduled', 'arrived', 'care_completed', 'closed', 'follow_up']:
        response = client.post(f'/api/v1/referrals/{referral_id}/transition', json={
            'state': state,
            'description': state,
        })
        assert response.status_code == 200

    follow_ups = client.get('/api/v1/followups', params={'patient_id': 'pat-ravi'})
    assert follow_ups.status_code == 200
    generated = [item for item in follow_ups.json() if item.get('referral_id') == referral_id]
    assert generated
    follow_up_id = generated[0]['follow_up_id']
    assert client.post(f'/api/v1/followups/{follow_up_id}/complete').status_code == 200
    assert client.post(f'/api/v1/followups/{follow_up_id}/complete').status_code == 409
    assert client.get('/api/v1/followups/not-found').status_code == 404

    starts_at = (datetime.now(timezone.utc) + timedelta(days=2)).replace(hour=9, minute=0, second=0, microsecond=0)
    appointment = client.post('/api/v1/appointments', json={
        'patient_id': 'pat-ravi',
        'facility_id': 'fac-udaipur-dh',
        'provider_id': 'provider-1',
        'service': 'cardiology',
        'starts_at': starts_at.isoformat(),
    })
    assert appointment.status_code == 201
    appointment_id = appointment.json()['appointment_id']
    assert client.post(f'/api/v1/appointments/{appointment_id}/transition', json={'status': 'completed'}).status_code == 200
    assert client.post(f'/api/v1/appointments/{appointment_id}/transition', json={'status': 'completed'}).status_code == 409
    assert client.post('/api/v1/appointments/not-found/transition', json={'status': 'completed'}).status_code == 404

    assert client.post('/api/v1/demo/reset').json()['status'] == 'reset'
    assert client.get('/api/v1/referrals').json() == []
    assert client.get('/api/v1/appointments').json() == []
