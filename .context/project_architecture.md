\# Vulnerable Bank - High-Level Architecture



\## System Overview

"Vulnerable Bank" is a microservices-based application designed to simulate a real-world fintech environment. It is intentionally engineered with specific security flaws to serve as a cyber security training platform.



\## 1. Service Map \& Responsibilities



\### A. The Gateway (Entry Point)

\* \*\*Service Name:\*\* `api-gateway`

\* \*\*Tech:\*\* Nginx (Reverse Proxy)

\* \*\*Role:\*\* Routes traffic to internal services (`/auth`, `/api/ledger`, `/api/transfer`).

\* \*\*Intended Weaknesses:\*\* Misconfigured CORS policies, lack of rate limiting.



\### B. Identity Service (Authentication)

\* \*\*Service Name:\*\* `auth-service`

\* \*\*Tech:\*\* Python (FastAPI)

\* \*\*Database:\*\* `user-db` (PostgreSQL)

\* \*\*Role:\*\* Handles User Registration, Login, and Token Generation (JWT).

\* \*\*Intended Weaknesses:\*\*

&nbsp;   \* \*\*Broken Auth:\*\* Hardcoded JWT signing keys.

&nbsp;   \* \*\*Mass Assignment:\*\* Privilege escalation via API body manipulation.

&nbsp;   \* \*\*Weak Password Policy:\*\* Allows "123456" etc.



\### C. Core Banking Service (The Ledger)

\* \*\*Service Name:\*\* `ledger-service`

\* \*\*Tech:\*\* Python (FastAPI)

\* \*\*Database:\*\* `ledger-db` (PostgreSQL)

\* \*\*Role:\*\*

&nbsp;   \* Manages Account balances.

&nbsp;   \* Records transaction history (Credits/Debits).

&nbsp;   \* Provides search functionality for transactions.

\* \*\*Intended Weaknesses:\*\*

&nbsp;   \* \*\*SQL Injection:\*\* Search endpoints use string concatenation.

&nbsp;   \* \*\*IDOR (Insecure Direct Object Reference):\*\* Users can view other users' balances by changing IDs in the URL.



\### D. Transaction Engine (Payment Rails)

\* \*\*Service Name:\*\* `transaction-worker`

\* \*\*Tech:\*\* Python (Consumer Script)

\* \*\*Messaging:\*\* RabbitMQ

\* \*\*Role:\*\*

&nbsp;   \* Listens to the `transfer\_queue`.

&nbsp;   \* Process funds movement between accounts.

&nbsp;   \* Performs rudimentary fraud checks.

\* \*\*Intended Weaknesses:\*\*

&nbsp;   \* \*\*Race Conditions:\*\* Time-of-check to time-of-use (TOCTOU) flaws allowing double spending.

&nbsp;   \* \*\*Logic Flaws:\*\* Allowing negative value transfers.



\### E. Interbank Simulator (External World)

\* \*\*Service Name:\*\* `interbank-api`

\* \*\*Tech:\*\* Node.js / Express

\* \*\*Role:\*\* Simulates external bank transfers (SWIFT/ISO format).

\* \*\*Intended Weaknesses:\*\*

&nbsp;   \* \*\*XXE (XML External Entity):\*\* Vulnerable XML parsing configuration.



\### F. Frontend (User Interface)

\* \*\*Service Name:\*\* `frontend-app`

\* \*\*Tech:\*\* React (Vite)

\* \*\*Role:\*\* User Dashboard, Transfer Forms, Admin Panel.

\* \*\*Intended Weaknesses:\*\*

&nbsp;   \* \*\*XSS (Cross-Site Scripting):\*\* Unsafe rendering of transaction descriptions.

&nbsp;   \* \*\*Sensitive Data Exposure:\*\* Storing tokens in `localStorage`.



---



\## 2. Data Flow Examples



\### Scenario: User Login

1\.  Frontend sends `POST /login` to `api-gateway`.

2\.  Gateway routes to `auth-service`.

3\.  `auth-service` validates credentials against `user-db`.

4\.  Returns a signed JWT (using a weak key).



\### Scenario: Fund Transfer

1\.  User initiates transfer on Frontend.

2\.  Request goes to `ledger-service` via Gateway.

3\.  `ledger-service` publishes message to RabbitMQ `transfer\_queue`.

4\.  `transaction-worker` consumes message.

5\.  Worker updates `ledger-db` balances (intentionally slow to allow Race Conditions).



\## 3. Infrastructure Constraints

\* \*\*Network:\*\* All services sit on a private Docker bridge network `bank-net`.

\* \*\*Exposure:\*\* Only `api-gateway` (Port 80) and `frontend-app` (Port 3000) are exposed to the host.

\* \*\*Persistence:\*\* Docker volumes used for Database persistence to ensure data survives container restarts.

