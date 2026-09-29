from dataclasses import dataclass
from typing import Sequence


@dataclass
class OfferWeight:
    """Модель оффера для расчёта весов."""

    offer_id: int
    is_active: bool = True  # False = локально удален (в истории, доступен через bring back)
    pinned_share: int | None = None  # Если запинен — фиксируем вес
    share: int = 0  # Текущий/результативный вес


class WeightService:
    """
    Сервис для пересчёта весов офферов в потоке.

    Правила:
    1. Сумма всех активных весов = 100%
    2. Запиненные офферы получают свой фиксированный вес
    3. Остаток (100 - сумма_запиненных) делится между незапиненными активными
    4. Остаток от деления отдаётся ПЕРВОМУ незапиненному (по position)
    5. Неактивные (is_active=False) и серые (deleted_in_keitaro=True) не участвуют в пересчёте,
       но серые сохраняют свой старый вес
    """

    @staticmethod
    def recalculate_weights(offers: Sequence[OfferWeight]) -> list[OfferWeight]:
        """
        Пересчитывает веса для списка офферов.
        
        Args:
            offers: Список офферов (должен быть отсортирован по position)
        
        Returns:
            Тот же список с обновлёнными share
        """
        if not offers:
            return list(offers)

        # Активные офферы для расчёта
        active_offers = [o for o in offers if o.is_active]
        
        if not active_offers:
            # Если нет активных, все веса = 0
            for offer in offers:
                offer.share = 0
            return list(offers)

        # 1. Считаем сумму запиненных
        pinned_sum = sum(
            o.pinned_share for o in active_offers if o.pinned_share is not None
        )
        
        # 2. Остаток для незапиненных
        remaining = 100 - pinned_sum
        
        # 3. Незапиненные активные
        unpinned_active = [o for o in active_offers if o.pinned_share is None]
        
        if unpinned_active:
            base_share = remaining // len(unpinned_active)
            remainder = remaining % len(unpinned_active)
            
            # Распределяем: первому (по position) достаётся остаток
            for i, offer in enumerate(unpinned_active):
                offer.share = base_share + (remainder if i == 0 else 0)
        
        # 4. Запиненные активные — их share = pinned_share
        for offer in active_offers:
            if offer.pinned_share is not None:
                offer.share = offer.pinned_share
        
        # 5. Неактивные (удалённые локально) — share = 0
        for offer in offers:
            if not offer.is_active:
                offer.share = 0
        
        return list(offers)

    @staticmethod
    def validate_weights(offers: Sequence[OfferWeight]) -> tuple[bool, str]:
        """
        Валидирует веса. Сумма активных должна быть 100%.
        
        Returns:
            (is_valid, error_message)
        """
        active_offers = [o for o in offers if o.is_active]
        
        if not active_offers:
            return False, "At least one active offer is required"
        
        # 1. Сначала проверяем, что сумма пинов не превышает 100 (грубая ошибка конфигурации)
        pinned_sum = sum(
            o.pinned_share for o in active_offers if o.pinned_share is not None
        )
        if pinned_sum > 100:
            return False, f"Sum of pinned offers ({pinned_sum}) exceeds 100"
        
        # 2. Затем проверяем общую сумму весов
        total = sum(o.share for o in active_offers)
        if total != 100:
            return False, f"Sum of active offers must be 100, got {total}"
        
        return True, ""

   