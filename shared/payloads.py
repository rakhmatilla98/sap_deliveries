from typing import Optional

from shared.models import Delivery


def build_delivery_payload(
    delivery: Delivery,
    items: Optional[list[dict]] = None
) -> dict:
    """
    Builds a unified delivery payload used by:
    - image renderer
    - telegram notifications
    - logs / audits
    """

    payload = {
        "doc_entry": delivery.doc_entry,
        "document_number": delivery.document_number,
        "card_code": delivery.card_code,
        "card_name": delivery.card_name,
        "date": str(delivery.date),
        "sales_manager": delivery.sales_manager,
        "remarks": delivery.remarks or "",
        "total_amount": float(delivery.document_total_amount),
        "currency": delivery.currency,
        "approved": delivery.approved,
        "items": items or []
    }

    return payload
