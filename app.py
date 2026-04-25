"""
WanderLog - Travel Planner Application
Task 2 Submission for Kinetrexa Software
Python Development Internship

ALL BUSINESS LOGIC IN PYTHON - Minimal JavaScript
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
import sqlite3
from datetime import datetime, date, timedelta
import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from werkzeug.utils import secure_filename

# ============================================
# CREATE FLASK APPLICATION
# ============================================
app = Flask(__name__, template_folder='templates')
app.secret_key = 'wanderlog_secret_key_2026'

# ============================================
# DEBUG: Check folder structure
# ============================================
print("=" * 50)
print("🌍 WanderLog Starting...")
print("Current Directory:", os.getcwd())
print("Templates folder exists?", os.path.exists('templates'))

if not os.path.exists('templates'):
    print("⚠️ Creating templates folder...")
    os.makedirs('templates')
    
if os.path.exists('templates'):
    files = os.listdir('templates')
    print(f"📁 Templates found: {files}")
print("=" * 50)

# ============================================
# DATABASE FUNCTIONS
# ============================================
def get_db_connection():
    conn = sqlite3.connect('travels.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT NOT NULL,
            country TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            travelers INTEGER DEFAULT 1,
            budget REAL DEFAULT 0,
            trip_type TEXT DEFAULT 'Leisure',
            notes TEXT,
            status TEXT DEFAULT 'Upcoming',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM trips')
    count = cursor.fetchone()[0]
    
    if count == 0:
        sample_trips = [
            ('Goa', 'India', '2026-05-15', '2026-05-20', 2, 25000, 'Leisure', 'Beach vacation with friends', 'Upcoming'),
            ('Manali', 'India', '2026-06-10', '2026-06-17', 4, 45000, 'Adventure', 'Trekking and snow activities', 'Upcoming'),
            ('Jaipur', 'India', '2026-04-01', '2026-04-05', 2, 18000, 'Heritage', 'Palace and fort visits', 'Completed'),
            ('Kerala', 'India', '2026-07-20', '2026-07-27', 2, 35000, 'Honeymoon', 'Backwaters and houseboat', 'Upcoming'),
            ('Mumbai', 'India', '2026-03-10', '2026-03-12', 1, 12000, 'Business', 'Client meetings', 'Completed')
        ]
        cursor.executemany('''
            INSERT INTO trips (destination, country, start_date, end_date, travelers, budget, trip_type, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_trips)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

# ============================================
# PYTHON HELPER FUNCTIONS (ALL LOGIC HERE)
# ============================================

def calculate_trip_duration(start_date, end_date):
    """Calculate number of days between two dates"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    return (end - start).days + 1

def get_trip_status(start_date, end_date):
    """Determine if trip is Upcoming, Ongoing, or Completed"""
    today = date.today()
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    if today < start:
        return "Upcoming"
    elif today > end:
        return "Completed"
    else:
        return "Ongoing"

def calculate_days_until(start_date):
    """Calculate days remaining until trip starts"""
    today = date.today()
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    days = (start - today).days
    return days if days > 0 else 0

def calculate_budget_breakdown(total_budget, days, travelers):
    """Smart budget allocation algorithm - PURE PYTHON"""
    if days <= 0:
        days = 1
    if travelers <= 0:
        travelers = 1
    return {
        'accommodation': round(total_budget * 0.35, 2),
        'food': round(total_budget * 0.25, 2),
        'transport': round(total_budget * 0.20, 2),
        'activities': round(total_budget * 0.15, 2),
        'emergency': round(total_budget * 0.05, 2),
        'daily_budget': round(total_budget / days, 2),
        'per_person': round(total_budget / travelers, 2)
    }

