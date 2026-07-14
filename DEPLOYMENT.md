# EchoLink — Deployment Guide (Docker Compose)
*Production and local containerized deployment guide for the EchoLink Music Recommendation Engine*

This document explains how to deploy the full EchoLink stack (PostgreSQL database, FastAPI backend, and Vite React frontend) using **Docker** and **Docker Compose**.

---

## Architecture Overview

Using Docker Compose, the system is separated into three containerized services communicating over an internal Docker network:

```
                  [ Web Browser (User) ]
                            │
                            │ Port 80 (HTTP)
                            ▼
              [ frontend service (Nginx) ]
                            │
                            │ API calls (Port 8000)
                            ▼
               [ backend service (FastAPI) ]
                            │
                            │ Port 5432
                            ▼
             [ db service (PostgreSQL 17) ]
                            │
                      (Docker Volume)
                     [ postgres_data ]
```

* **`db` service:** Hosts PostgreSQL 17. Maps database files to a persistent Docker volume (`postgres_data`) so data survives container restarts.
* **`backend` service:** Runs the FastAPI application on port `8000`.
* **`frontend` service:** Builds the React/TypeScript app and serves the built assets using a custom **Nginx** configuration on port `80`.

---

## Prerequisites

Before deploying, ensure you have the following installed on your target machine (local computer or VPS remote server):
* **Docker** (v20.10 or higher)
* **Docker Compose** (v2.0 or higher)

---

## 🛠️ Step-by-Step Deployment Instructions

### 1. Project Configuration (Dynamic Backend URL)
In the frontend configuration ([echolink_frontend/src/api.ts](echolink_frontend/src/api.ts)), we support a dynamic backend URL config:
```typescript
const BASE = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`;
```
This ensures the frontend automatically connects to the backend API running on port `8000` of the server hosting it, without hardcoding any IP addresses.

### 2. Launch the Services
From the root directory of the project, run:
```bash
docker compose up --build -d
```
This command:
* Builds the Backend Docker image.
* Runs a multi-stage build for the Frontend (Nginx + static compilation).
* Downloads PostgreSQL 17.
* Launches all services in detached background mode (`-d`).

Verify the status of the containers:
```bash
docker compose ps
```

---

## 💾 Populating the Database (Seeding the rules)

Because the large ruleset CSV datasets (1.5 GB+) are excluded from Git, the containerized PostgreSQL database starts empty. 

To seed the database, run the data loading script from your **local system** (where the raw CSVs are saved), pointing to the target server's host:

### For Local Docker Testing:
```bash
DB_HOST=localhost DB_PORT=5432 DB_PASSWORD=postgresql python3 phase_3a_database.py
```

### For Remote VPS Server Deployment:
```bash
DB_HOST=<YOUR_SERVER_IP_OR_DOMAIN> DB_PORT=5432 DB_PASSWORD=postgresql python3 phase_3a_database.py
```

*Note: Make sure your remote server's firewall allows incoming connections on port `5432` during the seeding phase, or perform the seeding locally before exporting a Docker DB volume.*

---

## 🧪 Verification & Access

Once built and seeded:
* **Frontend UI:** Open your browser and navigate to `http://localhost` (or `http://your-server-ip`).
* **FastAPI Backend Swagger UI:** Access endpoints directly and view documentation at `http://localhost:8000/docs`.
* **Database Access:** Connect directly using pgAdmin or a CLI client on port `5432`.
