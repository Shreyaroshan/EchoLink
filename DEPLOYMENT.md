# EchoLink — Unified Service Deployment Guide
*Production and local deployment guide for running the EchoLink Recommendation Engine inside a single container*

This guide explains how to deploy the EchoLink application as a **Unified Service** (serving the Vite React frontend directly from the FastAPI Python server). This allows the entire application to run on a **single port (8000)**, completely resolving CORS issues and making it 100% compatible with free-tier platforms (like Render's single web-service constraint).

---

## Architecture Overview

```
                  [ Web Browser (User) ]
                            │
                            │ Port 8000 (HTTP)
                            ▼
           [ echolink_app Service (FastAPI) ]
           ├── API Endpoints (/search, /recommend)
           └── Static Frontend (/assets, index.html)
                            │
                            │ Port 5432 (Internal)
                            ▼
             [ db Service (PostgreSQL 17) ]
                            │
                      (Docker Volume)
                     [ postgres_data ]
```

* **Frontend serving:** In production, the React frontend is compiled into static HTML/CSS/JS. FastAPI is configured to serve these files staticially under the `/` path.
* **CORS-Free:** Because the UI and API share the exact same host and port, no cross-origin configurations are needed.

---

## 🛠️ Local Deployment via Docker Compose

### 1. Run the Container Stack
From the project root directory, spin up the database and the unified application container:
```bash
docker compose up --build -d
```
This builds a **multi-stage Dockerfile**:
1. **Stage 1 (Node.js):** Installs frontend dependencies and builds the React app into `echolink_frontend/dist/`.
2. **Stage 2 (Python):** Installs FastAPI dependencies, copies the backend code, imports the frontend `dist/` directory, and starts Uvicorn.

### 2. Populate the Database (Seeding)
Because database `.csv` files are excluded from git, the PostgreSQL database initializes empty. Seed it by running the script from your **local system** (where the raw CSVs are saved), pointing to the dockerized server port:
```bash
DB_HOST=localhost DB_PORT=5432 DB_PASSWORD=postgresql python3 phase_3a_database.py
```

### 3. Verification
* **Access App:** Open `http://localhost:8000` in your web browser.
* **Access API Docs:** Open `http://localhost:8000/docs` to view the FastAPI Swagger UI.

---

## 🚀 Free Production Deployment (Render + Neon.tech)

To host EchoLink online completely for free, use a combination of **Neon** (for PostgreSQL database) and **Render** (for the Unified App Service):

### 1. Set Up the Free Database (Neon)
1. Go to [Neon.tech](https://neon.tech/) and create a free PostgreSQL project named `echolink`.
2. Copy the database connection string from the dashboard.
3. Seed the Neon database by running the loader locally from your computer:
   ```bash
   DB_HOST=your-neon-hostname.neon.tech DB_PORT=5432 DB_NAME=neondb DB_USER=your_user DB_PASSWORD=your_password python3 phase_3a_database.py
   ```

### 2. Deploy the App Container (Render)
1. Log in to [Render.com](https://render.com/).
2. Click **New +** and select **Web Service**.
3. Link your GitHub repository.
4. Set the following settings:
   * **Language:** `Docker`
   * **Docker Command:** *Leave empty (uses CMD from Dockerfile)*
   * **Instance Type:** `Free`
5. Click **Advanced** and add the following **Environment Variables**:
   * `DB_HOST`: *Your Neon database hostname*
   * `DB_PORT`: `5432`
   * `DB_NAME`: `neondb`
   * `DB_USER`: *Your Neon user*
   * `DB_PASSWORD`: *Your Neon password*
6. Click **Deploy Web Service**. Render will build the Docker container and host it at a free `onrender.com` URL!
