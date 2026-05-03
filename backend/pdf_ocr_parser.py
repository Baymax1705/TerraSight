"""
IGRS UP Circle Rate OCR Parser
================================
Reads scanned government PDFs using OCR (Tesseract + Hindi language),
extracts locality names and rates per sq.m, and loads them into the database.

Dependencies:
    pip install pytesseract pdf2image pdfplumber
    + Tesseract installed with Hindi (hin) language pack
    + Poppler installed and added to PATH

Usage:
    python pdf_ocr_parser.py
"""

import os
import re
import datetime
import pytesseract
from pdf2image import convert_from_path
from database import SessionLocal, OfficialCircleRate

# ─── CONFIG ───────────────────────────────────────────────────────────────────
PDF_ROOT        = os.path.join(os.path.dirname(__file__), '..', 'data', 'pdfs')
TESSERACT_PATH  = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH    = r"C:\Program Files\poppler-25.12.0\Library\bin"
EFFECTIVE_DATE  = datetime.datetime(2025, 8, 1)
TEHSIL_MAP = {
    "RateList_227": "Sadar-1",
    "RateList_228": "Sadar-2",
    "RateList_229": "Sadar-3",
    "RateList_230": "Sadar-4",
    "RateList_231": "Sadar-5",
    "RateList_232": "Sarojini Nagar-1",
    "RateList_233": "Sarojini Nagar-2",
    "RateList_234": "Mohanlalganj",
    "RateList_367": "Bakhshi Ka Talab",
    "RateList_383": "Malihabad",
}
# ──────────────────────────────────────────────────────────────────────────────

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_rates_from_line(line: str) -> list[float]:
    """Find all numeric rate values in a single text line."""
    # Match 4-6 digit numbers (rate range ₹1000 to ₹999999)
    nums = re.findall(r'\b(\d{4,6})\b', line)
    rates = []
    for n in nums:
        val = float(n)
        if 1000 <= val <= 500000:
            rates.append(val)
    return rates


def extract_locality_name(line: str) -> str | None:
    """
    Try to extract a locality/village name from a text line.
    Locality names in Hindi government docs are usually:
    - A mix of Hindi unicode chars or transliterated English
    - At least 3 characters long
    - Not purely numeric
    """
    # Remove serial numbers at start of line (e.g., "1.", "12.", "123.")
    line = re.sub(r'^\s*\d+[\.\)]\s*', '', line).strip()

    if not line:
        return None

    # Split on multiple spaces or tabs — locality is usually the first token
    parts = re.split(r'\s{2,}|\t', line)
    if parts:
        candidate = parts[0].strip()
        # Must be at least 3 chars and not purely a number
        if len(candidate) >= 3 and not re.fullmatch(r'[\d\s\.\,]+', candidate):
            return candidate

    return None


def ocr_pdf(pdf_path: str, district: str, tehsil: str) -> list[dict]:
    """Convert PDF to images, run OCR, extract locality + rate pairs."""
    records = []
    print(f"  📄 OCR: {os.path.basename(pdf_path)} → {tehsil}")

    try:
        images = convert_from_path(pdf_path, dpi=200, poppler_path=POPPLER_PATH)
    except Exception as e:
        print(f"    ❌ PDF conversion failed: {e}")
        return records

    for page_num, image in enumerate(images):
        try:
            # Use Hindi + English for best results on mixed government docs
            raw_text = pytesseract.image_to_string(image, lang='hin+eng', config='--psm 6')
        except Exception as e:
            print(f"    ⚠️  OCR failed on page {page_num + 1}: {e}")
            continue

        lines = raw_text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) < 5:
                continue

            rates = extract_rates_from_line(line)
            if not rates:
                continue

            locality = extract_locality_name(line)
            if not locality:
                continue

            # Use the first valid rate found (ordinary/base rate)
            rate_sqm = rates[0]

            # Deduplicate within this PDF
            if not any(r['locality'] == locality and r['district'] == district for r in records):
                records.append({
                    "district": district,
                    "tehsil": tehsil,
                    "locality": locality,
                    "property_type": "Residential",
                    "rate_sqm": rate_sqm,
                    "effective_date": EFFECTIVE_DATE
                })

    print(f"    → Extracted {len(records)} localities from {len(images)} pages")
    return records


def load_into_db(records: list[dict]):
    """Upsert all records into official_circle_rates table."""
    db = SessionLocal()
    inserted = updated = 0
    try:
        for r in records:
            existing = db.query(OfficialCircleRate).filter(
                OfficialCircleRate.district == r["district"],
                OfficialCircleRate.locality == r["locality"],
                OfficialCircleRate.property_type == r["property_type"]
            ).first()

            if existing:
                existing.rate_sqm = r["rate_sqm"]
                existing.tehsil = r["tehsil"]
                existing.effective_date = r["effective_date"]
                updated += 1
            else:
                db.add(OfficialCircleRate(
                    district=r["district"],
                    tehsil=r["tehsil"],
                    locality=r["locality"],
                    property_type=r["property_type"],
                    rate_sqm=r["rate_sqm"],
                    effective_date=r["effective_date"]
                ))
                inserted += 1

        db.commit()
        print(f"  💾 DB: +{inserted} inserted | {updated} updated")
    except Exception as e:
        db.rollback()
        print(f"  ❌ DB Error: {e}")
    finally:
        db.close()


def get_tehsil(filename: str) -> str:
    for key, tehsil in TEHSIL_MAP.items():
        if key in filename:
            return tehsil
    # For new districts, use the filename as tehsil name (strip extension)
    return os.path.splitext(filename)[0]


def run():
    print("🛰️  IGRS OCR Parser — TerraSight Intelligence Pipeline")
    print("=" * 55)

    total = 0
    for district_name in os.listdir(PDF_ROOT):
        district_path = os.path.join(PDF_ROOT, district_name)
        if not os.path.isdir(district_path):
            continue

        print(f"\n📁 District: {district_name}")
        district_records = []

        for pdf_file in sorted(os.listdir(district_path)):
            if not pdf_file.lower().endswith('.pdf'):
                continue
            pdf_path = os.path.join(district_path, pdf_file)
            tehsil = get_tehsil(pdf_file)
            records = ocr_pdf(pdf_path, district_name, tehsil)
            district_records.extend(records)

        if district_records:
            load_into_db(district_records)
            total += len(district_records)
        else:
            print(f"  ⚠️  No records extracted for {district_name}")

    print(f"\n🎉 Done! Total localities loaded: {total}")


if __name__ == "__main__":
    run()
