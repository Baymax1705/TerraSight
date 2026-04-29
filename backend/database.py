from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./geointel.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class CachedRate(Base):
    __tablename__ = "cached_rates"

    id = Column(Integer, primary_key=True, index=True)
    location_query = Column(String, unique=True, index=True)
    estimated_rate_sqm = Column(Integer)
    growth_potential = Column(String)
    risk_factors = Column(String)
    smart_insight = Column(String)
    source = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class OfficialCircleRate(Base):
    """
    Granular, exact government circle rates loaded via ETL pipeline.
    """
    __tablename__ = "official_circle_rates"

    id = Column(Integer, primary_key=True, index=True)
    district = Column(String, index=True)      # e.g., "Lucknow"
    tehsil = Column(String, index=True)        # e.g., "Sadar"
    locality = Column(String, index=True)      # e.g., "Gomti Nagar", "Indira Nagar"
    property_type = Column(String)             # "Residential", "Commercial", "Agricultural"
    rate_sqm = Column(Float)                   # Exact government rate per sq meter
    effective_date = Column(DateTime)          # When the rate list was published

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
