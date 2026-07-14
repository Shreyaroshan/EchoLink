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

## 🚀 Free Production Deployment Options

You can deploy the app and PostgreSQL database for free in Render using either the **Automated Blueprint** or a **Custom Setup**.

### Option A: Single-Click Automated Blueprint (e.g. Render Stack)
We have included a [render.yaml](render.yaml) file in the repository. Render reads this file and automatically provisions both the PostgreSQL database and the FastAPI Docker web service, linking their credentials together without manual copying.

1. Log in to [Render.com](https://render.com/).
2. In the dashboard, click **New +** and select **Blueprint**.
3. Connect your GitHub repository (`EchoLink`).
4. Render will read `render.yaml` and display the database (`echolink-db`) and application service (`echolink-app`) configuration.
5. Click **Apply**. Render will start the database and compile the Docker container.
6. Once deployed, copy the external connection details of `echolink-db` from the Render dashboard, and run the seeding script locally from your computer:
   ```bash
   DB_HOST=<RENDER_DB_HOST> DB_PORT=5432 DB_NAME=echolink DB_USER=postgres DB_PASSWORD=<RENDER_DB_PASSWORD> python3 phase_3a_database.py
   ```
*Note: Render's free PostgreSQL database expires and is deleted after 90 days. For a permanent free database, use Option B.*

---

### Option B: Permanent Free Database Setup (Render + Neon.tech)
To host the database permanently without any 90-day expiry limits, combine **Neon** (Postgres) and **Render** (App Service):

1. **Create the Database (Neon):** Go to [Neon.tech](https://neon.tech/), create a project, and copy the DB connection string.
2. **Seed the Database:** Run the data loader locally on your computer pointing to the Neon host:
   ```bash
   DB_HOST=your-neon-host.neon.tech DB_PORT=5432 DB_NAME=neondb DB_USER=your_user DB_PASSWORD=your_password python3 phase_3a_database.py
   ```
3. **Deploy the Web Service (Render):**
   * Go to Render, click **New +** -> **Web Service**, and link your repository.
   * Set **Language** to `Docker` and **Instance Type** to `Free`.
   * Under **Advanced**, add environment variables `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` matching your Neon database credentials.
   * Click **Deploy**. Render will host your app at a free `onrender.com` URL.
