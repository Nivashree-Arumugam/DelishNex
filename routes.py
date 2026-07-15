"""
routes.py - All Flask Routes for DelishNex
Contains authentication, user flows, reservation workflow, ordering,
admin panel, and API endpoints.
"""

import random
import uuid
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
from functools import wraps

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    session, jsonify, abort
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import func

from models import (
    db, User, Restaurant, RestaurantTable, Menu,
    Reservation, Order, OrderItem, Payment, Reward, Review
)

# ── Blueprint registration ──────────────────────────────────────────────
main = Blueprint('main', __name__)


# ═══════════════════════════════════════════════════════════════════════════
# DECORATORS
# ═══════════════════════════════════════════════════════════════════════════

def admin_required(f):
    """Decorator that restricts access to admin users only."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_cart():
    """Retrieve the shopping cart from the session."""
    return session.get('cart', [])


def save_cart(cart):
    """Persist the shopping cart to the session."""
    session['cart'] = cart
    session.modified = True


def calculate_cart_totals(cart_items):
    """Calculate subtotal, GST, service charge, and grand total for cart items."""
    subtotal = sum(Decimal(str(item['price'])) * item['quantity'] for item in cart_items)
    gst = subtotal * Decimal('0.05')            # 5% GST
    service_charge = subtotal * Decimal('0.02')  # 2% service charge
    grand_total = subtotal + gst + service_charge
    return {
        'subtotal': float(round(subtotal, 2)),
        'gst': float(round(gst, 2)),
        'service_charge': float(round(service_charge, 2)),
        'grand_total': float(round(grand_total, 2))
    }


def get_ai_recommendation(occasion, mood, members, restaurant_id=None):
    """
    Rule-based AI recommendation engine.
    Suggests restaurants and tables based on user preferences.
    Uses occasion, mood, and party size to rank and filter results.
    """
    # Map occasions to preferred table types and cuisine
    occasion_preferences = {
        'Birthday': {'types': ['private', 'booth'], 'cuisine': ['Multi-Cuisine', 'Italian']},
        'Anniversary': {'types': ['private', 'booth'], 'cuisine': ['Italian', 'North Indian']},
        'Date Night': {'types': ['booth', 'outdoor'], 'cuisine': ['Italian', 'Multi-Cuisine']},
        'Business Meeting': {'types': ['private', 'regular'], 'cuisine': ['Multi-Cuisine', 'North Indian']},
        'Family Gathering': {'types': ['private', 'regular'], 'cuisine': ['North Indian', 'South Indian', 'Multi-Cuisine']},
        'Friends Hangout': {'types': ['regular', 'outdoor', 'bar'], 'cuisine': ['Pan-Asian', 'Multi-Cuisine']},
        'Casual Dining': {'types': ['regular', 'outdoor'], 'cuisine': ['South Indian', 'Multi-Cuisine']},
    }

    # Map moods to preferred ambiences
    mood_preferences = {
        'Romantic': {'types': ['booth', 'outdoor', 'private'], 'min_rating': 4.5},
        'Lively': {'types': ['regular', 'bar', 'outdoor'], 'min_rating': 4.0},
        'Quiet': {'types': ['private', 'booth'], 'min_rating': 4.3},
        'Festive': {'types': ['regular', 'outdoor', 'private'], 'min_rating': 4.0},
        'Cozy': {'types': ['booth', 'private'], 'min_rating': 4.2},
        'Elegant': {'types': ['private', 'booth'], 'min_rating': 4.5},
    }

    occ_prefs = occasion_preferences.get(occasion, {'types': ['regular'], 'cuisine': []})
    mood_prefs = mood_preferences.get(mood, {'types': ['regular'], 'min_rating': 4.0})

    # Merge preferred table types
    preferred_types = list(set(occ_prefs['types'] + mood_prefs['types']))

    # Query restaurants matching criteria
    query = Restaurant.query.filter_by(is_active=True)
    if occ_prefs['cuisine']:
        query = query.filter(Restaurant.cuisine_type.in_(occ_prefs['cuisine']))

    restaurants = query.filter(Restaurant.rating >= mood_prefs.get('min_rating', 4.0)).all()

    # If no restaurants match cuisine filter, fall back to all
    if not restaurants:
        restaurants = Restaurant.query.filter_by(is_active=True).all()

    recommendations = []
    for restaurant in restaurants:
        # Score: base from rating + bonus for matching cuisine
        score = float(restaurant.rating) * 20
        if restaurant.cuisine_type in occ_prefs.get('cuisine', []):
            score += 15

        # Check if suitable tables exist
        suitable_tables = RestaurantTable.query.filter(
            RestaurantTable.restaurant_id == restaurant.id,
            RestaurantTable.capacity >= members,
            RestaurantTable.is_active == True,
            RestaurantTable.table_type.in_(preferred_types)
        ).count()

        if suitable_tables > 0:
            score += suitable_tables * 5

        recommendations.append({
            'restaurant': restaurant,
            'score': score,
            'suitable_tables': suitable_tables,
            'reason': _generate_reason(occasion, mood, restaurant)
        })

    # Sort by score descending
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return recommendations[:6]


def _generate_reason(occasion, mood, restaurant):
    """Generate a human-readable recommendation reason."""
    reasons = [
        f"Perfect for your {occasion.lower()} with its {mood.lower()} ambiance.",
        f"Rated {restaurant.rating}★ — guests love the {restaurant.cuisine_type.lower()} experience here.",
        f"Known for exceptional {restaurant.cuisine_type.lower()} cuisine, ideal for a {mood.lower()} {occasion.lower()}.",
        f"Top-rated {restaurant.cuisine_type.lower()} spot with the perfect atmosphere for your event.",
    ]
    return random.choice(reasons)


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@main.route('/')
def index():
    """Splash / Landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('index.html')


