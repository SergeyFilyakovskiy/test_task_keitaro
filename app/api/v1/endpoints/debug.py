import asyncio

from fastapi import APIRouter, Depends

from app.core.dependencies import get_keitaro
from app.infrastructure.external.keitaro_client import KeitaroClient

router = APIRouter()


@router.get("/debug/references")
async def get_references(client: KeitaroClient = Depends(get_keitaro)):
    """
    Dev-ручка: дампы справочников Keitaro.
    Использовать, чтобы проверить константы в app/services/keitaro_consts.py
    (имя фильтра страны, ключи action_type, схемы потоков).
    """
    filters, actions, schemas, types = await asyncio.gather(
        client.list_stream_filters(),
        client.list_stream_actions(),
        client.list_stream_schemas(),
        client.list_stream_types(),
    )
    return {
        "stream_filters": filters,
        "streams_actions": actions,
        "stream_schemas": schemas,
        "stream_types": types,
    }