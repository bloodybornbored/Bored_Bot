# utils/pdf_generator.py
from fpdf import FPDF
import json
from datetime import datetime

def generate_pdf():
    with open("db.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Отчёт от {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(5)

    for entry in data:
        timestamp = entry.get("timestamp", "")
        content = entry.get("content", "")
        entry_type = entry.get("type", "Unknown").capitalize()
        pdf.multi_cell(0, 10, f"[{entry_type}] {timestamp}\n{content}\n")

    file_path = "report.pdf"
    pdf.output(file_path)
    return file_path


# utils/mindmap_generator.py
from graphviz import Digraph
import json
from datetime import datetime

def generate_mindmap():
    with open("db.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    dot = Digraph(comment="Mind Map")
    root = f"📊 Трекинг {datetime.now().strftime('%Y-%m-%d')}"
    dot.node("root", root)

    categories = {}
    for entry in data:
        cat = entry["type"].capitalize()
        if cat not in categories:
            node_id = f"cat_{cat}"
            categories[cat] = node_id
            dot.node(node_id, cat)
            dot.edge("root", node_id)

        content = entry["content"][:50].replace("\n", " ")
        leaf_id = f"{categories[cat]}_{len(dot.body)}"
        dot.node(leaf_id, content)
        dot.edge(categories[cat], leaf_id)

    file_path = "mindmap.pdf"
    dot.render("mindmap", format="pdf", cleanup=True)
    return file_path
