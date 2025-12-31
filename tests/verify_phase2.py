import urllib.request
import json
import urllib.parse
import sys

BASE_URL = "http://localhost:80"

def test_registration():
    print("Testing Registration (Mass Assignment)...")
    url = f"{BASE_URL}/auth/register"
    payload = {
        "username": "hacker_std_lib",
        "password": "123",
        "is_admin": True
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            print(f"Status: {status}")
            print(f"Response: {body}")
            resp_json = json.loads(body)
            if status == 200 and resp_json.get("is_admin") is True:
                print("[PASS] Admin user created.")
            else:
                print("[FAIL] Could not create admin user.")
    except urllib.error.HTTPError as e:
        print(f"[FAIL] HTTP Error: {e.code} - {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"[FAIL] Check failed: {e}")

def test_login():
    print("\nTesting Login...")
    url = f"{BASE_URL}/auth/login"
    # OAuth2 specifies form-data usually, but checking main.py it uses OAuth2PasswordRequestForm which expects form data
    data = urllib.parse.urlencode({
        "username": "hacker_std_lib",
        "password": "123"
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            print(f"Status: {status}")
            print(f"Response: {body}")
            if status == 200 and "access_token" in json.loads(body):
                print("[PASS] Token received.")
            else:
                print("[FAIL] Login failed.")
    except urllib.error.HTTPError as e:
        print(f"[FAIL] HTTP Error: {e.code} - {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"[FAIL] Check failed: {e}")

if __name__ == "__main__":
    test_registration()
    test_login()
