# 🎓 Student Expense Manager – Backend API

AI-Powered Student Expense Management & Budget Recommendation System.

Built with **Flask**, **SQLAlchemy**, **Flask-Migrate**, **JWT Auth**, and **scikit-learn**.

---

## 📁 Project Structure

```
backend/
├── app.py                  # Flask application factory
├── config.py               # Configuration (env vars, DB, JWT)
├── models.py               # SQLAlchemy models
├── run.py                  # Dev server entry point
├── seed_db.py              # Database seeding script
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── routes/
│   ├── auth.py             # Authentication (register, login, refresh, me)
│   ├── profile.py          # User profile (GET/PUT)
│   ├── expenses.py         # Expense CRUD
│   ├── categories.py       # Categories listing
│   ├── budgets.py          # Budget CRUD
│   ├── analytics.py        # Spending analytics & financial health
│   ├── stores.py           # Nearby store comparison
│   ├── recommendations.py  # AI saving recommendations
│   └── parent.py           # Parent-student linking & view
├── utils/
│   ├── decorators.py       # @student_required, @parent_required
│   └── categorizer.py      # ML-powered expense categoriser
└── ml/
    ├── train.py             # Model training script
    ├── predict.py           # Prediction module
    └── models/              # Saved model artifacts (auto-created)
```

---

## 🚀 Quick Start

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialise Database (Flask-Migrate)

```bash
flask --app app:create_app db init
flask --app app:create_app db migrate -m "Initial migration"
flask --app app:create_app db upgrade
```

### 4. Seed the Database

```bash
python seed_db.py
```

This creates:
- **Student**: `student@test.com` / `Test@123`
- **Parent**: `parent@test.com` / `Test@123`
- 20 realistic expenses, 8 category budgets, 15 stores around Noida Sector 62

### 5. (Optional) Train ML Category Classifier

```bash
python ml/train.py
```

### 6. Run the Server

```bash
python run.py
```

The API will be available at **http://localhost:5000**

---

## 🔑 API Endpoints

### Authentication

| Method | Endpoint              | Description           | Auth |
|--------|-----------------------|-----------------------|------|
| POST   | `/api/auth/register`  | Register new user     | ❌   |
| POST   | `/api/auth/login`     | Login & get tokens    | ❌   |
| POST   | `/api/auth/refresh`   | Refresh access token  | 🔄   |
| GET    | `/api/auth/me`        | Get current user      | ✅   |

### Profile

| Method | Endpoint       | Description          | Auth |
|--------|----------------|----------------------|------|
| GET    | `/api/profile` | Get user profile     | ✅   |
| PUT    | `/api/profile` | Update profile       | ✅   |

### Expenses

| Method | Endpoint              | Description                 | Auth |
|--------|-----------------------|-----------------------------|------|
| POST   | `/api/expenses`       | Create expense (auto-cat)   | ✅   |
| GET    | `/api/expenses`       | List with filters           | ✅   |
| GET    | `/api/expenses/<id>`  | Get single expense          | ✅   |
| PUT    | `/api/expenses/<id>`  | Update expense              | ✅   |
| DELETE | `/api/expenses/<id>`  | Delete expense              | ✅   |

### Categories

| Method | Endpoint           | Description        | Auth |
|--------|--------------------|--------------------|------|
| GET    | `/api/categories`  | List all categories| ✅   |

### Budgets

| Method | Endpoint             | Description         | Auth |
|--------|----------------------|---------------------|------|
| GET    | `/api/budgets`       | List budgets        | ✅   |
| POST   | `/api/budgets`       | Create budget       | ✅   |
| PUT    | `/api/budgets/<id>`  | Update budget       | ✅   |
| DELETE | `/api/budgets/<id>`  | Delete budget       | ✅   |

### Analytics

| Method | Endpoint                                | Description               | Auth |
|--------|-----------------------------------------|---------------------------|------|
| GET    | `/api/analytics/spending-by-category`   | Category breakdown        | ✅   |
| GET    | `/api/analytics/spending-over-time`     | Monthly totals            | ✅   |
| GET    | `/api/analytics/budget-vs-actual`       | Budget vs actual compare  | ✅   |
| GET    | `/api/analytics/financial-health-score` | Health score (0-100)      | ✅   |

### Stores

| Method | Endpoint             | Description                | Auth |
|--------|----------------------|----------------------------|------|
| GET    | `/api/stores/nearby` | Nearby stores by distance  | ✅   |

### Recommendations

| Method | Endpoint                | Description           | Auth |
|--------|-------------------------|-----------------------|------|
| GET    | `/api/recommendations`  | AI saving tips        | ✅   |

### Parent

| Method | Endpoint                                       | Description              | Auth   |
|--------|------------------------------------------------|--------------------------|--------|
| POST   | `/api/parent/link`                             | Link student by email    | 🔒 Parent |
| GET    | `/api/parent/student/<student_id>/expenses`    | View student expenses    | 🔒 Parent |

---

## 🧪 Testing with cURL

### Register
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test@123","name":"Test User","role":"student"}'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test@123"}'
```

### Create Expense (with auto-categorisation)
```bash
curl -X POST http://localhost:5000/api/expenses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"amount":250,"description":"Lunch at canteen","store_name":"College Mess"}'
```

### Get Analytics
```bash
curl http://localhost:5000/api/analytics/spending-by-category?month=2026-04 \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## ⚙️ Configuration

Edit `.env` to customise:

```env
# Switch to PostgreSQL for production
DATABASE_URI=postgresql://user:password@localhost:5432/student_expense_db

# Change JWT secret
JWT_SECRET_KEY=your-secure-random-string

# Add AI API key for future chatbot
AI_API_KEY=your-api-key
```

---

## 📝 License

MIT – Built for academic use.
