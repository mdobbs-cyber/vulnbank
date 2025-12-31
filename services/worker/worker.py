import pika
import json
import time
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database Setup (Direct connection to bank_db)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db/bank_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    return SessionLocal()

def process_transfer(ch, method, properties, body):
    data = json.loads(body)
    sender_username = data.get("sender_username")
    to_account_num = data.get("to_account")
    amount = float(data.get("amount"))

    print(f" [x] Processing transfer: {sender_username} -> {to_account_num} (${amount})")

    db = get_db()
    try:
        # 1. Resolve Sender Account (Weakness: Assuming username maps to user_id in Auth... 
        # but we don't have access to Auth DB easily here OR we share the DB?
        # We share 'bank_db'. So we can join tables or just look up.
        # Wait, 'user_id' in Account table is integer. 'sender_username' is string.
        # We need to look up the User ID from the username.
        # Is the User table in the same DB? Yes, 'bank_db'. 
        # Models are in 'auth' and 'ledger' folders but tables are in same DB.
        
        # Raw SQL is easiest to cross-reference since we don't share Model code easily across services in this scaffold
        
        # Get Sender Account
        sender_query = text("SELECT a.id, a.balance FROM accounts a JOIN users u ON a.user_id = u.id WHERE u.username = :username")
        sender = db.execute(sender_query, {"username": sender_username}).fetchone()
        
        if not sender:
            print(" [!] Sender not found")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        sender_id, sender_balance = sender
        
        # Get Receiver Account
        receiver_query = text("SELECT id, balance FROM accounts WHERE account_number = :acc_num")
        receiver = db.execute(receiver_query, {"acc_num": to_account_num}).fetchone()
        
        if not receiver:
            print(" [!] Receiver not found")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
            
        receiver_id, receiver_balance = receiver

        # 2. Check Balance
        if sender_balance >= amount:
            print(f" [v] Balance sufficient ({sender_balance} >= {amount})... Sleeping for Race Condition...")
            
            # THE VULNERABILITY: Time-of-Check to Time-of-Use
            time.sleep(5) 
            
            # 3. Update Balances
            # Re-read? NO. That would fix it. We use the old values or simple update statements.
            # UPDATE accounts SET balance = balance - amount WHERE id = ...
            # Using atomic updates (SET balance = balance - 100) is actually SAFER against overwrite races,
            # BUT if we checked balance 5 seconds ago, the condition "balance >= amount" might no longer be true
            # if another worker ALREADY subtracted it.
            # So even with atomic updates, we double spend because we allowed the transaction to proceed based on stale check.
            
            db.execute(text("UPDATE accounts SET balance = balance - :amount WHERE id = :id"), {"amount": amount, "id": sender_id})
            db.execute(text("UPDATE accounts SET balance = balance + :amount WHERE id = :id"), {"amount": amount, "id": receiver_id})
            
            # Create Transaction Record
            db.execute(text("INSERT INTO transactions (account_id, amount, description, timestamp) VALUES (:aid, :amt, :desc, NOW())"), 
                       {"aid": sender_id, "amt": -amount, "desc": f"Transfer to {to_account_num}"})
            db.execute(text("INSERT INTO transactions (account_id, amount, description, timestamp) VALUES (:aid, :amt, :desc, NOW())"), 
                       {"aid": receiver_id, "amt": amount, "desc": f"Transfer from {sender_username}"})

            db.commit()
            print(" [x] Transfer Complete")
        else:
            print(f" [!] Insufficient funds: {sender_balance} < {amount}")
            
    except Exception as e:
        print(f" [!] Error: {e}")
        db.rollback()
    finally:
        db.close()
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    # Wait for RabbitMQ
    # Wait for RabbitMQ with retry
    connection = None
    while connection is None:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not yet ready, retrying in 5 seconds...")
            time.sleep(5)
    channel = connection.channel()
    channel.queue_declare(queue='money_transfer', durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='money_transfer', on_message_callback=process_transfer)

    print(' [*] Worker Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    main()
