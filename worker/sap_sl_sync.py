# worker/sap_sl_sync.py

import asyncio
import os

import requests

from shared.db import SessionLocal
from shared.models import Delivery

SL_HOST = os.getenv("SL_HOST", "https://hana_host:50000/b1s/v1")
SL_COMPANYDB = os.getenv("SL_COMPANYDB", "CompanyDB")
SL_USER = os.getenv("SL_USER", "username")
SL_PASSWORD = os.getenv("SL_PASSWORD", "password")


def sync_approved_to_sap():
    db = SessionLocal()
    try:
        deliveries = db.query(Delivery).filter(
            Delivery.approved == True,
            Delivery.sap_synced == False
        ).all()

        if not deliveries:
            return

        credentials = {
            "CompanyDB": SL_COMPANYDB,
            "UserName": SL_USER,
            "Password": SL_PASSWORD
        }

        with requests.Session() as s:
            login_resp = s.post(f"{SL_HOST}/Login", json=credentials, verify=False)
            if login_resp.status_code != 200:
                print("SAP Service Layer login failed")
                return

            for d in deliveries:
                patch_resp = s.patch(
                    f"{SL_HOST}/DeliveryNotes({d.doc_entry})",
                    json={"U_Approved": "Y"},
                    verify=False
                )
                if patch_resp.status_code == 204:
                    d.sap_synced = True
                    db.commit()
                    print(f"Delivery {d.document_number} synced to SAP")
                else:
                    print(f"Failed to sync delivery {d.document_number}, status {patch_resp.status_code}")
    finally:
        db.close()


async def sap_sl_sync_loop(period: int):
    while True:
        try:
            sync_approved_to_sap()
        except Exception as e:
            print("SAP SL sync error:", e)

        await asyncio.sleep(period)
