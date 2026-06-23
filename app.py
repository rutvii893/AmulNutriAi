import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from database import get_db, close_db, calculate_nutri_score
from config import SECRET_KEY, ai_client

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Ensure close_db is called
app.teardown_appcontext(close_db)

# --- Authentication Decorators ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Context Processor ---
@app.context_processor
def inject_session():
    return dict(session=session)

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
            
        db = get_db()
        cursor = db.cursor()
        
        try:
            hashed_pw = generate_password_hash(password)
            cursor.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)', (name, email, hashed_pw))
            db.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.rollback()
            flash('Email already exists or an error occurred.', 'error')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        next_url = request.form.get('next')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']
            flash('Logged in successfully.', 'success')
            return redirect(next_url or url_for('index'))
        else:
            flash('Invalid credentials.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/catalog')
def catalog():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE is_active = 1 ORDER BY name ASC')
    products = cursor.fetchall()
    return render_template('catalog.html', products=products)

@app.route('/scanner')
def scanner():
    return render_template('scanner.html')

@app.route('/api/scan', methods=['POST'])
def api_scan():
    data = request.get_json()
    base64_image = data.get('image')
    if not base64_image:
        return jsonify({'error': 'No image provided'}), 400
        
    try:
        response = ai_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "You are a nutrition expert. Look at this Amul dairy product image. Identify: 1) Product name, 2) Product category, 3) Key visible nutrition information. Return ONLY valid JSON with keys: product_name, category, calories, protein, fat, carbs, sugar, sodium, serving_size, confidence_score. No extra text."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
        )
        
        ai_response_text = response.choices[0].message.content.strip()
        if ai_response_text.startswith("```json"):
            ai_response_text = ai_response_text[7:-3]
        elif ai_response_text.startswith("```"):
            ai_response_text = ai_response_text[3:-3]
            
        ai_data = json.loads(ai_response_text)
        
        db = get_db()
        cursor = db.cursor()
        
        product_name = ai_data.get('product_name', '')
        words = product_name.split()
        if words:
            query_conditions = " OR ".join(["name LIKE ?"] * len(words))
            params = [f"%{w}%" for w in words]
            cursor.execute(f"SELECT * FROM products WHERE {query_conditions} LIMIT 1", params)
        else:
            cursor.execute("SELECT * FROM products WHERE name LIKE ? LIMIT 1", (f"%{product_name}%",))
            
        matched_product = cursor.fetchone()
        
        nutrition = {
            'calories': ai_data.get('calories'),
            'protein': ai_data.get('protein'),
            'fat': ai_data.get('fat'),
            'carbs': ai_data.get('carbs'),
            'sugar': ai_data.get('sugar'),
            'sodium': ai_data.get('sodium'),
            'serving_size': ai_data.get('serving_size')
        }
        
        grade = "C"
        
        if matched_product:
            nutrition = {
                'calories': matched_product['calories'],
                'protein': matched_product['protein'],
                'fat': matched_product['fat'],
                'carbs': matched_product['carbs'],
                'sugar': matched_product['sugar'],
                'sodium': matched_product['sodium'],
                'serving_size': matched_product['serving_size']
            }
            grade = matched_product['nutrition_grade']
        else:
            grade = calculate_nutri_score(
                calories=float(nutrition['calories'] or 0),
                fat=float(nutrition['fat'] or 0),
                sugar=float(nutrition['sugar'] or 0),
                sodium=float(nutrition['sodium'] or 0),
                protein=float(nutrition['protein'] or 0)
            )
            
        suitability = {'verdict': 'neutral', 'reason': 'No diet profile found. Log in to get recommendations.'}
        
        if 'user_id' in session:
            cursor.execute('SELECT * FROM health_profiles WHERE user_id = ?', (session['user_id'],))
            profile = cursor.fetchone()
            if profile:
                goal = profile['goal']
                health = profile['health_conditions']
                
                if goal == 'weight_loss' and float(nutrition['calories'] or 0) > 200:
                    suitability = {'verdict': 'avoid', 'reason': 'High calories limit weight loss.'}
                elif goal == 'muscle_gain' and float(nutrition['protein'] or 0) > 5:
                    suitability = {'verdict': 'recommend', 'reason': 'Good protein source.'}
                elif 'diabetes' in health and float(nutrition['sugar'] or 0) > 10:
                    suitability = {'verdict': 'avoid', 'reason': 'High sugar content.'}
                else:
                    suitability = {'verdict': 'recommend', 'reason': 'Fits within dietary goals.'}
                    
        prod_id = matched_product['id'] if matched_product else None
        if prod_id:
            cursor.execute('INSERT INTO product_views (product_id, user_id) VALUES (?, ?)', (prod_id, session.get('user_id')))
        if 'user_id' in session:
            cursor.execute('''
                INSERT INTO scan_history (user_id, product_id, ai_response, nutrition_score)
                VALUES (?, ?, ?, ?)
            ''', (session['user_id'], prod_id, ai_response_text, grade))
        db.commit()

        return jsonify({
            'product_name': product_name,
            'category': ai_data.get('category'),
            'nutrition': nutrition,
            'nutrition_grade': grade,
            'matched_product': dict(matched_product) if matched_product else None,
            'suitability': suitability
        })
        
    except Exception as e:
        print(f"Error during scan: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/diet')
@login_required
def diet():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM health_profiles WHERE user_id = ?', (session['user_id'],))
    profile = cursor.fetchone()
    return render_template('diet.html', profile=profile)

@app.route('/dashboard')
@login_required
def user_dashboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM health_profiles WHERE user_id = ?', (session['user_id'],))
    profile = cursor.fetchone()
    
    # Fetch historical logs
    cursor.execute('SELECT date, weight, calories_consumed, protein_consumed FROM user_progress_logs WHERE user_id = ? ORDER BY date ASC LIMIT 30', (session['user_id'],))
    logs = [dict(row) for row in cursor.fetchall()]
    
    # Calculate daily targets if profile exists
    targets = calculate_dietary_targets(profile)
    
    return render_template('dashboard.html', profile=profile, logs=logs, targets=targets)

@app.route('/api/progress/log', methods=['POST'])
@login_required
def api_progress_log():
    data = request.get_json()
    date_str = data.get('date') # Format YYYY-MM-DD
    weight = data.get('weight')
    calories = data.get('calories')
    protein = data.get('protein')
    
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400
        
    db = get_db()
    cursor = db.cursor()
    
    # Insert or Update
    cursor.execute('''
        INSERT INTO user_progress_logs (user_id, date, weight, calories_consumed, protein_consumed)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, date) DO UPDATE SET 
            weight=excluded.weight, 
            calories_consumed=excluded.calories_consumed, 
            protein_consumed=excluded.protein_consumed,
            logged_at=CURRENT_TIMESTAMP
    ''', (session['user_id'], date_str, weight, calories, protein))
    
    db.commit()
    return jsonify({'status': 'success'})

@app.route('/api/diet/profile', methods=['POST'])
@login_required
def api_diet_profile():
    data = request.get_json()
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT id FROM health_profiles WHERE user_id = ?', (session['user_id'],))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute('''
            UPDATE health_profiles 
            SET age=?, weight=?, height=?, goal=?, diet_type=?, lifestyle=?, health_conditions=?
            WHERE user_id=?
        ''', (data.get('age'), data.get('weight'), data.get('height'), data.get('goal'), 
              data.get('diet_type'), data.get('lifestyle'), data.get('health_conditions'), session['user_id']))
    else:
        cursor.execute('''
            INSERT INTO health_profiles (user_id, age, weight, height, goal, diet_type, lifestyle, health_conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], data.get('age'), data.get('weight'), data.get('height'), data.get('goal'), 
              data.get('diet_type'), data.get('lifestyle'), data.get('health_conditions')))
              
    db.commit()
    return jsonify({'status': 'success'})

