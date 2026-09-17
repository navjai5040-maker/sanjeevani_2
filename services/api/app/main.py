from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.routers.care import router as care_router
from services.api.routers.care_requests import router as care_request_router
from services.api.routers.facilities import router as facility_router
from services.api.routers.appointments import router as appointment_router
from services.api.routers.health import router as health_router
from services.api.routers.referrals import router as referral_router
from services.api.routers.demo import router as demo_router
from services.api.routers.patients import router as patient_router
from services.api.routers.followups import router as follow_up_router
from services.api.persistence import postgres_store
from services.api.repositories.facilities import facility_repository

app = FastAPI(
    title='Sanjeevani API',
    description='Healthcare coordination API for referrals, triage, and care matching.',
    version='0.1.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5173',
        'http://127.0.0.1:5173',
    ],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health_router)
app.include_router(care_request_router)
app.include_router(care_router)
app.include_router(facility_router)
app.include_router(appointment_router)
app.include_router(referral_router)
app.include_router(demo_router)
app.include_router(patient_router)
app.include_router(follow_up_router)


@app.on_event('startup')
def initialize_persistence() -> None:
    if postgres_store:
        postgres_store.initialize()
        facility_repository.seed()


@app.get('/')
def root() -> dict[str, str]:
    return {'message': 'Welcome to Sanjeevani'}
