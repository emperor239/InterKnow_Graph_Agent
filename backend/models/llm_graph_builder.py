import os
import json
import re
from typing import List, Dict, Any, Optional, Set
from volcenginesdkarkruntime import Ark

BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# 优先从环境变量读，避免把 Key 写死进仓库
# 仍保留旧常量作为 fallback
API_KEY = os.getenv("VOLC_ARK_API_KEY", "1f0dfbb6-494f-4378-9662-37d0d563891a")
MODEL_ID = os.getenv("VOLC_ARK_MODEL", "ep-20260117135142-6pp26")

# 规模限制：防止乱喷
MAX_NODES = 30
MAX_LINKS = 60

# 幻觉校验（内容层）相关参数
MIN_DISCIPLINES = 3          # 至少覆盖 3 个学科（跨学科基本要求）
MIN_VALID_LINKS = 5          # 至少保留 5 条有效边，否则认为图谱太“空”
MIN_RELATION_LEN = 4         # 关系描述太短通常没信息量
MAX_RELATION_LEN = 40        # 过长可能在灌水
MAX_GENERIC_REL_RATIO = 0.5  # 空泛关系占比超过 50% 认为低质量
MIN_CROSS_DISCIPLINE_EDGE_RATIO = 0.30  # 跨学科边比例最低要求

# 空泛关系（典型“幻觉式废话”）
GENERIC_REL_PATTERNS = [
    r"有关", r"相关", r"联系", r"关系", r"影响", r"作用", r"涉及", r"包含", r"属于",
    r"是一种", r"一种", r"类似", r"相似", r"相互", r"关联"
]

# 较“有信息量”的关系关键词（不是严格规则，只做弱约束）
INFORMATIVE_REL_KEYWORDS = [
    "用于", "导致", "推导", "定义", "推广", "对应", "解释", "建模", "优化", "学习",
    "编码", "度量", "估计", "约束", "预测", "控制", "演化", "证明", "依赖", "实现"
]

# 模型的“允许学科”白名单（用于约束输出）
DISCIPLINES = ["数学", "物理学", "计算机科学", "生物学", "哲学/社会科学"]

# 统一映射：保证图例一致（前端用 discipline）
DISCIPLINE_ALIAS = {
    "数学": "数学",
    "物理学": "物理",
    "计算机科学": "计算机",
    "生物学": "生物",
    "哲学/社会科学": "社会学",
    # 兼容一些可能出现的变体（尽量不丢节点）
    "社会科学": "社会学",
    "哲学": "社会学",
    "社会学": "社会学",
    "计算机": "计算机",
    "物理": "物理",
    "生物": "生物",
}

def _prompt(concept: str) -> str:
    return f"""
你是“跨学科知识图谱构建”智能体。给定核心概念：{concept}

任务：强制从不同学科（{", ".join(DISCIPLINES)}）挖掘相关概念，并构建知识图谱。

输出必须是严格 JSON（不要 markdown，不要解释，不要多余文本），格式如下：
{{
  "nodes": [
    {{"id": "unique_id", "name": "概念名", "category": "学科"}}
  ],
  "links": [
    {{"source": "node_id", "target": "node_id", "relation": "关系描述"}}
  ]
}}

硬性约束：
1) nodes 数量 <= {MAX_NODES}；links 数量 <= {MAX_LINKS}
2) node.id 必须唯一；links 的 source/target 必须存在于 nodes.id
3) category 必须来自这几个学科之一：{DISCIPLINES}
4) 关系要“跨学科”合理：不要牵强附会；不确定就不要编
5) 至少输出 5 个节点、5 条边（如果概念过于冷门，允许少一些，但要尽量给出）
6) relation 建议为 6~12 字的短语，避免长句；例如：“用于特征选择”“理论基础”“类比度量”“推导来源”

现在开始输出 JSON：
""".strip()

def _stronger_prompt_for_regen(concept: str, reason: str) -> str:
    """
    当内容层校验失败（跨学科覆盖不足/关系太空泛等）时，用更强约束重新生成一次。
    注意：这不是 repair JSON，是“重新生成更高质量的图谱”。
    """
    return f"""
你刚才生成的知识图谱质量不达标（原因：{reason}）。

请重新生成更高质量的跨学科知识图谱，并严格满足：
- 必须覆盖至少 {MIN_DISCIPLINES} 个不同学科（从 {DISCIPLINES} 中选）
- links 的 relation 必须具体、有信息量，避免“有关/相关/联系/影响/作用”等空泛表述
- 每条 relation 尽量用“动词短语”说明机制或用途（例如：用于、推导、定义、建模、优化、解释、预测…）
- nodes <= {MAX_NODES}, links <= {MAX_LINKS}
- node.id 唯一，links 的 source/target 必须存在于 nodes.id
- 只输出严格 JSON，不要任何解释

核心概念：{concept}

现在只输出 JSON：
""".strip()