# ═══════════════════════════════════════════════════════════════════════════
# AUTHENTICATION ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with email and password."""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        # Validate inputs
        if not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('login.html')

        # Find user by email
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact support.', 'danger')
                return render_template('login.html')
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.full_name}!', 'success')
            # Redirect admin to admin dashboard
            if user.is_admin:
                return redirect(url_for('main.admin_dashboard'))
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@main.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle new user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # ── Validation ──────────────────────────────────────────────────
        errors = []
        if not full_name or len(full_name) < 2:
            errors.append('Full name must be at least 2 characters.')
        if not email or '@' not in email or '.' not in email:
            errors.append('Please enter a valid email address.')
        if not phone or len(phone) < 10 or not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            errors.append('Please enter a valid phone number (at least 10 digits).')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('signup.html')

        # ── Create new user ─────────────────────────────────────────────
        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role='customer'
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()

            # Award 100 welcome reward points
            welcome_reward = Reward(
                user_id=new_user.id,
                points=100,
                description='Welcome bonus for joining DelishNex!',
                reward_type='earned'
            )
            new_user.reward_points = 100
            db.session.add(welcome_reward)
            db.session.commit()

            flash('Account created successfully! You earned 100 welcome reward points. Please log in.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')

    return render_template('signup.html')


@main.route('/logout')
@login_required
def logout():
    """Log out the current user and clear session data."""
    session.pop('cart', None)
    session.pop('reservation', None)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@main.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        # Always show success to prevent email enumeration
        flash('If an account with that email exists, password reset instructions have been sent.', 'info')
        return redirect(url_for('main.login'))
    return render_template('login.html', forgot_password=True)


# ═══════════════════════════════════════════════════════════════════════════
# HOME & MAIN PAGES
# ═══════════════════════════════════════════════════════════════════════════

@main.route('/home')
@login_required
def home():
    """Main home page with search, specials, popular dishes, and categories."""
    # Fetch today's specials (dishes marked as special)
    specials = Menu.query.filter_by(is_special=True, is_available=True).limit(8).all()

    # Fetch popular dishes (highest rated)
    popular = Menu.query.filter_by(is_available=True).order_by(Menu.rating.desc()).limit(8).all()

    # Fetch restaurants
    restaurants = Restaurant.query.filter_by(is_active=True).all()

    # Categories
    categories = [
        {'name': 'Starters', 'icon': 'fa-utensils', 'value': 'starter'},
        {'name': 'Main Course', 'icon': 'fa-drumstick-bite', 'value': 'main_course'},
        {'name': 'Desserts', 'icon': 'fa-ice-cream', 'value': 'dessert'},
        {'name': 'Beverages', 'icon': 'fa-glass-cheers', 'value': 'beverage'},
        {'name': 'Combos', 'icon': 'fa-layer-group', 'value': 'combo'},
    ]

    return render_template('home.html',
                           specials=specials,
                           popular=popular,
                           restaurants=restaurants,
                           categories=categories)


@main.route('/search')
@login_required
def search():
    """Search restaurants and menu items."""
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('main.home'))

    restaurants = Restaurant.query.filter(
        Restaurant.name.ilike(f'%{query}%') |
        Restaurant.cuisine_type.ilike(f'%{query}%')
    ).filter_by(is_active=True).all()

    menu_items = Menu.query.filter(
        Menu.name.ilike(f'%{query}%') |
        Menu.description.ilike(f'%{query}%')
    ).filter_by(is_available=True).all()

    return render_template('home.html',
                           search_query=query,
                           search_restaurants=restaurants,
                           search_menu=menu_items,
                           specials=[],
                           popular=[],
                           restaurants=[],
                           categories=[])


# ═══════════════════════════════════════════════════════════════════════════
# RESTAURANT GALLERY
# ═══════════════════════════════════════════════════════════════════════════

