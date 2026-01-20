import json
import sys
import os
sys.path.append(os.getcwd())
from backend.models.llm_graph_builder import build_knowledge_graph

g = build_knowledge_graph("熵")  # 可以换成别的概念
with open("sample_data.json", "w", encoding="utf-8") as f:
    json.dump(g, f, ensure_ascii=False, indent=2)

print("saved to sample_data.json")