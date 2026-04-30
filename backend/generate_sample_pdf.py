from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os

def generate_sample_pdf(filepath):
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    
    elements.append(Paragraph("OFFICIAL CIRCLE RATE EVALUATION LIST", title_style))
    elements.append(Paragraph("Department of Stamps and Registration, Government of Uttar Pradesh", styles['Normal']))
    elements.append(Paragraph("Notification No: IGRS-2023/4521", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Table Data
    data = [
        ["S.No", "District", "Tehsil", "Locality / Ward", "Property Type", "Rate per Sq.M (Rs)", "Effective Date"],
        ["1", "Lucknow", "Lucknow", "Gomti Nagar", "Residential", "6500", "2023-08-01"],
        ["2", "Lucknow", "Lucknow", "Gomti Nagar", "Commercial", "20100", "2023-08-01"],
        ["3", "Lucknow", "Lucknow", "Indira Nagar", "Residential", "5200", "2023-08-01"],
        ["4", "Lucknow", "Bakshi Ka Talab", "Sitapur Road", "Commercial", "14300", "2023-08-01"],
        ["5", "Noida", "Gautam Buddha Nagar", "Sector 18", "Commercial", "35000", "2023-08-01"],
        ["6", "Noida", "Gautam Buddha Nagar", "Sector 62", "Residential", "12500", "2023-08-01"],
        ["7", "Varanasi", "Varanasi", "Assi Ghat", "Commercial", "18000", "2023-08-01"],
        ["8", "Kanpur", "Kanpur Nagar", "Civil Lines", "Residential", "8900", "2023-08-01"],
        ["9", "Agra", "Agra", "Tajganj", "Commercial", "22000", "2023-08-01"],
        ["10", "Ghaziabad", "Ghaziabad", "Indirapuram", "Residential", "11000", "2023-08-01"],
    ]
    
    # Create Table
    t = Table(data, colWidths=[30, 60, 80, 100, 80, 80, 70])
    
    # Add Style
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(t)
    doc.build(elements)

if __name__ == "__main__":
    os.makedirs("../data", exist_ok=True)
    pdf_path = "../data/sample_igrs_rates.pdf"
    generate_sample_pdf(pdf_path)
    print(f"Sample PDF generated at: {pdf_path}")
