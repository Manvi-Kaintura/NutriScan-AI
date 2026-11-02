from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, session, flash
)

import requests
import os
import time
import sqlite3
import secrets

from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from google import genai


# =====================================================
# APPLICATION SETUP
# =====================================================

app = Flask(__name__)

load_dotenv()

DATABASE = os.path.join(app.root_path, 'nutriscan.db')

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    secrets.token_hex(32)
)


# =====================================================
# GEMINI API SETUP
# =====================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


# =====================================================
# DATABASE SETUP
# =====================================================

def init_db():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TEXT
        )
    ''')

    # Scan history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT,
            name TEXT,
            brand TEXT,
            calories TEXT,
            protein TEXT,
            carbs TEXT,
            fat TEXT,
            fibre TEXT,
            sugar TEXT,
            saturated_fat TEXT,
            sodium TEXT,
            score INTEGER,
            scanned_at TEXT
        )
    ''')

    # Add user_id to an existing scan_history table
    cursor.execute("PRAGMA table_info(scan_history)")

    columns = [column[1] for column in cursor.fetchall()]

    if 'user_id' not in columns:

        cursor.execute('''
            ALTER TABLE scan_history
            ADD COLUMN user_id INTEGER
        ''')

    conn.commit()
    conn.close()


init_db()


# =====================================================
# LOGIN REQUIRED DECORATOR
# =====================================================

def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if 'user_id' not in session:

            return redirect(url_for('login'))

        return function(*args, **kwargs)

    return decorated_function


# =====================================================
# SAVE SCAN
# =====================================================

def save_scan(data, user_id):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO scan_history (
            barcode, name, brand, calories, protein,
            carbs, fat, fibre, sugar, saturated_fat,
            sodium, score, scanned_at, user_id
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    ''', (
        data['barcode'],
        data['name'],
        data['brand'],
        data['calories'],
        data['protein'],
        data['carbs'],
        data['fat'],
        data['fibre'],
        data['sugar'],
        data['saturated_fat'],
        data['sodium'],
        data['score'],
        datetime.now().strftime('%d-%m-%Y %I:%M %p'),
        user_id
    ))

    conn.commit()
    conn.close()


# =====================================================
# API REQUEST SETUP
# =====================================================

HEADERS = {
    'User-Agent': 'NutriScanAI/1.0 (student project)'
}


def make_request(url, params=None, timeout=20, attempts=3):

    for attempt in range(attempts):

        try:

            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=timeout
            )

            response.raise_for_status()

            return response

        except requests.RequestException as e:

            print(
                f"API Request Failed (Attempt {attempt + 1}/{attempts}):",
                repr(e)
            )

            if attempt == attempts - 1:
                raise

            time.sleep(2 ** (attempt + 1))


# =====================================================
# REGISTRATION
# =====================================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if 'user_id' in session:

        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name or not email or not password or not confirm_password:

            flash("Please fill in all fields.", "error")

            return render_template('register.html')

        if len(password) < 8:

            flash("Password must contain at least 8 characters.", "error")

            return render_template('register.html')

        if password != confirm_password:

            flash("Passwords do not match.", "error")

            return render_template('register.html')

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        try:

            cursor.execute('''
                INSERT INTO users (name, email, password, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                name,
                email,
                hashed_password,
                datetime.now().strftime('%d-%m-%Y %I:%M %p')
            ))

            user_id = cursor.lastrowid

            # Assign old demo scans to the first registered user
            cursor.execute('SELECT COUNT(*) FROM users')

            user_count = cursor.fetchone()[0]

            if user_count == 1:

                cursor.execute('''
                    UPDATE scan_history
                    SET user_id = ?
                    WHERE user_id IS NULL
                ''', (user_id,))

            conn.commit()

            session.clear()
            session['user_id'] = user_id
            session['user_name'] = name

            conn.close()

            return redirect(url_for('dashboard'))

        except sqlite3.IntegrityError:

            conn.close()

            flash("An account with this email already exists.", "error")

            return render_template('register.html')

    return render_template('register.html')


# =====================================================
# LOGIN
# =====================================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if 'user_id' in session:

        return redirect(url_for('dashboard'))

    if request.method == 'POST':

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM users WHERE email = ?',
            (email,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user['password'], password):

            session.clear()

            session['user_id'] = user['id']
            session['user_name'] = user['name']

            return redirect(url_for('dashboard'))

        flash("Invalid email or password.", "error")

    return render_template('login.html')


# =====================================================
# LOGOUT
# =====================================================

@app.route('/logout')
@login_required
def logout():

    session.clear()

    return redirect(url_for('login'))


# =====================================================
# HOME PAGE
# =====================================================

@app.route('/')
def home():

    return render_template('index.html')


