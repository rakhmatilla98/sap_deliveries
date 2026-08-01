# worker/item_sync.py
import asyncio
import os
import requests
from datetime import datetime
from sqlalchemy.orm import Session

from shared.db import SessionLocal
from shared.models import Item, ItemCategory

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

def fetch_item_groups(s: requests.Session) -> dict:
    """Fetch item groups from SAP and return a dict mapping Number to GroupName."""
    groups_map = {}
    try:
        skip = 0
        top = 50
        while True:
            url = f"{SL_HOST}/ItemGroups"
            params = {
                "$select": "Number,GroupName",
                "$top": top,
                "$skip": skip
            }
            print(f"Fetching item groups with skip={skip}, top={top}...")
            resp = s.get(url, params=params, verify=False)
            if resp.status_code != 200:
                print(f"Failed to fetch ItemGroups: {resp.status_code} - {resp.text}")
                break
            
            data = resp.json()
            groups_data = data.get("value", [])
            if not groups_data:
                break
                
            for group in groups_data:
                groups_map[group["Number"]] = group["GroupName"]
                
            skip += len(groups_data)
            
        print(f"Fetched {len(groups_map)} item groups in total.")
    except Exception as e:
        print(f"Error fetching ItemGroups: {e}")
    return groups_map


def sync_items():
    print("Starting Item Sync...")
    s = get_sl_session()
    if not s:
        return

    # Fetch groups mapping from SAP
    groups_map = fetch_item_groups(s)

    try:
        skip = 0
        top = 50  # Increase batch size for efficiency
        total_synced = 0

        while True:
            # Fetch Items (OITM)
            # Filter: Valid='Y', SalesItem='Y', maybe Frozen='N'
            # Select: ItemCode, ItemName, QuantityOnStock, PriceList info, ItemsGroupCode
            
            url = f"{SL_HOST}/Items"
            params = {
                "$select": "ItemCode,ItemName,QuantityOnStock,ItemPrices,ItemsGroupCode,User_Text",
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
                # Load existing categories from DB to map name -> id
                local_categories = {cat.name: cat.id for cat in db.query(ItemCategory).all()}

                for i in items_data:
                    code = i["ItemCode"]
                    name = i["ItemName"]
                    description = i.get("User_Text")
                    qty = i["QuantityOnStock"]
                    group_code = i.get("ItemsGroupCode")
                    
                    # Resolve category_id
                    category_id = None
                    if group_code is not None and group_code in groups_map:
                        group_name = groups_map[group_code]
                        if group_name not in local_categories:
                            # Create new category dynamically in the local DB
                            new_cat = ItemCategory(name=group_name)
                            db.add(new_cat)
                            db.commit()
                            local_categories[group_name] = new_cat.id
                        category_id = local_categories[group_name]

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
                        existing.description = description
                        existing.quantity = qty
                        existing.price = price
                        existing.currency = currency
                        existing.category_id = category_id
                        existing.updated_at = datetime.utcnow()
                    else:
                        new_item = Item(
                            item_code=code,
                            item_name=name,
                            description=description,
                            quantity=qty,
                            price=price,
                            currency=currency,
                            category_id=category_id
                        )
                        db.add(new_item)
                
                db.commit()
                batch_count = len(items_data)
                total_synced += batch_count
                print(f"Synced batch of {batch_count} items. Total: {total_synced}")
                
                skip += batch_count

                
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
