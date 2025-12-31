from database import engine, SessionLocal
from models import Account, Transaction
from sqlalchemy import text

db = SessionLocal()
print("Inspecting Database...")

print("--- Accounts ---")
accounts = db.query(Account).all()
for acc in accounts:
    print(f"ID: {acc.id}, Num: {acc.account_number}, Bal: {acc.balance}, UserID: {acc.user_id}")

print("--- Transactions ---")
txns = db.query(Transaction).all()
for t in txns:
    print(f"ID: {t.id}, Desc: {t.description}")

print("--- Tables ---")
with engine.connect() as conn:
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
    for row in result:
        print(row)
db.close()
