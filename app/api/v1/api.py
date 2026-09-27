from fastapi import APIRouter
from app.api.v1.endpoints.verification import router as verification_router

api_router = APIRouter()
api_router.include_router(verification_router, prefix="/corporate", tags=["Corporate Verification"])