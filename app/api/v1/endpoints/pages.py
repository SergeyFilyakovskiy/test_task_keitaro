from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parents[3] / "templates")
)



@router.get("/campaigns/{campaign_id}", include_in_schema=False)
async def campaign_page(request: Request, campaign_id: int):
    return templates.TemplateResponse(
        request, "campaign.html", {"request": request, "campaign_id": campaign_id}
    )


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Заглушка, чтобы не было 404 в логах."""
    return Response(status_code=204)

@router.get("/", include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})