from app import create_app
from models import db, Restaurant, Menu

app = create_app()

with app.app_context():
    # Update restaurants
    r1 = Restaurant.query.get(1)
    if r1:
        r1.image_url = 'restaurant_1.png'
    
    r4 = Restaurant.query.get(4)
    if r4:
        r4.image_url = 'restaurant_4.png'

    # Update menu items
    m1 = Menu.query.get(1)
    if m1:
        m1.image_url = 'menu_1.png'

    m5 = Menu.query.get(5)
    if m5:
        m5.image_url = 'menu_5.png'

    m7 = Menu.query.get(7)
    if m7:
        m7.image_url = 'menu_7.png'

    db.session.commit()
    print("Database updated with image URLs.")
