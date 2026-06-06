# 🥛 AmulNutriAI: AI-Powered Dietitian & Packaging Scanner

AmulNutriAI is a premium, full-stack web application designed to help users make healthier dietary choices by integrating regional dairy nutrition metrics with AI-driven meal planning. The app evaluates, recommends, and customizes dietary guides utilizing authentic Amul dairy products.

---

## ✨ Key Features

*   📷 **AI Packaging Vision Scanner**: Upload photos of Amul products to instantly extract nutritional facts, assign an automated **Nutri-Score (A-E)**, and receive suitability badges (**Recommend / Avoid / Neutral**) based on user goals.
*   🥗 **Dynamic Weekly Meal Planner**: Generates custom 3-day or 7-day Indian meal grids, calculating real-time daily macro totals (Calories, Protein, Carbs, Fats) using the **Mifflin-St Jeor formula**.
*   🛒 **Automatic Shopping List Aggregator**: Scans generated meal plans to sum up the required quantities of Amul ingredients into a convenient grocery checkout checklist.
*   🩺 **Personalized Diet Profile Advisor**: Analyzes age, weight, physical activity, and health conditions (e.g. diabetes) to curate a targeted "Top 5 Recommended / Top 3 Avoid" Amul dairy lists.
*   📈 **Real-Time Admin Dashboard**: Provides visual analytics charts (using `Chart.js`) illustrating product views, top AI recommendations, user goal distributions, and full catalog CRUD tools.
*   🔒 **Secure Authentication**: Built-in user registration, login gates, session management, and admin access roles.

---

## 🛠️ Technology Stack

*   **Backend**: Python, Flask, SQLite3, OpenAI SDK (pointing to Google Gemini API)
*   **Frontend**: Pure HTML5, Vanilla JavaScript, Custom Responsive CSS (No external frameworks like Tailwind)
*   **Visualizations**: Chart.js for data dashboards
*   **Styling**: Premium custom color scheme (Amul Red `#E31E24`), interactive card hover transitions, and keyframe-animated progress loaders.

---

## 📂 Project Structure

```text
AmulNutriAi/
│
├── config.py              # Configuration & API client initialization
├── database.py            # SQLite database helper & Nutri-Score calculation
├── app.py                 # Flask app routes & main backend engine
├── requirements.txt       # Project dependencies
├── render.yaml            # Cloud deployment config
│
├── data/
│   └── seed_products.py   # Seeding script with 20 Amul products & dummy analytics
│
├── static/
│   ├── css/
│   │   └── style.css      # Premium custom CSS styling sheet
│   └── js/
│       ├── main.js        # Global UI helpers & notifications
│       ├── scanner.js     # Vision scanner client handler
│       ├── diet.js        # Profile recommendation handler
│       └── planner.js     # Weekly planner generator & macro tracker
│
└── templates/
    ├── base.html          # Shell layout & navbar/footer
    ├── index.html         # Portal home page
    ├── login.html         # User login screen
    ├── register.html      # Account registration screen
    ├── catalog.html       # Product catalog & Nutri-score overview
    ├── scanner.html       # Packaging image uploader
    ├── diet.html          # Physical profile setup wizard
    ├── planner.html       # Weekly plan macro grid & recipe modal
    └── admin/
        ├── dashboard.html # Admin analytics dashboard
        └── products.html  # Catalog database CRUD panel
```

---

## 🚀 Setup & Local Execution

### 1. Clone the repository
```bash
git clone https://github.com/rutvii893/AmulNutriAi.git
cd AmulNutriAi
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Create a `.env` file in the root directory and add your Google Gemini API key:
```env
OPENROUTER_API_KEY=your_gemini_api_key_here
SECRET_KEY=generate_a_random_flask_secret_key
```

### 4. Seed Database
Initialize tables and populate 20 products alongside realistic dummy analytics:
```bash
python data/seed_products.py
```

### 5. Launch the Web Server
```bash
python app.py
```
Open your browser and navigate to `http://localhost:5000`.

*   **Test User Account**: `john@example.com` / `password123`
*   **Admin Dashboard Account**: `admin@amulnutri.ai` / `adminpassword`
