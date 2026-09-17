from fastapi import APIRouter

router = APIRouter(prefix='/healthz', tags=['health'])


@router.get('/')
def health_check() -> dict[str, str]:
    return {'status': 'ok', 'service': 'sanjeevani-api'}