@main.route('/gallery')
@login_required
def gallery():
    """Display all restaurants in a gallery view."""
    restaurants = Restaurant.query.filter_by(is_active=True).all()
    return render_template('gallery.html', restaurants=restaurants)


# ═══════════════════════════════════════════════════════════════════════════
# RESERVATION FLOW
# ═══════════════════════════════════════════════════════════════════════════

@main.route('/occasion/<int:restaurant_id>')
@login_required
def occasion(restaurant_id):
    """Step 1: Choose the occasion for dining."""
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    occasions = [
        {'name': 'Birthday', 'icon': 'fa-birthday-cake', 'color': '#FF6B6B'},
        {'name': 'Anniversary', 'icon': 'fa-heart', 'color': '#E91E63'},
        {'name': 'Date Night', 'icon': 'fa-glass-cheers', 'color': '#9C27B0'},
        {'name': 'Business Meeting', 'icon': 'fa-briefcase', 'color': '#2196F3'},
        {'name': 'Family Gathering', 'icon': 'fa-users', 'color': '#4CAF50'},
        {'name': 'Friends Hangout', 'icon': 'fa-user-friends', 'color': '#FF9800'},
        {'name': 'Casual Dining', 'icon': 'fa-utensils', 'color': '#00BCD4'},
    ]
    # Initialize reservation session
    session['reservation'] = {'restaurant_id': restaurant_id}
    session.modified = True
    return render_template('occasion.html', restaurant=restaurant, occasions=occasions)


