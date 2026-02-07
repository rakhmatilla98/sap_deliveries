# worker/order_sync.py
import asyncio
import os
import requests
import datetime
from shared.db import SessionLocal
from shared.models import Order, OrderItem

SL_HOST = os.getenv("SL_HOST", "https://hana_host:50000/b1s/v1")
SL_COMPANYDB = os.getenv("SL_COMPANYDB", "CompanyDB")
SL_USER = os.getenv("SL_USER", "username")
SL_PASSWORD = os.getenv("SL_PASSWORD", "password")

def get_sl_session():
    s = requests.Session()
    credentials = {
        "CompanyDB": SL_COMPANYDB,
        "UserName": SL_USER,
        "Password": SL_PASSWORD
    }
    resp = s.post(f"{SL_HOST}/Login", json=credentials, verify=False)
    if resp.status_code != 200:
        print(f"SL Login Failed: {resp.text}")
        return None
    return s

def sync_orders():
    # 1. Find 'new' orders
    db = SessionLocal()
    try:
        # We might want to lock these rows or handle concurrency, but for now simple fetch
        new_orders = db.query(Order).filter(Order.status == 'new').all()
        if not new_orders:
            return

        s = get_sl_session()
        if not s:
            return

        for order in new_orders:
            print(f"Syncing Order {order.id}...")
            
            # Prepare Payload for SAP B1 Orders (Sales Order)
            # DocType: dDocument_Items
            # CardCode: order.card_code (must be valid BP)
            # DocumentLines: [ ... ]
            
            lines = []
            for item in order.items:
                lines.append({
                    "ItemCode": item.item_code,
                    "Quantity": item.quantity,
                    # "Price": item.price # Optional: Let SAP determine price or override
                })
            
            payload = {
                "CardCode": order.card_code,
                "DocDate": datetime.date.today().isoformat(),
                "DocDueDate": datetime.date.today().isoformat(),
                "DocumentLines": lines,
                "Comments": f"From Telegram Bot (Order #{order.id})"
            }

            try:
                resp = s.post(f"{SL_HOST}/Orders", json=payload, verify=False)
                if resp.status_code == 201:
                    data = resp.json()
                    new_doc_entry = data.get("DocEntry")
                    new_doc_num = str(data.get("DocNum"))
                    
                    order.sap_doc_entry = new_doc_entry
                    order.sap_doc_num = new_doc_num
                    order.status = "synced"
                    order.sap_error = None
                    print(f"Order {order.id} created in SAP: DocEntry {new_doc_entry}")
                else:
                    err_msg = resp.text
                    print(f"Failed to create Order {order.id}: {err_msg}")
                    order.status = "error"
                    order.sap_error = err_msg[:250] # Truncate
                    
            except Exception as e:
                print(f"Exception creating order {order.id}: {e}")
                order.status = "error"
                order.sap_error = str(e)[:250]
                
            db.commit()
            
    except Exception as e:
        print(f"Order Sync Error: {e}")
    finally:
        db.close()

async def order_sync_loop(period: int):
    while True:
        try:
            sync_orders()
        except Exception as e:
            print(f"Order Sync Loop Error: {e}")
        await asyncio.sleep(period)
