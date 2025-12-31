from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text
from jose import JWTError, jwt
import models
from database import engine, get_db

# Create tables
models.Base.metadata.create_all(bind=engine)

from pydantic import BaseModel
import pika
import json

app = FastAPI()

# RabbitMQ Connection Helper
def get_rabbitmq_channel():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='money_transfer', durable=True)
    return channel

class TransferRequest(BaseModel):
    to_account: str
    amount: float


# SHARED SECRET from Auth Service
SECRET_KEY = "vulnerable_bank_secret_123"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost/auth/token") # URL doesn't key here as we just parse

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    # Seed CEO Account if not exists
    ceo_account = db.query(models.Account).filter(models.Account.user_id == 99).first()
    if not ceo_account:
        print("Seeding CEO Account...")
        ceo_account = models.Account(user_id=99, account_number="CEO-001", balance=1000000.0)
        db.add(ceo_account)
        db.commit()
        db.refresh(ceo_account)
        
        # Seed Transaction
        txn = models.Transaction(account_id=ceo_account.id, amount=1000000.0, description="Confidential Bonus Payment")
        db.add(txn)
        db.commit()

# VULNERABILITY 1: IDOR in Balance Check
@app.get("/balance/{account_id}")
def get_balance(account_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # FLAW: No check if account_id belongs to current_user['sub'] (or implicit ID)
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account_number": account.account_number, "balance": account.balance}

# VULNERABILITY 2: SQL Injection in Search
@app.get("/transactions/search")
def search_transactions(q: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # FLAW: Using f-string for query construction
    query_str = f"SELECT * FROM transactions WHERE description LIKE '%{q}%'"
    print(f"Executing Query: {query_str}")
    
    try:
        # Use execute to run raw SQL
        result = db.execute(text(query_str))
        # Fetch results mapped to dict
        rows = result.fetchall()
        return [{"id": row[0], "amount": row[2], "description": row[3], "timestamp": row[4]} for row in rows]
        # Note: mapping indices depends on DB schema column order. 
        # Safer for display might be row._mapping if available or implicit mapping, 
        # but for raw SQL we often get tuples. Let's try to be robust or simple.
        # SQLAlchemy 1.4/2.0 text() results usually behave like named tuples.
    except Exception as e:
        return {"error": str(e), "query": query_str}

@app.post("/transfer", status_code=202)
def transfer_funds(request: TransferRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # VULNERABILITY: No balance check here. Just publish.
    # We need the sender's account ID. For simplicity, let's assume 1 User = 1 Account and look it up.
    # In a real app we'd get this from the user context better.
    # Let's find the account associated with the current user ID (from token sub).
    # Note: 'sub' is username in our Auth service. Models has user_id (int).
    # Phase 2 Auth puts username in 'sub'. Ledger Models use user_id.
    # We need a way to map username -> user_id OR just lookup account by username if we stored it?
    # BUT Phase 3 Models only have user_id (int).
    # Let's simple hack: Assume the token 'sub' IS the username, and we don't have a direct map here 
    # unless we call Auth service (microservice complexity).
    # For this CTF, let's assume the Auth service put the 'user_id' in the token?? 
    # Phase 2 MAIN.PY: access_token = create_access_token(data={"sub": user.username, "admin": user.is_admin})
    # It does NOT put user_id.
    
    # Workaround: We will lookup the account assuming the "username" matches "account_number" for simpler logic? 
    # No, account_number is "CEO-001".
    
    # Let's just pass the username in the message and let the worker resolve it?
    # The worker has access to the SAME DB. The worker can verify funds.
    # Models.Account has user_id. We don't have username in Account table.
    
    # OK, CRITICAL FIX: The Ledger Service Models needs to store username OR we trust the user to send their account_id?
    # Let's allow the user to send "from_account" in the body too? No, that's insecurity (Impressioning).
    # BUT we are building a vulnerable app.
    # Let's make it easy: The Token has 'sub' (username).
    # We will assume for this simplistic CTF that we can just pass the 'username' to the worker.
    # The worker will need to resolve Username -> Account.
    # But Account table doesn't have username.
    # Let's Add 'username' to the Account model? Or just be lazy and pass 'user_id' in the token?
    # I should have added user_id to the token in Phase 2.
    
    # RE-DECISION: I will assume the user has an account with ID corresponding to their User ID for simplicity,
    # OR i will just accept "from_account" in the body and verify it belongs to them?
    # That was the IDOR vulnerability earlier! verify_balance didn't check ownership.
    # Let's abuse that. Let's just send the "from_account" in the request.
    # If we want to prevent spoofing, we should check ownership.
    # Message: {"from_user": current_user["sub"], "to_account": ..., "amount": ...}
    
    message = {
        "sender_username": current_user["sub"], 
        "to_account": request.to_account,
        "amount": request.amount
    }
    
    try:
        channel = get_rabbitmq_channel()
        channel.basic_publish(
            exchange='',
            routing_key='money_transfer',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq')) # Re-open to close securely or use channel object?
        # get_rabbitmq_channel implementation opens new one every time. inefficient but fine for CTF.
        return {"status": "Transaction Queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Ledger Service Ready"}
