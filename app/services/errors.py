class AppError(Exception):
    """Базовая ошибка домена."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EntityNotFoundError(AppError):
    """Сущность не найдена в нашей БД."""


class FlowDirtyError(AppError):
    """Есть незапушенные изменения — операция запрещена (HTTP 409)."""


class DomainValidationError(AppError):
    """Нарушение бизнес-правил (HTTP 400)."""