import datetime
import os
import asyncio

from hdbcli import dbapi

from shared.db import SessionLocal

from shared.models import TelegramUser


# --- HANA connection settings ---
HANA_HOST = os.getenv("HANA_HOST", "hana_host")
HANA_PORT = int(os.getenv("HANA_PORT", 30015))
HANA_USER = os.getenv("HANA_USER", "username")
HANA_PASSWORD = os.getenv("HANA_PASSWORD", "password")
SL_COMPANYDB = os.getenv("SL_COMPANYDB", "CompanyDB")


def get_hana_connection():
    return dbapi.connect(
        address=HANA_HOST,
        port=HANA_PORT,
        user=HANA_USER,
        password=HANA_PASSWORD
    )


def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    return phone.replace(" ", "").replace("-", "").replace("+", "")


def sync_business_partners():
    """
    Syncs SAP Business Partners with Telegram users.
    SAP is the source of truth.
    """
    db = SessionLocal()
    sap_bps = load_business_partners()  # SAP source

    try:
        users = db.query(TelegramUser).filter(
            TelegramUser.phone_verified == True
        ).all()

        for user in users:
            phone = normalize_phone(user.phone_number)

            matched_bp = None
            for card_code, bp in sap_bps.items():
                if normalize_phone(bp["phone"]) == phone:
                    matched_bp = (card_code, bp)
                    break

            print(matched_bp)
            if matched_bp and bp["validFor"] == "Y":
                user.card_code = card_code
                user.card_name = bp["card_name"]
                user.is_active = True
            else:
                user.is_active = False

            user.last_sap_sync = datetime.datetime.utcnow()

        db.commit()

    finally:
        db.close()


def load_business_partners():
    """
    Loads Business Partners from SAP B1 (HANA)

    Returns:
    {
        "C0001": {
            "card_name": "Customer A",
            "phone": "+998901234567",
            "validFor": "Y"
        }
    }
    """
    conn = get_hana_connection()
    cursor = conn.cursor()

    sql = f"""
        SELECT
            "CardCode",
            "CardName",
            COALESCE(NULLIF("Cellular", ''),
                     NULLIF("Phone1", ''),
                     "Phone2") AS "Phone",
            "validFor"
        FROM "{SL_COMPANYDB}"."OCRD"
        WHERE "CardType" = 'C'
    """

    cursor.execute(sql)

    result = {}
    for card_code, card_name, phone, valid_for in cursor.fetchall():
        result[card_code] = {
            "card_name": card_name,
            "phone": phone or "",
            "validFor": valid_for
        }

    cursor.close()
    conn.close()
    return result


async def bp_sync_loop(period: int):
    while True:
        try:
            sync_business_partners()
        except Exception as e:
            print("BP sync error:", e)

        await asyncio.sleep(period)
