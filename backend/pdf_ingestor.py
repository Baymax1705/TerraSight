import pdfplumber
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, OfficialCircleRate
import datetime

def ingest_pdf(pdf_path: str):
    print(f"Reading PDF: {pdf_path}")
    extracted_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"Scanning page {i+1}...")
            # Extract tables
            table = page.extract_table()
            if table:
                # Assuming first row is header
                headers = [h.replace('\n', ' ').strip() if h else '' for h in table[0]]
                print(f"Found headers: {headers}")
                
                # Check if it matches our expected format
                if "Locality / Ward" in headers or "Locality" in headers:
                    # Extract rows
                    for row in table[1:]:
                        if not row or not row[1]: # Skip empty rows
                            continue
                            
                        # Map columns based on our sample
                        # S.No | District | Tehsil | Locality / Ward | Property Type | Rate per Sq.M (Rs) | Effective Date
                        try:
                            record = {
                                "district": row[1].strip(),
                                "tehsil": row[2].strip(),
                                "locality": row[3].strip(),
                                "property_type": row[4].strip(),
                                "rate_sqm": float(row[5].replace(',', '').strip()),
                                "effective_date": datetime.datetime.strptime(row[6].strip(), "%Y-%m-%d")
                            }
                            extracted_data.append(record)
                        except Exception as e:
                            print(f"Failed to parse row: {row}. Error: {e}")

    print(f"Successfully extracted {len(extracted_data)} records from PDF.")
    
    if not extracted_data:
        print("No valid data found.")
        return
        
    print("Saving to database...")
    db: Session = SessionLocal()
    try:
        inserted = 0
        for data in extracted_data:
            # Check if exists to avoid duplicates
            exists = db.query(OfficialCircleRate).filter(
                OfficialCircleRate.district == data["district"],
                OfficialCircleRate.locality == data["locality"],
                OfficialCircleRate.property_type == data["property_type"]
            ).first()
            
            if not exists:
                new_rate = OfficialCircleRate(**data)
                db.add(new_rate)
                inserted += 1
            else:
                # Update existing
                exists.rate_sqm = data["rate_sqm"]
                exists.effective_date = data["effective_date"]
                inserted += 1
                
        db.commit()
        print(f"Success! {inserted} records processed and synced to the database.")
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import os
    target_pdf = "../data/sample_igrs_rates.pdf"
    if os.path.exists(target_pdf):
        ingest_pdf(target_pdf)
    else:
        print(f"Error: {target_pdf} not found. Run generate_sample_pdf.py first.")