def get_weather_info(destination, month):
    """Returns weather prediction based on destination and month"""
    weather_data = {
        'Goa': {1: '☀️ Warm & Sunny', 2: '☀️ Pleasant', 3: '☀️ Warm', 
                4: '🌤️ Hot', 5: '🔥 Very Hot', 6: '🌧️ Rainy', 
                7: '🌧️ Monsoon', 8: '🌧️ Rainy', 9: '🌤️ Pleasant',
                10: '☀️ Warm', 11: '☀️ Perfect', 12: '☀️ Beach Weather'},
        'Manali': {1: '❄️ Snow', 2: '❄️ Cold', 3: '🌨️ Chilly',
                   4: '🌤️ Pleasant', 5: '☀️ Warm', 6: '☀️ Perfect',
                   7: '🌧️ Rainy', 8: '🌧️ Rainy', 9: '🌤️ Nice',
                   10: '🍂 Cool', 11: '❄️ Cold', 12: '❄️ Snow'},
        'Jaipur': {1: '🌤️ Cool', 2: '☀️ Pleasant', 3: '☀️ Warm',
                   4: '🔥 Hot', 5: '🔥 Very Hot', 6: '🔥 Extreme Heat',
                   7: '🌧️ Humid', 8: '🌧️ Rainy', 9: '☀️ Warm',
                   10: '☀️ Pleasant', 11: '🌤️ Perfect', 12: '🌤️ Cool'},
        'Kerala': {1: '☀️ Pleasant', 2: '☀️ Warm', 3: '🔥 Hot',
                   4: '🔥 Hot', 5: '🌧️ Pre-Monsoon', 6: '🌧️ Monsoon',
                   7: '🌧️ Heavy Rain', 8: '🌧️ Rainy', 9: '🌤️ Pleasant',
                   10: '🌤️ Nice', 11: '☀️ Warm', 12: '☀️ Perfect'},
        'Mumbai': {1: '🌤️ Pleasant', 2: '☀️ Warm', 3: '☀️ Hot',
                   4: '🔥 Hot', 5: '🔥 Humid', 6: '🌧️ Monsoon',
                   7: '🌧️ Heavy Rain', 8: '🌧️ Rainy', 9: '🌤️ Pleasant',
                   10: '🔥 Hot', 11: '☀️ Warm', 12: '🌤️ Cool'}
    }
    default = {1: '❄️ Winter', 2: '❄️ Winter', 3: '🌸 Spring',
               4: '🌸 Spring', 5: '🌸 Spring', 6: '☀️ Summer',
               7: '☀️ Summer', 8: '☀️ Summer', 9: '🍂 Autumn',
               10: '🍂 Autumn', 11: '🍂 Autumn', 12: '❄️ Winter'}
    
    if destination in weather_data:
        return weather_data[destination].get(month, '🌤️ Moderate')
    return default.get(month, '🌤️ Pleasant')

def generate_packing_list(trip_type, weather, days):
    """Generate smart packing suggestions - PURE PYTHON"""
    items = {
        'essentials': ['Passport/ID', 'Phone & Charger', 'Power Bank', 'Wallet/Cards'],
        'clothing': [],
        'toiletries': ['Toothbrush', 'Toothpaste', 'Shampoo', 'Soap', 'Deodorant'],
        'health': ['First Aid Kit', 'Prescription Medicines', 'Pain Relievers'],
        'electronics': ['Camera', 'Headphones'],
        'documents': ['Flight Tickets', 'Hotel Booking', 'Travel Insurance']
    }
    
    # Add clothing based on weather (Python string matching)
    if '❄️' in weather or 'Cold' in weather or 'Snow' in weather:
        items['clothing'] = ['Jacket', 'Sweaters', 'Thermal Wear', 'Woolen Socks', 'Gloves', 'Scarf']
    elif '🔥' in weather or 'Hot' in weather:
        items['clothing'] = ['Cotton T-shirts', 'Shorts', 'Sunglasses', 'Hat/Cap', 'Sunscreen']
    elif '🌧️' in weather or 'Rain' in weather:
        items['clothing'] = ['Raincoat', 'Umbrella', 'Quick-dry Clothes', 'Waterproof Shoes']
    else:
        items['clothing'] = ['Comfortable Clothes', 'Light Jacket', 'Walking Shoes']
    
    # Add trip type specific items (Python conditions)
    if trip_type == 'Adventure':
        items['essentials'].extend(['Flashlight', 'Multi-tool', 'Water Bottle'])
    elif trip_type == 'Honeymoon':
        items['essentials'].extend(['Camera', 'Romantic Outfit'])
    elif trip_type == 'Business':
        items['essentials'].extend(['Laptop', 'Business Cards', 'Formal Attire'])
    
    return items

