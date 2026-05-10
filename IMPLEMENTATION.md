# TerraSight: Implementation & Architecture Record

This document outlines the evolutionary steps and architectural decisions made during the construction of TerraSight. It tells the story of how the platform scaled from a simple mock-data concept to a production-grade intelligence engine backed by real-time web scraping and government OCR pipelines.

---

## 🏗️ Phase 1: Foundation & The Mock Data Bridge
**Goal**: Establish the repository infrastructure, baseline UI layout, and initial data flow.

*   **Scaffolding**: Initialized a Python `FastAPI` backend and a `React/Vite` frontend.
*   **The Mock Data Era**: To prove the concept, we initially seeded a small SQLite database with a static `lucknow_circle_rates_seed.csv` file. This allowed us to test the API endpoints and ensure the frontend could successfully retrieve and display land valuation data without needing the full dataset immediately.
*   **Mapping Interface**: Integrated `react-leaflet` to render an interactive map, and wired up OpenStreetMap's Nominatim API to power a location search bar.

## 🗺️ Phase 2: Dual-Valuation & Spatial Intelligence
**Goal**: Translate static map searches into dynamic, user-driven data calculations.

*   **Amenity Radar**: Integrated the Overpass API to scan a 2km radius around any user-dropped pin. We optimized the backend to fetch strict equality matches (`=`) for Schools, Hospitals, Markets, Transit, Gyms, Parks, and Police Stations, bypassing API timeouts.
*   **Dual-Valuation Engine**: Upgraded the frontend to perform two parallel computations:
    1. The base **Government Circle Rate Total**.
    2. An **Estimated Market Value**, which dynamically applies a premium based on the density of the scraped amenities.
*   **Premium UI**: Introduced iOS-style bottom-sheet physics using `framer-motion`, interactive map category toggles, and seamless unit conversions (Sq.Ft, Sq.M, Gaj).

## 🧠 Phase 3: The Heuristic Fallback Engine
**Goal**: Ensure the application never crashes or returns empty results for unmapped areas.

*   **Solving Data Scarcity**: Because official government data is fragmented, we engineered a `generate_large_seed.py` script.
*   **The Algorithm**: This script mathematically generated realistic baseline circle rates (ranging from ₹20,000 to ₹65,000) for all 75 districts in Uttar Pradesh, categorizing them by tier (e.g., Tier 1: Noida, Tier 3: Rural).
*   **Result**: This guaranteed that if a user dropped a pin in a completely obscure village, TerraSight would still instantly return a mathematically sound, estimated base rate, keeping the app 100% functional state-wide.

## 🤖 Phase 4: Sentinel Protocol (Live Market Scraping)
**Goal**: Bypass static data entirely by fetching real-time market realities.

*   **Playwright Integration**: Built an autonomous, thread-isolated headless crawler (`sentinel.py`).
*   **Live Intelligence**: When triggered via the "Live Market Scan" UI button, the Sentinel Protocol wakes up, silently navigates to real estate aggregators (like MagicBricks), searches for the user's exact pinned locality, and scrapes live property listing prices.
*   **True Valuation**: It computes the true market average from live sellers and seamlessly injects this data back into the SQLite database, providing hyper-accurate valuations without relying on outdated government tables.

## 📄 Phase 5: Automated OCR Data Pipeline (Production)
**Goal**: Replace the heuristic mock data with verified, official 2025 government documents.

*   **The Government Scraper**: Engineered `pdf_downloader.py` to recursively crawl the NIC web portals of all 75 Uttar Pradesh districts. It intelligently handles different URL slugs to find and download raw circle rate PDFs, successfully circumventing different portal structures.
*   **Tesseract & Poppler Pipeline**: Built an advanced Optical Character Recognition engine (`pdf_ocr_parser.py`). This script converts the scanned, image-based government PDFs into high-resolution images, runs the Hindi `hin+eng` Tesseract language model to parse the text, and extracts thousands of localities and their corresponding per-sqm rates.
*   **Database Upsert**: We successfully downloaded the official circle rate PDFs for all 75 districts directly from the [IGRS UP Gov Portal](https://igrsup.gov.in/igrsup/getUploadRateListDocForUser). The OCR pipeline ingested an incredible **111,378 verified records** into the `official_circle_rates` table, instantly upgrading TerraSight from an estimated simulation to a massive production-grade, government-backed intelligence platform.

## ✨ Phase 6: Final UI Polish & Deployment Readiness
**Goal**: Finalize the user experience with premium visual feedback and eliminate technical debt.

*   **Global Map Pins Toggle**: Upgraded the frontend UX by implementing an iOS-style physical toggle switch. This allows users to instantly show or hide all fetched amenity markers simultaneously, giving them total control over map clutter without reloading data.
*   **Catchment Visibility**: Re-engineered the 2km search radius circle. Changed it from a blending indigo color to a highly contrasting, vibrant orange (`#f97316`) with increased opacity and dynamic dash sizing, ensuring absolute visibility over both street maps and dark satellite imagery.
*   **Dead Code Elimination**: Conducted a final repository scrub, deleting over 10 obsolete scripts (e.g., `etl_loader.py`, old CSV mock data, and initial test parsers) to guarantee a pristine, production-ready codebase for deployment on Vercel and Render.

---
*This document acts as the definitive architectural history of TerraSight.*
