import main, asyncio
from database import SessionLocal

db = SessionLocal()
res = main.get_circle_rates('Gomti Nagar, Lucknow, Uttar Pradesh, 226010, India', db)
print(res)
