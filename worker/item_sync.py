# worker/item_sync.py
import asyncio
import os
import requests
from datetime import datetime
from sqlalchemy.orm import Session

from shared.db import SessionLocal
from shared.models import Item

# Config (Reuse or duplicate from sap_sl_sync for now, or move to unified config later)
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

def sync_items():
    print("Starting Item Sync...")
    s = get_sl_session()
    if not s:
        return

    try:
        skip = 0
        top = 20
        total_synced = 0

        while True:
            # Fetch Items (OITM)
            # Filter: Valid='Y', SalesItem='Y', maybe Frozen='N'
            # Select: ItemCode, ItemName, QuantityOnStock, PriceList info...
            
            # NOTE: Pricing is complex in SAP B1. We'll try to fetch from 'ItemPrices' or a specific Price List.
            # Let's assume Price List 1 is the base price.
            
            url = f"{SL_HOST}/Items"
            params = {
                "$select": "ItemCode,ItemName,QuantityOnStock,ItemPrices",
                "$filter": "Valid eq 'Y' and Frozen eq 'N'",
                "$top": top,
                "$skip": skip
            }
            
            print(f"Fetching items with skip={skip}, top={top}...")
            resp = s.get(url, params=params, verify=False)
            if resp.status_code != 200:
                print(f"Failed to fetch Items: {resp.status_code} - {resp.text}")
                break

            data = resp.json()
            items_data = data.get("value", [])
            
            if not items_data:
                print("No more items to fetch.")
                break

            db = SessionLocal()
            try:
                for i in items_data:
                    code = i["ItemCode"]
                    name = i["ItemName"]
                    qty = i["QuantityOnStock"]
                    
                    # Extract Price from Price List 1
                    price = 0.0
                    currency = "USD"
                    
                    if "ItemPrices" in i:
                        for p in i["ItemPrices"]:
                            if p["PriceList"] == 1: # Base Price List
                                price = p["Price"] or 0.0
                                currency = p["Currency"] or "USD"
                                break
                                
                    # Upsert to DB
                    existing = db.query(Item).filter(Item.item_code == code).first()
                    if existing:
                        existing.item_name = name
                        existing.quantity = qty
                        existing.price = price
                        existing.currency = currency
                        existing.updated_at = datetime.utcnow()
                    else:
                        new_item = Item(
                            item_code=code,
                            item_name=name,
                            quantity=qty,
                            price=price,
                            currency=currency
                        )
                        db.add(new_item)
                
                db.commit()
                batch_count = len(items_data)
                total_synced += batch_count
                print(f"Synced batch of {batch_count} items. Total: {total_synced}")
                
                if len(items_data) < top:
                    print("Fetched fewer items than requested (last page).")
                    break

                skip += top
                
            except Exception as e:
                print(f"DB Error during item sync: {e}")
                db.rollback()
            finally:
                db.close()

    except Exception as e:
        print(f"Item Sync Exception: {e}")
    finally:
        s.close()

async def item_sync_loop(period: int):
    while True:
        try:
            sync_items()
        except Exception as e:
            print(f"Item Sync Loop Error: {e}")
        await asyncio.sleep(period)