@main.route('/mood/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def mood(restaurant_id):
    """Step 2: Choose the dining mood / ambience."""
    restaurant = Restaurant.query.get_or_404(restaurant_id)

    if request.method == 'POST' or request.args.get('occasion'):
        occasion_choice = request.form.get('occasion') or request.args.get('occasion')
        if 'reservation' not in session:
            session['reservation'] = {'restaurant_id': restaurant_id}
        session['reservation']['occasion'] = occasion_choice
        session.modified = True

    moods = [
        {'name': 'Romantic', 'icon': 'fa-heart', 'color': '#E91E63', 'desc': 'Candlelit and intimate'},
        {'name': 'Lively', 'icon': 'fa-music', 'color': '#FF9800', 'desc': 'Energetic and vibrant'},
        {'name': 'Quiet', 'icon': 'fa-volume-mute', 'color': '#607D8B', 'desc': 'Peaceful and serene'},
        {'name': 'Festive', 'icon': 'fa-star', 'color': '#FFC107', 'desc': 'Celebratory and joyful'},
        {'name': 'Cozy', 'icon': 'fa-mug-hot', 'color': '#795548', 'desc': 'Warm and comfortable'},
        {'name': 'Elegant', 'icon': 'fa-gem', 'color': '#9C27B0', 'desc': 'Sophisticated and refined'},
    ]
    return render_template('mood.html', restaurant=restaurant, moods=moods)


@main.route('/date/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def select_date(restaurant_id):
    """Step 3: Select reservation date."""
    restaurant = Restaurant.query.get_or_404(restaurant_id)

    if request.method == 'POST' or request.args.get('mood'):
        mood_choice = request.form.get('mood') or request.args.get('mood')
        if 'reservation' not in session:
            session['reservation'] = {'restaurant_id': restaurant_id}
        session['reservation']['mood'] = mood_choice
        session.modified = True

    # Generate available dates for the next 30 days
    today = date.today()
    available_dates = [(today + timedelta(days=i)) for i in range(30)]

    return render_template('date.html', restaurant=restaurant, available_dates=available_dates)


@main.route('/time/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def select_time(restaurant_id):
    """Step 4: Select reservation time."""
    restaurant = Restaurant.query.get_or_404(restaurant_id)

    if request.method == 'POST' or request.args.get('date'):
        date_choice = request.form.get('date') or request.args.get('date')
        if 'reservation' not in session:
            session['reservation'] = {'restaurant_id': restaurant_id}
        session['reservation']['date'] = date_choice
        session.modified = True

    # Generate time slots based on restaurant hours
    time_slots = []
    start_hour = restaurant.opening_time.hour
    end_hour = restaurant.closing_time.hour
    for hour in range(start_hour, end_hour):
        for minute in [0, 30]:
            t = time(hour, minute)
            time_slots.append(t.strftime('%H:%M'))

    return render_template('time.html', restaurant=restaurant, time_slots=time_slots)


@main.route('/members/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def members(restaurant_id):
    """Step 5: Select number of members."""
    restaurant = Restaurant.query.get_or_404(restaurant_id)

    if request.method == 'POST' or request.args.get('time'):
        time_choice = request.form.get('time') or request.args.get('time')
        if 'reservation' not in session:
            session['reservation'] = {'restaurant_id': restaurant_id}
        session['reservation']['time'] = time_choice
        session.modified = True

    return render_template('members.html', restaurant=restaurant)


@main.route('/recommendation/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def recommendation(restaurant_id):
    """Step 6: AI-powered recommendation based on user preferences."""
    restaurant = Restaurant.query.get_or_404(restaurant_id)

    if request.method == 'POST' or request.args.get('members'):
        members_choice = request.form.get('members') or request.args.get('members')
        if 'reservation' not in session:
            session['reservation'] = {'restaurant_id': restaurant_id}
        session['reservation']['members'] = int(members_choice) if members_choice else 2
        session.modified = True

    res_data = session.get('reservation', {})
    occasion = res_data.get('occasion', 'Casual Dining')
    dining_mood = res_data.get('mood', 'Lively')
    member_count = res_data.get('members', 2)

    # Get AI recommendations
    recommendations = get_ai_recommendation(occasion, dining_mood, member_count, restaurant_id)

    return render_template('recommendation.html',
                           restaurant=restaurant,
                           recommendations=recommendations,
                           occasion=occasion,
                           mood=dining_mood,
                           members=member_count)


@main.route('/layout/<int:restaurant_id>')
@login_required
def restaurant_layout(restaurant_id):
    """Step 7: View restaurant floor layout with available tables."""
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    res_data = session.get('reservation', {})

    # Update restaurant_id in session (user may have picked a different restaurant from recommendation)
    res_data['restaurant_id'] = restaurant_id
    session['reservation'] = res_data
    session.modified = True

    reservation_date_str = res_data.get('date')
    reservation_time_str = res_data.get('time')
    member_count = res_data.get('members', 2)

    tables = RestaurantTable.query.filter_by(
        restaurant_id=restaurant_id,
        is_active=True
    ).all()

    # Find booked tables for the selected date/time
    booked_table_ids = set()
    if reservation_date_str and reservation_time_str:
        try:
            res_date = datetime.strptime(reservation_date_str, '%Y-%m-%d').date()
            res_time = datetime.strptime(reservation_time_str, '%H:%M').time()
            booked = Reservation.query.filter(
                Reservation.restaurant_id == restaurant_id,
                Reservation.reservation_date == res_date,
                Reservation.reservation_time == res_time,
                Reservation.status.in_(['pending', 'confirmed'])
            ).all()
            booked_table_ids = {r.table_id for r in booked}
        except (ValueError, TypeError):
            pass

    # Enrich table data with availability status
    table_data = []
    for t in tables:
        table_data.append({
            'id': t.id,
            'number': t.table_number,
            'capacity': t.capacity,
            'type': t.table_type,
            'pos_x': t.pos_x,
            'pos_y': t.pos_y,
            'is_booked': t.id in booked_table_ids,
            'is_suitable': t.capacity >= member_count
        })

    return render_template('floor_layout.html',
                           restaurant=restaurant,
                           tables=table_data,
                           members=member_count)


@main.route('/preview/<int:restaurant_id>/<int:table_id>')
@login_required
def preview(restaurant_id, table_id):
    """Step 8: Preview selected table before confirming."""
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    table = RestaurantTable.query.get_or_404(table_id)
    res_data = session.get('reservation', {})

    # Save selected table to session
    res_data['table_id'] = table_id
    session['reservation'] = res_data
    session.modified = True

    return render_template('preview.html',
                           restaurant=restaurant,
                           table=table,
                           reservation=res_data)


@main.route('/planner/<int:restaurant_id>')
@login_required
def planner(restaurant_id):
    """Step 9: Dining planner summary before proceeding to food ordering."""
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    res_data = session.get('reservation', {})
    table = None
    if res_data.get('table_id'):
        table = RestaurantTable.query.get(res_data['table_id'])

    return render_template('planner.html',
                           restaurant=restaurant,
                           table=table,
                           reservation=res_data)


@main.route('/confirm-reservation', methods=['POST'])
@login_required
def confirm_reservation():
    """Create the reservation record in the database."""
    res_data = session.get('reservation', {})

    # Validate required fields
    required = ['restaurant_id', 'table_id', 'date', 'time', 'members']
    for field in required:
        if field not in res_data:
            flash('Missing reservation details. Please start over.', 'danger')
            return redirect(url_for('main.gallery'))

    try:
        reservation = Reservation(
            user_id=current_user.id,
            restaurant_id=res_data['restaurant_id'],
            table_id=res_data['table_id'],
            occasion=res_data.get('occasion', ''),
            dining_mood=res_data.get('mood', ''),
            reservation_date=datetime.strptime(res_data['date'], '%Y-%m-%d').date(),
            reservation_time=datetime.strptime(res_data['time'], '%H:%M').time(),
            members=res_data.get('members', 2),
            status='confirmed',
            special_request=res_data.get('special_request', '')
        )
        db.session.add(reservation)
        db.session.commit()

        # Store reservation id for linking with food order
        session['reservation']['reservation_id'] = reservation.id
        session.modified = True

        # Award 50 reward points for booking
        reward = Reward(
            user_id=current_user.id,
            points=50,
            description=f'Reservation #{reservation.id} confirmed',
            reward_type='earned'
        )
        current_user.reward_points += 50
        db.session.add(reward)
        db.session.commit()

        flash('Reservation confirmed! You earned 50 reward points.', 'success')
        return redirect(url_for('main.menu', restaurant_id=res_data['restaurant_id']))
    except Exception as e:
        db.session.rollback()
        flash('Error creating reservation. Please try again.', 'danger')
        return redirect(url_for('main.gallery'))


# ═══════════════════════════════════════════════════════════════════════════
# FOOD MENU & ORDERING
# ═══════════════════════════════════════════════════════════════════════════

@main.route('/menu/<int:restaurant_id>')
@login_required
def menu(restaurant_id):
    """Display the restaurant menu with filtering and search."""
    restaurant = Restaurant.query.get_or_404(restaurant_id)

    category = request.args.get('category', 'all')
    search_q = request.args.get('q', '').strip()
    veg_only = request.args.get('veg') == '1'

    query = Menu.query.filter_by(restaurant_id=restaurant_id, is_available=True)

    if category != 'all':
        query = query.filter_by(category=category)
    if search_q:
        query = query.filter(Menu.name.ilike(f'%{search_q}%'))
    if veg_only:
        query = query.filter_by(is_vegetarian=True)

    menu_items = query.order_by(Menu.category, Menu.name).all()

    # Group by category
    grouped_menu = {}
    for item in menu_items:
        cat = item.category
        if cat not in grouped_menu:
            grouped_menu[cat] = []
        grouped_menu[cat].append(item)

    return render_template('menu.html',
                           restaurant=restaurant,
                           grouped_menu=grouped_menu,
                           current_category=category,
                           search_query=search_q,
                           veg_only=veg_only)


@main.route('/dish/<int:dish_id>')
@login_required
def dish(dish_id):
    """Display detailed view of a single dish."""
    item = Menu.query.get_or_404(dish_id)
    restaurant = Restaurant.query.get(item.restaurant_id)

    # Get related items from the same category
    related = Menu.query.filter(
        Menu.restaurant_id == item.restaurant_id,
        Menu.category == item.category,
        Menu.id != item.id,
        Menu.is_available == True
    ).limit(4).all()

    return render_template('dish.html',
                           dish=item,
                           restaurant=restaurant,
                           related=related)


# ── Cart API Endpoints ──────────────────────────────────────────────────

@main.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """Add an item to the shopping cart."""
    menu_id = request.form.get('menu_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)

    if not menu_id:
        flash('Invalid item.', 'danger')
        return redirect(request.referrer or url_for('main.home'))

    item = Menu.query.get_or_404(menu_id)
    cart = get_cart()

    # Check if item already in cart — update quantity
    found = False
    for cart_item in cart:
        if cart_item['menu_id'] == menu_id:
            cart_item['quantity'] += quantity
            found = True
            break

    if not found:
        cart.append({
            'menu_id': item.id,
            'name': item.name,
            'price': float(item.price),
            'quantity': quantity,
            'restaurant_id': item.restaurant_id,
            'is_vegetarian': item.is_vegetarian,
            'image_url': item.image_url
        })

    save_cart(cart)
    flash(f'{item.name} added to cart!', 'success')
    return redirect(request.referrer or url_for('main.menu', restaurant_id=item.restaurant_id))


@main.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    """Update item quantity in the cart."""
    menu_id = request.form.get('menu_id', type=int)
    action = request.form.get('action', '')

    cart = get_cart()
    for cart_item in cart:
        if cart_item['menu_id'] == menu_id:
            if action == 'increase':
                cart_item['quantity'] += 1
            elif action == 'decrease':
                cart_item['quantity'] -= 1
                if cart_item['quantity'] <= 0:
                    cart.remove(cart_item)
            elif action == 'remove':
                cart.remove(cart_item)
            break

    save_cart(cart)
    return redirect(url_for('main.cart'))


@main.route('/cart')
@login_required
def cart():
    """Display the shopping cart with totals."""
    cart_items = get_cart()
    totals = calculate_cart_totals(cart_items)

    # Check if a coupon is applied
    coupon = session.get('coupon', None)
    discount = 0
    if coupon:
        discount = totals['subtotal'] * 0.10  # 10% discount
        totals['discount'] = round(discount, 2)
        totals['grand_total'] = round(totals['grand_total'] - discount, 2)

    return render_template('cart.html',
                           cart_items=cart_items,
                           totals=totals,
                           coupon=coupon)


@main.route('/cart/coupon', methods=['POST'])
@login_required
def apply_coupon():
    """Apply a coupon code to the cart."""
    code = request.form.get('coupon_code', '').strip().upper()

    # Simple coupon validation
    valid_coupons = {
        'DELISH10': 10, 'WELCOME20': 20, 'SAVE15': 15,
        'FOODIE25': 25, 'FIRST50': 50
    }

    if code in valid_coupons:
        session['coupon'] = {'code': code, 'discount': valid_coupons[code]}
        session.modified = True
        flash(f'Coupon {code} applied! {valid_coupons[code]}% discount.', 'success')
    else:
        session.pop('coupon', None)
        flash('Invalid coupon code.', 'danger')

    return redirect(url_for('main.cart'))


# ── Checkout ────────────────────────────────────────────────────────────

@main.route('/checkout')
@login_required
def checkout():
    """Display checkout page with booking + food summary."""
    cart_items = get_cart()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('main.home'))

    totals = calculate_cart_totals(cart_items)
    coupon = session.get('coupon', None)
    if coupon:
        discount = totals['subtotal'] * (coupon['discount'] / 100)
        totals['discount'] = round(discount, 2)
        totals['grand_total'] = round(totals['grand_total'] - discount, 2)

    res_data = session.get('reservation', {})
    restaurant = None
    table = None
    if res_data.get('restaurant_id'):
        restaurant = Restaurant.query.get(res_data['restaurant_id'])
    if res_data.get('table_id'):
        table = RestaurantTable.query.get(res_data['table_id'])

    return render_template('checkout.html',
                           cart_items=cart_items,
                           totals=totals,
                           coupon=coupon,
                           reservation=res_data,
                           restaurant=restaurant,
                           table=table)


@main.route('/place-order', methods=['POST'])
@login_required
def place_order():
    """Process the order: create Order, OrderItems, and Payment records."""
    cart_items = get_cart()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('main.home'))

    payment_method = request.form.get('payment_method', 'cash')
    res_data = session.get('reservation', {})
    restaurant_id = res_data.get('restaurant_id') or (cart_items[0]['restaurant_id'] if cart_items else None)

    if not restaurant_id:
        flash('Could not determine restaurant. Please try again.', 'danger')
        return redirect(url_for('main.home'))

    totals = calculate_cart_totals(cart_items)
    coupon = session.get('coupon', None)
    discount = 0
    coupon_code = None
    if coupon:
        discount = totals['subtotal'] * (coupon['discount'] / 100)
        coupon_code = coupon['code']

    try:
        # ── Create Order ────────────────────────────────────────────────
        order = Order(
            user_id=current_user.id,
            restaurant_id=restaurant_id,
            reservation_id=res_data.get('reservation_id'),
            subtotal=totals['subtotal'],
            gst=totals['gst'],
            service_charge=totals['service_charge'],
            discount=round(discount, 2),
            grand_total=round(totals['grand_total'] - discount, 2),
            coupon_code=coupon_code,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()  # Get order.id without committing

        # ── Create Order Items ──────────────────────────────────────────
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                menu_id=item['menu_id'],
                quantity=item['quantity'],
                unit_price=item['price'],
                total_price=round(item['price'] * item['quantity'], 2)
            )
            db.session.add(order_item)

        # ── Create Payment ──────────────────────────────────────────────
        payment = Payment(
            order_id=order.id,
            user_id=current_user.id,
            amount=order.grand_total,
            payment_method=payment_method,
            payment_status='completed',
            transaction_id=f'TXN{uuid.uuid4().hex[:12].upper()}'
        )
        db.session.add(payment)

        # ── Award Reward Points (1 point per ₹10 spent) ────────────────
        points_earned = int(float(order.grand_total) // 10)
        if points_earned > 0:
            reward = Reward(
                user_id=current_user.id,
                points=points_earned,
                description=f'Order #{order.id} — ₹{order.grand_total}',
                reward_type='earned'
            )
            current_user.reward_points += points_earned
            db.session.add(reward)

        db.session.commit()

        # ── Clear cart and coupon ────────────────────────────────────────
        session.pop('cart', None)
        session.pop('coupon', None)
        session.modified = True

        flash('Order placed successfully!', 'success')
        return redirect(url_for('main.success', order_id=order.id))

    except Exception as e:
        db.session.rollback()
        flash('An error occurred while placing your order. Please try again.', 'danger')
        return redirect(url_for('main.checkout'))


@main.route('/success/<int:order_id>')
@login_required
def success(order_id):
    """Display order success / confirmation page."""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    items = OrderItem.query.filter_by(order_id=order.id).all()
    payment = Payment.query.filter_by(order_id=order.id).first()
    restaurant = Restaurant.query.get(order.restaurant_id)
    reservation = None
    if order.reservation_id:
        reservation = Reservation.query.get(order.reservation_id)

    return render_template('success.html',
                           order=order,
                           items=items,
                           payment=payment,
                           restaurant=restaurant,
                           reservation=reservation)


# ═══════════════════════════════════════════════════════════════════════════
# USER PAGES
# ═══════════════════════════════════════════════════════════════════════════

@main.route('/bookings')
@login_required
def bookings():
    """Display user's reservation and order history."""
    reservations = Reservation.query.filter_by(user_id=current_user.id) \
        .order_by(Reservation.created_at.desc()).all()
    orders = Order.query.filter_by(user_id=current_user.id) \
        .order_by(Order.created_at.desc()).all()

    return render_template('bookings.html',
                           reservations=reservations,
                           orders=orders)


@main.route('/rewards')
@login_required
def rewards():
    """Display user's reward points and transaction history."""
    reward_history = Reward.query.filter_by(user_id=current_user.id) \
        .order_by(Reward.created_at.desc()).all()

    return render_template('reward.html',
                           rewards=reward_history,
                           total_points=current_user.reward_points)


@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Display and update user profile."""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')

        errors = []
        if full_name and len(full_name) >= 2:
            current_user.full_name = full_name
        elif full_name:
            errors.append('Name must be at least 2 characters.')

        if phone:
            clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '')
            if len(clean_phone) >= 10 and clean_phone.isdigit():
                current_user.phone = phone
            else:
                errors.append('Invalid phone number.')

        # Password change
        if new_password:
            if not current_password:
                errors.append('Current password required to set a new password.')
            elif not current_user.check_password(current_password):
                errors.append('Current password is incorrect.')
            elif len(new_password) < 6:
                errors.append('New password must be at least 6 characters.')
            else:
                current_user.set_password(new_password)

        if errors:
            for e in errors:
                flash(e, 'danger')
        else:
            try:
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception:
                db.session.rollback()
                flash('Error updating profile.', 'danger')

        return redirect(url_for('main.profile'))

    # Get user statistics
    order_count = Order.query.filter_by(user_id=current_user.id).count()
    reservation_count = Reservation.query.filter_by(user_id=current_user.id).count()

    return render_template('profile.html',
                           order_count=order_count,
                           reservation_count=reservation_count)


# ═══════════════════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@main.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with key statistics."""
    total_users = User.query.filter_by(role='customer').count()
    total_orders = Order.query.count()
    total_reservations = Reservation.query.count()
    total_revenue = db.session.query(func.sum(Order.grand_total)).scalar() or 0

    pending_orders = Order.query.filter_by(status='pending').count()
    pending_reservations = Reservation.query.filter_by(status='pending').count()
    total_dishes = Menu.query.count()
    total_restaurants = Restaurant.query.count()

    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    # Recent reservations
    recent_reservations = Reservation.query.order_by(Reservation.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_orders=total_orders,
                           total_reservations=total_reservations,
                           total_revenue=float(total_revenue),
                           pending_orders=pending_orders,
                           pending_reservations=pending_reservations,
                           total_dishes=total_dishes,
                           total_restaurants=total_restaurants,
                           recent_orders=recent_orders,
                           recent_reservations=recent_reservations)


# ── Admin Menu Management ──────────────────────────────────────────────

@main.route('/admin/menu')
@admin_required
def admin_menu():
    """Admin: list all menu items with CRUD controls."""
    restaurant_id = request.args.get('restaurant_id', type=int)
    restaurants = Restaurant.query.filter_by(is_active=True).all()

    if restaurant_id:
        items = Menu.query.filter_by(restaurant_id=restaurant_id).order_by(Menu.category).all()
    else:
        items = Menu.query.order_by(Menu.restaurant_id, Menu.category).all()

    return render_template('admin/menu_management.html',
                           items=items,
                           restaurants=restaurants,
                           selected_restaurant=restaurant_id)


@main.route('/admin/menu/add', methods=['POST'])
@admin_required
def admin_add_dish():
    """Admin: add a new dish to the menu."""
    try:
        dish = Menu(
            restaurant_id=request.form.get('restaurant_id', type=int),
            name=request.form.get('name', '').strip(),
            description=request.form.get('description', '').strip(),
            price=Decimal(request.form.get('price', '0')),
            category=request.form.get('category', 'main_course'),
            rating=Decimal(request.form.get('rating', '0')),
            is_vegetarian=bool(request.form.get('is_vegetarian')),
            is_available=bool(request.form.get('is_available', True)),
            is_special=bool(request.form.get('is_special'))
        )
        db.session.add(dish)
        db.session.commit()
        flash(f'Dish "{dish.name}" added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding dish. Please check the form data.', 'danger')

    return redirect(url_for('main.admin_menu'))


@main.route('/admin/menu/edit/<int:dish_id>', methods=['POST'])
@admin_required
def admin_edit_dish(dish_id):
    """Admin: update an existing dish."""
    dish = Menu.query.get_or_404(dish_id)
    try:
        dish.name = request.form.get('name', dish.name).strip()
        dish.description = request.form.get('description', dish.description).strip()
        dish.price = Decimal(request.form.get('price', str(dish.price)))
        dish.category = request.form.get('category', dish.category)
        dish.rating = Decimal(request.form.get('rating', str(dish.rating)))
        dish.is_vegetarian = bool(request.form.get('is_vegetarian'))
        dish.is_available = bool(request.form.get('is_available'))
        dish.is_special = bool(request.form.get('is_special'))
        db.session.commit()
        flash(f'Dish "{dish.name}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating dish.', 'danger')

    return redirect(url_for('main.admin_menu'))


@main.route('/admin/menu/delete/<int:dish_id>', methods=['POST'])
@admin_required
def admin_delete_dish(dish_id):
    """Admin: delete a dish from the menu."""
    dish = Menu.query.get_or_404(dish_id)
    name = dish.name
    try:
        db.session.delete(dish)
        db.session.commit()
        flash(f'Dish "{name}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting dish.', 'danger')

    return redirect(url_for('main.admin_menu'))


# ── Admin Reservation Management ────────────────────────────────────────

@main.route('/admin/reservations')
@admin_required
def admin_reservations():
    """Admin: list all reservations with filtering."""
    status_filter = request.args.get('status', 'all')

    query = Reservation.query.order_by(Reservation.created_at.desc())
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    reservations = query.all()
    return render_template('admin/reservation_management.html',
                           reservations=reservations,
                           current_status=status_filter)


@main.route('/admin/reservation/update/<int:reservation_id>', methods=['POST'])
@admin_required
def admin_update_reservation(reservation_id):
    """Admin: update reservation status (approve/cancel)."""
    reservation = Reservation.query.get_or_404(reservation_id)
    new_status = request.form.get('status', reservation.status)

    try:
        reservation.status = new_status
        db.session.commit()
        flash(f'Reservation #{reservation.id} updated to {new_status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating reservation.', 'danger')

    return redirect(url_for('main.admin_reservations'))


# ── Admin Order Management ──────────────────────────────────────────────

@main.route('/admin/orders')
@admin_required
def admin_orders():
    """Admin: list all orders with filtering."""
    status_filter = request.args.get('status', 'all')

    query = Order.query.order_by(Order.created_at.desc())
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    orders = query.all()
    return render_template('admin/order_management.html',
                           orders=orders,
                           current_status=status_filter)


@main.route('/admin/order/update/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order(order_id):
    """Admin: update order status."""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status', order.status)

    try:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} updated to {new_status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating order.', 'danger')

    return redirect(url_for('main.admin_orders'))


# ═══════════════════════════════════════════════════════════════════════════
# API ENDPOINTS (used by JavaScript on the frontend)
# ═══════════════════════════════════════════════════════════════════════════

@main.route('/api/cart/count')
@login_required
def api_cart_count():
    """Return the number of items in the cart as JSON."""
    cart = get_cart()
    count = sum(item['quantity'] for item in cart)
    return jsonify({'count': count})


@main.route('/api/tables/<int:restaurant_id>')
@login_required
def api_tables(restaurant_id):
    """Return table availability data as JSON."""
    res_date = request.args.get('date')
    res_time = request.args.get('time')

    tables = RestaurantTable.query.filter_by(
        restaurant_id=restaurant_id, is_active=True
    ).all()

    booked_table_ids = set()
    if res_date and res_time:
        try:
            d = datetime.strptime(res_date, '%Y-%m-%d').date()
            t = datetime.strptime(res_time, '%H:%M').time()
            booked = Reservation.query.filter(
                Reservation.restaurant_id == restaurant_id,
                Reservation.reservation_date == d,
                Reservation.reservation_time == t,
                Reservation.status.in_(['pending', 'confirmed'])
            ).all()
            booked_table_ids = {r.table_id for r in booked}
        except (ValueError, TypeError):
            pass

    result = []
    for t in tables:
        result.append({
            'id': t.id,
            'number': t.table_number,
            'capacity': t.capacity,
            'type': t.table_type,
            'pos_x': t.pos_x,
            'pos_y': t.pos_y,
            'is_booked': t.id in booked_table_ids
        })

    return jsonify(result)


# ═══════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@main.app_errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    flash('Page not found.', 'warning')
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return redirect(url_for('main.index'))


@main.app_errorhandler(403)
def forbidden(error):
    """Handle 403 errors."""
    flash('Access denied.', 'danger')
    return redirect(url_for('main.home'))


@main.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    flash('An internal error occurred. Please try again.', 'danger')
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return redirect(url_for('main.index'))
