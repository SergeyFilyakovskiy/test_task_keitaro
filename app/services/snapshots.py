from app.infrastructure.db.models import Flow, FlowOffer


def build_snapshot(flow: Flow) -> dict:
    """Снапшот из загруженного объекта Flow (используется после refresh)."""
    return _snapshot_from_offers(sorted(flow.offers, key=lambda x: x.position))


def build_snapshot_from_rows(offer_rows: list[FlowOffer]) -> dict:
    """
    Снапшот из списка только что созданных FlowOffer.
    Используется сразу после bulk_create, чтобы не зависеть от relationship
    и не делать дополнительный refresh/SELECT.
    """
    return _snapshot_from_offers(sorted(offer_rows, key=lambda x: x.position))


def _snapshot_from_offers(offers) -> dict:
    return {
        "offers": [
            {
                "keitaro_offer_id": o.keitaro_offer_id,
                "offer_name": o.offer_name,
                "share": o.share,
                "pinned_share": o.pinned_share,
                "is_active": o.is_active,
                "is_deleted_in_keitaro": o.is_deleted_in_keitaro,
                "position": o.position,
            }
            for o in offers
        ]
    }