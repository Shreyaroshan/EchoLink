# EchoLink 🎵
> **A Music Recommendation Engine powered by Association Rule Mining**

EchoLink is a data-driven music recommendation system that recommends tracks based on playlist co-occurrence patterns. Instead of utilizing traditional machine learning embeddings or personal user profiles, it maps relationships using association rules mined from a dataset of **161,000 real Spotify playlists** (comprising 3.3M individual track entries).

---

## 📸 Screenshots

*Below are screenshots showcasing the EchoLink user interface. To add screenshots, place your image files in a `screenshots/` folder and link them below.*

| Discover View | Co-occurrence Network |
| :---: | :---: |
| ![Discover View Placeholder](https://via.placeholder.com/600x350/13131c/f1f5f9?text=Discover+Recommendations+View) | ![Co-occurrence Network Placeholder](https://via.placeholder.com/600x350/13131c/f1f5f9?text=Explorer+D3.js+Force+Graph+Network) |

| Benchmark Dashboard | About View |
| :---: | :---: |
| ![Benchmark Dashboard Placeholder](https://via.placeholder.com/600x350/13131c/f1f5f9?text=Algorithm+Benchmark+Dashboard) | ![About View Placeholder](https://via.placeholder.com/600x350/13131c/f1f5f9?text=How+It+Works+Documentation+View) |

---

## 🏗️ System Architecture

EchoLink is built using a modern decoupled architecture:

```
Raw CSV Data (3.3M rows)
       ↓ Preprocessing
spotify_clean.csv (Itemsets)
       ↓ Data Mining
Association Rules (Jaccard, Confidence, Lift, Support)
       ↓ Database Loading
PostgreSQL 17 Database
       ↓ Backend REST API
FastAPI (Python)
       ↓ Client Interface
Vite + React + TypeScript + D3.js (Force Directed Graph)
```

---

## ⚡ Tech Stack

* **Frontend:** React, TypeScript, Vite, D3.js (for the force-directed graph), Vanilla CSS (Glassmorphism design system)
* **Backend:** FastAPI, Uvicorn, psycopg2-binary
* **Database:** PostgreSQL 17 (optimized with composite indexes for sub-millisecond lookups)
* **Data Processing:** Python (Pandas, custom Apriori implementation, FP-Growth benchmark)
* **Testing:** Pytest (Unit & Integration tests)

---

## 🚀 Setup & Installation

### 1. Database Setup
1. Start your PostgreSQL database service.
2. Create a database named `echolink`.
3. Set your environment variables if using custom configurations (defaults: user `postgres`, password `postgresql`):
   ```bash
   export DB_PASSWORD="your_password"
   ```
4. Populate the database by running the schema script (it will load tracks and association rules from CSVs):
   ```bash
   python3 phase_3a_database.py
   ```

### 2. Run the Backend API
1. Navigate to the backend directory:
   ```bash
   cd echolink_api
   ```
2. Install Python requirements:
   ```bash
   pip install -r ../requirements.txt
   ```
3. Run the Uvicorn server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   *The interactive API docs will be available at [http://localhost:8000/docs](http://localhost:8000/docs).*

### 3. Run the Frontend
1. Navigate to the frontend directory:
   ```bash
   cd echolink_frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   *The web application will open at [http://localhost:5173](http://localhost:5173).*

---

## 🧪 Testing

EchoLink is backed by a robust test suite comprising **9 unit tests** (mocked database) and **6 integration tests** (live database).

To run the tests:
```bash
# Run all tests
pytest echolink_api/tests/ -v

# Run unit tests only (runs in <0.1s, no database required)
pytest echolink_api/tests/test_unit.py -v

# Run integration tests only
pytest echolink_api/tests/test_integration.py -v
```

See [TESTING.md](TESTING.md) for detailed test cases and architecture.

---

## 📝 Dataset Credits & Citation

This application is built on Spotify playlist data compiled in the following research paper:

> Pichl, Martin; Zangerle, Eva; Specht, Günther: *"Towards a Context-Aware Music Recommendation Approach: What is Hidden in the Playlist Name?"* in 15th IEEE International Conference on Data Mining Workshops (ICDM 2015), pp. 1360-1365, IEEE, Atlantic City, 2015.
