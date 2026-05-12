"""
register_images.py
------------------
Scans data/item_images/ and registers every image file into the
item_images database table.

Naming convention expected:  {item_code}_{seq}.{ext}
  e.g.  0120m_001.jpg  →  item_code="0120m", seq=1, is_primary=True

Run from project root:
    python register_images.py
"""

import os
import sys

# Make sure project root is on the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.db import SessionLocal
from shared.models import Item, ItemImage

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "item_images")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def parse_filename(filename: str):
    """
    Parse '{item_code}_{seq}.{ext}' into (item_code, seq_number).
    Returns (None, None) if the format doesn't match.
    """
    name, ext = os.path.splitext(filename)
    if ext.lower() not in SUPPORTED_EXTENSIONS:
        return None, None

    # Split on the LAST underscore to get seq number
    parts = name.rsplit("_", 1)
    if len(parts) != 2:
        print(f"  [SKIP] '{filename}' - cannot parse item_code_seq format")
        return None, None

    item_code, seq_str = parts
    if not seq_str.isdigit():
        print(f"  [SKIP] '{filename}' - sequence part '{seq_str}' is not numeric")
        return None, None

    return item_code, int(seq_str)


def register_images():
    if not os.path.isdir(IMAGES_DIR):
        print(f"[ERROR] Directory not found: {IMAGES_DIR}")
        sys.exit(1)

    db = SessionLocal()

    files = sorted(os.listdir(IMAGES_DIR))
    image_files = [f for f in files if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]

    print(f"[INFO] Found {len(image_files)} image file(s) in {IMAGES_DIR}\n")

    registered = 0
    skipped_no_item = 0
    skipped_exists = 0
    skipped_parse = 0

    try:
        for filename in image_files:
            item_code, seq = parse_filename(filename)

            if item_code is None:
                skipped_parse += 1
                continue

            # Check that the item exists in the items table
            item = db.query(Item).filter(Item.item_code == item_code).first()
            if not item:
                print(f"  [SKIP] '{filename}' - item_code '{item_code}' not found in items table")
                skipped_no_item += 1
                continue

            # Relative file path stored in DB (forward slashes, no leading slash)
            rel_path = f"data/item_images/{filename}"

            # Check if this file_path is already registered
            existing = db.query(ItemImage).filter(ItemImage.file_path == rel_path).first()
            if existing:
                print(f"  [EXISTS] '{filename}'")
                skipped_exists += 1
                continue

            # seq == 1 → mark as primary (unless another primary already exists)
            is_primary = False
            if seq == 1:
                already_primary = db.query(ItemImage).filter(
                    ItemImage.item_code == item_code,
                    ItemImage.is_primary == True
                ).first()
                is_primary = already_primary is None  # only set primary if none exists yet

            new_image = ItemImage(
                item_code=item_code,
                file_path=rel_path,
                is_primary=is_primary,
            )
            db.add(new_image)
            db.flush()  # get the id without committing yet

            print(f"  [OK] Registered '{filename}'  (item: {item_code}, seq: {seq:03d}, primary: {is_primary})")
            registered += 1

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        db.close()

    print(f"""
========================================
Done.
  Registered : {registered}
  Already existed : {skipped_exists}
  Item not found  : {skipped_no_item}
  Bad filename    : {skipped_parse}
========================================
""")


if __name__ == "__main__":
    register_images()
