# Vulnerable Bank - Instructor's Guide & Solutions

**CONFIDENTIAL:** This document contains the solutions to the Vulnerable Bank CTF. Do not distribute to students.

## Environment Overview
The application is a mock banking system composed of:
- **Auth Service:** Vulnerable user management.
- **Ledger Service:** Vulnerable transaction ledger.
- **Transaction Worker:** Vulnerable asynchronous processor.
- **Frontend:** Vulnerable React UI.

## Vulnerability Solutions

### 1. Mass Assignment (Privilege Escalation)
**Difficulty:** Easy
**Location:** Auth Service (`POST /register`)

*   **Vulnerability:** The `UserCreate` Pydantic model in `services/auth/models.py` explicitly defines `is_admin: bool = False`. The API endpoint accepts this field without filtering it out.
*   **Exploit:**
    Send a registration request with `"is_admin": true`.
    ```json
    POST /auth/register
    {
      "username": "hacker",
      "password": "123",
      "is_admin": true
    }
    ```
*   **Verification:** Login and inspect the returned JWT. The payload will contain `"admin": true` (or similar depending on implementation version).

### 2. Information Disclosure (IDOR)
**Difficulty:** Easy
**Location:** Ledger Service (`GET /ledger/balance/{account_id}`)

*   **Vulnerability:** The balance endpoint allows any authenticated user to request the balance of *any* account ID. It fails to check if the `current_user` owns the requested `account_id`.
*   **Exploit:**
    1.  Login as a normal user.
    2.  Request the balance of Account ID `1` (The CEO/Admin account seeded at startup).
    ```http
    GET /ledger/balance/1 HTTP/1.1
    Authorization: Bearer <your_token>
    ```
*   **Result:** The API returns the balance (e.g., $1,000,000) instead of 403 Forbidden.

### 3. SQL Injection (Data Exfiltration)
**Difficulty:** Medium
**Location:** Ledger Service (`GET /ledger/transactions/search`)

*   **Vulnerability:** The search endpoint constructs the SQL query using an f-string:
    ```python
    query_str = f"SELECT * FROM transactions WHERE description LIKE '%{q}%'"
    ```
    This allows direct injection of SQL commands.
*   **Exploit:**
    Inject a payload to make the `WHERE` clause always true or use `UNION` to extract data.
    *   **Simple Dump:** `q=' OR '1'='1`
        *   Resulting Query: `SELECT * FROM transactions WHERE description LIKE '%' OR '1'='1%'`
*   **Target:** Find the "Confidential Bonus Payment" transaction which is not normally visible or relevant to the user.

### 4. Race Condition (Double Spending)
**Difficulty:** Hard
**Location:** Transaction Worker (`services/worker/worker.py`)

*   **Vulnerability:** The worker processes transfers in the following order:
    1.  Check Sender Balance.
    2.  **Sleep 5 Seconds** (Simulating processing delay / TOCTOU gap).
    3.  Update Balance (Deduct funds).
    Because the check and update are not atomic (and the lock/sleep window is large), parallel requests can pass the check before the first one deducts the funds.
*   **Exploit:**
    1.  Seed an account with $100.
    2.  Send **two** simultaneous requests to transfer $100 to another account.
    3.  Both workers read $100 balance.
    4.  Both workers sleep.
    5.  Both workers deduct $100.
*   **Result:** Final balance is -$100.

### 5. Stored XSS (Cross-Site Scripting)
**Difficulty:** Medium/Hard
**Location:** Frontend (`Dashboard.jsx`) & Ledger Service (SQLi)

*   **Vulnerability:** The React Frontend renders transaction descriptions using `dangerouslySetInnerHTML`. The Ledger Service does not sanitize input, but more importantly, the SQL Injection vulnerability allows an attacker to *inject* a fake transaction record with a maliciously crafted description into the result set of the `search` endpoint.
*   **Exploit:**
    1.  Use the SQL Injection in `/transactions/search` to UNION SELECT a fake row.
    2.  Payload: `' UNION SELECT 9999, 1, 0, '<img src=x onerror=alert("XSS")>', NOW() --`
    3.  This forces the API to return a transaction object where `description` is `<img src=x onerror=alert("XSS")>`.
    4.  The Frontend renders this HTML, triggering the alert.

## Automated Verification
A script `exploit_suite.py` is provided in the root directory. It runs exploits for vulnerabilities 1-4 automatically.
To run it:
```bash
python exploit_suite.py
```