def _extract_json(text: str) -> Dict[str, Any]:
    """
    兼容模型偶尔在 JSON 外面夹杂文字：尽量把 JSON 对象抠出来再 parse。
    """
    try:
        return json.loads(text)
    except Exception:
        pass

    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("No JSON object found in model output")
    return json.loads(m.group(0))

def _normalize_discipline(cat: str) -> Optional[str]:
    cat = (cat or "").strip()
    if not cat:
        return None

    if cat not in DISCIPLINES:
        if cat in DISCIPLINE_ALIAS:
            return DISCIPLINE_ALIAS[cat]
        return None

    return DISCIPLINE_ALIAS.get(cat, cat)

def _compute_node_values(nodes: List[Dict[str, Any]], links: List[Dict[str, Any]]) -> Dict[str, int]:
    deg = {n["id"]: 0 for n in nodes}
    for e in links:
        s = e.get("source")
        t = e.get("target")
        if s in deg:
            deg[s] += 1
        if t in deg:
            deg[t] += 1

    for k in list(deg.keys()):
        deg[k] = max(1, deg[k])
    return deg

def _is_generic_relation(rel: str) -> bool:
    rel = (rel or "").strip()
    if not rel:
        return True
    for pat in GENERIC_REL_PATTERNS:
        if re.search(pat, rel):
            return True
    return False

def _is_informative_relation(rel: str) -> bool:
    rel = (rel or "").strip()
    if len(rel) < MIN_RELATION_LEN or len(rel) > MAX_RELATION_LEN:
        return False

    # 过于空泛直接否
    if _is_generic_relation(rel) and all(k not in rel for k in INFORMATIVE_REL_KEYWORDS):
        return False

    # 有信息量关键词则认为更可靠
    if any(k in rel for k in INFORMATIVE_REL_KEYWORDS):
        return True

    # 否则保守放行一部分（避免误伤）
    # 例如“X 是 Y 的基础/前提/推广”等
    if re.search(r"基础|前提|推广|对应|解释|定义|推导|建模|优化|估计|预测", rel):
        return True

    return False

def _shorten_relation(rel: str, max_len: int = 10) -> str:
    rel = (rel or "").strip()
    if not rel:
        return ""
    return rel if len(rel) <= max_len else rel[:max_len] + "…"

