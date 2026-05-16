<div align="center">
  <img src="assets/hero_banner.png" alt="TerraSight Hero Banner" />
  <h1>TerraSight 🌍</h1>
  <p><strong>Geospatial Intelligence & Probabilistic Geo-Economic Inference Engine for Uttar Pradesh</strong></p>
  <p>🚀 <strong><a href="https://terra-sight-kappa.vercel.app">Try TerraSight Live</a></strong> 🚀</p>
</div>

---

## 📖 What is TerraSight?
TerraSight is a premium geospatial intelligence platform that revolutionizes land valuation. It allows investors, buyers, and developers to pin any location on a map and instantly receive a **Probabilistic Geo-Economic Inference Report**—comparing official government circle rates with real-time market estimates based on local infrastructure density.

## 🚀 How is it Different?
Traditional real estate tools only show you what sellers are asking for. Government portals only show you rigid, hard-to-read PDF tables. 

**TerraSight bridges the gap.** It dynamically calculates the *true* worth of a land parcel by pulling real official government rates via an automated OCR pipeline, and then compares it against a live algorithmic market estimate powered by local amenities (hospitals, schools, transit) within a 2km radius. 

---

## ✨ Core Features
*   **⚖️ Probabilistic Geo-Economic Inference Engine**: Instantly compares Official IGRS Government Rates with Infrastructure-driven Market Values using advanced spatial mathematics.
*   **🗺️ Interactive Map Intelligence**: High-performance Leaflet mapping with Street/Satellite toggles and dynamic catchment area radius controls.
*   **🤖 Sentinel Live Market Protocol**: An autonomous headless crawler that actively scrapes real estate aggregators (like MagicBricks) to compute true market averages.
*   **📄 Automated OCR Ingestion**: Officially verified data downloaded directly from the [IGRS UP Portal](https://igrsup.gov.in/igrsup/getUploadRateListDocForUser) across all 75 UP districts. We parse these raw Hindi PDFs via Tesseract OCR to maintain a massive database of **111,378 verified records**.
*   **📱 Premium App Experience**: A Framer Motion-powered physics "Bottom Sheet" UI that feels like a native iOS/Android app.

---

## 🧮 Algorithmic Normalization & Valuation Math
To ensure hyper-realistic Estimated Market Prices, our Inference Engine passes the raw data through four sequential mathematical layers:
1. **Chronological Inflation**: Autonomously ages the official government rate (extracted via OCR) to the current month, applying a +0.5% compounded monthly inflation.
2. **Market Reality Gap**: Maps the pinned coordinate to its geographical Tier (1-3) and applies a base multiplier (1.4x - 2.0x) because actual UP market selling rates inherently diverge from official "white money" circle rates.
3. **Absolute Exponential Distance-Decay (Gravity Model)**: Amenity weight decays exponentially using `Math.exp(-(distance / 1000))`, ensuring a hospital 500m away adds premium value, while one 3km away is correctly dismissed as irrelevant, perfectly divorcing the mathematical valuation from the user's UI radius slider.
4. **Logarithmic Dampening**: Hyper-dense urban clusters are mathematically "braked" using `Math.log10`, capping massive clusters so that 100 nearby schools don't artificially inflate the price to infinity.

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