@app.route('/api/diet/recommend', methods=['POST'])
@login_required
def api_diet_recommend():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM health_profiles WHERE user_id = ?', (session['user_id'],))
    profile = cursor.fetchone()
    
    if not profile:
        return jsonify({'error': 'Profile not found.'}), 400
        
    cursor.execute('SELECT name, category, calories, protein, fat, sugar, sodium, nutrition_grade FROM products WHERE is_active=1')
    products = cursor.fetchall()
    product_list_text = "\\n".join([f"- {p['name']} ({p['category']}): {p['calories']}kcal, {p['protein']}g protein, {p['sugar']}g sugar, {p['fat']}g fat. Grade: {p['nutrition_grade']}" for p in products])
    
    profile_text = f"Age: {profile['age']}, Weight: {profile['weight']}kg, Height: {profile['height']}cm. Goal: {profile['goal']}, Diet Type: {profile['diet_type']}, Lifestyle: {profile['lifestyle']}, Conditions: {profile['health_conditions']}"

    try:
        response = ai_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{
                "role": "user",
                "content": f"You are a certified nutritionist. The user has the following profile: [{profile_text}]. From this list of Amul products: [{product_list_text}]. Return top 5 recommended products and top 3 products to avoid. For each, give: product_name, verdict (recommend/avoid/neutral), reason (1 sentence), suggested_serving. Return ONLY valid JSON with keys: recommended (list), avoid (list), no extra text."
            }]
        )
        
        ai_response_text = response.choices[0].message.content.strip()
        if ai_response_text.startswith("```json"):
            ai_response_text = ai_response_text[7:-3]
        elif ai_response_text.startswith("```"):
            ai_response_text = ai_response_text[3:-3]
            
        data = json.loads(ai_response_text)
        try:
            for item in data.get('recommended', []):
                p_name = item.get('product_name', '')
                cursor.execute('SELECT id FROM products WHERE name LIKE ? LIMIT 1', (f"%{p_name}%",))
                p_row = cursor.fetchone()
                if p_row:
                    cursor.execute('INSERT INTO product_recommendations (product_id, user_id, type) VALUES (?, ?, ?)', (p_row['id'], session['user_id'], 'recommend'))
            for item in data.get('avoid', []):
                p_name = item.get('product_name', '')
                cursor.execute('SELECT id FROM products WHERE name LIKE ? LIMIT 1', (f"%{p_name}%",))
                p_row = cursor.fetchone()
                if p_row:
                    cursor.execute('INSERT INTO product_recommendations (product_id, user_id, type) VALUES (?, ?, ?)', (p_row['id'], session['user_id'], 'avoid'))
            db.commit()
        except Exception as e_log:
            print(f"Error logging recommendations: {e_log}")
        return jsonify(data)
    except Exception as e:
        print(f"Recommend error: {e}")
        return jsonify({'error': str(e)}), 500

