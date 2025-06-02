# app/api/v1/health.py

from fastapi import APIRouter, Response, status

router = APIRouter()

@router.get("/health/live")
def liveness_probe():
    """
    Liveness probe: indicates if application process is up.
    """
    return Response(
        status_code=status.HTTP_200_OK,
        headers={"Access-Control-Allow-Origin": "*"},
    )

@router.get("/health/ready")
def readiness_probe():
    """
    Readiness probe: indicates if application is ready to serve traffic.
    Here, always returns ready; extend with dependency checks as needed.
    """
    return Response(
        status_code=status.HTTP_200_OK,
        headers={"Access-Control-Allow-Origin": "*"},
    )
