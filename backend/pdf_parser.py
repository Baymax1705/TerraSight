"""
IGRS UP Circle Rate PDF Parser
================================
Reads official government circle rate PDFs district-by-district,
extracts locality names and rates per sq.m, and loads them into the database.

Usage:
    python pdf_parser.py

Dependencies:
    pip install pdfplumber
"""

import os
import re
import pdfplumber
import datetime
from database import SessionLocal, OfficialCircleRate, Base
from sqlalchemy import create_engine

# Path to the PDFs directory (relative to backend/)
PDF_ROOT = os.path.join(os.path.dirname(__file__), '..', 'data', 'pdfs')

def clean_rate(text: str) -> float | None:
    """Extract a numeric rate from a string like '31,000' or '₹ 31000' or '31000.00'"""
    if not text:
        return None
    # Remove currency symbol, spaces, commas
    cleaned = re.sub(r'[₹,\s]', '', str(text).strip())
    try:
        val = float(cleaned)
        # Sanity check: rates should be between ₹500 and ₹5,00,000 per sq.m
        if 500 <= val <= 500000:
            return val
    except (ValueError, TypeError):
        pass
    return None


def extract_rates_from_pdf(pdf_path: str, district: str, tehsil: str) -> list[dict]:
    """
    Opens a single IGRS PDF and extracts all locality rows with rates.
    Returns a list of dicts with keys: district, tehsil, locality, property_type, rate_sqm, effective_date
    """
    records = []
    effective_date = datetime.date(2025, 8, 1)

    print(f"  📄 Parsing: {os.path.basename(pdf_path)}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    for row in table:
                        if not row or len(row) < 3:
                            continue

                        # Try to find the locality name column (usually col index 1)
                        # and the rate columns (usually col index 6 and 7 for ordinary/premium)
                        locality = None
                        rate_ordinary = None
                        rate_premium = None

                        # Search all cells for a locality name (skip header rows)
                        for i, cell in enumerate(row):
                            if cell is None:
                                continue
                            cell_str = str(cell).strip()

                            # Skip header rows that contain Hindi column headers
                            if any(kw in cell_str for kw in ['क्र०', 'राजस्व', 'वार्ड', 'श्रेणी', 'दरें', 'सं०']):
                                locality = None
                                break

                            # Look for locality name: index 1 typically
                            if i == 1 and len(cell_str) > 2:
                                locality = cell_str

                            # Look for rate values in later columns
                            if i >= 5:
                                rate = clean_rate(cell_str)
                                if rate and rate_ordinary is None:
                                    rate_ordinary = rate
                                elif rate and rate_premium is None:
                                    rate_premium = rate

                        if locality and (rate_ordinary or rate_premium):
                            # Use ordinary rate as the base; if missing use premium
                            final_rate = rate_ordinary or rate_premium
                            records.append({
                                "district": district,
                                "tehsil": tehsil,
                                "locality": locality,
                                "property_type": "Residential",
                                "rate_sqm": final_rate,
                                "effective_date": effective_date
                            })
    except Exception as e:
        print(f"    ⚠️  Error reading {pdf_path}: {e}")

    return records


def get_tehsil_from_filename(filename: str) -> str:
    """
    Maps PDF filenames to tehsil names.
    Since IGRS filenames are just IDs (RateList_227_...), we use order/numbering.
    You can manually update this mapping after inspecting the PDFs.
    """
    mapping = {
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
    for key, tehsil in mapping.items():
        if key in filename:
            return tehsil
    return "Unknown"


def load_into_db(records: list[dict]):
    """Upserts all extracted records into the official_circle_rates table."""
    db = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for r in records:
            # Check if this locality already exists for this district
            existing = db.query(OfficialCircleRate).filter(
                OfficialCircleRate.district == r["district"],
                OfficialCircleRate.locality == r["locality"],
                OfficialCircleRate.property_type == r["property_type"]
            ).first()

            if existing:
                # Update with fresh government rate
                existing.rate_sqm = r["rate_sqm"]
                existing.tehsil = r["tehsil"]
                existing.effective_date = datetime.datetime.combine(r["effective_date"], datetime.time())
                skipped += 1
            else:
                new_record = OfficialCircleRate(
                    district=r["district"],
                    tehsil=r["tehsil"],
                    locality=r["locality"],
                    property_type=r["property_type"],
                    rate_sqm=r["rate_sqm"],
                    effective_date=datetime.datetime.combine(r["effective_date"], datetime.time())
                )
                db.add(new_record)
                inserted += 1

        db.commit()
        print(f"  ✅ Inserted: {inserted} | Updated: {skipped}")
    except Exception as e:
        db.rollback()
        print(f"  ❌ DB Error: {e}")
    finally:
        db.close()


def run():
    print("🛰️  IGRS PDF Parser — TerraSight Intelligence Pipeline")
    print("=" * 55)

    if not os.path.exists(PDF_ROOT):
        print(f"❌ PDF root directory not found: {PDF_ROOT}")
        return

    total_records = 0

    # Iterate over each district folder
    for district_name in os.listdir(PDF_ROOT):
        district_path = os.path.join(PDF_ROOT, district_name)
        if not os.path.isdir(district_path):
            continue

        print(f"\n📁 District: {district_name}")
        district_records = []

        # Iterate over each PDF in the district folder
        for pdf_file in sorted(os.listdir(district_path)):
            if not pdf_file.lower().endswith('.pdf'):
                continue

            pdf_path = os.path.join(district_path, pdf_file)
            tehsil = get_tehsil_from_filename(pdf_file)
            records = extract_rates_from_pdf(pdf_path, district_name, tehsil)
            district_records.extend(records)
            print(f"    → {tehsil}: {len(records)} localities extracted")

        if district_records:
            print(f"  💾 Loading {len(district_records)} records into database...")
            load_into_db(district_records)
            total_records += len(district_records)
        else:
            print(f"  ⚠️  No records extracted for {district_name}")

    print(f"\n🎉 Done! Total records processed: {total_records}")
    print("Run your TerraSight backend now for live accurate rates!")


if __name__ == "__main__":
    run()