def get_attractions(destination):
    """Returns popular attractions - PURE PYTHON DICTIONARY"""
    attractions_dict = {
        'Goa': ['🏖️ Baga Beach', '🏰 Aguada Fort', '⛪ Basilica of Bom Jesus', '🌴 Palolem Beach', '🍛 Fish Curry Trail'],
        'Manali': ['🏔️ Rohtang Pass', '🛕 Hidimba Temple', '🌉 Solang Valley', '🏞️ Jogini Falls', '🛷 Snow Activities'],
        'Jaipur': ['🏰 Amber Fort', '🌅 Hawa Mahal', '🏛️ City Palace', '🌟 Jantar Mantar', '🐘 Elephant Ride'],
        'Kerala': ['🚤 Alleppey Backwaters', '🌴 Munnar Tea Gardens', '🏖️ Kovalam Beach', '🐘 Periyar Wildlife', '💆 Ayurvedic Spa'],
        'Mumbai': ['🚪 Gateway of India', '🌊 Marine Drive', '🎬 Bollywood Tour', '🕉️ Siddhivinayak Temple', '🛍️ Colaba Causeway']
    }
    return attractions_dict.get(destination, ['🏛️ Local Museum', '🌳 Central Park', '🛍️ Shopping District', '🍽️ Local Restaurants'])

def get_travel_tips(destination):
    """Returns helpful travel tips - PURE PYTHON"""
    tips = {
        'Goa': ['Rent a scooter for easy travel', 'Try authentic Goan fish curry', 'Visit beaches early morning', 'Carry cash for beach shacks'],
        'Manali': ['Acclimatize for 1 day before activities', 'Book Rohtang Pass permit in advance', 'Carry warm clothes even in summer', 'Try local Himachali food'],
        'Jaipur': ['Start sightseeing early to beat heat', 'Hire a guide at Amber Fort', 'Try Rajasthani thali', 'Bargain at local markets'],
        'Kerala': ['Book houseboat in advance', 'Carry mosquito repellent', 'Try banana chips and toddy', 'Best time is Sept-March'],
        'Mumbai': ['Use local trains for cheap travel', 'Try vada pav and pav bhaji', 'Visit Marine Drive at sunset', 'Book hotels near station']
    }
    return tips.get(destination, ['Research local customs', 'Keep emergency contacts handy', 'Learn basic local phrases', 'Stay hydrated'])

def get_destination_stats(trips):
    """Calculate statistics from trips - PURE PYTHON"""
    total_trips = len(trips)
    total_budget = sum(trip['budget'] for trip in trips)
    upcoming_trips = sum(1 for trip in trips if trip['status'] == 'Upcoming')
    completed_trips = sum(1 for trip in trips if trip['status'] == 'Completed')
    ongoing_trips = sum(1 for trip in trips if trip['status'] == 'Ongoing')
    countries = set(trip['country'] for trip in trips)
    countries_count = len(countries)
    
    # Get unique destinations
    destinations = set(trip['destination'] for trip in trips)
    
    # Calculate average budget
    avg_budget = total_budget / total_trips if total_trips > 0 else 0
    
    return {
        'total_trips': total_trips,
        'total_budget': total_budget,
        'upcoming_trips': upcoming_trips,
        'completed_trips': completed_trips,
        'ongoing_trips': ongoing_trips,
        'countries_count': countries_count,
        'destinations_count': len(destinations),
        'avg_budget': round(avg_budget, 2),
        'countries_list': sorted(list(countries))
    }

def filter_trips_python(trips, query):
    """Filter trips based on search query - PURE PYTHON"""
    if not query:
        return trips
    
    query = query.lower()
    filtered = []
    for trip in trips:
        if (query in trip['destination'].lower() or 
            query in trip['country'].lower() or 
            query in trip['trip_type'].lower() or
            (trip['notes'] and query in trip['notes'].lower())):
            filtered.append(trip)
    return filtered

def sort_trips_python(trips, sort_by='created_at', reverse=True):
    """Sort trips by given criteria - PURE PYTHON"""
    if sort_by == 'budget':
        return sorted(trips, key=lambda x: x['budget'], reverse=reverse)
    elif sort_by == 'start_date':
        return sorted(trips, key=lambda x: x['start_date'], reverse=reverse)
    elif sort_by == 'destination':
        return sorted(trips, key=lambda x: x['destination'], reverse=reverse)
    else:
        return sorted(trips, key=lambda x: x['created_at'], reverse=reverse)

