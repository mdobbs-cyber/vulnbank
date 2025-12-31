import urllib.request
import json
import time

BASE_URL = "http://localhost:80"

def verify_frontend_accessible():
    print("Checking Frontend Accessibility...")
    try:
        # Should return the React index.html
        resp = urllib.request.urlopen(BASE_URL)
        content = resp.read().decode('utf-8')
        if "<title>Vulnerable Bank</title>" in content:
            print("[PASS] Frontend loaded (via Gateway).")
        else:
            print(f"[FAIL] Frontend content mismatch: {content[:100]}")
    except Exception as e:
        print(f"[FAIL] Frontend access failed: {e}")

if __name__ == "__main__":
    verify_frontend_accessible()
