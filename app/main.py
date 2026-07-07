import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin

from app.core.config import settings
from app.db.session import engine
from app.admin.auth import get_admin_auth
from app.admin.views import ALL_ADMIN_VIEWS
from app.api.routes import (
    auth,
    products,
    retailers,
    orders,
    trainings,
    delivery_locations,
    notifications,
    support,
)

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Tubura API",
    description="Agricultural marketplace backend for One Acre Fund Rwanda",
    version="1.0.0",
)

origins = [settings.FRONTEND_ORIGIN] if settings.FRONTEND_ORIGIN else ["*"]
if settings.APP_ENV != "production":
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(retailers.router)
app.include_router(orders.router)
app.include_router(trainings.router)
app.include_router(delivery_locations.router)
app.include_router(notifications.router)
app.include_router(support.router)

# ── Admin dashboard: browse to /admin, log in, see all your data as tables ──
admin = Admin(app, engine, authentication_backend=get_admin_auth(), title="Tubura Admin")
for view in ALL_ADMIN_VIEWS:
    admin.add_view(view)


@app.get("/")
def root():
    return {"name": "Tubura API", "status": "ok", "env": settings.APP_ENV}


@app.get("/health")
def health():
    return {"status": "healthy"}