# ============================================
# THEME MANAGEMENT (PYTHON + COOKIES)
# ============================================

def get_theme_from_cookie():
    """Get theme from cookie - PURE PYTHON"""
    theme = request.cookies.get('wanderlog_theme')
    return theme if theme in ['light', 'dark'] else 'light'

# ============================================
# FLASK ROUTES (ALL PYTHON BACKEND)
# ============================================

@app.route('/')
def dashboard():
    """Dashboard - Shows all trips with Python-calculated statistics"""
    conn = get_db_connection()
    trips = conn.execute('SELECT * FROM trips ORDER BY created_at DESC').fetchall()
    conn.close()
    
    # Convert to list of dicts for easier Python manipulation
    trips_list = [dict(trip) for trip in trips]
    
    # Get search query from URL parameters
    search_query = request.args.get('query', '')
    sort_by = request.args.get('sort', 'created_at')
    
    # Filter trips using Python (not JavaScript)
    if search_query:
        trips_list = filter_trips_python(trips_list, search_query)
    
    # Sort trips using Python
    trips_list = sort_trips_python(trips_list, sort_by)
    
    # Calculate statistics using Python
    stats = get_destination_stats(trips_list)
    
    # Get theme from cookie
    theme = get_theme_from_cookie()
    
    # Create response with cookie
    response = make_response(render_template('dashboard.html', 
                         trips=trips_list,
                         stats=stats,
                         search_query=search_query,
                         sort_by=sort_by,
                         theme=theme))
    
    # Set theme cookie if not exists
    if not request.cookies.get('wanderlog_theme'):
        response.set_cookie('wanderlog_theme', 'light', max_age=60*60*24*365)
    
    return response

@app.route('/set-theme/<theme>')
def set_theme(theme):
    """Set theme via Python route - NO JAVASCRIPT NEEDED"""
    if theme in ['light', 'dark']:
        response = make_response(redirect(request.referrer or url_for('dashboard')))
        response.set_cookie('wanderlog_theme', theme, max_age=60*60*24*365)
        flash(f'Theme changed to {theme} mode', 'success')
        return response
    return redirect(url_for('dashboard'))

@app.route('/trip/<int:trip_id>')
def trip_detail(trip_id):
    """Shows detailed information about a specific trip - ALL PYTHON CALCULATIONS"""
    conn = get_db_connection()
    trip = conn.execute('SELECT * FROM trips WHERE id = ?', (trip_id,)).fetchone()
    conn.close()
    
    if trip is None:
        flash('Trip not found!', 'error')
        return redirect(url_for('dashboard'))
    
    # Convert to dict
    trip = dict(trip)
    
    # ALL CALCULATIONS DONE IN PYTHON
    duration = calculate_trip_duration(trip['start_date'], trip['end_date'])
    days_until = calculate_days_until(trip['start_date'])
    budget_breakdown = calculate_budget_breakdown(trip['budget'], duration, trip['travelers'])
    
    # Update status automatically
    current_status = get_trip_status(trip['start_date'], trip['end_date'])
    if current_status != trip['status']:
        conn = get_db_connection()
        conn.execute('UPDATE trips SET status = ? WHERE id = ?', (current_status, trip_id))
        conn.commit()
        conn.close()
        trip['status'] = current_status
    
    trip_month = datetime.strptime(trip['start_date'], '%Y-%m-%d').month
    weather = get_weather_info(trip['destination'], trip_month)
    packing_list = generate_packing_list(trip['trip_type'], weather, duration)
    attractions = get_attractions(trip['destination'])
    tips = get_travel_tips(trip['destination'])
    
    theme = get_theme_from_cookie()
    
    return render_template('trip_detail.html',
                         trip=trip,
                         duration=duration,
                         days_until=days_until,
                         budget_breakdown=budget_breakdown,
                         weather=weather,
                         packing_list=packing_list,
                         attractions=attractions,
                         tips=tips,
                         theme=theme)

