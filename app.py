from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from functools import wraps
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = 'djoint-secret-key-2026'  # In production, use environment variable

# Configure Database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'djoint.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============ MIDDLEWARE TO PRESERVE BAR IN ALL REQUESTS ============
@app.before_request
def preserve_bar_in_url():
    """Automatically add bar parameter to all URLs if missing"""
    # Skip static files and auth routes
    if request.endpoint in ['static', 'admin_login', 'admin_logout', 'set_bar', 'demo_mode']:
        return None
    
    # Skip POST requests
    if request.method == 'POST':
        return None
    
    # Get bar from URL or session
    url_bar = request.args.get('bar')
    session_bar = session.get('current_bar', 'djoint')
    
    # If bar in URL but different from session, update session
    if url_bar and url_bar != session_bar:
        session['current_bar'] = url_bar
        return None
    
    # If no bar in URL but session has bar, redirect to add it
    if not url_bar and session_bar:
        # Get current URL parameters
        args = {k: v for k, v in request.args.items()}
        args['bar'] = session_bar
        
        # Build new URL
        new_url = f"{request.base_url}?{urlencode(args)}"
        return redirect(new_url)
    
    return None

# ============ BAR CONFIGURATION (MAKE GLOBAL) ============
BARS = {
    'djoint': {
        'id': 'djoint',
        'name': 'D Joint Lounge',
        'address': '123 Main Street, Lagos',
        'phone': '+234 800 000 0000',
        'email': 'info@djoint.com',
        'color': '#667eea',
        'secondary': '#764ba2',
        'logo': 'cocktail',
        'slogan': 'Premier Viewing Center & Relaxation Spot'
    },
    'signature': {
        'id': 'signature',
        'name': 'Signature Lounge',
        'address': '45 Victoria Island, Lagos',
        'phone': '+234 800 111 2222',
        'email': 'info@signaturelounge.ng',
        'color': '#c026d3',
        'secondary': '#a21caf',
        'logo': 'wine-glass-alt',
        'slogan': 'Where Style Meets Comfort'
    },
    'vaniti': {
        'id': 'vaniti',
        'name': 'Vaniti Lounge',
        'address': '12 Ikoyi Road, Lagos',
        'phone': '+234 800 333 4444',
        'email': 'bookings@vaniti.ng',
        'color': '#2563eb',
        'secondary': '#1d4ed8',
        'logo': 'crown',
        'slogan': 'Experience Luxury Redefined'
    },
    'eagles': {
        'id': 'eagles',
        'name': 'Eagles Lounge',
        'address': '78 Abeokuta Expressway',
        'phone': '+234 800 555 6666',
        'email': 'info@eagleslounge.ng',
        'color': '#16a34a',
        'secondary': '#15803d',
        'logo': 'dove',
        'slogan': 'Your Home Away From Home'
    }
}

# Helper function to get current bar
def get_current_bar():
    """Get current bar from URL or session, ensuring consistency"""
    # URL parameter has highest priority
    url_bar = request.args.get('bar')
    if url_bar:
        session['current_bar'] = url_bar
        return url_bar
    
    # Then check session
    session_bar = session.get('current_bar', 'djoint')
    return session_bar

# Admin login required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login to access admin area', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============ DATABASE MODELS ============

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_id = db.Column(db.String(50), default='djoint')
    name = db.Column(db.String(100), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Room {self.name}>'

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_id = db.Column(db.String(50), default='djoint')
    seat_number = db.Column(db.String(10), nullable=False)
    seat_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Seat {self.seat_number}>'

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_id = db.Column(db.String(50), default='djoint')
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    booking_type = db.Column(db.String(20), nullable=False)  # 'seat' or 'room'
    
    # For seat bookings
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=True)
    
    # For room bookings
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)
    hours = db.Column(db.Integer, nullable=True)
    
    # Common fields
    booking_date = db.Column(db.String(20), nullable=False)
    booking_time = db.Column(db.String(20), nullable=True)  # for seats
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    seat = db.relationship('Seat', backref='bookings')
    room = db.relationship('Room', backref='bookings')
    
    def __repr__(self):
        return f'<Booking {self.id} - {self.customer_name}>'

# Food Menu Models
class FoodCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_id = db.Column(db.String(50), default='djoint')
    name = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200), default='category-default.jpg')
    items = db.relationship('FoodItem', backref='category', lazy=True)

