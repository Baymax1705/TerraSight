"""Quick diagnostic to check if PDFs are text-based or image-based (scanned)."""
import pdfplumber
import os

pdf_path = r"C:\Users\yashv\Desktop\TerraSight\data\pdfs\Lucknow\RateList_227_01-08-2025.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    text = page.extract_text()
    tables = page.extract_tables()
    
    print("=== TEXT EXTRACTED (first 500 chars) ===")
    print(repr(text[:500]) if text else ">>> NO TEXT FOUND — This is a scanned image PDF!")
    
    print("\n=== TABLES FOUND ===")
    print(f"Number of tables: {len(tables)}")
    if tables:
        print("First table sample:", tables[0][:3])
    else:
        print(">>> NO TABLES FOUND")
        
    print("\n=== PAGE IMAGES ===")
    print(f"Number of images on page: {len(page.images)}")
