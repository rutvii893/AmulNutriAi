import sqlite3
import os
from flask import g
from config import DATABASE, INSTANCE_DIR

def calculate_nutri_score(calories, fat, sugar, sodium, protein):
    """
    Computes Nutri-Score grade A–E for a product.
    - Negative points: calories, sugar, fat, sodium (higher = more points)
    - Positive points: protein (higher = fewer points)
    - Total score = Negatives - Positives
    - Total score -> A (0–2), B (3–10), C (11–18), D (19–25), E (26+)
    """
    # Calories (kcal): 1 pt per 80 kcal (max 10)
    cal_pts = min(10, int(calories / 80)) if calories else 0
    # Sugar (g): 1 pt per 4.5g (max 10)
    sugar_pts = min(10, int(sugar / 4.5)) if sugar else 0
    # Fat (g): 1 pt per 3g (max 10)
    fat_pts = min(10, int(fat / 3)) if fat else 0
    # Sodium (mg): 1 pt per 90mg (max 10)
    sodium_pts = min(10, int(sodium / 90)) if sodium else 0

    neg_points = cal_pts + sugar_pts + fat_pts + sodium_pts

    # Protein (g): 1 pt per 1.6g (max 5)
    protein_pts = min(5, int(protein / 1.6)) if protein else 0

    total_score = neg_points - protein_pts

    if total_score <= 2:
        return 'A'
    elif total_score <= 10:
        return 'B'
    elif total_score <= 18:
        return 'C'
    elif total_score <= 25:
        return 'D'
    else:
        return 'E'

def get_db():
    """
    Opens a unique connection to the SQLite database per request context.
    """
    db = getattr(g, '_database', None)
    if db is None:
        # Ensure the instance directory exists before connecting
        os.makedirs(INSTANCE_DIR, exist_ok=True)
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def get_db_direct():
    """
    Gets a connection directly (outside Flask request context, e.g., for seeding).
    """
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def close_db(exception=None):
    """
    Closes database connection at the end of a request context.
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """
    Creates tables if they do not exist.
    """
    conn = get_db_direct()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            image_url TEXT,
            calories REAL,
            protein REAL,
            fat REAL,
            carbs REAL,
            sugar REAL,
            sodium REAL,
            serving_size TEXT,
            nutrition_grade TEXT,
            description TEXT,
            recipes TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # Create health_profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            age INTEGER,
            weight REAL,
            height REAL,
            goal TEXT,
            diet_type TEXT,
            lifestyle TEXT,
            health_conditions TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create scan_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            image_path TEXT,
            ai_response TEXT,
            nutrition_score TEXT,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Create meal_plans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meal_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan_json TEXT,
            goal TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create product_views table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            user_id INTEGER,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create user_progress_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date DATE,
            weight REAL,
            calories_consumed INTEGER,
            protein_consumed INTEGER,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, date)
        )
    ''')

    # Create product_recommendations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            user_id INTEGER,
            type TEXT,
            recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
