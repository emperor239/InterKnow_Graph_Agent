from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from backend.models.llm_graph_builder import build_knowledge_graph

router = FastAPI()
templates = Jinja2Templates(directory="frontend/templates")
router.mount("/frontend/static", StaticFiles(directory="frontend/static"), name="frontend/static")

# 功能路由
@router.post("/api/add")
async def add_numbers(request: Request):
    try:
        data = await request.json()
        num1 = float(data.get("num1", 0))
        num2 = float(data.get("num2", 0))
        import asyncio
        await asyncio.sleep(10) 
        
        result = num1 + num2
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}, 400

@router.post("/api/subtract")
async def subtract_numbers(request: Request):
    try:
        data = await request.json()
        num1 = float(data.get("num1", 0))
        num2 = float(data.get("num2", 0))
        
        import asyncio
        await asyncio.sleep(10)
        
        result = num1 - num2
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}, 400

@router.post("/api/graph")
async def build_graph(request: Request):
    try:
        data = await request.json()
        concept = (data.get("concept") or "").strip()
        if not concept:
            return {"error": "empty concept", "nodes": [], "links": []}

        # original_data = build_knowledge_graph(concept)
        original_data = {
  "nodes": [
    {"id": "p1", "name": "热力学熵", "category": "物理学", "discipline": "物理", "value": 1},
    {"id": "p2", "name": "熵增定律", "category": "物理学", "discipline": "物理", "value": 1},
    {"id": "m1", "name": "香农熵", "category": "数学", "discipline": "数学", "value": 3},
    {"id": "m2", "name": "相对熵", "category": "数学", "discipline": "数学", "value": 1},
    {"id": "c1", "name": "熵编码", "category": "计算机科学", "discipline": "计算机", "value": 1},
    {"id": "c2", "name": "特征选择", "category": "计算机科学", "discipline": "计算机", "value": 2},
    {"id": "b1", "name": "生物熵", "category": "生物学", "discipline": "生物", "value": 1},
    {"id": "b2", "name": "耗散结构", "category": "生物学", "discipline": "生物", "value": 1},
    {"id": "s1", "name": "社会熵", "category": "哲学/社会科学", "discipline": "社会学", "value": 2},
    {"id": "s2", "name": "熵增哲学", "category": "哲学/社会科学", "discipline": "社会学", "value": 1}
  ],
  "links": [
    {"source": "m1", "target": "c1", "relation": "提供理论基础", "label": "提供理论基础", "name": "提供理论基础", "relation_short": "提供理论基础", "edge_label": "提供理论基础"},
    {"source": "m1", "target": "c2", "relation": "用于特征选择", "label": "用于特征选择", "name": "用于特征选择", "relation_short": "用于特征选择", "edge_label": "用于特征选择"},
    {"source": "p2", "target": "s1", "relation": "类比推导来源", "label": "类比推导来源", "name": "类比推导来源", "relation_short": "类比推导来源", "edge_label": "类比推导来源"},
    {"source": "m1", "target": "s1", "relation": "类比度量无序程度", "label": "类比度量无序程度", "name": "类比度量无序程度", "relation_short": "类比度量无序程度", "edge_label": "类比度量无序程度"},
    {"source": "m2", "target": "c2", "relation": "用于差异度量", "label": "用于差异度量", "name": "用于差异度量", "relation_short": "用于差异度量", "edge_label": "用于差异度量"}
  ],
  "warnings": ["content_check: filtered 4 low-quality relations"]
}
        nodes=[]
        links=[]
        for node in original_data["nodes"]:
            nodes.append({"id":node["id"],"name":node["name"],"discipline":node["discipline"],"value":node["value"]})
        for link in original_data["links"]:
            links.append({"source":link["source"],"target":link["target"],"relation":link["relation"]})
        graph={"nodes":nodes, "links":links}
        print(graph)
        return 0

    except Exception as e:
        return {"error": str(e), "nodes": [], "links": []}

# 页面路由
@router.get("/index.html", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/favicon.ico")
async def favicon():
    return Response(status_code=200)

@router.get("/graph.html", response_class=HTMLResponse)
async def calculator2(request: Request):
    return templates.TemplateResponse("graph.html", {"request": request})

@router.get("/technologies.html", response_class=HTMLResponse)
async def calculator2(request: Request):
    return templates.TemplateResponse("technologies.html", {"request": request})