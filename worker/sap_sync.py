from hdbcli import dbapi

from shared.db import SessionLocal
import datetime
import os

from shared.models import Delivery

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
        T0."DocEntry"
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


def sync_deliveries_from_sap(sap_rows):
    """
    Insert new deliveries from SAP into SQLite
    """
    db = SessionLocal()
    try:
        for row in sap_rows:
            doc_entry = row['DocEntry']

            # Skip if already exists
            if db.query(Delivery).filter(Delivery.doc_entry == doc_entry).first():
                continue

            delivery = Delivery(
                doc_entry=doc_entry,
                document_number=row.get('DocNum', -1),
                sales_manager=row.get('SlpName', 'Unknown'),
                date=row.get('DocDate', datetime.datetime.utcnow()),
                remarks=row.get('Comments', None),
                document_total_amount=row.get('DocTotal', 0.0),
                approved=False,
                created_at=datetime.datetime.utcnow()
            )
            db.add(delivery)
        db.commit()
    finally:
        db.close()


def sync_deliveries():
    """
    High-level function: fetch from SAP and insert into SQLite
    """
    sap_rows = fetch_deliveries_from_sap()
    sync_deliveries_from_sap(sap_rows)
    print(f"Synced {len(sap_rows)} deliveries from SAP.")
