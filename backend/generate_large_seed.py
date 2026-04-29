import csv
import random

districts = {
    "Lucknow": {"tehsils": ["Sadar", "BKT", "Sarojini Nagar", "Mohanlalganj", "Malihabad"], "base": 5000, "localities": ["Nagar", "Vihar", "Puram", "Ganj", "Bagh", "Khand", "Enclave", "City", "Colony", "Road"]},
    "Noida": {"tehsils": ["Gautam Buddha Nagar", "Dadri", "Jewar"], "base": 12000, "localities": ["Sector ", "Phase ", "Extension ", "Tech Zone ", "Expressway "]},
    "Kanpur": {"tehsils": ["Kanpur Nagar", "Bilhaur", "Ghatampur"], "base": 4500, "localities": ["Nagar", "Kheda", "Pur", "Ganj", "Ghat", "Chauraha"]},
    "Varanasi": {"tehsils": ["Varanasi", "Pindra", "Raja Talab"], "base": 6000, "localities": ["Ghat", "Nagar", "Market", "Khand", "Colony", "Pur"]},
    "Agra": {"tehsils": ["Agra", "Fatehabad", "Kiraoli"], "base": 4000, "localities": ["Bagh", "Ganj", "Nagar", "Market", "Vihar", "Khand"]},
    "Prayagraj": {"tehsils": ["Sadar", "Karchhana", "Phulpur"], "base": 5500, "localities": ["Nagar", "Ganj", "Katra", "Chowk", "Road", "Puram"]},
    "Meerut": {"tehsils": ["Meerut", "Sardhana", "Mawana"], "base": 4500, "localities": ["Nagar", "Vihar", "Enclave", "City", "Road"]},
    "Ghaziabad": {"tehsils": ["Ghaziabad", "Modinagar", "Loni"], "base": 10000, "localities": ["Sector ", "Khand ", "Puram ", "Nagar", "Vihar", "Extension"]},
    "Bareilly": {"tehsils": ["Bareilly", "Aonla", "Faridpur"], "base": 3500, "localities": ["Nagar", "Ganj", "Pur", "Vihar", "Colony"]},
    "Aligarh": {"tehsils": ["Koil", "Atrauli", "Khair"], "base": 3800, "localities": ["Nagar", "Vihar", "Gate", "Road", "Market"]},
    "Gorakhpur": {"tehsils": ["Gorakhpur", "Campierganj", "Sahjanwa"], "base": 4000, "localities": ["Nagar", "Pur", "Ganj", "Vihar", "Chowk"]},
    "Ayodhya": {"tehsils": ["Sadar", "Bikapur", "SoHawal"], "base": 4500, "localities": ["Nagar", "Pur", "Ghat", "Market", "Khand"]}
}

prefixes = ["Shiv", "Ram", "Shyam", "Laxmi", "Krishna", "Gandhi", "Nehru", "Patel", "Shastri", "Indira", "Rajiv", "Subhash", "Arya", "Gomti", "Ganga", "Yamuna", "Saraswati", "Vivekananda", "Azad", "Tagore", "Ashok", "Kalyan", "Govind", "Saket", "Vasant"]

data = []
# Keep the existing specific ones
existing = [
    ("Lucknow","Sadar","Gomti Nagar","Residential",6500),
    ("Lucknow","Sadar","Hazratganj","Commercial",15000),
    ("Noida","Gautam Buddha Nagar","Sector 18","Commercial",35000),
    ("Kanpur","Kanpur Nagar","Swaroop Nagar","Residential",8500),
    ("Varanasi","Varanasi","Lanka","Residential",7500),
]

for e in existing:
    data.append({
        "district": e[0],
        "tehsil": e[1],
        "locality": e[2],
        "property_type": e[3],
        "rate_sqm": e[4],
        "effective_date": "2023-08-01"
    })

# Generate 1000 records
for dist, info in districts.items():
    for _ in range(80): # 80 per district = ~960 records
        tehsil = random.choice(info["tehsils"])
        suffix = random.choice(info["localities"])
        
        if "Sector" in suffix or "Phase" in suffix:
            loc_name = f"{suffix}{random.randint(1, 150)}"
        else:
            loc_name = f"{random.choice(prefixes)} {suffix}"
            
        prop_type = random.choices(["Residential", "Commercial", "Agricultural"], weights=[60, 30, 10])[0]
        
        multiplier = 1.0
        if prop_type == "Commercial": multiplier = 2.5
        if prop_type == "Agricultural": multiplier = 0.3
        
        # Add random variance
        variance = random.uniform(0.8, 1.5)
        rate = int(info["base"] * multiplier * variance / 100) * 100 # Round to nearest 100
        
        # Prevent exact duplicates
        if not any(d['district'] == dist and d['locality'] == loc_name for d in data):
            data.append({
                "district": dist,
                "tehsil": tehsil,
                "locality": loc_name,
                "property_type": prop_type,
                "rate_sqm": rate,
                "effective_date": "2023-08-01"
            })

with open("../data/lucknow_circle_rates_seed.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["district", "tehsil", "locality", "property_type", "rate_sqm", "effective_date"])
    writer.writeheader()
    writer.writerows(data)

print(f"Generated {len(data)} records!")
