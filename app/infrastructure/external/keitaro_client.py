import logging
from typing import Any

import httpx

from app.core.config import settings
from app.infrastructure.external.exceptions import (
    KeitaroAPIError,
    KeitaroAuthError,
    KeitaroNotFoundError,
)

logger = logging.getLogger(__name__)


class KeitaroClient:
    """Async HTTP-клиент Keitaro Admin API v1. Только используемые методы."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        self._base_url = (base_url or settings.keitaro_api_url).rstrip("/")
        self._api_key = api_key or settings.keitaro_api_key.get_secret_value()
        self._timeout = timeout

    def _build_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Api-Key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=self._timeout,
            verify=False,  # dev: у тестового Keitaro может быть кривой SSL
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        clean_path = path.lstrip("/")
        logger.debug("Keitaro %s %s params=%s json=%s", method, clean_path, params, json)

        try:
            async with self._build_client() as client:
                response = await client.request(method, path, json=json, params=params)
        except httpx.RequestError as exc:
            logger.error("Keitaro network error: %s %s — %s", method, clean_path, exc)
            raise KeitaroAPIError(
                status_code=502,
                message=f"Network error connecting to Keitaro: {exc}",
            ) from exc

        if response.status_code == 401:
            raise KeitaroAuthError(
                status_code=401,
                message=response.text or "Access denied",
            )

        if response.status_code == 404:
            raise KeitaroNotFoundError(
                status_code=404,
                message=f"Not found: {clean_path}",
            )

        if response.status_code >= 400:
            try:
                data = response.json()
            except Exception:
                data = {"raw": response.text}

            # Keitaro возвращает ошибки валидации в формате {"field": ["msg"]}
            if isinstance(data, dict):
                error_msg = (
                    data.get("error") or str(list(data.values())[0])
                    if data
                    else "Unknown error"
                )
            else:
                error_msg = str(data)

            logger.error(
                "Keitaro API error %s %s: %s", response.status_code, clean_path, error_msg
            )
            raise KeitaroAPIError(
                status_code=response.status_code,
                message=error_msg,
                response_data=data,
            )

        if response.status_code == 204 or not response.content:
            return None

        try:
            return response.json()
        except Exception:
            return response.text

    # ---------- Campaigns ----------

    async def create_campaign(self, payload: dict) -> dict:
        """POST /campaigns. payload должен содержать минимум name и alias."""
        return await self._request("POST", "/campaigns", json=payload)

    # ---------- Streams (Flows) ----------

    async def list_campaign_streams(self, campaign_id: int) -> list[dict]:
        """GET /campaigns/{id}/streams — все потоки кампании (fetch from KT)."""
        return await self._request("GET", f"/campaigns/{campaign_id}/streams")

    async def create_stream(self, payload: dict) -> dict:
        """POST /streams. Обязательные поля: campaign_id, schema, type, name, action_type."""
        return await self._request("POST", "/streams", json=payload)

    async def update_stream(self, stream_id: int, payload: dict) -> dict:
        """PUT /streams/{id} — это и есть "push to kt"."""
        return await self._request("PUT", f"/streams/{stream_id}", json=payload)

    # ---------- Offers ----------

    async def list_offers(self) -> list[dict]:
        """GET /offers — для автокомплита."""
        return await self._request("GET", "/offers")

    async def get_offer(self, offer_id: int) -> dict:
        """GET /offers/{id} — имя оффера при добавлении в поток."""
        return await self._request("GET", f"/offers/{offer_id}")

    # ---------- Справочники (резолв при создании кампании) ----------

    async def list_domains(self) -> list[dict]:
        return await self._request("GET", "/domains")

    async def list_groups(self, group_type: str) -> list[dict]:
        """group_type: campaigns | offers | landings | domains"""
        return await self._request("GET", "/groups", params={"type": group_type})

    async def create_group(self, name: str, group_type: str) -> dict:
        return await self._request(
            "POST", "/groups", json={"name": name, "type": group_type}
        )

    async def list_traffic_sources(self) -> list[dict]:
        return await self._request("GET", "/traffic_sources")

    async def create_traffic_source(self, name: str) -> dict:
        return await self._request("POST", "/traffic_sources", json={"name": name})

    # ---------- Справочники потоков (dev-ручка /debug/references) ----------

    async def list_stream_filters(self) -> list[dict]:
        return await self._request("GET", "/stream_filters")

    async def list_stream_actions(self) -> list[dict]:
        return await self._request("GET", "/streams_actions")

    async def list_stream_schemas(self) -> list[dict]:
        return await self._request("GET", "/stream_schemas")

    async def list_stream_types(self) -> list[dict]:
        return await self._request("GET", "/stream_types")
    