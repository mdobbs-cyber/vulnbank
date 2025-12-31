# Vulnerable Bank - Blue Team Solutions Guide

This guide details how to detect the Red Team's attacks using Splunk. All logs are ingested with `sourcetype=_json`.

## 1. Mass Assignment (Privilege Escalation)
**Flag:** Admin Account Creation
**Attack Indicators:**
- A user registers with `"is_admin": true`.
- The `User registered` log entry explicitly shows `Admin: True`.

**Splunk Search:**
```splunk
index=* sourcetype=_json "Admin: True"
```
*Or correlation:*
```splunk
index=* sourcetype=_json message="User registered" is_admin=true
```

## 2. Information Disclosure (IDOR)
**Flag:** Accessing CEO's Balance
**Attack Indicators:**
- The request logs show a user checking a balance (`/balance/{id}`).
- The `Balance checked` log entry shows a discrepancy between the requester (`by ...`) and the account owner (implied).

**Splunk Search:**
```splunk
index=* sourcetype=_json "Balance checked for account"
| rex field=message "account (?<target_account>\d+) by (?<actor>.*)"
| where target_account=1 AND actor!="ceo"
```
*(Note: Account 1 is the CEO's account).*

## 3. SQL Injection (Data Exfiltration)
**Flag:** Dumping Database
**Attack Indicators:**
- The `Executing Query` log shows raw SQL containing unexpected clauses like `UNION`, `OR '1'='1`.
- Database error logs (`Search query error`) revealing syntax errors from failed injection attempts.

**Splunk Search:**
```splunk
index=* sourcetype=_json "Executing Query" ("UNION" OR "1=1" OR "' OR '")
```
*Detecting failed attempts:*
```splunk
index=* sourcetype=_json "Search query error"
```

## 4. Race Condition (Double Spending)
**Flag:** Negative Balance / Double Spend
**Attack Indicators:**
- Two `Transaction queued` events for the *same user* occur within milliseconds of each other.
- The timestamps are identical or extremely close, indicating parallel execution during the race window.

**Splunk Search:**
```splunk
index=* sourcetype=_json "Transaction queued"
| transaction "sender_username" maxspan=1s
| where eventcount > 1
```

## 5. Stored XSS
**Flag:** Malicious Payload Injection
**Attack Indicators:**
- A transaction description contains HTML tags (`<script>`, `<img>`, `onerror`).
- The `Executing Query` log reveals the payload being injected (often via SQLi `UNION SELECT`).

**Splunk Search:**
```splunk
index=* sourcetype=_json "description"="*<*>*"
```
*Specific Payload Detection:*
```splunk
index=* sourcetype=_json "onerror" OR "alert"
```

---
**Note:** Ensure `index=*` and `sourcetype=_json` are included in all queries to filter for the relevant application logs.
