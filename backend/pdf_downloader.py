"""
IGRS UP - Automated Circle Rate PDF Downloader
================================================
Visits each UP district's NIC portal, finds all circle rate PDF links,
and downloads them into data/pdfs/<DistrictName>/ automatically.

Usage:
    python pdf_downloader.py                    # Download all districts
    python pdf_downloader.py --district Noida   # Download specific district
"""

import os
import re
import time
import argparse
import requests
from bs4 import BeautifulSoup

# Output directory (relative to backend/)
PDF_ROOT = os.path.join(os.path.dirname(__file__), '..', 'data', 'pdfs')

# URL patterns to try for each district (in order of priority)
URL_PATTERNS = [
    "https://{slug}.nic.in/document-category/circle-rate/",
    "https://{slug}.nic.in/tehsil-list/",
    "https://{slug}.nic.in/rate-list-of-district-{slug}/",
    "https://{slug}.nic.in/circle-rate/",
    "https://{slug}.nic.in/circle-rate-list/",
]

# All 75 UP districts with their NIC subdomain slugs
UP_DISTRICTS = {
    "Agra":             "agra",
    "Aligarh":          "aligarh",
    "Ambedkar Nagar":   "ambedkarnagar",
    "Amethi":           "amethi",
    "Amroha":           "amroha",
    "Auraiya":          "auraiya",
    "Ayodhya":          "ayodhya",
    "Azamgarh":         "azamgarh",
    "Baghpat":          "baghpat",
    "Bahraich":         "bahraich",
    "Ballia":           "ballia",
    "Balrampur":        "balrampur",
    "Banda":            "banda",
    "Barabanki":        "barabanki",
    "Bareilly":         "bareilly",
    "Basti":            "basti",
    "Bhadohi":          "bhadohi",
    "Bijnor":           "bijnor",
    "Budaun":           "budaun",
    "Bulandshahr":      "bulandshahr",
    "Chandauli":        "chandauli",
    "Chitrakoot":       "chitrakoot",
    "Deoria":           "deoria",
    "Etah":             "etah",
    "Etawah":           "etawah",
    "Farrukhabad":      "farrukhabad",
    "Fatehpur":         "fatehpur",
    "Firozabad":        "firozabad",
    "GB Nagar":         "gbnagar",
    "Ghaziabad":        "ghaziabad",
    "Ghazipur":         "ghazipur",
    "Gonda":            "gonda",
    "Gorakhpur":        "gorakhpur",
    "Hamirpur":         "hamirpur",
    "Hapur":            "hapur",
    "Hardoi":           "hardoi",
    "Hathras":          "hathras",
    "Jalaun":           "jalaun",
    "Jaunpur":          "jaunpur",
    "Jhansi":           "jhansi",
    "Kannauj":          "kannauj",
    "Kanpur Dehat":     "kanpurdehat",
    "Kanpur Nagar":     "kanpurnagar",
    "Kasganj":          "kasganj",
    "Kaushambi":        "kaushambi",
    "Kheri":            "kheri",
    "Kushinagar":       "kushinagar",
    "Lalitpur":         "lalitpur",
    "Lucknow":          "lucknow",
    "Maharajganj":      "maharajganj",
    "Mahoba":           "mahoba",
    "Mainpuri":         "mainpuri",
    "Mathura":          "mathura",
    "Mau":              "mau",
    "Meerut":           "meerut",
    "Mirzapur":         "mirzapur",
    "Moradabad":        "moradabad",
    "Muzaffarnagar":    "muzaffarnagar",
    "Pilibhit":         "pilibhit",
    "Pratapgarh":       "pratapgarh",
    "Prayagraj":        "prayagraj",
    "Raebareli":        "raebareli",
    "Rampur":           "rampur",
    "Saharanpur":       "saharanpur",
    "Sambhal":          "sambhal",
    "Sant Kabir Nagar": "santkabir",
    "Shahjahanpur":     "shahjahanpur",
    "Shamli":           "shamli",
    "Shravasti":        "shravasti",
    "Siddharthnagar":   "siddharthnagar",
    "Sitapur":          "sitapur",
    "Sonbhadra":        "sonbhadra",
    "Sultanpur":        "sultanpur",
    "Unnao":            "unnao",
    "Varanasi":         "varanasi",
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36'
}


def find_pdf_links(district: str, slug: str) -> list[str]:
    """Try multiple URL patterns for a district and return all PDF links found."""
    from urllib.parse import urljoin

    urls_to_try = [p.format(slug=slug) for p in URL_PATTERNS]

    for url in urls_to_try:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                continue

            soup = BeautifulSoup(res.text, 'html.parser')
            pdf_links = []

            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.lower().endswith('.pdf') or 's3waas.gov.in' in href:
                    full_url = href if href.startswith('http') else urljoin(url, href)
                    if full_url not in pdf_links:
                        pdf_links.append(full_url)

            if pdf_links:
                print(f"  🔗 Found {len(pdf_links)} PDFs at: {url}")
                return pdf_links

        except Exception:
            continue

    return []


def download_pdf(url: str, dest_path: str) -> bool:
    """Download a single PDF to dest_path."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        if res.status_code == 200:
            with open(dest_path, 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"    ❌ Download failed: {e}")
    return False


def download_district(district: str, slug: str):
    """Download all PDFs for a single district."""
    print(f"\n📁 {district}")

    pdf_links = find_pdf_links(district, slug)
    if not pdf_links:
        print(f"  ⚠️  No PDFs found for {district} (tried all URL patterns)")
        return 0

    # Create district folder
    district_dir = os.path.join(PDF_ROOT, district)
    os.makedirs(district_dir, exist_ok=True)

    downloaded = 0
    for pdf_url in pdf_links:
        filename = pdf_url.split('/')[-1]
        dest = os.path.join(district_dir, filename)

        if os.path.exists(dest):
            print(f"  ⏭️  Already exists: {filename}")
            downloaded += 1
            continue

        print(f"  ⬇️  Downloading: {filename}")
        if download_pdf(pdf_url, dest):
            size_kb = os.path.getsize(dest) // 1024
            print(f"  ✅ Saved ({size_kb} KB)")
            downloaded += 1
        else:
            print(f"  ❌ Failed: {filename}")

        time.sleep(0.5)  # Be polite to the server

    print(f"  📊 {downloaded}/{len(pdf_links)} PDFs downloaded for {district}")
    return downloaded


def run(target_district: str = None):
    print("🛰️  TerraSight — Automated Circle Rate PDF Downloader")
    print("=" * 55)
    os.makedirs(PDF_ROOT, exist_ok=True)

    districts = {target_district: UP_DISTRICTS[target_district]} if target_district else UP_DISTRICTS
    total = 0

    for district, url in districts.items():
        total += download_district(district, url)

    print(f"\n🎉 Done! Total PDFs downloaded: {total}")
    print("Now run: python pdf_ocr_parser.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download UP circle rate PDFs")
    parser.add_argument('--district', type=str, help='Download a specific district only', default=None)
    args = parser.parse_args()

    if args.district and args.district not in UP_DISTRICTS:
        print(f"❌ District '{args.district}' not found. Available: {list(UP_DISTRICTS.keys())}")
    else:
        run(args.district)