@app.route('/add', methods=['GET', 'POST'])
def add_trip():
    """Add new trip - Form handling in Python"""
    if request.method == 'POST':
        # Get data from form
        destination = request.form['destination']
        country = request.form['country']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        travelers = int(request.form['travelers'])
        budget = float(request.form['budget'])
        trip_type = request.form['trip_type']
        notes = request.form.get('notes', '')
        
        # Python validation
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        if end < start:
            flash('End date cannot be before start date!', 'error')
            return render_template('add_trip.html', 
                                 form_data=request.form,
                                 theme=get_theme_from_cookie())
        
        # Calculate status automatically (Python)
        status = get_trip_status(start_date, end_date)
        
        # Save to database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO trips (destination, country, start_date, end_date, travelers, budget, trip_type, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (destination, country, start_date, end_date, travelers, budget, trip_type, notes, status))
        conn.commit()
        conn.close()
        
        flash('Trip added successfully! 🎉', 'success')
        return redirect(url_for('dashboard'))
    
    theme = get_theme_from_cookie()
    return render_template('add_trip.html', theme=theme, form_data={})

@app.route('/trip/<int:trip_id>/edit', methods=['GET', 'POST'])
def edit_trip(trip_id):
    """Edit trip - Python form handling"""
    conn = get_db_connection()
    trip = conn.execute('SELECT * FROM trips WHERE id = ?', (trip_id,)).fetchone()
    
    if trip is None:
        conn.close()
        flash('Trip not found!', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        destination = request.form['destination']
        country = request.form['country']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        travelers = int(request.form['travelers'])
        budget = float(request.form['budget'])
        trip_type = request.form['trip_type']
        notes = request.form.get('notes', '')
        
        # Python validation
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        if end < start:
            flash('End date cannot be before start date!', 'error')
            return render_template('edit_trip.html', trip=dict(trip), theme=get_theme_from_cookie())
        
        status = get_trip_status(start_date, end_date)
        
        conn.execute('''
            UPDATE trips 
            SET destination = ?, country = ?, start_date = ?, end_date = ?, 
                travelers = ?, budget = ?, trip_type = ?, notes = ?, status = ?
            WHERE id = ?
        ''', (destination, country, start_date, end_date, travelers, budget, trip_type, notes, status, trip_id))
        conn.commit()
        conn.close()
        
        flash('Trip updated successfully! ✏️', 'success')
        return redirect(url_for('trip_detail', trip_id=trip_id))
    
    conn.close()
    theme = get_theme_from_cookie()
    return render_template('edit_trip.html', trip=dict(trip), theme=theme)

@app.route('/trip/<int:trip_id>/delete', methods=['POST'])
def delete_trip(trip_id):
    """Delete trip - Python backend"""
    conn = get_db_connection()
    conn.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
    conn.commit()
    conn.close()
    flash('Trip deleted successfully! 🗑️', 'success')
    return redirect(url_for('dashboard'))

@app.route('/search')
def search_trips():
    """Search trips - Python backend filtering"""
    query = request.args.get('query', '')
    conn = get_db_connection()
    trips = conn.execute('SELECT * FROM trips ORDER BY created_at DESC').fetchall()
    conn.close()
    
    trips_list = [dict(trip) for trip in trips]
    
    # Filter using Python
    filtered_trips = filter_trips_python(trips_list, query)
    stats = get_destination_stats(filtered_trips)
    
    theme = get_theme_from_cookie()
    
    return render_template('dashboard.html', 
                         trips=filtered_trips,
                         stats=stats,
                         search_query=query,
                         theme=theme)

@app.route('/api/theme', methods=['GET', 'POST'])
def api_theme():
    """REST API endpoint for theme - Python backend"""
    if request.method == 'POST':
        data = request.get_json()
        theme = data.get('theme', 'light')
        if theme in ['light', 'dark']:
            response = make_response(jsonify({'status': 'success', 'theme': theme}))
            response.set_cookie('wanderlog_theme', theme, max_age=60*60*24*365)
            return response
    else:
        theme = get_theme_from_cookie()
        return jsonify({'theme': theme})
    
    return jsonify({'status': 'error'}), 400

# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    print("🌍 Initializing WanderLog Travel Planner...")
    init_database()
    print("=" * 50)
    print("🚀 Starting server at http://127.0.0.1:5000")
    print("📱 Open your browser and go to: http://127.0.0.1:5000")
    print("🎨 Theme toggle works via Python cookies (no JavaScript needed!)")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000)