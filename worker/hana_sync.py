# worker/hana_sync.py

import asyncio
import os

from hdbcli import dbapi

from shared.db import SessionLocal
from shared.models import Delivery, TelegramUser, DeliveryItem
from shared.payloads import build_delivery_payload
from shared.telegram_notify import send_telegram_delivery_image
from shared.image_renderer import render_delivery_image

# --- HANA connection settings ---
HANA_HOST = os.getenv("HANA_HOST", "hana_host")
HANA_PORT = int(os.getenv("HANA_PORT", 30015))
HANA_USER = os.getenv("HANA_USER", "username")
HANA_PASSWORD = os.getenv("HANA_PASSWORD", "password")
SL_COMPANYDB = os.getenv("SL_COMPANYDB", "CompanyDB")

temp_item = [
    {
        "line_num": 0,
        "item_code": "A0001",
        "item_name": "Product A",
        "quantity": 10,
        "price": 120000,
        "line_total": 1200000
    }
]

def fetch_deliveries_from_sap():
    """
    Connects to SAP B1 HANA and fetches new deliveries.
    Returns a list of dictionaries with keys matching our Delivery model.
    """
    conn = dbapi.connect(
        address=HANA_HOST,
        port=HANA_PORT,
        user=HANA_USER,
        password=HANA_PASSWORD
    )

    cursor = conn.cursor()

    # Example query: deliveries from today
    query = f"""
    SELECT
        H."DocEntry",
        H."DocNum",
        H."CardCode",
        H."CardName",
        H."DocDate",
        T1."SlpName",
        H."Comments",
        H."DocTotal",
        L."LineNum",
        L."ItemCode",
        L."Dscription"  AS "ItemName",
        L."Quantity",
        L."Price",
        L."LineTotal"
    FROM "{SL_COMPANYDB}"."ODLN" H INNER JOIN "{SL_COMPANYDB}"."OSLP" T1
    JOIN "{SL_COMPANYDB}"."DLN1" L ON L."DocEntry" = H."DocEntry"
    WHERE T0."DocDate" >= CURRENT_DATE AND T0."U_Approved" = 'N'
    ORDER BY H."DocEntry", L."LineNum";
    """
    query1 = f"""
    SELECT 
        T0."DocNum",
        T0."DocDate",
        T1."SlpName",
        T0."Comments",
        T0."DocTotal",
        T0."DocEntry",
        T0."CardCode"
    FROM "{SL_COMPANYDB}"."ODLN" T0 INNER JOIN "{SL_COMPANYDB}"."OSLP" T1
    ON T0."SlpCode" = T1."SlpCode"
    WHERE T0."DocDate" >= CURRENT_DATE AND T0."U_Approved" = 'N'
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    # Map SAP SlpCode to Sales Manager name if needed
    # For simplicity, we keep SlpCode as sales_manager
    deliveries = []
    for row in rows:
        deliveries.append({
            "CardCode": row[6],
            "DocEntry": row[5],
            "DocNum": row[0],
            "DocDate": row[1],
            "SlpName": row[2],
            "Comments": row[3],
            "DocTotal": float(row[4])
        })

    cursor.close()
    conn.close()
    return deliveries


async def hana_sync_loop(period: int):
    while True:
        try:
            sync_deliveries()
        except Exception as e:
            print("HANA sync error:", e)

        await asyncio.sleep(period)


def sync_deliveries():
    db = SessionLocal()
    try:
        sap_docs = fetch_deliveries_from_sap()
        grouped = group_deliveries(sap_docs)

        for doc_entry, data in grouped.items():
            exists = db.query(Delivery).filter(
                Delivery.doc_entry == doc_entry
            ).first()

            if exists:
                continue

            delivery = Delivery(
                doc_entry=doc_entry,
                card_code=data["card_code"],
                document_number=data["document_number"],
                date=data["date"],
                sales_manager=data["sales_manager"],
                remarks=data["remarks"],
                document_total_amount=data["total_amount"],
                approved=False
            )

            db.add(delivery)
            db.flush()  # 🔔 ensure ID is generated

            for item in data["items"]:
                db.add(DeliveryItem(
                    delivery_id=delivery.id,
                    line_num=item["line_num"],
                    item_code=item["item_code"],
                    item_name=item["item_name"],
                    quantity=item["quantity"],
                    price=item["price"],
                    line_total=item["line_total"]
                ))

            # 🔔 find telegram users for this CardCode
            users = db.query(TelegramUser).filter(
                TelegramUser.card_code == data["card_code"],
                TelegramUser.is_active == True
            ).all()

            # 🔔 notify users
            for user in users:
                delivery_data = build_delivery_payload(delivery, temp_item)
                #print(delivery_data)
                image = render_delivery_image(delivery_data)

                caption = (
                    f"<b>📦 New delivery</b>\n"
                    f"No: <b>{delivery.document_number}</b>\n"
                    f"Date: {delivery.date}\n"
                    f"Amount: <b>{delivery.document_total_amount:,}</b>"
                )

                send_telegram_delivery_image(
                    user=user,
                    image_path=image,
                    caption=caption
                )

        db.commit()
        print(f"Synced {len(sap_docs)} deliveries from SAP.")
    finally:
        db.close()


def group_deliveries(rows: list[dict]) -> dict:
    deliveries = {}

    for r in rows:
        doc_entry = r["DocEntry"]

        if doc_entry not in deliveries:
            deliveries[doc_entry] = {
                "doc_entry": doc_entry,
                "document_number": r["DocNum"],
                "card_code": r["CardCode"],
                "card_name": r["CardName"],
                "date": r["DocDate"],
                "sales_manager": r["SlpName"],
                "remarks": r["Comments"],
                "total_amount": r["DocTotal"],
                "items": []
            }

        deliveries[doc_entry]["items"].append({
            "line_num": r["LineNum"],
            "item_code": r["ItemCode"],
            "item_name": r["ItemName"],
            "quantity": r["Quantity"],
            "price": r["Price"],
            "line_total": r["LineTotal"]
        })

    return deliveries
