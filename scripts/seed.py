"""
Seed the fresh V1 database with:
  1. The nine product categories from the Tubura plan (trilingual).
  2. The first superadmin account, taken from the ADMIN_USERNAME and
     ADMIN_PASSWORD environment variables you already have set
     (in .env locally, and in Railway's Variables tab in production).

No demo products, no demo retailers, no trainings — real data will be
entered by administrators through the dashboard.

Run with:  python scripts/seed.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.context import CryptContext

from app.db.session import SessionLocal
from app.models import Category, Administrator

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

CATEGORIES = [
    dict(name_en="Seeds",                name_rw="Imbuto",                        name_fr="Semences",                 sort_order=1),
    dict(name_en="Fertilizers",          name_rw="Ifumbire",                      name_fr="Engrais",                  sort_order=2),
    dict(name_en="Pesticides",           name_rw="Imiti yica udukoko",            name_fr="Pesticides",               sort_order=3),
    dict(name_en="Farm Equipment",       name_rw="Ibikoresho by'ubuhinzi",        name_fr="Équipement agricole",      sort_order=4),
    dict(name_en="Gardening Supplies",   name_rw="Ibikoresho byo mu busitani",    name_fr="Fournitures de jardinage", sort_order=5),
    dict(name_en="Animal Feed",          name_rw="Ibiribwa by'amatungo",          name_fr="Aliments pour animaux",    sort_order=6),
    dict(name_en="Veterinary Products",  name_rw="Imiti y'amatungo",              name_fr="Produits vétérinaires",    sort_order=7),
    dict(name_en="Irrigation Equipment", name_rw="Ibikoresho byo kuhira",         name_fr="Équipement d'irrigation",  sort_order=8),
    dict(name_en="Other Products",       name_rw="Ibindi bicuruzwa",              name_fr="Autres produits",          sort_order=9),
]


def seed():
    db = SessionLocal()
    try:
        # ── Categories ────────────────────────────────────────────────────
        if db.query(Category).count() == 0:
            for c in CATEGORIES:
                db.add(Category(**c))
            print(f"Seeded {len(CATEGORIES)} categories")
        else:
            print("Categories already exist, skipping")

        # ── First superadmin ─────────────────────────────────────────────
        username = os.getenv("ADMIN_USERNAME")
        password = os.getenv("ADMIN_PASSWORD")
        if not username or not password:
            print("WARNING: ADMIN_USERNAME / ADMIN_PASSWORD not set — "
                  "no admin account created.")
        elif db.query(Administrator).filter_by(username=username).first():
            print(f"Admin '{username}' already exists, skipping")
        else:
            db.add(Administrator(
                username=username,
                password_hash=pwd.hash(password),
                role="superadmin",
                permissions=["products", "categories", "retailers", "stock",
                             "orders", "preorders", "customers",
                             "notifications", "support", "admins"],
            ))
            print(f"Created superadmin '{username}'")

        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