import re

def calculate_dietary_targets(profile):
    """
    Computes custom daily calorie & macronutrient targets using Mifflin-St Jeor formula
    """
    if not profile:
        return {
            'calories': 2000,
            'protein': 100,
            'carbs': 250,
            'fat': 65
        }
    
    weight = float(profile['weight'] or 70)
    height = float(profile['height'] or 170)
    age = int(profile['age'] or 30)
    goal = profile['goal'] or 'maintenance'
    lifestyle = profile['lifestyle'] or 'moderate'
    
    # BMR formula (neutral average)
    bmr = 10 * weight + 6.25 * height - 5 * age - 80
    
    multipliers = {
        'sedentary': 1.2,
        'moderate': 1.375,
        'active': 1.55
    }
    tdee = bmr * multipliers.get(lifestyle, 1.375)
    
    if goal == 'weight_loss':
        target_calories = max(1200, tdee - 500)
        p_pct, c_pct, f_pct = 0.35, 0.35, 0.30
    elif goal == 'muscle_gain':
        target_calories = tdee + 300
        p_pct, c_pct, f_pct = 0.30, 0.40, 0.30
    elif goal == 'diabetes':
        target_calories = tdee - 100
        p_pct, c_pct, f_pct = 0.25, 0.35, 0.40
    else:
        target_calories = tdee
        p_pct, c_pct, f_pct = 0.20, 0.50, 0.30
        
    target_calories = round(target_calories)
    return {
        'calories': target_calories,
        'protein': round((target_calories * p_pct) / 4),
        'carbs': round((target_calories * c_pct) / 4),
        'fat': round((target_calories * f_pct) / 9)
    }

