# worker/hana_sync.py

import asyncio
import os

from hdbcli import dbapi

from shared.db import SessionLocal
from shared.models import Delivery, TelegramUser
from shared.telegram_notify import send_telegram_message

# --- HANA connection settings ---
HANA_HOST = os.getenv("HANA_HOST", "hana_host")
HANA_PORT = int(os.getenv("HANA_PORT", 30015))
HANA_USER = os.getenv("HANA_USER", "username")
HANA_PASSWORD = os.getenv("HANA_PASSWORD", "password")
SL_COMPANYDB = os.getenv("SL_COMPANYDB", "CompanyDB")


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

        for doc in sap_docs:
            exists = db.query(Delivery).filter(
                Delivery.doc_entry == doc["DocEntry"]
            ).first()

            if exists:
                continue

            db.add(Delivery(
                card_code=doc["CardCode"],
                doc_entry=doc["DocEntry"],
                document_number=doc["DocNum"],
                sales_manager=doc["SlpName"],
                date=doc["DocDate"],
                remarks=doc["Comments"],
                document_total_amount=doc["DocTotal"],
                approved=False
            ))
            db.flush()  # 🔔 ensure ID is generated

            # 🔔 find telegram users for this CardCode
            users = db.query(TelegramUser).filter(
                TelegramUser.card_code == doc["CardCode"],
                TelegramUser.is_active == True
            ).all()

            # 🔔 notify users
            for user in users:
                send_telegram_message(
                    user.telegram_id,
                    (
                        "📦 <b>New delivery received</b>\n\n"
                        f"№ {doc['DocNum']}\n"
                        f"Amount: {doc['DocTotal']}\n"
                        f"Manager: {doc['SlpName']}\n\n"
                        "Tap below to review and approve 👇"
                    )
                )

        db.commit()
        print(f"Synced {len(sap_docs)} deliveries from SAP.")
    finally:
        db.close()
