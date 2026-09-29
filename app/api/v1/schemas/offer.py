from pydantic import BaseModel, Field


class OfferSearchItem(BaseModel):
    id: int
    name: str


class AddOfferRequest(BaseModel):
    offer_id: int = Field(..., description="ID оффера Keitaro")


class PinOfferRequest(BaseModel):
    share: int = Field(..., ge=0, le=100, description="Фиксированный вес, %")