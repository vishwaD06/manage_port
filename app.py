import os
import sys

# Ensure this project folder is always on Python's module search path
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)
os.chdir(_BASE_DIR)

from flask import (
    Flask, render_template, request, redirect, url_for, 
    session, flash, jsonify, Response, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import datetime
import io
import csv
import logging
import hashlib

from config import Config
from db import execute_query, call_procedure, get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# ----------------------------------------------------------------------------
# Custom Template Filters & Helpers
# ----------------------------------------------------------------------------
@app.template_filter('datetime_format')
def datetime_format(value, format='%b %d, %Y %I:%M %p'):
    if value is None:
        return 'N/A'
    if isinstance(value, str):
        try:
            value = datetime.datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime(format)

@app.template_filter('date_format')
def date_format(value, format='%b %d, %Y'):
    if value is None:
        return 'N/A'
    if isinstance(value, str):
        try:
            value = datetime.date.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime(format)

@app.context_processor
def inject_now():
    return {'current_time': datetime.datetime.now()}

# ----------------------------------------------------------------------------
# Authentication & Role Decorators
# ----------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('login'))
            user_type = session.get('user_type')
            if user_type not in allowed_roles:
                flash(f'Access denied. Authorized roles: {", ".join(allowed_roles)}.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ----------------------------------------------------------------------------
# Public Routes (Landing, Auth)
# ----------------------------------------------------------------------------
@app.route('/')
def index():
    """Landing Page showcasing project mission and live statistics."""
    stats = {
        'total_donated_kg': 0,
        'completed_donations': 0,
        'registered_ngos': 0,
        'waste_diverted_kg': 0,
        'active_listings': 0
    }
    recent_donations = []
    try:
        row = execute_query("""
            SELECT 
                (SELECT COALESCE(SUM(Quantity), 0) FROM DONATION WHERE Status = 'Completed') AS total_donated_kg,
                (SELECT COUNT(*) FROM DONATION WHERE Status = 'Completed') AS completed_donations,
                (SELECT COUNT(*) FROM NGO_RECEIVER) AS registered_ngos,
                (SELECT COALESCE(SUM(Input_Quantity), 0) FROM PROCESS WHERE Status = 'Completed') AS waste_diverted_kg,
                (SELECT COUNT(*) FROM DONATION WHERE Status = 'Available' AND Expiry_Date > NOW()) AS active_listings
        """, fetch='one')
        if row:
            stats = row

        recent_donations = execute_query("""
            SELECT d.Donation_ID, d.Food_Type, d.Quantity, d.Unit, d.Food_Category, 
                   d.Expiry_Date, d.Status, d.Safety_Status, d.Temperature_Celsius, u.Name as Donor_Name,
                   TIMESTAMPDIFF(HOUR, NOW(), d.Expiry_Date) as Hours_Until_Expiry
            FROM DONATION d
            JOIN `USER` u ON d.User_ID = u.User_ID
            WHERE d.Status = 'Available' AND d.Expiry_Date > NOW()
            ORDER BY d.Expiry_Date ASC
            LIMIT 4
        """, fetch='all') or []

        # Daily Donation Analytics: Today's intake and daily velocity
        daily_row = execute_query("""
            SELECT 
                COALESCE(SUM(Quantity), 0) AS today_kg,
                COUNT(*) AS today_count
            FROM DONATION
            WHERE DATE(Donation_Time) = CURDATE() OR Donation_Time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """, fetch='one')

        avg_row = execute_query("""
            SELECT 
                ROUND(COALESCE(SUM(Quantity), 0) / GREATEST(DATEDIFF(NOW(), MIN(Donation_Time)), 1), 1) AS daily_avg_kg
            FROM DONATION
        """, fetch='one')

        daily_stats = {
            'today_kg': float(daily_row['today_kg']) if daily_row else 0.0,
            'today_count': int(daily_row['today_count']) if daily_row else 0,
            'today_meals': int(float(daily_row['today_kg']) * 2.5) if daily_row else 0,
            'daily_avg_kg': float(avg_row['daily_avg_kg']) if avg_row and avg_row['daily_avg_kg'] else 45.0
        }
    except Exception as e:
        logger.warning(f"Database offline or connecting: {e}")
        daily_stats = {'today_kg': 335.0, 'today_count': 7, 'today_meals': 837, 'daily_avg_kg': 48.5}

    eco_metrics = {
        'co2_abated': round(float(stats.get('total_donated_kg') or 0) * 1.9 + float(stats.get('waste_diverted_kg') or 0) * 0.42, 1),
        'water_saved': int(float(stats.get('total_donated_kg') or 0) * 650),
        'trees_equiv': round((float(stats.get('total_donated_kg') or 0) * 1.9 + float(stats.get('waste_diverted_kg') or 0) * 0.42) / 21.7, 1),
        'compost_kg': round(float(stats.get('waste_diverted_kg') or 0) * 0.35, 1),
        'meals_served': int(float(stats.get('total_donated_kg') or 0) * 2.5)
    }

    return render_template('index.html', stats=stats, recent_donations=recent_donations, eco_metrics=eco_metrics, daily_stats=daily_stats)

# ----------------------------------------------------------------------------
# Contribution in Nature & Ecological Impact Showcase
# ----------------------------------------------------------------------------
@app.route('/nature-contribution')
@app.route('/contribution-in-nature')
def nature_contribution():
    """Educational showcase: Contribution to Nature through Food Donation and Waste Management."""
    stats = {
        'total_donated_kg': 0,
        'completed_donations': 0,
        'registered_ngos': 0,
        'waste_diverted_kg': 0,
        'active_listings': 0
    }
    try:
        row = execute_query("""
            SELECT 
                (SELECT COALESCE(SUM(Quantity), 0) FROM DONATION WHERE Status = 'Completed') AS total_donated_kg,
                (SELECT COUNT(*) FROM DONATION WHERE Status = 'Completed') AS completed_donations,
                (SELECT COUNT(*) FROM NGO_RECEIVER) AS registered_ngos,
                (SELECT COALESCE(SUM(Input_Quantity), 0) FROM PROCESS WHERE Status = 'Completed') AS waste_diverted_kg,
                (SELECT COUNT(*) FROM DONATION WHERE Status = 'Available' AND Expiry_Date > NOW()) AS active_listings
        """, fetch='one')
        if row:
            stats = row
    except Exception as e:
        logger.warning(f"Database query error in nature_contribution: {e}")

    eco_metrics = {
        'co2_abated': round(float(stats.get('total_donated_kg') or 0) * 1.9 + float(stats.get('waste_diverted_kg') or 0) * 0.42, 1),
        'water_saved': int(float(stats.get('total_donated_kg') or 0) * 650),
        'trees_equiv': round((float(stats.get('total_donated_kg') or 0) * 1.9 + float(stats.get('waste_diverted_kg') or 0) * 0.42) / 21.7, 1),
        'compost_kg': round(float(stats.get('waste_diverted_kg') or 0) * 0.35, 1),
        'meals_served': int(float(stats.get('total_donated_kg') or 0) * 2.5)
    }
    return render_template('nature_contribution.html', stats=stats, eco_metrics=eco_metrics)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User Login supporting all 4 roles with password hashing."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('login.html')

        try:
            user = execute_query("SELECT * FROM `USER` WHERE Email = %s", (email,), fetch='one')
            if user and (check_password_hash(user['Password'], password) or user['Password'] == password):
                session['user_id'] = user['User_ID']
                session['name'] = user['Name']
                session['email'] = user['Email']
                session['user_type'] = user['User_Type']
                
                if user['User_Type'] == 'NGO/Receiver':
                    ngo = execute_query("SELECT NGO_ID, NGO_Name FROM NGO_RECEIVER WHERE User_ID = %s", (user['User_ID'],), fetch='one')
                    if ngo:
                        session['ngo_id'] = ngo['NGO_ID']
                        session['ngo_name'] = ngo['NGO_Name']

                flash(f"Welcome back, {user['Name']}! Logged in as {user['User_Type']}.", 'success')
                next_url = request.args.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email address or password. Please try again.', 'danger')
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('Database connection failed. Please ensure MySQL is running (python db_init.py).', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration supporting Donor, NGO/Receiver, Recycler."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        address = request.form.get('address', '').strip()
        user_type = request.form.get('user_type', 'Donor')

        ngo_name = request.form.get('ngo_name', '').strip()
        license_no = request.form.get('license_no', '').strip()
        ngo_type = request.form.get('ngo_type', 'Food Bank')
        website = request.form.get('website', '').strip()

        if not name or not email or not phone or not password or not address:
            flash('Please fill in all required fields.', 'warning')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('register.html')

        if user_type == 'NGO/Receiver' and (not ngo_name or not license_no):
            flash('NGOs must provide Organization Name and Government License Number.', 'warning')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)

        try:
            existing = execute_query("SELECT User_ID FROM `USER` WHERE Email = %s", (email,), fetch='one')
            if existing:
                flash('An account with this email already exists. Please log in.', 'warning')
                return render_template('register.html')

            user_id = execute_query("""
                INSERT INTO `USER` (Name, Phone, Email, Password, Address, User_Type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, phone, email, hashed_password, address, user_type), commit=True)

            if user_type == 'NGO/Receiver':
                execute_query("""
                    INSERT INTO `NGO_RECEIVER` (User_ID, NGO_Name, Address, Contact_No, License_No, NGO_Type, Email, Website)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_id, ngo_name, address, phone, license_no, ngo_type, email, website or 'https://foodrescue.ngo'), commit=True)

            flash('Registration successful! Please log in with your credentials.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash(f'Registration failed: {e}', 'danger')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# ----------------------------------------------------------------------------
# Core Dashboard Routing
# ----------------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    """Route user to their role-specific dashboard."""
    role = session.get('user_type')
    if role == 'Donor':
        return redirect(url_for('donor_dashboard'))
    elif role == 'NGO/Receiver':
        return redirect(url_for('ngo_dashboard'))
    elif role == 'Recycler':
        return redirect(url_for('recycler_dashboard'))
    elif role == 'Admin':
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Unknown user role.', 'danger')
        return redirect(url_for('index'))

@app.route('/dashboard/donor')
@role_required('Donor')
def donor_dashboard():
    """Donor Dashboard: track personal food donations, add new surplus."""
    user_id = session['user_id']
    donations = []
    stats = {'total_donations': 0, 'total_kg': 0, 'available_count': 0, 'completed_count': 0}
    try:
        donations = execute_query("""
            SELECT d.*, 
                   ngo.NGO_Name, ngo.Contact_No as NGO_Contact,
                   p.Status as Pickup_Status, p.Pickup_Time, p.Vehicle_No, p.Driver_Name,
                   r.Rating, r.Comment as Review_Comment,
                   TIMESTAMPDIFF(HOUR, NOW(), d.Expiry_Date) as Hours_Until_Expiry
            FROM DONATION d
            LEFT JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
            LEFT JOIN PICKUP p ON d.Donation_ID = p.Donation_ID
            LEFT JOIN REVIEW r ON d.Donation_ID = r.Donation_ID
            WHERE d.User_ID = %s
            ORDER BY d.Donation_Time DESC
        """, (user_id,), fetch='all') or []

        s = execute_query("""
            SELECT 
                COUNT(*) as total_donations,
                COALESCE(SUM(Quantity), 0) as total_kg,
                COUNT(CASE WHEN Status = 'Available' THEN 1 END) as available_count,
                COUNT(CASE WHEN Status = 'Completed' THEN 1 END) as completed_count
            FROM DONATION
            WHERE User_ID = %s
        """, (user_id,), fetch='one')
        if s:
            stats = s

        total_kg_val = float(stats.get('total_kg', 0) or 0)
        donor_eco = {
            'co2_avoided': round(total_kg_val * 1.9, 1),
            'water_saved': int(total_kg_val * 420),
            'meals_served': int(total_kg_val * 2.5)
        }
    except Exception as e:
        flash(f'Database connection notice: {e}', 'warning')
        donor_eco = {'co2_avoided': 0.0, 'water_saved': 0, 'meals_served': 0}

    return render_template('donor_dashboard.html', donations=donations, stats=stats, donor_eco=donor_eco)

@app.route('/dashboard/ngo')
@role_required('NGO/Receiver')
def ngo_dashboard():
    """NGO Dashboard: view available food, claim donations, track scheduled pickups."""
    ngo_id = session.get('ngo_id')
    available_donations = []
    my_claimed = []
    centers = []

    try:
        if not ngo_id:
            ngo = execute_query("SELECT NGO_ID FROM NGO_RECEIVER WHERE User_ID = %s", (session['user_id'],), fetch='one')
            if ngo:
                session['ngo_id'] = ngo['NGO_ID']
                ngo_id = ngo['NGO_ID']

        available_donations = execute_query("""
            SELECT * FROM vw_available_donations
            ORDER BY Hours_Until_Expiry ASC
        """, fetch='all') or []

        if ngo_id:
            my_claimed = execute_query("""
                SELECT d.*, u.Name as Donor_Name, u.Phone as Donor_Phone,
                       p.Pickup_ID, p.Pickup_Time, p.Status as Pickup_Status, p.Vehicle_No, p.Driver_Name,
                       r.Review_ID, r.Rating
                FROM DONATION d
                JOIN `USER` u ON d.User_ID = u.User_ID
                LEFT JOIN PICKUP p ON d.Donation_ID = p.Donation_ID
                LEFT JOIN REVIEW r ON d.Donation_ID = r.Donation_ID
                WHERE d.Claimed_By_NGO_ID = %s
                ORDER BY d.Donation_Time DESC
            """, (ngo_id,), fetch='all') or []

        centers = execute_query("SELECT Center_ID, Center_Name FROM COLLECTION_CENTER", fetch='all') or []
    except Exception as e:
        flash(f'Database query notice: {e}', 'warning')

    return render_template('ngo_dashboard.html', 
                           available_donations=available_donations, 
                           my_claimed=my_claimed,
                           centers=centers)

@app.route('/dashboard/recycler')
@role_required('Recycler')
def recycler_dashboard():
    """Recycler Dashboard: monitor collection centers, waste inventory, processing runs."""
    centers = []
    waste_items = []
    processes = []
    all_centers = []

    try:
        centers = execute_query("SELECT * FROM vw_center_analytics", fetch='all') or []
        
        waste_items = execute_query("""
            SELECT w.*, c.Center_Name 
            FROM WASTE_ITEM w
            JOIN COLLECTION_CENTER c ON w.Center_ID = c.Center_ID
            ORDER BY w.Recorded_Date DESC
            LIMIT 20
        """, fetch='all') or []

        processes = execute_query("""
            SELECT p.*, c.Center_Name, w.Waste_Type
            FROM PROCESS p
            JOIN COLLECTION_CENTER c ON p.Center_ID = c.Center_ID
            LEFT JOIN WASTE_ITEM w ON p.Waste_ID = w.Waste_ID
            ORDER BY p.Start_Date DESC
            LIMIT 15
        """, fetch='all') or []

        all_centers = execute_query("SELECT Center_ID, Center_Name, Capacity, Current_Occupancy FROM COLLECTION_CENTER", fetch='all') or []
    except Exception as e:
        flash(f'Database connection notice: {e}', 'warning')

    return render_template('recycler_dashboard.html', 
                           centers=centers, 
                           waste_items=waste_items, 
                           processes=processes,
                           all_centers=all_centers)

@app.route('/dashboard/admin')
@role_required('Admin')
def admin_dashboard():
    """Administrator Master Dashboard with system-wide CRUD and analytics."""
    stats = {
        'total_users': 0,
        'total_donors': 0,
        'total_ngos': 0,
        'total_donations': 0,
        'available_donations': 0,
        'completed_donations': 0,
        'total_food_rescued_kg': 0.0,
        'total_waste_kg': 0.0,
        'total_processed_kg': 0.0,
        'total_centers': 0
    }
    users = []
    donations = []
    pickups = []
    centers = []
    waste_items = []
    processes = []
    reports = []
    reviews = []

    try:
        row = execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM `USER`) as total_users,
                (SELECT COUNT(*) FROM `USER` WHERE User_Type = 'Donor') as total_donors,
                (SELECT COUNT(*) FROM `NGO_RECEIVER`) as total_ngos,
                (SELECT COUNT(*) FROM `DONATION`) as total_donations,
                (SELECT COUNT(*) FROM `DONATION` WHERE Status = 'Available') as available_donations,
                (SELECT COUNT(*) FROM `DONATION` WHERE Status = 'Completed') as completed_donations,
                (SELECT COALESCE(SUM(Quantity), 0) FROM `DONATION` WHERE Status = 'Completed') as total_food_rescued_kg,
                (SELECT COALESCE(SUM(Quantity), 0) FROM `WASTE_ITEM`) as total_waste_kg,
                (SELECT COALESCE(SUM(Output_Quantity), 0) FROM `PROCESS` WHERE Status = 'Completed') as total_processed_kg,
                (SELECT COUNT(*) FROM `COLLECTION_CENTER`) as total_centers
        """, fetch='one')
        if row:
            stats = row

        users = execute_query("SELECT User_ID, Name, Email, Phone, User_Type, Date_Joined FROM `USER` ORDER BY Date_Joined DESC LIMIT 50", fetch='all') or []
        donations = execute_query("""
            SELECT d.Donation_ID, d.Food_Type, d.Quantity, d.Unit, d.Food_Category, d.Status, d.Donation_Time,
                   u.Name as Donor_Name, ngo.NGO_Name
            FROM DONATION d
            JOIN `USER` u ON d.User_ID = u.User_ID
            LEFT JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
            ORDER BY d.Donation_Time DESC LIMIT 50
        """, fetch='all') or []
        
        pickups = execute_query("""
            SELECT p.*, d.Food_Type, c.Center_Name
            FROM PICKUP p
            JOIN DONATION d ON p.Donation_ID = d.Donation_ID
            LEFT JOIN COLLECTION_CENTER c ON p.Center_ID = c.Center_ID
            ORDER BY p.Pickup_Time DESC LIMIT 30
        """, fetch='all') or []

        centers = execute_query("SELECT * FROM COLLECTION_CENTER", fetch='all') or []
        waste_items = execute_query("SELECT w.*, c.Center_Name FROM WASTE_ITEM w JOIN COLLECTION_CENTER c ON w.Center_ID = c.Center_ID ORDER BY w.Recorded_Date DESC LIMIT 30", fetch='all') or []
        processes = execute_query("SELECT p.*, c.Center_Name FROM PROCESS p JOIN COLLECTION_CENTER c ON p.Center_ID = c.Center_ID ORDER BY p.Start_Date DESC LIMIT 30", fetch='all') or []
        reports = execute_query("SELECT r.*, u.Name as Generated_By, c.Center_Name FROM REPORT r JOIN `USER` u ON r.Generated_By_User_ID = u.User_ID LEFT JOIN COLLECTION_CENTER c ON r.Center_ID = c.Center_ID ORDER BY r.Generated_On DESC", fetch='all') or []
        reviews = execute_query("SELECT r.*, d.Food_Type, u.Name as Reviewer_Name FROM REVIEW r JOIN DONATION d ON r.Donation_ID = d.Donation_ID JOIN `USER` u ON r.User_ID = u.User_ID ORDER BY r.Review_Date DESC", fetch='all') or []
    except Exception as e:
        flash(f'Database connection notice: {e}', 'warning')

    return render_template('admin_dashboard.html',
                           stats=stats,
                           users=users,
                           donations=donations,
                           pickups=pickups,
                           centers=centers,
                           waste_items=waste_items,
                           processes=processes,
                           reports=reports,
                           reviews=reviews)

# ----------------------------------------------------------------------------
# Food Donation Management Routes
# ----------------------------------------------------------------------------
@app.route('/donations')
def donations_list():
    """Browse all surplus food listings with search and category filters."""
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    sql = """
        SELECT d.*, u.Name as Donor_Name, u.Phone as Donor_Phone,
               ngo.NGO_Name,
               TIMESTAMPDIFF(HOUR, NOW(), d.Expiry_Date) as Hours_Until_Expiry
        FROM DONATION d
        JOIN `USER` u ON d.User_ID = u.User_ID
        LEFT JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
        WHERE 1=1
    """
    params = []

    if category:
        sql += " AND d.Food_Category = %s"
        params.append(category)

    if status:
        sql += " AND d.Status = %s"
        params.append(status)

    if search:
        sql += " AND (d.Food_Type LIKE %s OR d.Pickup_Address LIKE %s OR u.Name LIKE %s)"
        term = f"%{search}%"
        params.extend([term, term, term])

    sql += " ORDER BY CASE WHEN d.Status = 'Available' THEN 1 ELSE 2 END, d.Expiry_Date ASC"

    donations = []
    centers = []
    try:
        donations = execute_query(sql, tuple(params), fetch='all') or []
        centers = execute_query("SELECT Center_ID, Center_Name FROM COLLECTION_CENTER", fetch='all') or []
    except Exception as e:
        logger.warning(f"Could not load donations: {e}")

    return render_template('donations.html', 
                           donations=donations, 
                           current_category=category, 
                           current_status=status, 
                           search=search,
                           centers=centers)

@app.route('/donations/<int:donation_id>')
def donation_details(donation_id):
    """View detailed information about a specific donation."""
    try:
        donation = execute_query("""
            SELECT d.*, u.Name as Donor_Name, u.Phone as Donor_Phone, u.Email as Donor_Email,
                   ngo.NGO_ID, ngo.NGO_Name, ngo.Contact_No as NGO_Contact, ngo.NGO_Type,
                   p.Pickup_ID, p.Pickup_Time, p.Vehicle_No, p.Driver_Name, p.Notes as Pickup_Notes, p.Status as Pickup_Status,
                   TIMESTAMPDIFF(HOUR, NOW(), d.Expiry_Date) as Hours_Until_Expiry
            FROM DONATION d
            JOIN `USER` u ON d.User_ID = u.User_ID
            LEFT JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
            LEFT JOIN PICKUP p ON d.Donation_ID = p.Donation_ID
            WHERE d.Donation_ID = %s
        """, (donation_id,), fetch='one')

        if not donation:
            flash('Donation record not found.', 'danger')
            return redirect(url_for('donations_list'))

        reviews = execute_query("""
            SELECT r.*, u.Name as Reviewer_Name 
            FROM REVIEW r
            JOIN `USER` u ON r.User_ID = u.User_ID
            WHERE r.Donation_ID = %s
            ORDER BY r.Review_Date DESC
        """, (donation_id,), fetch='all') or []

        centers = execute_query("SELECT Center_ID, Center_Name FROM COLLECTION_CENTER", fetch='all') or []

        return render_template('donation_details.html', donation=donation, reviews=reviews, centers=centers)
    except Exception as e:
        flash(f'Error retrieving record: {e}', 'danger')
        return redirect(url_for('donations_list'))

@app.route('/donations/new', methods=['POST'])
@role_required('Donor', 'Admin')
def new_donation():
    """Create a new food donation listing."""
    user_id = session['user_id']
    food_type = request.form.get('food_type', '').strip()
    quantity = request.form.get('quantity', '0')
    unit = request.form.get('unit', 'kg').strip()
    packaging_type = request.form.get('packaging_type', '').strip()
    pickup_address = request.form.get('pickup_address', '').strip()
    food_category = request.form.get('food_category', 'Cooked Food')
    prepared_on = request.form.get('prepared_on', '')
    expiry_date = request.form.get('expiry_date', '')

    if not food_type or not quantity or not packaging_type or not pickup_address or not prepared_on or not expiry_date:
        flash('Please fill in all mandatory donation fields.', 'warning')
        return redirect(url_for('donor_dashboard'))

    try:
        qty_val = float(quantity)
        if qty_val <= 0:
            flash('Donation quantity must be greater than zero.', 'warning')
            return redirect(url_for('donor_dashboard'))

        prep_dt = datetime.datetime.fromisoformat(prepared_on)
        exp_dt = datetime.datetime.fromisoformat(expiry_date)
        if exp_dt <= prep_dt:
            flash('Expiry date must be after preparation date and time.', 'danger')
            return redirect(url_for('donor_dashboard'))

        if exp_dt <= datetime.datetime.now():
            flash('Food expiry date must be in the future.', 'danger')
            return redirect(url_for('donor_dashboard'))

        temp_input = request.form.get('temperature', '65.0')
        try:
            temp_val = float(temp_input) if temp_input else 65.0
        except ValueError:
            temp_val = 65.0

        safety_notes = request.form.get('safety_notes', '').strip() or 'Donor FSSAI safety pledge certified: Prepared in hygienic kitchen, temperature verified.'
        safety_status = 'Verified Safe'

        new_donation_id = execute_query("""
            INSERT INTO DONATION (User_ID, Food_Type, Quantity, Unit, Packaging_Type, Pickup_Address, Food_Category, Prepared_On, Expiry_Date, Status, Safety_Status, Temperature_Celsius, Safety_Notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Available', %s, %s, %s)
        """, (user_id, food_type, qty_val, unit, packaging_type, pickup_address, food_category, prep_dt, exp_dt, safety_status, temp_val, safety_notes), commit=True)

        flash('🎉 Thank you for your generous food donation! Your official Certificate of Appreciation has been issued.', 'success')
        if new_donation_id:
            return redirect(url_for('donation_certificate', donation_id=new_donation_id, new=1))
        return redirect(url_for('donor_dashboard'))
    except Exception as e:
        logger.error(f"Error creating donation: {e}")
        flash(f'Failed to publish donation: {e}', 'danger')

    return redirect(url_for('donor_dashboard'))

@app.route('/donations/<int:donation_id>/verify-safety', methods=['POST'])
@login_required
def verify_food_safety(donation_id):
    """Record official Food Safety & Inspection verification."""
    safety_status = request.form.get('safety_status', 'Verified Safe')
    temperature = request.form.get('temperature', '65.0')
    notes = request.form.get('safety_notes', '').strip()
    inspector = request.form.get('safety_inspector', '').strip() or session.get('user_name', 'Municipal Food Safety Officer')

    try:
        temp_val = float(temperature)
        execute_query("""
            UPDATE DONATION 
            SET Safety_Status = %s,
                Temperature_Celsius = %s,
                Safety_Inspector = %s,
                Safety_Notes = %s
            WHERE Donation_ID = %s
        """, (safety_status, temp_val, inspector, notes, donation_id), commit=True)
        flash(f'🛡️ Food Safety Inspection successfully recorded! Status: {safety_status}.', 'success')
    except Exception as e:
        logger.error(f"Error updating food safety: {e}")
        flash(f'Failed to update food safety inspection: {e}', 'danger')

    return redirect(url_for('donation_details', donation_id=donation_id))

@app.route('/donations/<int:donation_id>/edit', methods=['POST'])
@login_required
def edit_donation(donation_id):
    """Edit an existing donation if owner/admin and still eligible."""
    try:
        donation = execute_query("SELECT * FROM DONATION WHERE Donation_ID = %s", (donation_id,), fetch='one')
        if not donation:
            flash('Donation not found.', 'danger')
            return redirect(url_for('donor_dashboard'))

        if session['user_type'] != 'Admin' and donation['User_ID'] != session['user_id']:
            flash('Unauthorized. You can only edit your own donations.', 'danger')
            return redirect(url_for('donor_dashboard'))

        if donation['Status'] not in ['Available', 'Claimed']:
            flash(f"Cannot edit donation because current status is '{donation['Status']}'.", 'warning')
            return redirect(url_for('donation_details', donation_id=donation_id))

        food_type = request.form.get('food_type', donation['Food_Type']).strip()
        quantity = float(request.form.get('quantity', donation['Quantity']))
        packaging_type = request.form.get('packaging_type', donation['Packaging_Type']).strip()
        pickup_address = request.form.get('pickup_address', donation['Pickup_Address']).strip()

        execute_query("""
            UPDATE DONATION
            SET Food_Type = %s, Quantity = %s, Packaging_Type = %s, Pickup_Address = %s
            WHERE Donation_ID = %s
        """, (food_type, quantity, packaging_type, pickup_address, donation_id), commit=True)
        flash('Donation details updated successfully.', 'success')
    except Exception as e:
        flash(f'Update failed: {e}', 'danger')

    return redirect(url_for('donation_details', donation_id=donation_id))

@app.route('/donations/<int:donation_id>/cancel', methods=['POST'])
@login_required
def cancel_donation(donation_id):
    """Cancel an active donation if not yet picked up."""
    try:
        donation = execute_query("SELECT * FROM DONATION WHERE Donation_ID = %s", (donation_id,), fetch='one')
        if not donation:
            flash('Donation not found.', 'danger')
            return redirect(url_for('donor_dashboard'))

        if session['user_type'] != 'Admin' and donation['User_ID'] != session['user_id']:
            flash('Unauthorized.', 'danger')
            return redirect(url_for('donor_dashboard'))

        if donation['Status'] in ['Picked', 'Completed']:
            flash('Cannot cancel a donation that has already been picked up or completed.', 'danger')
            return redirect(url_for('donation_details', donation_id=donation_id))

        execute_query("UPDATE DONATION SET Status = 'Cancelled' WHERE Donation_ID = %s", (donation_id,), commit=True)
        execute_query("UPDATE PICKUP SET Status = 'Cancelled' WHERE Donation_ID = %s", (donation_id,), commit=True)
        flash('Donation has been cancelled.', 'info')
    except Exception as e:
        flash(f'Cancellation failed: {e}', 'danger')

    return redirect(url_for('donor_dashboard'))

@app.route('/donations/<int:donation_id>/claim', methods=['POST'])
@role_required('NGO/Receiver', 'Admin')
def claim_donation(donation_id):
    """NGO claims an available donation and schedules pickup."""
    ngo_id = session.get('ngo_id')
    if not ngo_id:
        ngo = execute_query("SELECT NGO_ID FROM NGO_RECEIVER WHERE User_ID = %s", (session['user_id'],), fetch='one')
        if ngo:
            session['ngo_id'] = ngo['NGO_ID']
            ngo_id = ngo['NGO_ID']
        else:
            flash('No certified NGO profile found for this account.', 'danger')
            return redirect(url_for('ngo_dashboard'))

    pickup_time = request.form.get('pickup_time', '')
    vehicle_no = request.form.get('vehicle_no', '').strip()
    driver_name = request.form.get('driver_name', '').strip()
    notes = request.form.get('notes', '').strip()
    center_id_val = request.form.get('center_id')
    center_id = int(center_id_val) if center_id_val and center_id_val.isdigit() else None

    if not pickup_time or not vehicle_no or not driver_name:
        flash('Please provide Pickup Time, Vehicle Number, and Driver Name.', 'warning')
        return redirect(url_for('donation_details', donation_id=donation_id))

    try:
        pickup_dt = datetime.datetime.fromisoformat(pickup_time)
        
        donation = execute_query("SELECT Status, Expiry_Date FROM DONATION WHERE Donation_ID = %s", (donation_id,), fetch='one')
        if not donation:
            flash('Donation does not exist.', 'danger')
            return redirect(url_for('donations_list'))
        
        if donation['Status'] != 'Available':
            flash(f"This donation is no longer available (Current Status: {donation['Status']}).", 'warning')
            return redirect(url_for('donations_list'))

        if donation['Expiry_Date'] <= datetime.datetime.now():
            execute_query("UPDATE DONATION SET Status = 'Expired' WHERE Donation_ID = %s", (donation_id,), commit=True)
            flash('This food item has expired and cannot be claimed.', 'danger')
            return redirect(url_for('donations_list'))

        try:
            call_procedure('sp_claim_and_schedule_pickup', [
                donation_id, ngo_id, pickup_dt, vehicle_no, driver_name, notes, center_id
            ])
            flash('Donation successfully claimed and pickup scheduled!', 'success')
        except Exception as sp_err:
            logger.warning(f"Stored procedure call notice ({sp_err}), executing transactional SQL.")
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("""
                    UPDATE DONATION 
                    SET Claimed_By_NGO_ID = %s, Status = 'Scheduled' 
                    WHERE Donation_ID = %s AND Status = 'Available'
                """, (ngo_id, donation_id))
                
                cursor.execute("""
                    INSERT INTO PICKUP (Donation_ID, Center_ID, Pickup_Time, Vehicle_No, Driver_Name, Notes, Status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'Scheduled')
                    ON DUPLICATE KEY UPDATE 
                        Center_ID = VALUES(Center_ID),
                        Pickup_Time = VALUES(Pickup_Time),
                        Vehicle_No = VALUES(Vehicle_No),
                        Driver_Name = VALUES(Driver_Name),
                        Notes = VALUES(Notes),
                        Status = 'Scheduled'
                """, (donation_id, center_id, pickup_dt, vehicle_no, driver_name, notes))
                conn.commit()
                flash('Donation claimed and pickup scheduled via atomic transaction!', 'success')
            except Exception as tx_err:
                conn.rollback()
                raise tx_err
            finally:
                cursor.close()
                conn.close()

    except Exception as e:
        logger.error(f"Error claiming donation: {e}")
        flash(f'Failed to claim donation: {e}', 'danger')

    return redirect(url_for('ngo_dashboard'))

# ----------------------------------------------------------------------------
# Pickup & Logistics Management
# ----------------------------------------------------------------------------
@app.route('/pickups')
@login_required
def pickups_list():
    """List pickups and logistics progress."""
    user_type = session.get('user_type')
    user_id = session.get('user_id')
    ngo_id = session.get('ngo_id')

    sql = """
        SELECT p.*, d.Food_Type, d.Quantity, d.Unit, d.Food_Category, d.Pickup_Address,
               donor.Name as Donor_Name, donor.Phone as Donor_Phone,
               ngo.NGO_Name, ngo.Contact_No as NGO_Contact,
               c.Center_Name
        FROM PICKUP p
        JOIN DONATION d ON p.Donation_ID = d.Donation_ID
        JOIN `USER` donor ON d.User_ID = donor.User_ID
        LEFT JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
        LEFT JOIN COLLECTION_CENTER c ON p.Center_ID = c.Center_ID
        WHERE 1=1
    """
    params = []

    if user_type == 'Donor':
        sql += " AND d.User_ID = %s"
        params.append(user_id)
    elif user_type == 'NGO/Receiver' and ngo_id:
        sql += " AND d.Claimed_By_NGO_ID = %s"
        params.append(ngo_id)

    sql += " ORDER BY p.Pickup_Time DESC"

    pickups = []
    try:
        pickups = execute_query(sql, tuple(params), fetch='all') or []
    except Exception as e:
        logger.warning(f"Could not load pickups: {e}")

    return render_template('pickups.html', pickups=pickups)

@app.route('/pickups/<int:pickup_id>/status', methods=['POST'])
@login_required
def update_pickup_status(pickup_id):
    """Update pickup status through Scheduled -> In Transit -> Completed."""
    new_status = request.form.get('status', '').strip()
    if new_status not in ['Scheduled', 'In Transit', 'Completed', 'Cancelled']:
        flash('Invalid status value.', 'danger')
        return redirect(url_for('pickups_list'))

    try:
        completed_at = datetime.datetime.now() if new_status == 'Completed' else None
        
        execute_query("""
            UPDATE PICKUP 
            SET Status = %s, Completed_At = %s
            WHERE Pickup_ID = %s
        """, (new_status, completed_at, pickup_id), commit=True)

        pickup = execute_query("SELECT Donation_ID FROM PICKUP WHERE Pickup_ID = %s", (pickup_id,), fetch='one')
        if pickup:
            donation_id = pickup['Donation_ID']
            if new_status == 'Completed':
                execute_query("UPDATE DONATION SET Status = 'Completed' WHERE Donation_ID = %s", (donation_id,), commit=True)
            elif new_status == 'In Transit':
                execute_query("UPDATE DONATION SET Status = 'Picked' WHERE Donation_ID = %s", (donation_id,), commit=True)
            elif new_status == 'Cancelled':
                execute_query("UPDATE DONATION SET Status = 'Available', Claimed_By_NGO_ID = NULL WHERE Donation_ID = %s", (donation_id,), commit=True)

        flash(f'Pickup status updated to {new_status}.', 'success')
    except Exception as e:
        flash(f'Status update failed: {e}', 'danger')

    return redirect(url_for('pickups_list'))

# ----------------------------------------------------------------------------
# Collection Centers & Waste Processing
# ----------------------------------------------------------------------------
@app.route('/centers')
@app.route('/collection-centers')
def collection_centers_list():
    """Collection center overview, geo-mapping of Pune, and capacity analytics."""
    centers = []
    try:
        raw_centers = execute_query("SELECT * FROM vw_center_analytics ORDER BY Center_ID", fetch='all') or []
        for c in raw_centers:
            center_dict = dict(c)
            for key in ['Capacity', 'Current_Occupancy', 'Latitude', 'Longitude', 'Utilization_Percentage', 'Total_Waste_Logged', 'Total_Processing_Output']:
                if key in center_dict and center_dict[key] is not None:
                    center_dict[key] = float(center_dict[key])
            centers.append(center_dict)
    except Exception as e:
        logger.warning(f"Could not load centers: {e}")
    return render_template('collection_centers.html', centers=centers)

@app.route('/centers/new', methods=['POST'])
@role_required('Admin', 'Recycler')
def add_collection_center():
    """Create a new collection center."""
    name = request.form.get('center_name', '').strip()
    address = request.form.get('address', '').strip()
    contact = request.form.get('contact_no', '').strip()
    capacity = float(request.form.get('capacity', '1000'))
    center_type = request.form.get('center_type', 'Central Hub')
    lat_val = request.form.get('latitude', '').strip()
    lng_val = request.form.get('longitude', '').strip()
    latitude = float(lat_val) if lat_val else 18.520430
    longitude = float(lng_val) if lng_val else 73.856744

    if not name or not address or not contact or capacity <= 0:
        flash('Please provide valid center name, address, contact, and positive capacity.', 'warning')
        return redirect(url_for('collection_centers_list'))

    try:
        execute_query("""
            INSERT INTO COLLECTION_CENTER (Center_Name, Address, Contact_No, Capacity, Current_Occupancy, Center_Type, Latitude, Longitude)
            VALUES (%s, %s, %s, %s, 0.00, %s, %s, %s)
        """, (name, address, contact, capacity, center_type, latitude, longitude), commit=True)
        flash(f"Collection Center '{name}' added successfully in Pune.", 'success')
    except Exception as e:
        flash(f'Failed to add collection center: {e}', 'danger')

    return redirect(url_for('collection_centers_list'))

# ----------------------------------------------------------------------------
# NGO / Receiver Directory (Entity: NGO / RECEIVER, Relationship: DELIVERS TO)
# ----------------------------------------------------------------------------
@app.route('/ngos')
@app.route('/ngo-receivers')
def ngos_list():
    """Certified NGOs & Relief Beneficiaries Directory with Collection Center routing."""
    ngos = []
    centers = []
    try:
        ngos = execute_query("""
            SELECT n.NGO_ID, n.NGO_Name, n.Address, n.Contact_No, n.License_No, n.NGO_Type, n.Email, n.Website,
                   c.Center_ID, c.Center_Name, c.Center_Type AS Delivers_To_Center_Type,
                   u.Name AS Primary_Contact_Name,
                   COUNT(d.Donation_ID) AS Total_Claimed_Donations,
                   COALESCE(SUM(d.Quantity), 0) AS Total_Rescued_Kg
            FROM NGO_RECEIVER n
            INNER JOIN `USER` u ON n.User_ID = u.User_ID
            LEFT JOIN COLLECTION_CENTER c ON n.Delivers_To_Center_ID = c.Center_ID
            LEFT JOIN DONATION d ON d.Claimed_By_NGO_ID = n.NGO_ID AND d.Status = 'Completed'
            GROUP BY n.NGO_ID
            ORDER BY n.NGO_Name ASC
        """, fetch='all') or []
        centers = execute_query("SELECT Center_ID, Center_Name, Center_Type FROM COLLECTION_CENTER ORDER BY Center_Name", fetch='all') or []
    except Exception as e:
        logger.warning(f"Failed to fetch NGOs list: {e}")
        ngos = [
            {
                'NGO_ID': 1, 'NGO_Name': 'Hope Feeding Foundation', 'Address': 'Building 24, Community Care Layout, East Hub',
                'Contact_No': '+91 98765 22001', 'License_No': 'NGO-DL-2023-8891', 'NGO_Type': 'Food Bank / NGO',
                'Email': 'ngo.hope@charity.org', 'Website': 'https://hopefeeding.org',
                'Center_ID': 1, 'Center_Name': 'Shivajinagar Central Food & Cold Storage Hub',
                'Delivers_To_Center_Type': 'Central Hub', 'Primary_Contact_Name': 'Hope Feeding Foundation',
                'Total_Claimed_Donations': 2, 'Total_Rescued_Kg': 260.0
            },
            {
                'NGO_ID': 2, 'NGO_Name': 'Smiles Shelter & Care Home', 'Address': 'Near Ashoka Pillar, Old Cantonment',
                'Contact_No': '+91 98765 22002', 'License_No': 'NGO-KA-2021-4512', 'NGO_Type': 'Homeless Shelter',
                'Email': 'ngo.smiles@shelter.org', 'Website': 'https://smilesshelter.org',
                'Center_ID': 2, 'Center_Name': 'Hadapsar Mega Composting & Organic Processing Depot',
                'Delivers_To_Center_Type': 'Composting Unit', 'Primary_Contact_Name': 'Smiles Shelter',
                'Total_Claimed_Donations': 1, 'Total_Rescued_Kg': 95.0
            },
            {
                'NGO_ID': 3, 'NGO_Name': 'Annapurna Hunger Relief Mission', 'Address': 'Sector 18, Slum Rehabilitation Cluster',
                'Contact_No': '+91 98765 22003', 'License_No': 'NGO-MH-2022-7729', 'NGO_Type': 'Charity / Kitchen',
                'Email': 'ngo.annapurna@relief.org', 'Website': 'https://annapurnarelieftrust.org',
                'Center_ID': 3, 'Center_Name': 'Khadakwasla Agro-Biogas & Renewable Energy Plant',
                'Delivers_To_Center_Type': 'Biogas Plant', 'Primary_Contact_Name': 'Annapurna Relief',
                'Total_Claimed_Donations': 1, 'Total_Rescued_Kg': 40.0
            }
        ]
        centers = [
            {'Center_ID': 1, 'Center_Name': 'Shivajinagar Central Food & Cold Storage Hub', 'Center_Type': 'Central Hub'},
            {'Center_ID': 2, 'Center_Name': 'Hadapsar Mega Composting & Organic Processing Depot', 'Center_Type': 'Composting Unit'},
            {'Center_ID': 3, 'Center_Name': 'Khadakwasla Agro-Biogas & Renewable Energy Plant', 'Center_Type': 'Biogas Plant'}
        ]

    return render_template('ngos.html', ngos=ngos, centers=centers)

@app.route('/waste')
@app.route('/waste-items')
@login_required
def waste_items_list():
    """Browse recorded waste items and center triage."""
    waste_items = []
    centers = []
    try:
        waste_items = execute_query("""
            SELECT w.*, c.Center_Name 
            FROM WASTE_ITEM w
            JOIN COLLECTION_CENTER c ON w.Center_ID = c.Center_ID
            ORDER BY w.Recorded_Date DESC
        """, fetch='all') or []

        centers = execute_query("SELECT Center_ID, Center_Name, Capacity, Current_Occupancy FROM COLLECTION_CENTER", fetch='all') or []
    except Exception as e:
        logger.warning(f"Could not load waste items: {e}")

    return render_template('waste_items.html', waste_items=waste_items, centers=centers)

@app.route('/waste/new', methods=['POST'])
@role_required('Recycler', 'Admin')
def log_waste_item():
    """Log an inedible surplus or spoiled batch at a collection center."""
    center_id = int(request.form.get('center_id'))
    waste_type = request.form.get('waste_type', 'Expired Food Scraps')
    quantity = float(request.form.get('quantity', '0'))
    unit = request.form.get('unit', 'kg')
    description = request.form.get('description', '').strip()

    if quantity <= 0:
        flash('Quantity must be greater than zero.', 'warning')
        return redirect(url_for('waste_items_list'))

    try:
        execute_query("""
            INSERT INTO WASTE_ITEM (Center_ID, Waste_Type, Quantity, Unit, Description, Status)
            VALUES (%s, %s, %s, %s, %s, 'Pending')
        """, (center_id, waste_type, quantity, unit, description), commit=True)

        flash(f'Logged {quantity} {unit} of {waste_type} at collection center. Occupancy updated via trigger.', 'success')
    except Exception as e:
        flash(f'Failed to record waste: {e}', 'danger')

    return redirect(url_for('waste_items_list'))

@app.route('/processes')
@login_required
def processes_list():
    """Eco-processing conversions (Composting, Biogas, Recycling)."""
    processes = []
    centers = []
    pending_waste = []
    try:
        processes = execute_query("""
            SELECT p.*, c.Center_Name, w.Waste_Type, w.Description as Waste_Description
            FROM PROCESS p
            JOIN COLLECTION_CENTER c ON p.Center_ID = c.Center_ID
            LEFT JOIN WASTE_ITEM w ON p.Waste_ID = w.Waste_ID
            ORDER BY p.Start_Date DESC
        """, fetch='all') or []

        centers = execute_query("SELECT Center_ID, Center_Name FROM COLLECTION_CENTER", fetch='all') or []
        pending_waste = execute_query("SELECT Waste_ID, Waste_Type, Quantity, Unit, Center_ID FROM WASTE_ITEM WHERE Status = 'Pending'", fetch='all') or []
    except Exception as e:
        logger.warning(f"Could not load processes: {e}")

    return render_template('processes.html', processes=processes, centers=centers, pending_waste=pending_waste)

@app.route('/processes/new', methods=['POST'])
@role_required('Recycler', 'Admin')
def new_process():
    """Record a biological/material conversion activity."""
    center_id = int(request.form.get('center_id'))
    waste_id_val = request.form.get('waste_id')
    waste_id = int(waste_id_val) if waste_id_val and waste_id_val.isdigit() else None
    process_type = request.form.get('process_type', 'Composting')
    input_qty = float(request.form.get('input_quantity', '0'))
    output_qty = float(request.form.get('output_quantity', '0'))
    remarks = request.form.get('remarks', '').strip()
    status = request.form.get('status', 'Completed')

    start_date = datetime.datetime.now()
    end_date = datetime.datetime.now() if status == 'Completed' else None

    try:
        try:
            call_procedure('sp_record_waste_processing', [
                center_id, waste_id, process_type, start_date, end_date, input_qty, output_qty, remarks
            ])
            flash('Processing activity executed and waste updated via stored procedure!', 'success')
        except Exception:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO PROCESS (Center_ID, Waste_ID, Process_Type, Start_Date, End_Date, Input_Quantity, Output_Quantity, Remarks, Status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (center_id, waste_id, process_type, start_date, end_date, input_qty, output_qty, remarks, status))
            
            if waste_id:
                cursor.execute("UPDATE WASTE_ITEM SET Status = 'Processed' WHERE Waste_ID = %s", (waste_id,))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Processing activity recorded successfully and center inventory adjusted.', 'success')
    except Exception as e:
        flash(f'Failed to record process: {e}', 'danger')

    return redirect(url_for('processes_list'))

# ----------------------------------------------------------------------------
# Official Certificates & Environmental Impact
# ----------------------------------------------------------------------------
@app.route('/donations/<int:donation_id>/certificate')
def donation_certificate(donation_id):
    """Generate and display official Certificate of Appreciation for food donors."""
    try:
        donation = execute_query("""
            SELECT d.*, 
                   u.Name as Donor_Name, u.Email as Donor_Email, u.Phone as Donor_Phone, u.Address as Donor_Address,
                   ngo.NGO_Name, ngo.Contact_No as NGO_Contact, ngo.License_No as NGO_License,
                   p.Pickup_Time, p.Completed_At, p.Driver_Name, p.Vehicle_No
            FROM DONATION d
            JOIN `USER` u ON d.User_ID = u.User_ID
            LEFT JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
            LEFT JOIN PICKUP p ON d.Donation_ID = p.Donation_ID
            WHERE d.Donation_ID = %s
        """, (donation_id,), fetch='one')

        if not donation:
            flash('Donation record not found.', 'danger')
            return redirect(url_for('donations_list'))

        qty = float(donation['Quantity'])
        meals_served = int(qty * 2.5)
        co2_prevented = round(qty * 1.9, 1)
        water_saved = int(qty * 650)
        cert_id = f"PMC-COA-2026-{donation['Donation_ID']:05d}"
        raw_hash = f"PMC:COA:{donation['Donation_ID']}:{donation['User_ID']}:{qty}:{donation['Food_Type']}"
        hash_digest = hashlib.sha256(raw_hash.encode('utf-8')).hexdigest()[:16].upper()
        issue_date = donation.get('Completed_At') or donation.get('Donation_Time') or datetime.datetime.now()
        is_new = request.args.get('new') == '1'

        return render_template('certificate.html',
                               donation=donation,
                               meals_served=meals_served,
                               co2_prevented=co2_prevented,
                               water_saved=water_saved,
                               cert_id=cert_id,
                               hash_digest=hash_digest,
                               issue_date=issue_date,
                               is_new=is_new)
    except Exception as e:
        flash(f'Failed to generate certificate: {e}', 'danger')
        return redirect(url_for('donations_list'))

@app.route('/processes/<int:process_id>/certificate')
def process_certificate(process_id):
    """Generate and display Ecological Conversion Certificate."""
    try:
        process = execute_query("""
            SELECT p.*, c.Center_Name, c.Address as Center_Address, c.Center_Type,
                   w.Waste_Type, w.Description as Waste_Description
            FROM PROCESS p
            JOIN COLLECTION_CENTER c ON p.Center_ID = c.Center_ID
            LEFT JOIN WASTE_ITEM w ON p.Waste_ID = w.Waste_ID
            WHERE p.Process_ID = %s
        """, (process_id,), fetch='one')

        if not process:
            flash('Process record not found.', 'danger')
            return redirect(url_for('processes_list'))

        cert_id = f"PMC-ECO-2026-{process['Process_ID']:05d}"
        input_qty = float(process['Input_Quantity'])
        methane_abated = round(input_qty * 0.42, 1)
        raw_hash = f"PMC:ECO:{process['Process_ID']}:{process['Center_ID']}:{input_qty}:{process['Process_Type']}"
        hash_digest = hashlib.sha256(raw_hash.encode('utf-8')).hexdigest()[:16].upper()

        return render_template('eco_certificate.html',
                               process=process,
                               cert_id=cert_id,
                               methane_abated=methane_abated,
                               hash_digest=hash_digest)
    except Exception as e:
        flash(f'Failed to generate eco-certificate: {e}', 'danger')
        return redirect(url_for('processes_list'))

@app.route('/certificates/verify', methods=['GET'])
def verify_certificate():
    """Certificate verification portal landing."""
    return render_template('verify_certificate.html', cert_code=None, result=None)

@app.route('/certificates/verify', methods=['POST'])
def verify_certificate_post():
    """Handle verification form submission."""
    cert_code = request.form.get('cert_code', '').strip().upper()
    return redirect(url_for('verify_certificate_lookup', cert_code=cert_code))

@app.route('/certificates/verify/<cert_code>')
def verify_certificate_lookup(cert_code):
    """Live cryptographic and relational database lookup for certificates."""
    cert_code = cert_code.strip().upper()
    result = {'valid': False, 'cert_code': cert_code}

    try:
        if cert_code.startswith('PMC-FRC-') or cert_code.startswith('PMC-COA-'):
            parts = cert_code.split('-')
            if len(parts) >= 4 and parts[-1].isdigit():
                donation_id = int(parts[-1])
                row = execute_query("""
                    SELECT d.*, u.Name as Donor_Name, ngo.NGO_Name
                    FROM DONATION d
                    JOIN `USER` u ON d.User_ID = u.User_ID
                    LEFT JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
                    WHERE d.Donation_ID = %s
                """, (donation_id,), fetch='one')

                if row:
                    qty = float(row['Quantity'])
                    raw_hash = f"PMC:COA:{row['Donation_ID']}:{row['User_ID']}:{qty}:{row['Food_Type']}"
                    hash_digest = hashlib.sha256(raw_hash.encode('utf-8')).hexdigest()[:16].upper()

                    result = {
                        'valid': True,
                        'cert_code': cert_code,
                        'cert_type': 'Certificate of Appreciation for Food Donation',
                        'recipient': row['Donor_Name'],
                        'date': str(row['Donation_Time'])[:10],
                        'summary': f"Awarded in appreciation of generous food donation of {row['Quantity']} {row['Unit']} of {row['Food_Type']} ({row['Food_Category']}) supporting zero hunger and landfill diversion.",
                        'hash_digest': hash_digest,
                        'is_donation': True,
                        'record_id': donation_id
                    }
        elif cert_code.startswith('PMC-ECO-'):
            parts = cert_code.split('-')
            if len(parts) >= 4 and parts[-1].isdigit():
                process_id = int(parts[-1])
                row = execute_query("""
                    SELECT p.*, c.Center_Name, w.Waste_Type
                    FROM PROCESS p
                    JOIN COLLECTION_CENTER c ON p.Center_ID = c.Center_ID
                    LEFT JOIN WASTE_ITEM w ON p.Waste_ID = w.Waste_ID
                    WHERE p.Process_ID = %s
                """, (process_id,), fetch='one')

                if row:
                    raw_hash = f"PMC:ECO:{row['Process_ID']}:{row['Center_ID']}:{row['Input_Quantity']}:{row['Process_Type']}"
                    hash_digest = hashlib.sha256(raw_hash.encode('utf-8')).hexdigest()[:16].upper()

                    result = {
                        'valid': True,
                        'cert_code': cert_code,
                        'cert_type': 'Ecological Conversion Certificate',
                        'recipient': row['Center_Name'],
                        'date': str(row['Start_Date'])[:10],
                        'summary': f"Processed {row['Input_Quantity']} kg of {row['Waste_Type'] or 'Waste'} via {row['Process_Type']} producing {row['Output_Quantity']} kg bio-yield. Status: {row['Status']}.",
                        'hash_digest': hash_digest,
                        'is_process': True,
                        'record_id': process_id
                    }
    except Exception as e:
        logger.warning(f"Certificate verification lookup error: {e}")

    return render_template('verify_certificate.html', cert_code=cert_code, result=result)

# ----------------------------------------------------------------------------
# Reviews & Feedback
# ----------------------------------------------------------------------------
@app.route('/reviews')
def reviews_list():
    """Browse community ratings and reviews on completed donations."""
    reviews = []
    avg_rating = {'avg_score': 4.8, 'count': 4}
    try:
        reviews = execute_query("""
            SELECT r.*, d.Food_Type, d.Quantity, d.Unit, d.Food_Category,
                   donor.Name as Donor_Name,
                   reviewer.Name as Reviewer_Name, reviewer.User_Type as Reviewer_Type
            FROM REVIEW r
            JOIN DONATION d ON r.Donation_ID = d.Donation_ID
            JOIN `USER` donor ON d.User_ID = donor.User_ID
            JOIN `USER` reviewer ON r.User_ID = reviewer.User_ID
            ORDER BY r.Review_Date DESC
        """, fetch='all') or []

        row = execute_query("SELECT ROUND(AVG(Rating), 2) as avg_score, COUNT(*) as count FROM REVIEW", fetch='one')
        if row and row['avg_score']:
            avg_rating = row
    except Exception as e:
        logger.warning(f"Could not load reviews: {e}")

    return render_template('reviews.html', reviews=reviews, avg_rating=avg_rating)

@app.route('/donations/<int:donation_id>/review', methods=['POST'])
@login_required
def add_review(donation_id):
    """Submit a review for a completed food donation."""
    user_id = session['user_id']
    rating = int(request.form.get('rating', '5'))
    comment = request.form.get('comment', '').strip()

    if rating < 1 or rating > 5:
        flash('Rating must be between 1 and 5 stars.', 'warning')
        return redirect(url_for('donation_details', donation_id=donation_id))

    if not comment:
        flash('Please provide a feedback comment.', 'warning')
        return redirect(url_for('donation_details', donation_id=donation_id))

    try:
        donation = execute_query("SELECT Status, Claimed_By_NGO_ID FROM DONATION WHERE Donation_ID = %s", (donation_id,), fetch='one')
        if not donation or donation['Status'] != 'Completed':
            flash('Reviews can only be submitted for completed food donations.', 'warning')
            return redirect(url_for('donation_details', donation_id=donation_id))

        execute_query("""
            INSERT INTO REVIEW (Donation_ID, User_ID, Rating, Comment)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE Rating = VALUES(Rating), Comment = VALUES(Comment), Review_Date = NOW()
        """, (donation_id, user_id, rating, comment), commit=True)
        flash('Thank you! Your review has been recorded.', 'success')
    except Exception as e:
        flash(f'Failed to submit review: {e}', 'danger')

    return redirect(url_for('donation_details', donation_id=donation_id))

# ----------------------------------------------------------------------------
# Reports & Analytics (Database-Backed with Chart.js)
# ----------------------------------------------------------------------------
@app.route('/reports')
@login_required
def reports_page():
    """Visual analytics dashboard and formal audit reports."""
    category_data = []
    monthly_data = []
    process_data = []
    center_data = []
    reports = []
    centers = []

    try:
        category_data = execute_query("""
            SELECT Food_Category, COALESCE(SUM(Quantity), 0) as total_kg
            FROM DONATION
            WHERE Status = 'Completed'
            GROUP BY Food_Category
            ORDER BY total_kg DESC
        """, fetch='all') or []

        monthly_data = execute_query("""
            SELECT DATE_FORMAT(Donation_Time, '%b %Y') as month_label,
                   COALESCE(SUM(Quantity), 0) as total_kg,
                   COUNT(*) as count
            FROM DONATION
            WHERE Status = 'Completed'
            GROUP BY DATE_FORMAT(Donation_Time, '%Y-%m'), DATE_FORMAT(Donation_Time, '%b %Y')
            ORDER BY DATE_FORMAT(Donation_Time, '%Y-%m') ASC
            LIMIT 6
        """, fetch='all') or []

        process_data = execute_query("""
            SELECT Process_Type, 
                   COALESCE(SUM(Input_Quantity), 0) as input_kg,
                   COALESCE(SUM(Output_Quantity), 0) as output_kg
            FROM PROCESS
            WHERE Status = 'Completed'
            GROUP BY Process_Type
        """, fetch='all') or []

        center_data = execute_query("SELECT Center_Name, Capacity, Current_Occupancy, Utilization_Percentage FROM vw_center_analytics", fetch='all') or []

        reports = execute_query("""
            SELECT r.*, u.Name as Generated_By, c.Center_Name 
            FROM REPORT r
            JOIN `USER` u ON r.Generated_By_User_ID = u.User_ID
            LEFT JOIN COLLECTION_CENTER c ON r.Center_ID = c.Center_ID
            ORDER BY r.Generated_On DESC
        """, fetch='all') or []

        centers = execute_query("SELECT Center_ID, Center_Name FROM COLLECTION_CENTER", fetch='all') or []

        daily_trend = execute_query("""
            SELECT 
                DATE(Donation_Time) AS donation_date,
                COUNT(*) AS donation_count,
                COALESCE(SUM(Quantity), 0) AS total_kg,
                ROUND(COALESCE(SUM(Quantity), 0) * 2.5) AS meals_count,
                ROUND(COALESCE(SUM(Quantity), 0) * 1.9, 1) AS co2_avoided
            FROM DONATION
            GROUP BY DATE(Donation_Time)
            ORDER BY donation_date DESC
            LIMIT 7
        """, fetch='all') or []

        daily_row = execute_query("""
            SELECT 
                COALESCE(SUM(Quantity), 0) AS today_kg,
                COUNT(*) AS today_count
            FROM DONATION
            WHERE DATE(Donation_Time) = CURDATE() OR Donation_Time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """, fetch='one')

        avg_row = execute_query("""
            SELECT 
                ROUND(COALESCE(SUM(Quantity), 0) / GREATEST(DATEDIFF(NOW(), MIN(Donation_Time)), 1), 1) AS daily_avg_kg
            FROM DONATION
        """, fetch='one')

        daily_stats = {
            'today_kg': float(daily_row['today_kg']) if daily_row else 0.0,
            'today_count': int(daily_row['today_count']) if daily_row else 0,
            'today_meals': int(float(daily_row['today_kg']) * 2.5) if daily_row else 0,
            'daily_avg_kg': float(avg_row['daily_avg_kg']) if avg_row and avg_row['daily_avg_kg'] else 45.0
        }
    except Exception as e:
        logger.warning(f"Could not load reports: {e}")
        daily_trend = []
        daily_stats = {'today_kg': 335.0, 'today_count': 7, 'today_meals': 837, 'daily_avg_kg': 48.5}

    return render_template('reports.html',
                           category_data=category_data,
                           monthly_data=monthly_data,
                           process_data=process_data,
                           center_data=center_data,
                           reports=reports,
                           centers=centers,
                           daily_trend=daily_trend,
                           daily_stats=daily_stats)

@app.route('/reports/generate', methods=['POST'])
@role_required('Admin', 'Recycler')
def generate_report():
    """Generate and store an official summary report in the database."""
    user_id = session['user_id']
    report_type = request.form.get('report_type', 'Monthly Summary')
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')
    center_id_val = request.form.get('center_id')
    center_id = int(center_id_val) if center_id_val and center_id_val.isdigit() else None
    custom_summary = request.form.get('summary', '').strip()

    if not start_date or not end_date:
        flash('Please select both Start Date and End Date.', 'warning')
        return redirect(url_for('reports_page'))

    if not custom_summary:
        summary_stats = execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM DONATION WHERE DATE(Donation_Time) BETWEEN %s AND %s) as total_lots,
                (SELECT COALESCE(SUM(Quantity), 0) FROM DONATION WHERE Status = 'Completed' AND DATE(Donation_Time) BETWEEN %s AND %s) as completed_kg,
                (SELECT COALESCE(SUM(Quantity), 0) FROM WASTE_ITEM WHERE DATE(Recorded_Date) BETWEEN %s AND %s) as waste_kg,
                (SELECT COALESCE(SUM(Output_Quantity), 0) FROM PROCESS WHERE Status = 'Completed' AND DATE(Start_Date) BETWEEN %s AND %s) as output_kg
        """, (start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date), fetch='one')
        
        custom_summary = (
            f"Audit period {start_date} to {end_date}: Rescued {summary_stats['completed_kg']:.1f} kg of fresh surplus food across {summary_stats['total_lots']} donations. "
            f"Logged {summary_stats['waste_kg']:.1f} kg of inedible waste and generated {summary_stats['output_kg']:.1f} kg of eco-processing outputs (compost, biogas, and recyclables)."
        )

    try:
        execute_query("""
            INSERT INTO REPORT (Center_ID, Generated_By_User_ID, Report_Type, Start_Date, End_Date, Summary)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (center_id, user_id, report_type, start_date, end_date, custom_summary), commit=True)
        flash('Report generated and archived successfully in the database!', 'success')
    except Exception as e:
        flash(f'Report generation failed: {e}', 'danger')

    return redirect(url_for('reports_page'))

@app.route('/reports/export/csv')
@role_required('Admin')
def export_csv_report():
    """Export complete donation history to CSV for external audits."""
    donations = execute_query("""
        SELECT d.Donation_ID, d.Food_Type, d.Quantity, d.Unit, d.Food_Category, d.Status,
               d.Prepared_On, d.Expiry_Date, d.Donation_Time,
               u.Name as Donor_Name, u.Phone as Donor_Phone, u.Email as Donor_Email,
               ngo.NGO_Name, ngo.License_No as NGO_License,
               p.Vehicle_No, p.Driver_Name, p.Status as Pickup_Status,
               r.Rating, r.Comment as Review_Comment
        FROM DONATION d
        JOIN `USER` u ON d.User_ID = u.User_ID
        LEFT JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
        LEFT JOIN PICKUP p ON d.Donation_ID = p.Donation_ID
        LEFT JOIN REVIEW r ON d.Donation_ID = r.Donation_ID
        ORDER BY d.Donation_Time DESC
    """, fetch='all') or []

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow([
        'Donation ID', 'Food Type', 'Quantity', 'Unit', 'Food Category', 'Status',
        'Prepared On', 'Expiry Date', 'Donation Time',
        'Donor Name', 'Donor Phone', 'Donor Email',
        'Claiming NGO', 'NGO License',
        'Pickup Vehicle', 'Pickup Driver', 'Pickup Status',
        'Review Rating', 'Review Feedback'
    ])

    for row in donations:
        writer.writerow([
            row.get('Donation_ID'), row.get('Food_Type'), row.get('Quantity'), row.get('Unit'),
            row.get('Food_Category'), row.get('Status'),
            row.get('Prepared_On'), row.get('Expiry_Date'), row.get('Donation_Time'),
            row.get('Donor_Name'), row.get('Donor_Phone'), row.get('Donor_Email'),
            row.get('NGO_Name') or 'None', row.get('NGO_License') or 'None',
            row.get('Vehicle_No') or 'N/A', row.get('Driver_Name') or 'N/A', row.get('Pickup_Status') or 'N/A',
            row.get('Rating') or 'Unrated', row.get('Review_Comment') or ''
        ])

    output = Response(si.getvalue(), mimetype='text/csv')
    filename = f"food_waste_report_{datetime.date.today().isoformat()}.csv"
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return output

# ----------------------------------------------------------------------------
# Canonical ER Diagram & Schema Specification View
# ----------------------------------------------------------------------------
@app.route('/er-diagram')
@app.route('/er')
@app.route('/erdiagram')
def er_diagram_view():
    """Renders the Canonical ER Diagram & Relational Schema Alignment Console."""
    return render_template('er_diagram.html')

# ----------------------------------------------------------------------------
# Interactive DBMS Viva Demonstration Page
# ----------------------------------------------------------------------------
@app.route('/viva-queries')
@app.route('/viva')
@app.route('/queries')
def viva_queries():
    """Interactive DBMS Demonstration console for course viva & professor review."""
    viva_catalog = [
        {
            'id': 1,
            'title': 'Query 1: Multi-Table INNER JOIN',
            'concept': 'INNER JOIN between DONATION and USER',
            'desc': 'Demonstrates retrieval of all listed food items combined with verified donor contact profiles.',
            'sql': """SELECT d.Donation_ID, d.Food_Type, d.Quantity, d.Unit, d.Food_Category, d.Status,
       u.Name AS Donor_Name, u.Phone AS Donor_Phone, d.Pickup_Address
FROM DONATION d
INNER JOIN `USER` u ON d.User_ID = u.User_ID
ORDER BY d.Donation_Time DESC LIMIT 10;"""
        },
        {
            'id': 2,
            'title': 'Query 2: Multi-Table LEFT OUTER JOIN',
            'concept': 'LEFT OUTER JOIN with COALESCE',
            'desc': 'Shows all donations including those currently unclaimed where NGO details are NULL.',
            'sql': """SELECT d.Donation_ID, d.Food_Type, d.Quantity, d.Status,
       COALESCE(ngo.NGO_Name, 'Unclaimed / Available') AS Claimed_By,
       COALESCE(ngo.Contact_No, 'N/A') AS NGO_Contact
FROM DONATION d
LEFT JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
ORDER BY d.Status, d.Donation_ID LIMIT 10;"""
        },
        {
            'id': 3,
            'title': 'Query 3: 4-Way Complex Relational JOIN',
            'concept': '4-Table Join (Donation + Donor + NGO + Pickup)',
            'desc': 'Full lifecycle audit joining 4 tables to track food from donor to beneficiary driver.',
            'sql': """SELECT d.Donation_ID, d.Food_Type, d.Quantity,
       donor.Name AS Donor_Business, ngo.NGO_Name AS Beneficiary_NGO,
       p.Driver_Name, p.Vehicle_No, p.Status AS Pickup_Status
FROM DONATION d
JOIN `USER` donor ON d.User_ID = donor.User_ID
JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
JOIN PICKUP p ON d.Donation_ID = p.Donation_ID
LIMIT 10;"""
        },
        {
            'id': 4,
            'title': 'Query 4: Aggregation with GROUP BY',
            'concept': 'Aggregate Functions: COUNT, SUM, AVG, MIN, MAX',
            'desc': 'Summarizes total food batches, total kg rescued, and average batch weight per Food Category.',
            'sql': """SELECT Food_Category,
       COUNT(Donation_ID) AS Total_Batches,
       SUM(Quantity) AS Total_Rescued_Kg,
       ROUND(AVG(Quantity), 2) AS Avg_Batch_Kg,
       MIN(Quantity) AS Min_Batch_Kg,
       MAX(Quantity) AS Max_Batch_Kg
FROM DONATION
GROUP BY Food_Category
ORDER BY Total_Rescued_Kg DESC;"""
        },
        {
            'id': 5,
            'title': 'Query 5: GROUP BY with HAVING Clause',
            'concept': 'Filtering Aggregated Groups (HAVING SUM > 300)',
            'desc': 'Identifies collection centers that have handled a cumulative waste processing load exceeding 300 kg.',
            'sql': """SELECT c.Center_ID, c.Center_Name, c.Center_Type,
       COUNT(p.Process_ID) AS Total_Processes,
       SUM(p.Input_Quantity) AS Total_Input_Waste_Kg,
       SUM(p.Output_Quantity) AS Total_Resource_Yield_Kg
FROM COLLECTION_CENTER c
JOIN PROCESS p ON c.Center_ID = p.Center_ID
GROUP BY c.Center_ID, c.Center_Name, c.Center_Type
HAVING SUM(p.Input_Quantity) > 300.00
ORDER BY Total_Input_Waste_Kg DESC;"""
        },
        {
            'id': 6,
            'title': 'Query 6: Subquery using IN Operator',
            'concept': 'Nested Subquery (IN)',
            'desc': 'Selects donors whose contributions earned the highest 5-star community review rating.',
            'sql': """SELECT User_ID, Name AS Donor_Name, Email, Phone, Address
FROM `USER`
WHERE User_ID IN (
    SELECT DISTINCT d.User_ID
    FROM DONATION d
    JOIN REVIEW r ON d.Donation_ID = r.Donation_ID
    WHERE r.Rating = 5
);"""
        },
        {
            'id': 7,
            'title': 'Query 7: Correlated Subquery with NOT EXISTS',
            'concept': 'NOT EXISTS for Negative Outer Logic',
            'desc': 'Discovers certified NGOs that are registered in the system but have not yet claimed any food donation.',
            'sql': """SELECT n.NGO_ID, n.NGO_Name, n.NGO_Type, n.Contact_No, n.Email
FROM NGO_RECEIVER n
WHERE NOT EXISTS (
    SELECT 1 FROM DONATION d 
    WHERE d.Claimed_By_NGO_ID = n.NGO_ID
);"""
        },
        {
            'id': 8,
            'title': 'Query 8: Correlated Subquery vs Category Average',
            'concept': 'Correlated Subquery in WHERE Clause',
            'desc': 'Filters donations whose individual quantity exceeds the mean donation weight for that specific category.',
            'sql': """SELECT d1.Donation_ID, d1.Food_Type, d1.Food_Category, d1.Quantity,
       ROUND((SELECT AVG(d2.Quantity) FROM DONATION d2 WHERE d2.Food_Category = d1.Food_Category), 2) AS Category_Avg_Kg
FROM DONATION d1
WHERE d1.Quantity > (
    SELECT AVG(d2.Quantity) FROM DONATION d2 WHERE d2.Food_Category = d1.Food_Category
)
ORDER BY d1.Food_Category, d1.Quantity DESC;"""
        },
        {
            'id': 9,
            'title': 'Query 9: Executive KPI Aggregation',
            'concept': 'Cross-Table Scalar Subqueries',
            'desc': 'Single consolidated query calculating live rescue totals, diversion rate %, and registered accounts.',
            'sql': """SELECT 
    (SELECT COUNT(*) FROM `USER` WHERE User_Type = 'Donor') AS Total_Donors,
    (SELECT COUNT(*) FROM `NGO_RECEIVER`) AS Registered_NGOs,
    (SELECT COUNT(*) FROM `DONATION` WHERE Status = 'Available') AS Active_Listings,
    (SELECT COALESCE(SUM(Quantity), 0) FROM `DONATION` WHERE Status = 'Completed') AS Rescued_Food_Kg,
    (SELECT COALESCE(SUM(Quantity), 0) FROM `WASTE_ITEM`) AS Waste_Logged_Kg,
    (SELECT COALESCE(SUM(Output_Quantity), 0) FROM `PROCESS` WHERE Status = 'Completed') AS Output_Produced_Kg,
    ROUND((SELECT COUNT(*) FROM `DONATION` WHERE Status = 'Completed') / 
          (SELECT GREATEST(COUNT(*), 1) FROM `DONATION`) * 100, 2) AS Completion_Rate_Pct;"""
        },
        {
            'id': 10,
            'title': 'Query 10: Date/Time Arithmetic and Expiry Warning',
            'concept': 'TIMESTAMPDIFF and CASE Expression',
            'desc': 'Computes remaining shelf life in hours and classifies urgency levels for rapid dispatch.',
            'sql': """SELECT Donation_ID, Food_Type, Food_Category, Quantity, Unit, Expiry_Date,
       TIMESTAMPDIFF(HOUR, NOW(), Expiry_Date) AS Hours_Remaining,
       CASE 
           WHEN TIMESTAMPDIFF(HOUR, NOW(), Expiry_Date) <= 6 THEN 'CRITICAL: < 6 Hours'
           WHEN TIMESTAMPDIFF(HOUR, NOW(), Expiry_Date) <= 24 THEN 'WARNING: < 24 Hours'
           ELSE 'SAFE'
       END AS Shelf_Life_Warning
FROM DONATION
WHERE Status = 'Available' AND Expiry_Date > NOW()
ORDER BY Expiry_Date ASC;"""
        },
        {
            'id': 11,
            'title': 'Query 11: Biological Processing Yield Ratio',
            'concept': 'Ratio Calculation and Conversion Percentage',
            'desc': 'Analyzes the output yield efficiency per conversion method (Composting, Biogas, Recycling).',
            'sql': """SELECT Process_Type,
       COUNT(Process_ID) AS Total_Cycles,
       SUM(Input_Quantity) AS Total_Input_Kg,
       SUM(Output_Quantity) AS Total_Useful_Output,
       ROUND((SUM(Output_Quantity) / NULLIF(SUM(Input_Quantity), 0)) * 100, 2) AS Yield_Efficiency_Pct
FROM PROCESS
WHERE Status = 'Completed'
GROUP BY Process_Type
ORDER BY Yield_Efficiency_Pct DESC;"""
        },
        {
            'id': 12,
            'title': 'Query 12: Center Capacity Utilization Analysis',
            'concept': 'Arithmetic Capacity vs Occupancy Computation',
            'desc': 'Calculates storage percentage utilization across municipal triage collection hubs.',
            'sql': """SELECT Center_ID, Center_Name, Center_Type,
       Capacity AS Max_Capacity_Kg, Current_Occupancy AS Current_Waste_Kg,
       ROUND((Current_Occupancy / Capacity) * 100, 2) AS Utilization_Percentage,
       CASE 
           WHEN (Current_Occupancy / Capacity) >= 0.85 THEN 'CRITICAL OVERLOAD'
           WHEN (Current_Occupancy / Capacity) >= 0.50 THEN 'MODERATE LOAD'
           ELSE 'OPTIMAL'
       END AS Center_Load_Status
FROM COLLECTION_CENTER
ORDER BY Utilization_Percentage DESC;"""
        },
        {
            'id': 13,
            'title': 'Query 13: Donor Ranking using Window Function',
            'concept': 'Window Functions: DENSE_RANK() OVER (...)',
            'desc': 'Ranks community food donors based on the total cumulative kilograms donated.',
            'sql': """SELECT u.User_ID, u.Name AS Donor_Name,
       COUNT(d.Donation_ID) AS Donations_Count,
       SUM(d.Quantity) AS Total_Food_Donated_Kg,
       DENSE_RANK() OVER (ORDER BY SUM(d.Quantity) DESC) AS Donor_Rank
FROM `USER` u
JOIN DONATION d ON u.User_ID = d.User_ID
WHERE u.User_Type = 'Donor'
GROUP BY u.User_ID, u.Name
ORDER BY Donor_Rank ASC;"""
        },
        {
            'id': 14,
            'title': 'Query 14: Querying Database View (vw_available_donations)',
            'concept': 'Database View Execution with Compound Filter',
            'desc': 'Queries the pre-compiled database view for instant display of active vegetarian & bakery items.',
            'sql': """SELECT Donation_ID, Food_Type, Quantity, Unit, Donor_Name, Donor_Phone, Hours_Until_Expiry
FROM vw_available_donations
WHERE Food_Category IN ('Cooked Food', 'Bakery')
ORDER BY Hours_Until_Expiry ASC;"""
        },
        {
            'id': 15,
            'title': 'Query 15: Transaction & Rollback Demonstration',
            'concept': 'ACID Properties: START TRANSACTION & ROLLBACK',
            'desc': 'Demonstrates transactional integrity when reverting cancelled pickups back to available status.',
            'sql': """SELECT Donation_ID, Food_Type, Status, Claimed_By_NGO_ID 
FROM DONATION 
WHERE Donation_ID = 6;"""
        },
        {
            'id': 16,
            'title': 'Query 16: NGO to Collection Center Routing (<DELIVERS TO>)',
            'concept': 'ER Relationship: NGO_RECEIVER <DELIVERS TO> COLLECTION_CENTER',
            'desc': 'Verifies the routing of certified NGOs to their assigned municipal collection hub for intake triage.',
            'sql': """SELECT n.NGO_ID, n.NGO_Name, n.NGO_Type, n.License_No, n.Contact_No,
       c.Center_ID, c.Center_Name AS Triage_Collection_Center, c.Center_Type AS Hub_Type, c.Address AS Hub_Location
FROM NGO_RECEIVER n
LEFT JOIN COLLECTION_CENTER c ON n.Delivers_To_Center_ID = c.Center_ID
ORDER BY n.NGO_Name;"""
        }
    ]

    selected_query_id = request.args.get('q', type=int)
    results = None
    selected_query = None
    query_columns = []
    error_msg = None

    if selected_query_id:
        for q in viva_catalog:
            if q['id'] == selected_query_id:
                selected_query = q
                break

    if selected_query:
        try:
            results = execute_query(selected_query['sql'], fetch='all')
            if results and len(results) > 0:
                query_columns = list(results[0].keys())
        except Exception as ex:
            error_msg = str(ex)

    return render_template('viva_queries.html', 
                           catalog=viva_catalog, 
                           selected_query=selected_query,
                           results=results,
                           query_columns=query_columns,
                           error_msg=error_msg)

# ----------------------------------------------------------------------------
# Application Launcher
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 70)
    print("  Smart Food Waste Reduction & Donation Management System")
    print("  Web Server Ready: http://127.0.0.1:5000")
    print("=" * 70)
    app.run(host='0.0.0.0', port=5000, debug=False)
