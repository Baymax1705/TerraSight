<div align="center">
  <img src="assets/hero_banner.png" alt="TerraSight Hero Banner" />
  <h1>TerraSight 🌍</h1>
  <p><strong>Geospatial Intelligence & Dual-Valuation Engine for Uttar Pradesh</strong></p>
  <p>🚀 <strong><a href="https://terra-sight-kappa.vercel.app">Try TerraSight Live</a></strong> 🚀</p>
</div>

---

## 📖 What is TerraSight?
TerraSight is a premium geospatial intelligence platform that revolutionizes land valuation. It allows investors, buyers, and developers to pin any location on a map and instantly receive a **Dual-Valuation Report**—comparing official government circle rates with real-time market estimates based on local infrastructure density.

## 🚀 How is it Different?
Traditional real estate tools only show you what sellers are asking for. Government portals only show you rigid, hard-to-read PDF tables. 

**TerraSight bridges the gap.** It dynamically calculates the *true* worth of a land parcel by pulling real official government rates via an automated OCR pipeline, and then compares it against a live algorithmic market estimate powered by local amenities (hospitals, schools, transit) within a 2km radius. 

---

## ✨ Core Features
*   **⚖️ Dual-Valuation Engine**: Instantly compares Official IGRS Government Rates with Infrastructure-driven Market Values.
*   **🗺️ Interactive Map Intelligence**: High-performance Leaflet mapping with Street/Satellite toggles and dynamic catchment area radius controls.
*   **🤖 Sentinel Live Market Protocol**: An autonomous headless crawler that actively scrapes real estate aggregators (like MagicBricks) to compute true market averages.
*   **📄 Automated OCR Ingestion**: Web scrapers automatically pull raw PDF circle rate lists across 75 UP districts, parsed via Tesseract OCR to maintain a database of 1,650+ verified 2025 records.
*   **📱 Premium App Experience**: A Framer Motion-powered physics "Bottom Sheet" UI that feels like a native iOS/Android app.

---

## 🛡️ Data Architecture & Error Handling (Three-Tier Fallback)
We engineered TerraSight to **never fail or show empty screens**, even when public government data is hidden behind captcha walls or simply unavailable. We handle data scarcity using a strict **Three-Tier Fallback System**:

1. **Official OCR Data (Primary)**: Instantly serves verified 2025 government circle rates directly extracted from government PDFs for 16 major districts.
2. **Heuristic Engine (Fallback 1)**: If a user queries an unmapped district, the platform instantly falls back to a realistic, algorithmically calculated base rate from a pre-seeded heuristic database.
3. **Sentinel Protocol (Fallback 2)**: For ultimate accuracy in missing regions, users can trigger a "Live Market Scan." The Sentinel Protocol autonomously spins up a headless browser, scrapes live MagicBricks property listings for that exact coordinate, and returns real-time market selling prices.

---

## 🛠️ Tech Stack
*   **Frontend**: React 19, Vite, Tailwind CSS (Glassmorphism), Framer Motion, Leaflet.js
*   **Backend**: FastAPI (Python 3), SQLite, SQLAlchemy
*   **Data Pipelines**: Playwright (Headless Scraping), Tesseract OCR, Poppler, BeautifulSoup4
*   **Geospatial**: Overpass API (OSM), Haversine Proximity Algorithms, Custom Nominatim Bounding Boxes

---

## ⚙️ How to Set Up Locally

### 1. Clone the Repository
```bash
git clone https://github.com/Baymax1705/TerraSight.git
cd TerraSight
```

### 2. Start the Backend
```bash
cd backend
python -m venv venv
source venv/bin/scripts/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```

*Open `http://localhost:5173` in your browser to view the app!*

---
<div align="center">
  <i>Developed with ❤️ for Smart Land Intelligence.</i>
</div>
