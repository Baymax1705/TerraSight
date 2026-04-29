import csv
import datetime
from sqlalchemy.orm import Session
from database import engine, SessionLocal, OfficialCircleRate, Base

def load_csv_to_db(filepath: str):
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Clear existing data to avoid duplicates for now
            db.query(OfficialCircleRate).delete()
            
            count = 0
            for row in reader:
                try:
                    date_obj = datetime.datetime.strptime(row['effective_date'], "%Y-%m-%d")
                except:
                    date_obj = datetime.datetime.utcnow()

                rate = OfficialCircleRate(
                    district=row['district'].strip(),
                    tehsil=row['tehsil'].strip(),
                    locality=row['locality'].strip(),
                    property_type=row['property_type'].strip(),
                    rate_sqm=float(row['rate_sqm']),
                    effective_date=date_obj
                )
                db.add(rate)
                count += 1
                
            db.commit()
            print(f"Successfully loaded {count} precision circle rates into the database!")
            
    except Exception as e:
        db.rollback()
        print(f"Error loading CSV: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    csv_path = "../data/lucknow_circle_rates_seed.csv"
    print(f"Starting ETL load from {csv_path}...")
    load_csv_to_db(csv_path)
