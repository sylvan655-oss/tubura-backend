# Tubura Backend — FastAPI

Agricultural marketplace API for One Acre Fund Rwanda.

## Quick Start

### 1. Clone and set up environment
```bash
cd tubura-backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your DATABASE_URL, SECRET_KEY, AT_API_KEY, etc.
```

### 3. Set up PostgreSQL
```bash
# Create the database (run in psql or pgAdmin)
CREATE USER tubura_user WITH PASSWORD 'yourpassword';
CREATE DATABASE tubura_db OWNER tubura_user;
```

### 4. Run migrations
```bash
alembic upgrade head
```

### 5. Seed the database
```bash
python scripts/seed.py
```

### 6. Start the server
```bash
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** to explore the API in Swagger UI.

### Admin dashboard

Open **http://localhost:8000/admin** and log in with the `ADMIN_USERNAME` /
`ADMIN_PASSWORD` you set in `.env`. You'll see a sidebar of every table —
Farmers, Orders, Products, Retailers, Trainings, Delivery Locations,
Notifications, Support Requests — each with search, filters, sorting,
pagination, and CSV export, generated directly from the database models
(no separate frontend to build or deploy).

Sensitive fields (like password hashes) are deliberately excluded from
every list, search, and export — they're never rendered in the browser.

**Before deploying to production**, change `ADMIN_PASSWORD` in your `.env`
(or hosting provider's environment variables) to something only you know —
the default in `.env.example` is not safe to ship.

---

## Project Structure

```
tubura-backend/
├── app/
│   ├── main.py              # FastAPI app + CORS + routers
│   ├── api/routes/
│   │   ├── auth.py          # POST /api/auth/request-otp, verify-otp, signup, GET /me
│   │   ├── products.py      # GET /api/products
│   │   ├── retailers.py     # GET /api/retailers, /api/retailers/nearby
│   │   ├── orders.py        # POST /api/orders, GET /api/orders, webhooks
│   │   └── trainings.py     # GET /api/trainings, POST /api/training-requests
│   ├── core/
│   │   ├── config.py        # All settings from .env
│   │   └── security.py      # OTP generation, JWT, password hashing
│   ├── db/
│   │   └── session.py       # SQLAlchemy engine, session, Base
│   ├── models/
│   │   ├── farmer.py        # Farmer account
│   │   ├── otp.py           # OTP codes
│   │   ├── product.py       # Products (trilingual columns)
│   │   ├── retailer.py      # Retailers with GPS coords
│   │   ├── order.py         # Orders + OrderItems
│   │   └── training.py      # Trainings + Bookings
│   ├── schemas/
│   │   ├── auth.py          # Pydantic request/response types for auth
│   │   ├── order.py         # Order schemas
│   │   └── training.py      # Training schemas
│   └── services/
│       ├── sms.py           # Africa's Talking SMS (OTP + order updates)
│       └── payment.py       # MTN MoMo + Airtel Money Collections API
├── alembic/                 # Database migrations
├── scripts/
│   └── seed.py              # Populate DB with products, trainings, retailers
├── .env.example             # All required environment variables
├── requirements.txt
└── README.md
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/request-otp` | — | Send OTP SMS to phone |
| POST | `/api/auth/verify-otp` | — | Verify OTP, get JWT token |
| POST | `/api/auth/signup` | — | Create farmer account |
| GET  | `/api/auth/me` | JWT | Get current farmer profile |
| GET  | `/api/products?lang=en` | — | List all products |
| GET  | `/api/products/{id}?lang=en` | — | Single product |
| GET  | `/api/retailers` | — | List all retailers |
| GET  | `/api/retailers/nearby?lat=X&lng=Y` | — | Retailers sorted by GPS distance |
| POST | `/api/orders` | — | Create an order (triggers MoMo push) |
| GET  | `/api/orders` | JWT | Farmer's order history |
| GET  | `/api/orders/{ref}` | — | Single order by ref |
| POST | `/api/orders/{ref}/cancel` | JWT | Cancel an order |
| GET  | `/api/trainings?lang=en` | — | List all trainings |
| POST | `/api/training-requests` | — | Book a training session |
| POST | `/api/payments/mtn/callback` | — | MTN MoMo payment webhook |
| POST | `/api/payments/airtel/callback` | — | Airtel Money payment webhook |

---

## Deployment (Railway — fastest option)

1. Push this folder to a GitHub repository
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add a PostgreSQL plugin in Railway
4. Copy the `DATABASE_URL` Railway gives you into your environment variables
5. Add all other env vars (AT_API_KEY, SECRET_KEY, MTN keys, etc.)
6. Railway auto-detects Python and runs `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Add a `Procfile` for Railway:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Your API will be live at `https://tubura-backend.up.railway.app` in minutes.

---

## Connecting the Frontend

In `tubura_i18n.html`, change:
```javascript
const BASE = '';  // currently uses fallback data
```
to:
```javascript
const BASE = 'https://your-api-url.railway.app';
```

The frontend already handles API calls and falls back to local data if the API is unreachable.
