from fastapi import APIRouter

from app.api.v1.endpoints import campaigns, debug, flows, offers

api_router = APIRouter()
api_router.include_router(campaigns.router, prefix="/v1", tags=["Campaigns"])
api_router.include_router(flows.router, prefix="/v1", tags=["Flows"])
api_router.include_router(offers.router, prefix="/v1", tags=["Offers"])
api_router.include_router(debug.router, prefix="/v1", tags=["Debug"])