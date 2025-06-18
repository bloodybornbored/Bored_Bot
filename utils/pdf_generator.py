from fpdf import FPDF
import json
from datetime import datetime

def generate_pdf(log_path="db.json", output_path="report.pdf"):
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = []

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Отчёт от {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True)

    if not data:
        pdf.cell(200, 10, txt="Нет записей.", ln=True)
    else:
        for entry in data[-50:]:
            timestamp = entry.get("timestamp", "")[:19].replace("T", " ")
            line = f"[{timestamp}] {entry['type'].capitalize()}: {entry['content']}"
            pdf.multi_cell(0, 10, txt=line)

    pdf.output(output_path)
    return output_path
