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

        original_data = build_knowledge_graph(concept)
        nodes=[]
        links=[]
        for node in original_data["nodes"]:
            nodes.append({"id":node["id"],"name":node["name"],"discipline":node["discipline"],"value":node["value"],"description":node["description"]})
        for link in original_data["links"]:
            sourseName = [node["name"] for node in original_data["nodes"] if node["id"] == link["source"]]
            targetName = [node["name"] for node in original_data["nodes"] if node["id"] == link["target"]]
            links.append({"source":link["source"],"target":link["target"],"sourseName":sourseName,"targetName":targetName,"relation":link["relation"],"description":link["description"]})
        graph={"nodes":nodes, "links":links}
        # print(graph)
        return graph

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