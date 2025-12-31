# Vulnerable Bank CTF

**Vulnerable Bank** is a microservices-based banking application designed as a Capture The Flag (CTF) training environment. It contains deliberate security vulnerabilities for educational purposes.

> **⚠️ WARNING: DO NOT DEPLOY THIS APPLICATION TO A PRODUCTION ENVIRONMENT/INTERNET.**
> This application contains critical security flaws including SQL Injection, Remote Code Execution (potential), and weak authentication.

## 🏗️ Architecture

The system is built using Docker Compose and consists of the following services:

*   **Gateway:** Nginx reverse proxy routing traffic.
*   **Frontend:** React (Vite) application for user interaction.
*   **Auth Service:** FastAPI service managing users and authentication.
*   **Ledger Service:** FastAPI service managing accounts and transactions.
*   **Transaction Worker:** Python worker processing generic transfer checks (RabbitMQ).
*   **Database:** PostgreSQL (shared by services).
*   **Broker:** RabbitMQ.

## 🚀 Getting Started

### Prerequisites
*   Docker
*   Docker Compose

### Setup

1.  **Start the environment:**
    ```bash
    docker-compose up -d --build
    ```

2.  **Access the application:**
    *   **Frontend:** [http://localhost](http://localhost)
    *   **Auth API Docs:** [http://localhost/auth/docs](http://localhost/auth/docs)
    *   **Ledger API Docs:** [http://localhost/ledger/docs](http://localhost/ledger/docs)

### 🛑 Troubleshooting
If the frontend or services fail to start, check the logs:
```bash
docker-compose logs -f
```

## 🎯 CTF Objectives

Your mission is to uncover and exploit vulnerabilities across the system. Look for weaknesses in:
1.  **Authentication:** How are users registered and tokens issued?
2.  **Data Access:** Can you access data you shouldn't?
3.  **Input Validation:** Are your inputs being sanitized safely?
4.  **Business Logic:** Can you manipulate the flow of money?
5.  **Frontend Security:** Is the client-side code safe?

**Good luck!**

---
*For Instructors/Solutions: Check the `solution/` directory.*
