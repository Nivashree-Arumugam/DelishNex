import os
import shutil
from app import create_app
from models import db, Restaurant, Menu

source_dir = r"C:\Users\Niva\.gemini\antigravity-ide\brain\ce8ecb90-477d-4c21-bf9b-4341f3ba5c6b"
dest_dir = r"d:\DelishNex\static\images"

files_to_copy = {
    "restaurant_2_1784104585534.png": "restaurant_2.png",
    "restaurant_3_1784104598002.png": "restaurant_3.png",
    "restaurant_5_1784104610229.png": "restaurant_5.png",
    "restaurant_6_1784104622955.png": "restaurant_6.png",
    "cat_starter_1784104635189.png": "cat_starter.png",
    "cat_main_1784104648053.png": "cat_main.png",
    "cat_dessert_1784104659229.png": "cat_dessert.png",
    "cat_beverage_1784104671883.png": "cat_beverage.png",
    "cat_combo_1784104683249.png": "cat_combo.png",
}

print("Copying images...")
for src, dst in files_to_copy.items():
    src_path = os.path.join(source_dir, src)
    dst_path = os.path.join(dest_dir, dst)
    if os.path.exists(src_path):
        shutil.copy(src_path, dst_path)
    else:
        print(f"File not found: {src_path}")

print("Updating database...")
app = create_app()
with app.app_context():
    # Update restaurants
    r2 = Restaurant.query.get(2)
    if r2: r2.image_url = 'restaurant_2.png'
    r3 = Restaurant.query.get(3)
    if r3: r3.image_url = 'restaurant_3.png'
    r5 = Restaurant.query.get(5)
    if r5: r5.image_url = 'restaurant_5.png'
    r6 = Restaurant.query.get(6)
    if r6: r6.image_url = 'restaurant_6.png'
    
    # Update menus by category, except the ones we already set specifically
    menus = Menu.query.all()
    for m in menus:
        # Don't overwrite the specific ones (Paneer Tikka=1, Butter Chicken=5, Mutton Biryani=7)
        if m.id in [1, 5, 7]:
            continue
            
        if m.category == 'starter':
            m.image_url = 'cat_starter.png'
        elif m.category == 'main_course':
            m.image_url = 'cat_main.png'
        elif m.category == 'dessert':
            m.image_url = 'cat_dessert.png'
        elif m.category == 'beverage':
            m.image_url = 'cat_beverage.png'
        elif m.category == 'combo':
            m.image_url = 'cat_combo.png'

    db.session.commit()
    print("Database updated successfully.")
