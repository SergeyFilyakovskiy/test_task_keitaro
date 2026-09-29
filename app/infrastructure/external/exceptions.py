class KeitaroAPIError(Exception):
    """Базовая ошибка Keitaro API."""

    def __init__(self, status_code: int, message: str, response_data: dict | None = None):
        self.status_code = status_code
        self.message = message
        self.response_data = response_data
        super().__init__(f"Keitaro API error [{status_code}]: {message}")


class KeitaroNotFoundError(KeitaroAPIError):
    """404 — сущность не найдена."""
    pass


class KeitaroAuthError(KeitaroAPIError):
    """401/402 — проблемы с доступом."""
    pass