
import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from shared.db import SessionLocal
from shared.models import Item, ItemImage

def verify_images():
    db = SessionLocal()
    try:
        # 1. Create a dummy item
        item_code = "TEST_IMG_ITEM_001"
        item = db.query(Item).filter(Item.item_code == item_code).first()
        if item:
            db.delete(item)
            db.commit()
        
        item = Item(item_code=item_code, item_name="Test Image Item", quantity=10, price=100)
        db.add(item)
        db.commit()
        
        # 2. Add an image
        img_path = "data/item_images/TEST_IMG_ITEM_001_uuid.jpg"
        item_image = ItemImage(item_code=item_code, file_path=img_path, is_primary=True)
        db.add(item_image)
        db.commit()
        
        # 3. Verify
        db.refresh(item)
        print(f"Item images count: {len(item.images)}")
        if len(item.images) == 1 and item.images[0].file_path == img_path:
            print("Image verification successful")
        else:
            print("Image verification failed")
            
        # 4. Cleanup
        db.delete(item)
        db.commit()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_images()