# =====================================================
# DASHBOARD
# =====================================================

@app.route('/dashboard')
@login_required
def dashboard():

    user_id = session['user_id']

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) FROM scan_history
        WHERE user_id = ?
    ''', (user_id,))

    total_scans = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COUNT(*) FROM scan_history
        WHERE user_id = ? AND score >= 7
    ''', (user_id,))

    healthy_scans = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COUNT(*) FROM scan_history
        WHERE user_id = ? AND score BETWEEN 5 AND 6
    ''', (user_id,))

    moderate_scans = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COUNT(*) FROM scan_history
        WHERE user_id = ? AND score BETWEEN 1 AND 4
    ''', (user_id,))

    unhealthy_scans = cursor.fetchone()[0]

    cursor.execute('''
        SELECT * FROM scan_history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
    ''', (user_id,))

    recent_scans = cursor.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        total_scans=total_scans,
        healthy_scans=healthy_scans,
        moderate_scans=moderate_scans,
        unhealthy_scans=unhealthy_scans,
        recent_scans=recent_scans
    )


# =====================================================
# SCAN PAGE
# =====================================================

@app.route('/scan')
@login_required
def scan():

    return render_template('scan.html')


# =====================================================
# SCAN HISTORY
# =====================================================

@app.route('/history')
@login_required
def history():

    user_id = session['user_id']

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM scan_history
        WHERE user_id = ?
        ORDER BY id DESC
    ''', (user_id,))

    scans = cursor.fetchall()

    conn.close()

    return render_template('history.html', scans=scans)


# Delete individual scan
@app.route('/delete_scan/<int:scan_id>', methods=['POST'])
@login_required
def delete_scan(scan_id):

    user_id = session['user_id']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM scan_history
        WHERE id = ? AND user_id = ?
    ''', (scan_id, user_id))

    conn.commit()
    conn.close()

    return redirect(url_for('history'))


# Clear history
@app.route('/clear_history', methods=['POST'])
@login_required
def clear_history():

    user_id = session['user_id']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM scan_history
        WHERE user_id = ?
    ''', (user_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('history'))


# =====================================================
# PRODUCT COMPARISON
# =====================================================

@app.route('/compare', methods=['GET', 'POST'])
@login_required
def compare():

    user_id = session['user_id']

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM scan_history
        WHERE user_id = ?
        ORDER BY id DESC
    ''', (user_id,))

    products = cursor.fetchall()

    product_a = None
    product_b = None
    winner = None
    message = None

    if request.method == 'POST':

        id_a = request.form.get('product_a')
        id_b = request.form.get('product_b')

        if not id_a or not id_b:

            message = "Please select both products."

        elif id_a == id_b:

            message = "Please select two different scans."

        else:

            cursor.execute('''
                SELECT * FROM scan_history
                WHERE id = ? AND user_id = ?
            ''', (id_a, user_id))

            product_a = cursor.fetchone()

            cursor.execute('''
                SELECT * FROM scan_history
                WHERE id = ? AND user_id = ?
            ''', (id_b, user_id))

            product_b = cursor.fetchone()

            if product_a is None or product_b is None:

                message = "One or both selected products were not found."

            else:

                score_a = product_a['score']
                score_b = product_b['score']

                if score_a is None or score_b is None:

                    winner = "Cannot determine a winner because a nutrition score is unavailable."

                elif score_a > score_b:

                    winner = product_a['name']

                elif score_b > score_a:

                    winner = product_b['name']

                else:

                    winner = "It's a tie!"

    conn.close()

    return render_template(
        'compare.html',
        products=products,
        product_a=product_a,
        product_b=product_b,
        winner=winner,
        message=message
    )


# =====================================================
# NUTRITION CALCULATIONS
# =====================================================

def get_number(nutrients, key):

    value = nutrients.get(key)

    if value is None:
        return None

    try:
        return float(value)

    except (ValueError, TypeError):
        return None


def calculate_score(nutrients):

    score = 5
    available = 0

    sugar = get_number(nutrients, 'sugars_100g')
    saturated_fat = get_number(nutrients, 'saturated-fat_100g')
    sodium = get_number(nutrients, 'sodium_100g')
    fibre = get_number(nutrients, 'fiber_100g')
    protein = get_number(nutrients, 'proteins_100g')
    calories = get_number(nutrients, 'energy-kcal_100g')

    if sugar is not None:

        available += 1

        if sugar <= 5:
            score += 1
        elif sugar > 22.5:
            score -= 2
        elif sugar > 10:
            score -= 1

    if saturated_fat is not None:

        available += 1

        if saturated_fat <= 1:
            score += 1
        elif saturated_fat > 5:
            score -= 2
        elif saturated_fat > 2:
            score -= 1

    if sodium is not None:

        available += 1

        sodium_mg = sodium * 1000

        if sodium_mg <= 120:
            score += 1
        elif sodium_mg > 600:
            score -= 2
        elif sodium_mg > 300:
            score -= 1

    if fibre is not None:

        available += 1

        if fibre >= 6:
            score += 1
        elif fibre >= 3:
            score += 0.5

    if protein is not None:

        available += 1

        if protein >= 10:
            score += 1
        elif protein >= 5:
            score += 0.5

    if calories is not None:

        available += 1

        if calories > 400:
            score -= 1
        elif calories <= 150:
            score += 1

    if available < 3:
        return None

    return max(1, min(10, round(score)))