def calculate_plan_daily_totals(plan_data):
    """
    Computes actual macros for each day based on database product entries
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT name, calories, protein, fat, carbs, serving_size FROM products WHERE is_active=1')
    products_map = {p['name']: p for p in cursor.fetchall()}
    
    def extract_number(s):
        if not s:
            return None
        match = re.search(r'([\d.]+)', s)
        return float(match.group(1)) if match else None

    for day in plan_data.get('days', []):
        day_cal = 0.0
        day_prot = 0.0
        day_fat = 0.0
        day_carbs = 0.0
        
        for meal in day.get('meals', {}).values():
            prod_names_str = meal.get('product', '')
            quants_str = meal.get('quantity', '')
            
            prod_list = [x.strip() for x in prod_names_str.split(',')]
            quant_list = [x.strip() for x in quants_str.split(',')]
            
            for i, p_name in enumerate(prod_list):
                matched_p = None
                for db_name, p in products_map.items():
                    if db_name.lower() == p_name.lower() or db_name.lower() in p_name.lower():
                        matched_p = p
                        break
                        
                if matched_p:
                    db_val = extract_number(matched_p['serving_size'])
                    meal_val = None
                    if i < len(quant_list):
                        meal_val = extract_number(quant_list[i])
                        
                    multiplier = 1.0
                    if db_val and meal_val and db_val > 0:
                        multiplier = meal_val / db_val
                        
                    day_cal += (matched_p['calories'] or 0) * multiplier
                    day_prot += (matched_p['protein'] or 0) * multiplier
                    day_fat += (matched_p['fat'] or 0) * multiplier
                    day_carbs += (matched_p['carbs'] or 0) * multiplier
                
        day['totals'] = {
            'calories': round(day_cal),
            'protein': round(day_prot),
            'fat': round(day_fat),
            'carbs': round(day_carbs)
        }

@app.route('/planner')
@login_required
def planner():
    return render_template('planner.html')

@app.route('/api/planner/generate', methods=['POST'])
@login_required
def api_planner_generate():
    data = request.get_json()
    goal = data.get('goal', 'maintenance')
    days = data.get('days', 3)
    restriction = data.get('restriction', 'none')
    
    db = get_db()
    cursor = db.cursor()
    # Fetch minimal product data for the AI to keep prompt small and generation fast
    cursor.execute('SELECT name, category, serving_size FROM products WHERE is_active=1')
    products_for_llm = [dict(p) for p in cursor.fetchall()]
    
    try:
        response = ai_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{
                "role": "user",
                "content": f"You are a dietitian creating a {days}-day Indian meal plan using ONLY Amul dairy products from this list: {json.dumps(products_for_llm)}. Goal: {goal}. Dietary restriction: {restriction}. For each day provide Breakfast, Lunch, Dinner, and Snack using Amul products. Include product name, quantity, and a simple 1-line preparation tip. Return ONLY valid JSON with structure: {{ \"days\": [{{ \"day\": \"Day 1\", \"meals\": {{ \"breakfast\": {{\"product\":\"\", \"quantity\":\"\", \"tip\":\"\"}}, \"lunch\": {{...}}, \"dinner\": {{...}}, \"snack\": {{...}} }} }}] }}. No extra text."
            }]
        )
        
        ai_response_text = response.choices[0].message.content.strip()
        if ai_response_text.startswith("```json"):
            ai_response_text = ai_response_text[7:-3]
        elif ai_response_text.startswith("```"):
            ai_response_text = ai_response_text[3:-3]
            
        plan_data = json.loads(ai_response_text)
        plan_data['goal'] = goal
        plan_data['restriction'] = restriction
        
        # Inject recipes from DB manually so the AI doesn't have to generate them (speeds up by ~5x)
        cursor.execute('SELECT name, recipes FROM products WHERE is_active=1')
        product_recipes = {p['name']: p['recipes'] for p in cursor.fetchall()}
        
        for day in plan_data.get('days', []):
            for meal_key, meal_info in day.get('meals', {}).items():
                prod_name_str = meal_info.get('product', '')
                # Find the first matching recipe
                for p_name, recipe_json in product_recipes.items():
                    if p_name.lower() in prod_name_str.lower() and recipe_json != '[]' and recipe_json is not None:
                        meal_info['recipe'] = recipe_json
                        break
        
        # Calculate targets and daily totals
        cursor.execute('SELECT * FROM health_profiles WHERE user_id = ?', (session['user_id'],))
        profile = cursor.fetchone()
        targets = calculate_dietary_targets(profile)
        plan_data['targets'] = targets
        calculate_plan_daily_totals(plan_data)
        
        cursor.execute('INSERT INTO meal_plans (user_id, plan_json, goal) VALUES (?, ?, ?)',
                       (session['user_id'], json.dumps(plan_data), goal))
        db.commit()
        
        return jsonify(plan_data)
    except Exception as e:
        print(f"Planner error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/planner/latest', methods=['GET'])
@login_required
def api_planner_latest():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT plan_json FROM meal_plans WHERE user_id = ? ORDER BY generated_at DESC LIMIT 1', (session['user_id'],))
    row = cursor.fetchone()
    
    if row and row['plan_json']:
        plan_data = json.loads(row['plan_json'])
        if 'targets' not in plan_data or not plan_data.get('days', [{}])[0].get('totals'):
            cursor.execute('SELECT * FROM health_profiles WHERE user_id = ?', (session['user_id'],))
            profile = cursor.fetchone()
            targets = calculate_dietary_targets(profile)
            plan_data['targets'] = targets
            calculate_plan_daily_totals(plan_data)
            # Save recalculated plan back
            cursor.execute('UPDATE meal_plans SET plan_json = ? WHERE user_id = ? AND plan_json = ?',
                           (json.dumps(plan_data), session['user_id'], row['plan_json']))
            db.commit()
        return jsonify(plan_data)
    return jsonify({})

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()
    
    stats = {}
    cursor.execute('SELECT COUNT(*) as c FROM users')
    stats['users'] = cursor.fetchone()['c']
    cursor.execute('SELECT COUNT(*) as c FROM products WHERE is_active=1')
    stats['products'] = cursor.fetchone()['c']
    cursor.execute('SELECT COUNT(*) as c FROM scan_history')
    stats['scans'] = cursor.fetchone()['c']
    cursor.execute('SELECT COUNT(*) as c FROM meal_plans')
    stats['meal_plans'] = cursor.fetchone()['c']
    
    # Query views analytics
    cursor.execute('''
        SELECT p.name, COUNT(pv.id) as views 
        FROM products p
        LEFT JOIN product_views pv ON p.id = pv.product_id
        GROUP BY p.id
        ORDER BY views DESC
        LIMIT 5
    ''')
    most_viewed = [dict(row) for row in cursor.fetchall()]

    # Query recommendations analytics
    cursor.execute('''
        SELECT p.name, COUNT(pr.id) as recs 
        FROM products p
        JOIN product_recommendations pr ON p.id = pr.product_id
        WHERE pr.type = 'recommend'
        GROUP BY p.id
        ORDER BY recs DESC
        LIMIT 5
    ''')
    most_recommended = [dict(row) for row in cursor.fetchall()]

    # Query user goals
    cursor.execute('''
        SELECT goal, COUNT(*) as count 
        FROM health_profiles 
        GROUP BY goal
    ''')
    goals_data = [dict(row) for row in cursor.fetchall()]
    
    return render_template('admin/dashboard.html', stats=stats, most_viewed=most_viewed, most_recommended=most_recommended, goals_data=goals_data)

@app.route('/admin/products')
@admin_required
def admin_products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products ORDER BY id DESC')
    products = cursor.fetchall()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['POST'])
@admin_required
def admin_product_add():
    db = get_db()
    cursor = db.cursor()
    
    name = request.form['name']
    category = request.form['category']
    image_url = request.form['image_url'] or '/static/images/products/placeholder.png'
    calories = float(request.form['calories'])
    protein = float(request.form['protein'])
    fat = float(request.form['fat'])
    carbs = float(request.form['carbs'])
    sugar = float(request.form['sugar'])
    sodium = float(request.form['sodium'])
    serving_size = request.form['serving_size']
    description = request.form['description']
    recipes = request.form.get('recipes', '[]')
    
    grade = calculate_nutri_score(calories, fat, sugar, sodium, protein)
    
    cursor.execute('''
        INSERT INTO products (name, category, image_url, calories, protein, fat, carbs, sugar, sodium, serving_size, nutrition_grade, description, recipes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, category, image_url, calories, protein, fat, carbs, sugar, sodium, serving_size, grade, description, recipes))
    db.commit()
    flash('Product added successfully.', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/edit/<int:id>', methods=['POST'])
@admin_required
def admin_product_edit(id):
    db = get_db()
    cursor = db.cursor()
    
    name = request.form['name']
    category = request.form['category']
    image_url = request.form['image_url'] or '/static/images/products/placeholder.png'
    calories = float(request.form['calories'])
    protein = float(request.form['protein'])
    fat = float(request.form['fat'])
    carbs = float(request.form['carbs'])
    sugar = float(request.form['sugar'])
    sodium = float(request.form['sodium'])
    serving_size = request.form['serving_size']
    description = request.form['description']
    recipes = request.form.get('recipes', '[]')
    
    grade = calculate_nutri_score(calories, fat, sugar, sodium, protein)
    
    cursor.execute('''
        UPDATE products 
        SET name=?, category=?, image_url=?, calories=?, protein=?, fat=?, carbs=?, sugar=?, sodium=?, serving_size=?, nutrition_grade=?, description=?, recipes=?
        WHERE id=?
    ''', (name, category, image_url, calories, protein, fat, carbs, sugar, sodium, serving_size, grade, description, recipes, id))
    db.commit()
    flash('Product updated successfully.', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
@admin_required
def admin_product_delete(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM products WHERE id=?', (id,))
    db.commit()
    flash('Product deleted.', 'success')
    return redirect(url_for('admin_products'))

@app.route('/api/products/<int:product_id>/view', methods=['POST'])
def api_product_view(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO product_views (product_id, user_id) VALUES (?, ?)', (product_id, session.get('user_id')))
    db.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
