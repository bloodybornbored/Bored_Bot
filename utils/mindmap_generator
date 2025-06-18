import json
from graphviz import Digraph

def generate_mindmap():
    try:
        with open("db.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = []

    categories = {}
    for entry in data:
        cat = entry["type"].capitalize()
        categories.setdefault(cat, []).append(entry["content"])

    dot = Digraph(comment="Mind Map")
    dot.attr(rankdir='LR')
    dot.node("MindMap", "📘 My Tracker")

    for cat, items in categories.items():
        dot.node(cat, cat)
        dot.edge("MindMap", cat)
        for i, item in enumerate(items):
            node_id = f"{cat}_{i}"
            dot.node(node_id, item[:40])  # обрезаем длинные строки
            dot.edge(cat, node_id)

    output_path = "mindmap.pdf"
    dot.render("mindmap", format="pdf", cleanup=True)
    return output_path