class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_id = db.Column(db.String(50), default='djoint')
    category_id = db.Column(db.Integer, db.ForeignKey('food_category.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(200), default='food-default.jpg')
    available = db.Column(db.Boolean, default=True)
    popular = db.Column(db.Boolean, default=False)

class FoodOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_id = db.Column(db.String(50), default='djoint')
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    table_number = db.Column(db.String(10))
    order_type = db.Column(db.String(20))
    total_amount = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_id = db.Column(db.String(50), default='djoint')
    order_id = db.Column(db.Integer, db.ForeignKey('food_order.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Integer)
    food_item = db.relationship('FoodItem')

# Snooker/Pool Tables
class SnookerTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_id = db.Column(db.String(50), default='djoint')
    table_number = db.Column(db.String(10), nullable=False)
    table_type = db.Column(db.String(20))
    price_per_hour = db.Column(db.Integer, nullable=False)
    available = db.Column(db.Boolean, default=True)

class SnookerBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_id = db.Column(db.String(50), default='djoint')
    table_id = db.Column(db.Integer, db.ForeignKey('snooker_table.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    booking_date = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    hours = db.Column(db.Integer)
    total_amount = db.Column(db.Integer)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    table = db.relationship('SnookerTable')

# DJ/Artist Platform
class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_id = db.Column(db.String(50), default='djoint')
    stage_name = db.Column(db.String(100), nullable=False)
    real_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20), nullable=False)
    genre = db.Column(db.String(50))
    bio = db.Column(db.Text)
    social_media = db.Column(db.JSON)
    music_links = db.Column(db.JSON)
    photo = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Performance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_id = db.Column(db.String(50), default='djoint')
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    performance_date = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    artist = db.relationship('Artist')

# ============ MULTI-BAR SUPPORT ============

@app.context_processor
def inject_bar_settings():
    """Inject bar settings based on URL parameter - URL takes priority"""
    bar_id = get_current_bar()
    current_bar = BARS.get(bar_id, BARS['djoint'])
    return dict(bar=current_bar, bar_id=bar_id, bars=BARS)

# Debug switcher (only shows when debug=show in URL)
@app.context_processor
def inject_debug_switcher():
    show_debug = request.args.get('debug') == 'show'
    return dict(show_debug=show_debug)

# Context processor for current time
@app.context_processor
def utility_processor():
    return {'now': datetime.now}

# ============ DEMO MODE ROUTES ============

@app.route('/demo-mode/<action>')
def demo_mode(action):
    """Toggle demo mode - shows/hides the bar switcher"""
    if action == 'on':
        session['demo_mode'] = True
        flash('Demo mode enabled. Bar switcher visible.', 'info')
    elif action == 'off':
        session['demo_mode'] = False
        flash('Demo mode disabled.', 'info')
    elif action == 'toggle':
        session['demo_mode'] = not session.get('demo_mode', False)
        status = 'enabled' if session['demo_mode'] else 'disabled'
        flash(f'Demo mode {status}.', 'info')
    
    return redirect(request.referrer or url_for('home'))

# Add demo_mode to all templates
@app.context_processor
def inject_demo_mode():
    return {'demo_mode_enabled': session.get('demo_mode', False)}

# ============ BAR SWITCHER ROUTE (FIXES PERSISTENCE) ============

@app.route('/set-bar/<bar_id>')
def set_bar(bar_id):
    """Force set the current bar and redirect back to the same page"""
    if bar_id in BARS:
        session['current_bar'] = bar_id
        # Get the page to redirect back to
        redirect_to = request.args.get('redirect', url_for('home'))
        # Ensure the redirect URL has the bar parameter
        if '?' in redirect_to:
            redirect_to += f'&bar={bar_id}'
        else:
            redirect_to += f'?bar={bar_id}'
        bar_name = BARS.get(bar_id, {}).get('name', bar_id.title())
        flash(f'Switched to {bar_name}', 'info')
        return redirect(redirect_to)
    return redirect(url_for('home'))

# ============ CREATE TABLES WITH SAMPLE DATA ============

with app.app_context():
    db.create_all()
    
    # Add sample rooms for each bar if none exist
    bars = ['djoint', 'signature', 'vaniti', 'eagles']
    for bar_id in bars:
        if Room.query.filter_by(bar_id=bar_id).count() == 0:
            sample_rooms = [
                Room(bar_id=bar_id, name='VIP Party Room', room_type='party', price=50000, capacity=20),
                Room(bar_id=bar_id, name='Short Rest Room 1', room_type='rest', price=5000, capacity=2),
                Room(bar_id=bar_id, name='Short Rest Room 2', room_type='rest', price=5000, capacity=2),
            ]
            db.session.add_all(sample_rooms)
    
    # Add sample seats for each bar
    for bar_id in bars:
        if Seat.query.filter_by(bar_id=bar_id).count() == 0:
            sample_seats = []
            for i in range(1, 51):
                seat_type = 'regular' if i > 10 else 'vip'
                price = 2000 if i > 10 else 5000
                seat = Seat(
                    bar_id=bar_id,
                    seat_number=f'S{i:03d}',
                    seat_type=seat_type,
                    price=price,
                    available=True
                )
                sample_seats.append(seat)
            db.session.add_all(sample_seats)
    
    # Add sample snooker tables for each bar
    for bar_id in bars:
        if SnookerTable.query.filter_by(bar_id=bar_id).count() == 0:
            tables = [
                SnookerTable(bar_id=bar_id, table_number='P1', table_type='pool', price_per_hour=5000, available=True),
                SnookerTable(bar_id=bar_id, table_number='P2', table_type='pool', price_per_hour=5000, available=True),
                SnookerTable(bar_id=bar_id, table_number='S1', table_type='snooker', price_per_hour=8000, available=True),
                SnookerTable(bar_id=bar_id, table_number='S2', table_type='snooker', price_per_hour=8000, available=True),
                SnookerTable(bar_id=bar_id, table_number='VIP1', table_type='snooker', price_per_hour=12000, available=True),
            ]
            db.session.add_all(tables)
    
    db.session.commit()

# ============ ADMIN LOGIN ROUTES ============

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    bar_id = get_current_bar()
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email == f'admin@{bar_id}.com' and password == 'Admin123!':
            session['admin_logged_in'] = True
            session['admin_email'] = email
            session['admin_bar_id'] = bar_id
            session['admin_login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            flash(f'Welcome to {bar_id.title()} Lounge Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    session.pop('admin_bar_id', None)
    session.pop('admin_login_time', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('home'))

# ============ CUSTOMER ROUTES (UPDATED TO USE get_current_bar) ============

@app.route('/')
def home():
    bar_id = get_current_bar()
    rooms = Room.query.filter_by(bar_id=bar_id).limit(3).all()
    seats = Seat.query.filter_by(bar_id=bar_id).limit(6).all()
    return render_template('home.html', rooms=rooms, seats=seats)

@app.route('/book-seat', methods=['GET', 'POST'])
def book_seat():
    bar_id = get_current_bar()
    if request.method == 'POST':
        booking = Booking(
            bar_id=bar_id,
            customer_name=request.form['name'],
            customer_phone=request.form['phone'],
            booking_type='seat',
            seat_id=int(request.form['seat_id']),
            booking_date=request.form['date'],
            booking_time=request.form['time'],
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        flash('Seat booked successfully!', 'success')
        return redirect(url_for('my_bookings', bar=bar_id))
    
    seats = Seat.query.filter_by(bar_id=bar_id, available=True).all()
    return render_template('book_seat.html', seats=seats)

@app.route('/book-room', methods=['GET', 'POST'])
def book_room():
    bar_id = get_current_bar()
    if request.method == 'POST':
        booking = Booking(
            bar_id=bar_id,
            customer_name=request.form['name'],
            customer_phone=request.form['phone'],
            booking_type='room',
            room_id=int(request.form['room_id']),
            booking_date=request.form['date'],
            hours=int(request.form['hours']),
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        flash('Room booked successfully!', 'success')
        return redirect(url_for('my_bookings', bar=bar_id))
    
    rooms = Room.query.filter_by(bar_id=bar_id).all()
    return render_template('book_room.html', rooms=rooms)

@app.route('/my-bookings')
def my_bookings():
    bar_id = get_current_bar()
    bookings = Booking.query.filter_by(bar_id=bar_id).order_by(Booking.created_at.desc()).all()
    return render_template('bookings.html', bookings=bookings)

# Food Menu Routes
@app.route('/menu')
def menu():
    bar_id = get_current_bar()
    categories = FoodCategory.query.filter_by(bar_id=bar_id).all()
    popular_items = FoodItem.query.filter_by(bar_id=bar_id, popular=True, available=True).limit(6).all()
    return render_template('menu.html', categories=categories, popular_items=popular_items)

@app.route('/order-food', methods=['GET', 'POST'])
def order_food():
    bar_id = get_current_bar()
    if request.method == 'POST':
        order = FoodOrder(
            bar_id=bar_id,
            customer_name=request.form['name'],
            customer_phone=request.form['phone'],
            table_number=request.form.get('table_number', ''),
            order_type=request.form['order_type'],
            total_amount=int(request.form['total_amount']),
            status='pending'
        )
        db.session.add(order)
        db.session.flush()
        
        items = request.form.getlist('items[]')
        quantities = request.form.getlist('quantities[]')
        prices = request.form.getlist('prices[]')
        
        for i in range(len(items)):
            if int(quantities[i]) > 0:
                item = OrderItem(
                    bar_id=bar_id,
                    order_id=order.id,
                    food_item_id=int(items[i]),
                    quantity=int(quantities[i]),
                    price=int(prices[i])
                )
                db.session.add(item)
        
        db.session.commit()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id, bar=bar_id))
    
    categories = FoodCategory.query.filter_by(bar_id=bar_id).all()
    items = FoodItem.query.filter_by(bar_id=bar_id, available=True).all()
    return render_template('order_food.html', categories=categories, items=items)

@app.route('/order-confirmation/<int:order_id>')
def order_confirmation(order_id):
    order = FoodOrder.query.get_or_404(order_id)
    return render_template('order_confirmation.html', order=order)

# Snooker Routes
@app.route('/snooker')
def snooker():
    bar_id = get_current_bar()
    tables = SnookerTable.query.filter_by(bar_id=bar_id).all()
    return render_template('snooker.html', tables=tables)

@app.route('/book-snooker', methods=['GET', 'POST'])
def book_snooker():
    bar_id = get_current_bar()
    if request.method == 'POST':
        start = request.form['start_time']
        hours = int(request.form['hours'])
        end_hour = int(start.split(':')[0]) + hours
        end_time = f"{end_hour}:{start.split(':')[1]}"
        
        booking = SnookerBooking(
            bar_id=bar_id,
            table_id=int(request.form['table_id']),
            customer_name=request.form['name'],
            customer_phone=request.form['phone'],
            booking_date=request.form['date'],
            start_time=start,
            end_time=end_time,
            hours=hours,
            total_amount=int(request.form['total_amount']),
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        flash('Snooker table booked successfully!', 'success')
        return redirect(url_for('my_snooker_bookings', bar=bar_id))
    
    tables = SnookerTable.query.filter_by(bar_id=bar_id, available=True).all()
    return render_template('book_snooker.html', tables=tables)

@app.route('/my-snooker-bookings')
def my_snooker_bookings():
    bar_id = get_current_bar()
    bookings = SnookerBooking.query.filter_by(bar_id=bar_id).order_by(SnookerBooking.created_at.desc()).all()
    return render_template('my_snooker_bookings.html', bookings=bookings)

# DJ/Artist Routes
@app.route('/artists')
def artists():
    bar_id = get_current_bar()
    featured = Artist.query.filter_by(bar_id=bar_id, status='featured').all()
    upcoming = Artist.query.filter_by(bar_id=bar_id, status='approved').all()
    performances = Performance.query.filter_by(bar_id=bar_id, status='scheduled').order_by(Performance.performance_date).all()
    return render_template('artists.html', featured=featured, upcoming=upcoming, performances=performances)

@app.route('/artist-signup', methods=['GET', 'POST'])
def artist_signup():
    bar_id = get_current_bar()
    if request.method == 'POST':
        artist = Artist(
            bar_id=bar_id,
            stage_name=request.form['stage_name'],
            real_name=request.form.get('real_name', ''),
            email=request.form.get('email', ''),
            phone=request.form['phone'],
            genre=request.form['genre'],
            bio=request.form['bio'],
            social_media={
                'instagram': request.form.get('instagram', ''),
                'twitter': request.form.get('twitter', ''),
                'tiktok': request.form.get('tiktok', '')
            },
            music_links={
                'soundcloud': request.form.get('soundcloud', ''),
                'youtube': request.form.get('youtube', '')
            },
            status='pending'
        )
        db.session.add(artist)
        db.session.commit()
        flash('Application submitted! We\'ll contact you soon.', 'success')
        return redirect(url_for('artists', bar=bar_id))
    
    return render_template('artist_signup.html', artist=None)

# ============ ADMIN ROUTES (ALL PROTECTED) ============

@app.route('/admin')
@admin_required
def admin_dashboard():
    bar_id = session.get('admin_bar_id', 'djoint')
    bookings = Booking.query.filter_by(bar_id=bar_id).order_by(Booking.created_at.desc()).all()
    rooms = Room.query.filter_by(bar_id=bar_id).all()
    seats = Seat.query.filter_by(bar_id=bar_id).all()
    
    total_bookings = Booking.query.filter_by(bar_id=bar_id).count()
    confirmed_bookings = Booking.query.filter_by(bar_id=bar_id, status='confirmed').count()
    pending_bookings = Booking.query.filter_by(bar_id=bar_id, status='pending').count()
    total_rooms = Room.query.filter_by(bar_id=bar_id).count()
    
    return render_template('admin.html', 
                         bookings=bookings, 
                         rooms=rooms, 
                         seats=seats,
                         total_bookings=total_bookings,
                         confirmed_bookings=confirmed_bookings,
                         pending_bookings=pending_bookings,
                         total_rooms=total_rooms)

@app.route('/admin/confirm/<int:booking_id>')
@admin_required
def confirm_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'confirmed'
    db.session.commit()
    flash(f'Booking #{booking_id} confirmed!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/add-room', methods=['POST'])
@admin_required
def add_room():
    bar_id = session.get('admin_bar_id', 'djoint')
    new_room = Room(
        bar_id=bar_id,
        name=request.form['name'],
        room_type=request.form['type'],
        price=int(request.form['price']),
        capacity=int(request.form['capacity'])
    )
    db.session.add(new_room)
    db.session.commit()
    flash('New room added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    bar_id = session.get('admin_bar_id', 'djoint')
    orders = FoodOrder.query.filter_by(bar_id=bar_id).order_by(FoodOrder.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/update-order/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = FoodOrder.query.get_or_404(order_id)
    order.status = request.form['status']
    db.session.commit()
    flash(f'Order #{order_id} updated to {order.status}', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/artist-applications')
@admin_required
def artist_applications():
    bar_id = session.get('admin_bar_id', 'djoint')
    pending = Artist.query.filter_by(bar_id=bar_id, status='pending').all()
    approved = Artist.query.filter_by(bar_id=bar_id, status='approved').all()
    featured = Artist.query.filter_by(bar_id=bar_id, status='featured').all()
    return render_template('admin/artists.html', pending=pending, approved=approved, featured=featured)

@app.route('/admin/approve-artist/<int:artist_id>')
@admin_required
def approve_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    artist.status = 'approved'
    db.session.commit()
    flash(f'{artist.stage_name} approved!', 'success')
    return redirect(url_for('artist_applications'))

@app.route('/admin/feature-artist/<int:artist_id>')
@admin_required
def feature_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    artist.status = 'featured'
    db.session.commit()
    flash(f'{artist.stage_name} is now featured!', 'success')
    return redirect(url_for('artist_applications'))

@app.route('/admin/reject-artist/<int:artist_id>')
@admin_required
def reject_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    db.session.delete(artist)
    db.session.commit()
    flash('Artist application rejected', 'info')
    return redirect(url_for('artist_applications'))

@app.route('/admin/schedule-performance', methods=['POST'])
@admin_required
def schedule_performance():
    bar_id = session.get('admin_bar_id', 'djoint')
    performance = Performance(
        bar_id=bar_id,
        artist_id=int(request.form['artist_id']),
        performance_date=request.form['date'],
        start_time=request.form['start_time'],
        end_time=request.form['end_time'],
        status='scheduled'
    )
    db.session.add(performance)
    db.session.commit()
    flash('Performance scheduled!', 'success')
    return redirect(url_for('artist_applications'))

@app.route('/admin/snooker-bookings')
@admin_required
def admin_snooker_bookings():
    bar_id = session.get('admin_bar_id', 'djoint')
    bookings = SnookerBooking.query.filter_by(bar_id=bar_id).order_by(SnookerBooking.created_at.desc()).all()
    tables = SnookerTable.query.filter_by(bar_id=bar_id).all()
    return render_template('admin/snooker.html', bookings=bookings, tables=tables)

@app.route('/admin/confirm-snooker/<int:booking_id>')
@admin_required
def confirm_snooker_booking(booking_id):
    booking = SnookerBooking.query.get_or_404(booking_id)
    booking.status = 'confirmed'
    db.session.commit()
    flash(f'Snooker booking #{booking_id} confirmed!', 'success')
    return redirect(url_for('admin_snooker_bookings'))

@app.route('/admin/add-snooker-table', methods=['POST'])
@admin_required
def add_snooker_table():
    bar_id = session.get('admin_bar_id', 'djoint')
    new_table = SnookerTable(
        bar_id=bar_id,
        table_number=request.form['table_number'],
        table_type=request.form['table_type'],
        price_per_hour=int(request.form['price_per_hour']),
        available=True
    )
    db.session.add(new_table)
    db.session.commit()
    flash('New snooker table added successfully!', 'success')
    return redirect(url_for('admin_snooker_bookings'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)