import pytest
from app.services.weight_service import OfferWeight, WeightService


class TestWeightService:
    """Тесты для сервиса весов."""

    def test_equal_distribution_3_offers(self):
        """3 оффера: 100/3 = 33.33 → [34, 33, 33] (остаток первому)"""
        offers = [
            OfferWeight(offer_id=1),
            OfferWeight(offer_id=2),
            OfferWeight(offer_id=3),
        ]
        
        result = WeightService.recalculate_weights(offers)
        
        assert result[0].share == 34
        assert result[1].share == 33
        assert result[2].share == 33
        assert sum(o.share for o in result) == 100

    def test_equal_distribution_4_offers(self):
        """4 оффера: 100/4 = 25 → [25, 25, 25, 25]"""
        offers = [OfferWeight(offer_id=i) for i in range(1, 5)]
        
        result = WeightService.recalculate_weights(offers)
        
        assert all(o.share == 25 for o in result)
        assert sum(o.share for o in result) == 100

    def test_equal_distribution_7_offers(self):
        """7 офферов: 100/7 = 14.28 → [16, 14, 14, 14, 14, 14, 14]"""
        offers = [OfferWeight(offer_id=i) for i in range(1, 8)]
        
        result = WeightService.recalculate_weights(offers)
        
        assert result[0].share == 16
        assert all(o.share == 14 for o in result[1:])
        assert sum(o.share for o in result) == 100

    def test_empty_offers(self):
        """Пустой список офферов"""
        result = WeightService.recalculate_weights([])
        assert result == []

    def test_all_inactive_offers(self):
        """Все офферы неактивны"""
        offers = [
            OfferWeight(offer_id=1, is_active=False),
            OfferWeight(offer_id=2, is_active=False),
        ]
        
        result = WeightService.recalculate_weights(offers)
        
        assert all(o.share == 0 for o in result)

    def test_validate_weights_valid(self):
        """Валидация корректных весов"""
        offers = [
            OfferWeight(offer_id=1, share=34),
            OfferWeight(offer_id=2, share=33),
            OfferWeight(offer_id=3, share=33),
        ]
        
        is_valid, error = WeightService.validate_weights(offers)
        
        assert is_valid is True
        assert error == ""

    def test_validate_weights_invalid_sum(self):
        """Валидация: сумма не 100"""
        offers = [
            OfferWeight(offer_id=1, share=30),
            OfferWeight(offer_id=2, share=30),
            OfferWeight(offer_id=3, share=30),
        ]
        
        is_valid, error = WeightService.validate_weights(offers)
        
        assert is_valid is False
        assert "must be 100" in error

    def test_validate_weights_no_active(self):
        """Валидация: нет активных офферов"""
        offers = [OfferWeight(offer_id=1, is_active=False)]
        
        is_valid, error = WeightService.validate_weights(offers)
        
        assert is_valid is False
        assert "At least one active offer" in error

    def test_validate_weights_pinned_exceeds_100(self):
        """Валидация: сумма запиненных > 100"""
        offers = [
            OfferWeight(offer_id=1, share=50, pinned_share=60),
            OfferWeight(offer_id=2, share=50, pinned_share=60),
        ]
        
        is_valid, error = WeightService.validate_weights(offers)
        
        assert is_valid is False
        assert "exceeds 100" in error