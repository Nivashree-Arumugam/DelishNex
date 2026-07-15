"""
models.py - SQLAlchemy ORM Models for DelishNex
Defines all database tables as Python classes with relationships,
validation, and helper methods.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# ── SQLAlchemy instance (shared across the application) ─────────────────
db = SQLAlchemy()


# ═══════════════════════════════════════════════════════════════════════════
# USER MODEL
# ═══════════════════════════════════════════════════════════════════════════
class User(UserMixin, db.Model):
    """Represents a registered user (customer or admin)."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('customer', 'admin'), nullable=False, default='customer')
    avatar_url = db.Column(db.String(256), default=None)
    reward_points = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ───────────────────────────────────────────────────
    reservations = db.relationship('Reservation', backref='user', lazy='dynamic')
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    rewards = db.relationship('Reward', backref='user', lazy='dynamic')
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    payments = db.relationship('Payment', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        """Check if the user has admin privileges."""
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'


# ═══════════════════════════════════════════════════════════════════════════
# RESTAURANT MODEL
# ═══════════════════════════════════════════════════════════════════════════
class Restaurant(db.Model):
    """Represents a restaurant listed on the platform."""
    __tablename__ = 'restaurants'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(300), nullable=False)
    phone = db.Column(db.String(20))
    image_url = db.Column(db.String(256), default=None)
    cuisine_type = db.Column(db.String(100))
    rating = db.Column(db.Numeric(2, 1), nullable=False, default=0.0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    opening_time = db.Column(db.Time, nullable=False)
    closing_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ───────────────────────────────────────────────────
    tables = db.relationship('RestaurantTable', backref='restaurant', lazy='dynamic')
    menu_items = db.relationship('Menu', backref='restaurant', lazy='dynamic')
    reservations = db.relationship('Reservation', backref='restaurant', lazy='dynamic')
    orders = db.relationship('Order', backref='restaurant', lazy='dynamic')
    reviews = db.relationship('Review', backref='restaurant', lazy='dynamic')

    def __repr__(self):
        return f'<Restaurant {self.name}>'


# ═══════════════════════════════════════════════════════════════════════════
# RESTAURANT TABLE MODEL
# ═══════════════════════════════════════════════════════════════════════════
class RestaurantTable(db.Model):
    """Represents a physical table in a restaurant."""
    __tablename__ = 'restaurant_tables'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    table_number = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=4)
    table_type = db.Column(db.Enum('regular', 'booth', 'outdoor', 'private', 'bar'),
                           nullable=False, default='regular')
    pos_x = db.Column(db.Integer, nullable=False, default=0)
    pos_y = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ───────────────────────────────────────────────────
    reservations = db.relationship('Reservation', backref='table', lazy='dynamic')

    def __repr__(self):
        return f'<Table {self.table_number} @ Restaurant {self.restaurant_id}>'


# ═══════════════════════════════════════════════════════════════════════════
# MENU MODEL
# ═══════════════════════════════════════════════════════════════════════════
class Menu(db.Model):
    """Represents a food or drink item on a restaurant's menu."""
    __tablename__ = 'menu'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.Enum('starter', 'main_course', 'dessert', 'beverage', 'combo'),
                         nullable=False)
    image_url = db.Column(db.String(256), default=None)
    rating = db.Column(db.Numeric(2, 1), nullable=False, default=0.0)
    is_vegetarian = db.Column(db.Boolean, nullable=False, default=False)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    is_special = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ───────────────────────────────────────────────────
    order_items = db.relationship('OrderItem', backref='menu_item', lazy='dynamic')

    def __repr__(self):
        return f'<Menu {self.name} ₹{self.price}>'


# ═══════════════════════════════════════════════════════════════════════════
# RESERVATION MODEL
# ═══════════════════════════════════════════════════════════════════════════
class Reservation(db.Model):
    """Represents a table reservation made by a customer."""
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('restaurant_tables.id'), nullable=False)
    occasion = db.Column(db.String(100))
    dining_mood = db.Column(db.String(100))
    reservation_date = db.Column(db.Date, nullable=False)
    reservation_time = db.Column(db.Time, nullable=False)
    members = db.Column(db.Integer, nullable=False, default=2)
    status = db.Column(db.Enum('pending', 'confirmed', 'cancelled', 'completed'),
                       nullable=False, default='pending')
    special_request = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ───────────────────────────────────────────────────
    orders = db.relationship('Order', backref='reservation', lazy='dynamic')

    def __repr__(self):
        return f'<Reservation {self.id} on {self.reservation_date}>'


# ═══════════════════════════════════════════════════════════════════════════
# ORDER MODEL
# ═══════════════════════════════════════════════════════════════════════════
class Order(db.Model):
    """Represents a food order placed by a customer."""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'), default=None)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    gst = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    service_charge = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    discount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    grand_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    coupon_code = db.Column(db.String(50), default=None)
    status = db.Column(db.Enum('pending', 'preparing', 'ready', 'delivered', 'cancelled'),
                       nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ───────────────────────────────────────────────────
    items = db.relationship('OrderItem', backref='order', lazy='dynamic')
    payment = db.relationship('Payment', backref='order', uselist=False)

    def __repr__(self):
        return f'<Order {self.id} ₹{self.grand_total}>'


# ═══════════════════════════════════════════════════════════════════════════
# ORDER ITEM MODEL
# ═══════════════════════════════════════════════════════════════════════════
class OrderItem(db.Model):
    """Represents a single item within an order."""
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<OrderItem {self.menu_id} x{self.quantity}>'


# ═══════════════════════════════════════════════════════════════════════════
# PAYMENT MODEL
# ═══════════════════════════════════════════════════════════════════════════
class Payment(db.Model):
    """Represents a payment transaction for an order."""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum('upi', 'card', 'wallet', 'cash'),
                               nullable=False, default='cash')
    payment_status = db.Column(db.Enum('pending', 'completed', 'failed', 'refunded'),
                               nullable=False, default='pending')
    transaction_id = db.Column(db.String(100), default=None)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Payment {self.id} ₹{self.amount}>'


# ═══════════════════════════════════════════════════════════════════════════
# REWARD MODEL
# ═══════════════════════════════════════════════════════════════════════════
class Reward(db.Model):
    """Tracks reward point transactions for loyalty program."""
    __tablename__ = 'rewards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(256), nullable=False)
    reward_type = db.Column(db.Enum('earned', 'redeemed'), nullable=False, default='earned')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Reward {self.points} pts ({self.reward_type})>'


# ═══════════════════════════════════════════════════════════════════════════
# REVIEW MODEL
# ═══════════════════════════════════════════════════════════════════════════
class Review(db.Model):
    """Stores customer reviews for restaurants."""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), default=None)
    rating = db.Column(db.Numeric(2, 1), nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Review {self.rating}★ for Restaurant {self.restaurant_id}>'
