"""
One-off cleanup: pre-orders created before the "Received" tab was removed
still carry status='received'. This moves them to 'under_review' so they
appear in the right admin tab. Safe to run more than once.

Run from C:\\tubura\\tubura-backend with the venv active:
    python scripts/fix_preorder_status.py
"""
from app.db.session import SessionLocal
from app.models import PreOrder

db = SessionLocal()
rows = db.query(PreOrder).filter(PreOrder.status == "received").all()
for p in rows:
    p.status = "under_review"
db.commit()
print(f"moved {len(rows)} pre-order(s) from 'received' to 'under_review'")

# Summary of what's now in the table
from collections import Counter
counts = Counter(p.status for p in db.query(PreOrder).all())
for status, n in counts.items():
    print(f"  {status}: {n}")
db.close()