def _content_check(nodes: List[Dict[str, Any]], links: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    内容层幻觉校验：
    - 过滤空泛/无信息量 relation
    - 统计学科覆盖
    - 输出 warnings 与是否需要“重新生成”的判断
    """
    warnings: List[str] = []

    # 1) 过滤 relation
    kept_links: List[Dict[str, Any]] = []
    generic_cnt = 0
    for e in links:
        rel = str(e.get("relation", "")).strip()
        if not rel:
            continue
        if not _is_informative_relation(rel):
            # 认为是低信息量关系，丢掉
            if _is_generic_relation(rel):
                generic_cnt += 1
            continue
        kept_links.append(e)

    if len(kept_links) < len(links):
        warnings.append(f"content_check: filtered {len(links) - len(kept_links)} low-quality relations")

    # 记录被过滤的“空泛关系”数量
    if generic_cnt > 0:
        warnings.append(
            f"content_check: generic relations filtered = {generic_cnt}"
        )

    # 2) 学科覆盖
    disciplines: Set[str] = set()
    for n in nodes:
        d = n.get("discipline")
        if isinstance(d, str) and d.strip():
            disciplines.add(d.strip())

    if len(disciplines) < MIN_DISCIPLINES:
        warnings.append(
            f"content_check: discipline coverage too low ({len(disciplines)}<{MIN_DISCIPLINES}), disciplines={sorted(disciplines)}"
        )
    
    # 跨学科边比例检查：source.discipline != target.discipline
    id2disc = {n.get("id"): n.get("discipline") for n in nodes if isinstance(n.get("id"), str)}
    cross_cnt = 0
    edge_cnt = 0
    for e in kept_links:  # 用“过滤后的高质量边”来统计更合理
        s = e.get("source")
        t = e.get("target")
        if s not in id2disc or t not in id2disc:
            continue
        ds = id2disc.get(s)
        dt = id2disc.get(t)
        if not isinstance(ds, str) or not isinstance(dt, str):
            continue
        edge_cnt += 1
        if ds != dt:
            cross_cnt += 1

    cross_ratio = (cross_cnt / edge_cnt) if edge_cnt > 0 else 0.0
    if edge_cnt > 0 and cross_ratio < MIN_CROSS_DISCIPLINE_EDGE_RATIO:
        warnings.append(
            f"content_check: cross-discipline edge ratio too low ({cross_ratio:.2f} < {MIN_CROSS_DISCIPLINE_EDGE_RATIO}), "
            f"cross={cross_cnt}/{edge_cnt}"
        )

    # 3) 空泛关系占比（基于过滤后的高质量边）
    generic_ratio = generic_cnt / max(1, len(kept_links))
    if generic_ratio > MAX_GENERIC_REL_RATIO:
        warnings.append(
            f"content_check: too many generic relations after filtering "
            f"(ratio={generic_ratio:.2f} > {MAX_GENERIC_REL_RATIO})"
        )

    # 4) 低边数也认为质量不足
    if len(kept_links) < MIN_VALID_LINKS:
        warnings.append(
            f"content_check: too few valid links after filtering ({len(kept_links)}<{MIN_VALID_LINKS})"
        )

    need_regen = (
        len(disciplines) < MIN_DISCIPLINES
        or generic_ratio > MAX_GENERIC_REL_RATIO
        or len(kept_links) < MIN_VALID_LINKS
        or (edge_cnt > 0 and cross_ratio < MIN_CROSS_DISCIPLINE_EDGE_RATIO)
    )

    reason = "; ".join(warnings) if warnings else ""
    return {
        "links": kept_links,
        "warnings": warnings,
        "need_regen": need_regen,
        "reason": reason,
    }

def _validate_and_fix(graph: Dict[str, Any]) -> Dict[str, Any]:
    """
    结构层校验
    """
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])

    if not isinstance(nodes, list) or not isinstance(links, list):
        raise ValueError("Invalid graph structure: nodes/links must be lists")

    nodes = nodes[:MAX_NODES]
    links = links[:MAX_LINKS]

    seen = set()
    cleaned_nodes: List[Dict[str, Any]] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id", "")).strip()
        name = str(n.get("name", "")).strip()
        cat = str(n.get("category", "")).strip()

        if not nid or not name:
            continue
        if nid in seen:
            continue

        discipline = _normalize_discipline(cat)
        if discipline is None:
            continue

        seen.add(nid)
        cleaned_nodes.append({
            "id": nid,
            "name": name,
            "category": cat,
            "discipline": discipline,
        })

    node_ids = {n["id"] for n in cleaned_nodes}

    cleaned_links: List[Dict[str, Any]] = []
    for e in links:
        if not isinstance(e, dict):
            continue
        s = str(e.get("source", "")).strip()
        t = str(e.get("target", "")).strip()
        r = str(e.get("relation", "")).strip()

        if not s or not t or not r:
            continue
        if s not in node_ids or t not in node_ids:
            continue

        short_r = _shorten_relation(r, max_len=10)
        cleaned_links.append({
            "source": s,
            "target": t,
            "relation": r,
            "label": r,
            "name": r,
            "relation_short": short_r,
            "edge_label": short_r,
        })

    return {"nodes": cleaned_nodes, "links": cleaned_links}

def extract_text_from_ark_response(resp) -> str:
    for attr in ("output_text", "text"):
        if hasattr(resp, attr):
            val = getattr(resp, attr)
            if isinstance(val, str) and val.strip():
                return val.strip()

    output = getattr(resp, "output", None)
    if isinstance(output, list):
        texts = []
        for item in output:
            content = getattr(item, "content", None)
            if content is None and isinstance(item, dict):
                content = item.get("content")

            if isinstance(content, list):
                for c in content:
                    t = getattr(c, "text", None)
                    if t is None and isinstance(c, dict):
                        t = c.get("text")
                    if isinstance(t, str) and t.strip():
                        texts.append(t.strip())

            t2 = getattr(item, "text", None)
            if isinstance(t2, str) and t2.strip():
                texts.append(t2.strip())

        if texts:
            return "\n".join(texts).strip()

    return str(resp).strip()

def _force_json_repair_prompt(bad_text: str) -> str:
    return f"""
你刚才的输出不是严格 JSON，导致程序解析失败。

请你把下面内容“改写”为严格 JSON，只允许输出 JSON（不要解释，不要 markdown）。
JSON 格式必须是：
{{
  "nodes": [{{"id":"...","name":"...","category":"数学/物理学/计算机科学/生物学/哲学/社会科学"}}],
  "links": [{{"source":"...","target":"...","relation":"..."}}]
}}
并满足：nodes<={MAX_NODES}，links<={MAX_LINKS}，id唯一，source/target必须存在于nodes。

下面是刚才的原始输出（请基于它改写）：
{bad_text}
""".strip()

def build_knowledge_graph(concept: str) -> Dict[str, Any]:
    concept = (concept or "").strip()
    if not concept:
        return {"error": "empty concept", "nodes": [], "links": []}

    if not API_KEY or not MODEL_ID:
        return {"error": "missing VOLC_ARK_API_KEY or VOLC_ARK_MODEL", "nodes": [], "links": []}

    client = Ark(base_url=BASE_URL, api_key=API_KEY)

    model_text: Optional[str] = None

    def _call_once(prompt_text: str) -> str:
        resp = client.responses.create(
            model=MODEL_ID,
            input=[{"role": "user", "content": [{"type": "input_text", "text": prompt_text}]}],
        )
        return extract_text_from_ark_response(resp)

    # 1) 第一次生成
    try:
        model_text = _call_once(_prompt(concept))
        graph_raw = _extract_json(model_text)
        graph = _validate_and_fix(graph_raw)

        # 2) 内容层校验（幻觉校验）
        cc = _content_check(graph["nodes"], graph["links"])
        graph["links"] = cc["links"]

        # 补 value（度数）放在内容层过滤之后
        values = _compute_node_values(graph["nodes"], graph["links"])
        for n in graph["nodes"]:
            n["value"] = values.get(n["id"], 1)

        # warnings 不影响前端，可用于报告/日志
        if cc["warnings"]:
            graph["warnings"] = cc["warnings"]

        # 3) 若内容层判定质量不足：重新生成一次（更强约束）
        if cc["need_regen"]:
            regen_prompt = _stronger_prompt_for_regen(concept, cc["reason"] or "content_check_failed")
            model_text_regen = _call_once(regen_prompt)

            graph_raw2 = _extract_json(model_text_regen)
            graph2 = _validate_and_fix(graph_raw2)

            cc2 = _content_check(graph2["nodes"], graph2["links"])
            graph2["links"] = cc2["links"]

            values2 = _compute_node_values(graph2["nodes"], graph2["links"])
            for n in graph2["nodes"]:
                n["value"] = values2.get(n["id"], 1)

            if cc2["warnings"]:
                graph2["warnings"] = cc2["warnings"]

            # 如果第二次更好（更多有效边 & 学科覆盖更高），就用第二次
            def _score(g: Dict[str, Any]) -> int:
                # 优先选择“有效边更多、学科覆盖更广”的图谱
                dset = {n.get("discipline") for n in g.get("nodes", []) if isinstance(n.get("discipline"), str)}
                return (len(g.get("links", [])) * 10) + len(dset)

            if _score(graph2) >= _score(graph):
                graph = graph2

        if len(graph["nodes"]) == 0:
            return {"error": "no valid nodes after validation", "nodes": [], "links": []}

        return graph

    # JSON 结构级失败：走 repair（仍然只用模型原始输出）
    except Exception as e1:
        if not model_text or not model_text.strip():
            return {
                "error": f"llm_output_empty_or_unreadable: {type(e1).__name__}: {e1}",
                "nodes": [],
                "links": [],
            }

        bad = model_text
        try:
            model_text2 = _call_once(_force_json_repair_prompt(bad))
            graph_raw2 = _extract_json(model_text2)
            graph2 = _validate_and_fix(graph_raw2)

            cc2 = _content_check(graph2["nodes"], graph2["links"])
            graph2["links"] = cc2["links"]

            values2 = _compute_node_values(graph2["nodes"], graph2["links"])
            for n in graph2["nodes"]:
                n["value"] = values2.get(n["id"], 1)

            if cc2["warnings"]:
                graph2["warnings"] = cc2["warnings"]

            if len(graph2["nodes"]) == 0:
                return {"error": "no valid nodes after validation", "nodes": [], "links": []}

            return graph2

        except Exception as e2:
            return {"error": f"llm_call_failed: {type(e2).__name__}: {e2}", "nodes": [], "links": []}

if __name__ == "__main__":
    print(build_knowledge_graph("熵"))