# =====================================================
# PRODUCT LOOKUP
# =====================================================

@app.route('/lookup', methods=['POST'])
@login_required
def lookup():

    data = request.get_json(silent=True) or {}

    barcode = str(data.get('barcode', '')).strip()

    if not barcode.isdigit():

        return jsonify({
            'error': 'Invalid barcode.'
        }), 400

    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

    try:

        response = make_request(url, timeout=20)

        result = response.json()

        if result.get('status') != 1 or not isinstance(result.get('product'), dict):

            return jsonify({
                'error': 'Product not found. Please check the barcode and try again.'
            }), 404

        product = result['product']

        # Reject placeholder/test records returned by the food database.
        product_name = str(product.get('product_name', '')).strip()
        placeholder_names = {
            'test product api',
            'test product',
            'unknown product'
        }

        if not product_name or product_name.casefold() in placeholder_names:

            return jsonify({
                'error': 'Product not found. Please check the barcode and try again.'
            }), 404

        nutrients = product.get('nutriments', {})

        def get_value(key, unit):

            value = get_number(nutrients, key)

            if value is None:
                return "Not available"

            return f"{round(value, 1):g} {unit}"

        sodium = get_number(nutrients, 'sodium_100g')

        if sodium is not None:
            sodium_display = f"{round(sodium * 1000, 1):g} mg"
        else:
            sodium_display = "Not available"

        product_data = {

            'barcode': barcode,
            'name': product.get('product_name', 'Unknown Product'),
            'brand': product.get('brands', 'Not available'),

            'calories': get_value('energy-kcal_100g', 'kcal'),
            'protein': get_value('proteins_100g', 'g'),
            'carbs': get_value('carbohydrates_100g', 'g'),
            'fat': get_value('fat_100g', 'g'),
            'fibre': get_value('fiber_100g', 'g'),
            'sugar': get_value('sugars_100g', 'g'),

            'saturated_fat': get_value('saturated-fat_100g', 'g'),
            'sodium': sodium_display,

            'protein_value': get_number(nutrients, 'proteins_100g'),
            'carbs_value': get_number(nutrients, 'carbohydrates_100g'),
            'fat_value': get_number(nutrients, 'fat_100g'),

            'score': calculate_score(nutrients)

        }

        try:

            save_scan(product_data, session['user_id'])

            print("Product saved for user:", session['user_id'])

        except sqlite3.Error as e:

            print("Database Save Error:", repr(e))

        return jsonify(product_data)

    except requests.RequestException as e:

        print("Food Database Error:", repr(e))

        return jsonify({
            'error': 'Food database is temporarily unavailable.'
        }), 503


# =====================================================
# GEMINI AI SUMMARY
# =====================================================

@app.route('/summary', methods=['POST'])
@login_required
def summary():

    if client is None:

        return jsonify({
            'summary': 'Gemini API key is missing.'
        }), 500

    product = request.get_json(silent=True) or {}

    prompt = f"""
    Analyse this food product using only the supplied information.

    Product: {product.get('name')}
    Brand: {product.get('brand')}

    Nutrition per 100g:

    Calories: {product.get('calories')}
    Protein: {product.get('protein')}
    Carbohydrates: {product.get('carbs')}
    Fat: {product.get('fat')}
    Fibre: {product.get('fibre')}
    Sugar: {product.get('sugar')}

    Write a concise summary in simple English.

    Include:
    1. Overall overview
    2. Nutritional advantages
    3. Nutritional disadvantages
    4. Regular consumption

    Use short bullet points.
    Do not invent missing values.
    Avoid medical claims.
    Keep the answer under 150 words.
    """

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            return jsonify({
                'summary': response.text
            })

        except Exception as e:

            print(
                f"Gemini Error (Attempt {attempt + 1}/3):",
                repr(e)
            )

            if attempt < 2:
                time.sleep(2 ** (attempt + 1))

    return jsonify({
        'summary': 'AI analysis is temporarily unavailable.'
    }), 503


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == '__main__':

    app.run(debug=True)