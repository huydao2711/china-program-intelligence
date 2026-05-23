"""
agents/ecosystem_agent.py
Build ecosystem map: nodes (orgs, universities, programs, regions),
edges (funds, organizes, distributes, hosts, reports_to, partners).
Outputs Mermaid graph + JSON relationship DB.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import json
from datetime import datetime
from pathlib import Path
from config import ECOSYSTEM_DIR, WEIXIN_ACCOUNTS, UNIVERSITIES, REPORTS_DIR, VIZ_DIR

ECOSYSTEM_DIR.mkdir(parents=True, exist_ok=True)
VIZ_DIR.mkdir(parents=True, exist_ok=True)

# ── Static Knowledge Graph (from research + article analysis) ─────────────────

KNOWN_NODES = [
    # Government
    {"id": "MOE",   "label": "国务院/教育部", "type": "government", "region": "China", "tier": 0},
    {"id": "CHDEC", "label": "中国华文教育发展中心", "type": "government_agency", "region": "China", "tier": 0},
    {"id": "OCAO",  "label": "国务院侨务办公室", "type": "government", "region": "China", "tier": 0},
    {"id": "CLEF",  "label": "中国华文教育基金会", "type": "foundation", "region": "China", "tier": 1},

    # Embassies
    {"id": "EMBASSY", "label": "各驻外使领馆", "type": "embassy", "region": "Global", "tier": 1},
    {"id": "EMB_CA",  "label": "中国驻加拿大大使馆", "type": "embassy", "region": "North America", "tier": 2},
    {"id": "EMB_US",  "label": "中国驻美国大使馆",   "type": "embassy", "region": "North America", "tier": 2},
    {"id": "EMB_EU",  "label": "中国驻欧洲使领馆",   "type": "embassy", "region": "Europe", "tier": 2},
    {"id": "EMB_AU",  "label": "中国驻澳大利亚大使馆", "type": "embassy", "region": "Oceania", "tier": 2},
    {"id": "EMB_SEA", "label": "中国驻东南亚使领馆",  "type": "embassy", "region": "Southeast Asia", "tier": 2},

    # OC Specialist Universities
    {"id": "BCL",  "label": "北京华文学院",         "type": "oc_university", "region": "China", "tier": 1,
     "weixin_biz": "MjM5NjY0MTk5NQ=="},
    {"id": "JNU",  "label": "暨南大学华文学院",      "type": "oc_university", "region": "China", "tier": 1},
    {"id": "HQU",  "label": "华侨大学华文教育处",    "type": "oc_university", "region": "China", "tier": 1},

    # Elite Universities
    {"id": "THU",  "label": "清华大学",  "type": "c9_university", "region": "China", "tier": 1},
    {"id": "ZJU",  "label": "浙江大学",  "type": "c9_university", "region": "China", "tier": 1},
    {"id": "FDU",  "label": "复旦大学",  "type": "c9_university", "region": "China", "tier": 1},
    {"id": "USTC", "label": "中国科技大学", "type": "c9_university", "region": "China", "tier": 1},
    {"id": "NJU",  "label": "南京大学",  "type": "c9_university", "region": "China", "tier": 1},
    {"id": "WLU",  "label": "西湖大学",  "type": "private_elite", "region": "China", "tier": 2},
    {"id": "XJTLU","label": "西交利物浦大学", "type": "joint_intl", "region": "China", "tier": 2},
    {"id": "NPU",  "label": "西北工业大学", "type": "p985_university", "region": "China", "tier": 2},

    # Diaspora Federations
    {"id": "FCSC",    "label": "加拿大华文学校联合总会", "type": "diaspora_federation", "region": "North America",
     "weixin_biz": "MzkxNTM0Njg4MQ=="},
    {"id": "CAYAUS",  "label": "全美华裔青少年协会",      "type": "diaspora_federation", "region": "North America"},
    {"id": "EFCSA",   "label": "欧洲华文教育联合总会",    "type": "diaspora_federation", "region": "Europe"},
    {"id": "ACCSF",   "label": "澳大利亚华文学校联合会",  "type": "diaspora_federation", "region": "Oceania"},
    {"id": "DONGZONG","label": "马来西亚华校董事联合会总会", "type": "diaspora_federation", "region": "Southeast Asia"},
    {"id": "HKECE",   "label": "香港教育交流中心",        "type": "hk_org", "region": "Hong Kong"},

    # Programs
    {"id": "P001", "label": "寻根之旅夏令营",         "type": "program", "category": "cultural", "annual_participants": 2000},
    {"id": "P002", "label": "校长研习班",              "type": "program", "category": "teacher_training", "annual_participants": 400},
    {"id": "P003", "label": "华文教师研习班",          "type": "program", "category": "teacher_training", "annual_participants": 2400},
    {"id": "P006", "label": "AI华文教育培训班★",       "type": "program", "category": "ai_camp", "annual_participants": 80},
    {"id": "P007", "label": "Westlake国际科学营",       "type": "program", "category": "stem", "annual_participants": 80},
    {"id": "P008", "label": "XJTLU AI Camp",            "type": "program", "category": "ai_camp", "annual_participants": 200},
    {"id": "P009", "label": "Tsinghua SIGS暑期学校",   "type": "program", "category": "university", "annual_participants": 120},
    {"id": "P010", "label": "GRIPS联合科研实习",       "type": "program", "category": "research", "annual_participants": 50},
    {"id": "P011", "label": "Tsinghua GenAI暑期学校",  "type": "program", "category": "ai_camp", "annual_participants": 300},
    {"id": "P012", "label": "NPU国际夏令营",           "type": "program", "category": "university", "annual_participants": 150},

    # Data Infrastructure
    {"id": "DATA_REG", "label": "全球华文教育工作者注册系统", "type": "data_system", "region": "China"},
    {"id": "WECHAT_INFRA", "label": "WeChat生态基础设施",    "type": "platform",     "region": "Global"},
    {"id": "AI_TOOLS",     "label": "AI工具生态 (iFlytek/文心)", "type": "technology", "region": "China"},
]

KNOWN_EDGES = [
    # Government command chain
    {"from": "MOE",   "to": "CHDEC",   "type": "funds",       "label": "政策+资金"},
    {"from": "MOE",   "to": "OCAO",    "type": "policy",      "label": "主管"},
    {"from": "MOE",   "to": "EMBASSY", "type": "directs",     "label": "政策"},
    {"from": "OCAO",  "to": "CHDEC",   "type": "supervises",  "label": "主管"},
    {"from": "CLEF",  "to": "P003",    "type": "funds",       "label": "资助"},

    # CHDEC as orchestrator
    {"from": "CHDEC", "to": "BCL",     "type": "commissions", "label": "委托"},
    {"from": "CHDEC", "to": "JNU",     "type": "commissions", "label": "委托"},
    {"from": "CHDEC", "to": "HQU",     "type": "commissions", "label": "委托"},
    {"from": "CHDEC", "to": "P003",    "type": "organizes",   "label": "主办"},
    {"from": "CHDEC", "to": "P002",    "type": "organizes",   "label": "主办"},
    {"from": "CHDEC", "to": "P001",    "type": "organizes",   "label": "主办"},

    # University hosts programs
    {"from": "BCL",   "to": "P006",    "type": "hosts",       "label": "承办"},
    {"from": "BCL",   "to": "P003",    "type": "hosts",       "label": "承办"},
    {"from": "JNU",   "to": "P001",    "type": "hosts",       "label": "承办"},
    {"from": "WLU",   "to": "P007",    "type": "hosts",       "label": "承办"},
    {"from": "XJTLU", "to": "P008",    "type": "hosts",       "label": "承办"},
    {"from": "THU",   "to": "P009",    "type": "hosts",       "label": "承办"},
    {"from": "THU",   "to": "P011",    "type": "hosts",       "label": "承办"},
    {"from": "ZJU",   "to": "P010",    "type": "consortium",  "label": "联合"},
    {"from": "FDU",   "to": "P010",    "type": "consortium",  "label": "联合"},
    {"from": "USTC",  "to": "P010",    "type": "consortium",  "label": "联合"},
    {"from": "NJU",   "to": "P010",    "type": "consortium",  "label": "联合"},
    {"from": "NPU",   "to": "P012",    "type": "hosts",       "label": "承办"},

    # Distribution channels
    {"from": "CHDEC", "to": "FCSC",    "type": "distributes_via", "label": "通过"},
    {"from": "CHDEC", "to": "CAYAUS",  "type": "distributes_via", "label": "通过"},
    {"from": "CHDEC", "to": "EFCSA",   "type": "distributes_via", "label": "通过"},
    {"from": "CHDEC", "to": "ACCSF",   "type": "distributes_via", "label": "通过"},
    {"from": "CHDEC", "to": "DONGZONG","type": "distributes_via", "label": "通过"},
    {"from": "HKECE", "to": "P001",    "type": "distributes",     "label": "推广"},

    # Embassy control
    {"from": "EMBASSY", "to": "P003",   "type": "audits",    "label": "强制审核"},
    {"from": "EMBASSY", "to": "P002",   "type": "audits",    "label": "强制审核"},
    {"from": "EMBASSY", "to": "P006",   "type": "audits",    "label": "强制审核"},
    {"from": "EMBASSY", "to": "DATA_REG","type": "collects", "label": "注册数据"},
    {"from": "EMB_CA",  "to": "FCSC",   "type": "monitors",  "label": "监控"},

    # Technology lock-in chain
    {"from": "P006",      "to": "AI_TOOLS",      "type": "triggers",  "label": "推广使用"},
    {"from": "AI_TOOLS",  "to": "WECHAT_INFRA",  "type": "integrates","label": "集成"},
    {"from": "WECHAT_INFRA", "to": "FCSC",        "type": "platform",  "label": "WeChat公众号"},
    {"from": "WECHAT_INFRA", "to": "BCL",         "type": "platform",  "label": "WeChat公众号"},

    # Data flow
    {"from": "FCSC", "to": "DATA_REG",  "type": "feeds",    "label": "报名数据→"},
    {"from": "CAYAUS","to": "DATA_REG", "type": "feeds",    "label": "报名数据→"},
    {"from": "DATA_REG","to": "CHDEC",  "type": "informs",  "label": "全球华文教育工作者注册库"},
]


def build_mermaid_graph(nodes: list, edges: list, title: str = "China Education Ecosystem") -> str:
    type_colors = {
        "government":          "fill:#c62828,color:#fff",
        "government_agency":   "fill:#c62828,color:#fff",
        "foundation":          "fill:#e53935,color:#fff",
        "embassy":             "fill:#b71c1c,color:#fff",
        "oc_university":       "fill:#1565c0,color:#fff",
        "c9_university":       "fill:#0d47a1,color:#fff",
        "private_elite":       "fill:#283593,color:#fff",
        "joint_intl":          "fill:#1a237e,color:#fff",
        "p985_university":     "fill:#1976d2,color:#fff",
        "diaspora_federation": "fill:#2e7d32,color:#fff",
        "hk_org":              "fill:#388e3c,color:#fff",
        "program":             "fill:#e65100,color:#fff",
        "data_system":         "fill:#4a148c,color:#fff",
        "platform":            "fill:#6a1b9a,color:#fff",
        "technology":          "fill:#7b1fa2,color:#fff",
    }

    edge_type_styles = {
        "funds":          "-->|资金|",
        "commissions":    "-->|委托|",
        "hosts":          "-->|承办|",
        "organizes":      "-->|主办|",
        "distributes_via":"-->|分发|",
        "distributes":    "-->|推广|",
        "audits":         "-.->|审核|",
        "monitors":       "-.->|监控|",
        "triggers":       "-->|触发|",
        "integrates":     "-->|集成|",
        "platform":       "-->|平台|",
        "feeds":          "-->|数据|",
        "informs":        "-->|反馈|",
        "policy":         "-->|政策|",
        "directs":        "-->|指令|",
        "supervises":     "-->|主管|",
        "consortium":     "-->|联合|",
    }

    lines = ["graph TB", f'    %% {title}', ""]

    # Group nodes by type
    groups = {
        "GOVERNMENT": ["government", "government_agency"],
        "EMBASSIES":  ["embassy"],
        "UNIVERSITIES": ["oc_university", "c9_university", "private_elite", "joint_intl", "p985_university"],
        "PROGRAMS":   ["program"],
        "DISTRIBUTION": ["diaspora_federation", "hk_org"],
        "INFRASTRUCTURE": ["data_system", "platform", "technology", "foundation"],
    }

    for group_name, types in groups.items():
        group_nodes = [n for n in nodes if n.get("type") in types]
        if not group_nodes:
            continue
        lines.append(f'    subgraph {group_name}["{group_name}"]')
        for n in group_nodes:
            safe_label = n["label"].replace('"', "'")
            lines.append(f'        {n["id"]}["{safe_label}"]')
        lines.append("    end")
        lines.append("")

    # Edges
    lines.append("    %% Relationships")
    for e in edges:
        style = edge_type_styles.get(e["type"], f'-->|{e.get("label","")}|')
        lines.append(f'    {e["from"]} {style} {e["to"]}')

    # Style nodes by type
    lines.append("")
    lines.append("    %% Styling")
    for n in nodes:
        color = type_colors.get(n.get("type", ""), "fill:#9e9e9e,color:#fff")
        lines.append(f'    style {n["id"]} {color}')

    return "\n".join(lines)


def compute_influence_scores(nodes: list, edges: list) -> dict:
    """Simple in-degree + weighted influence score per node."""
    scores = {n["id"]: 0 for n in nodes}
    weights = {
        "funds": 5, "commissions": 4, "organizes": 4, "hosts": 3,
        "distributes_via": 3, "distributes": 2, "audits": 3, "monitors": 2,
        "triggers": 2, "informs": 2, "feeds": 1,
    }
    for e in edges:
        w = weights.get(e["type"], 1)
        scores[e["from"]] = scores.get(e["from"], 0) + w
    return scores


def run_ecosystem_agent() -> dict:
    print("=" * 60)
    print("[Ecosystem Agent] Building ecosystem map")

    # Merge with dynamically discovered nodes from crawlers
    all_nodes = list(KNOWN_NODES)
    all_edges = list(KNOWN_EDGES)

    # Load any dynamically discovered relationships from crawlers
    for source in ["weixin", "baidu", "university"]:
        results_file = Path("extracted_data") / source / "all_results.json"
        if not results_file.exists():
            continue
        try:
            data = json.loads(results_file.read_text(encoding="utf-8"))
            for item in data:
                # Discover new account nodes
                acc_name = item.get("account_name", "")
                if acc_name and not any(n["label"] == acc_name for n in all_nodes):
                    all_nodes.append({
                        "id": f"DISC_{len(all_nodes)}",
                        "label": acc_name,
                        "type": "discovered",
                        "region": "Unknown",
                        "tier": 99,
                        "discovered_from": source,
                    })
        except Exception as e:
            print(f"[Ecosystem] Skipping {source}: {e}")

    # Compute influence scores
    influence = compute_influence_scores(all_nodes, all_edges)

    # Build Mermaid graph
    mermaid = build_mermaid_graph(all_nodes, all_edges, "China Overseas Chinese Education Ecosystem 2026")
    (VIZ_DIR / "ecosystem_full_2026.mmd").write_text(mermaid, encoding="utf-8")
    print(f"[Ecosystem] Mermaid graph written: {len(all_nodes)} nodes, {len(all_edges)} edges")

    # Save JSON knowledge graph
    kg = {
        "generated_at": datetime.now().isoformat(),
        "nodes": all_nodes,
        "edges": all_edges,
        "influence_scores": influence,
        "top_influencers": sorted(
            [(nid, score) for nid, score in influence.items()],
            key=lambda x: x[1], reverse=True
        )[:10],
    }
    kg_file = ECOSYSTEM_DIR / "knowledge_graph.json"
    kg_file.write_text(json.dumps(kg, ensure_ascii=False, indent=2), encoding="utf-8")

    # Generate influence ranking report
    top = kg["top_influencers"]
    node_labels = {n["id"]: n["label"] for n in all_nodes}
    report_lines = [
        "# Ecosystem Influence Ranking",
        f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "| Rank | Organization | Score | Type |",
        "|------|-------------|-------|------|",
    ]
    for i, (nid, score) in enumerate(top, 1):
        node = next((n for n in all_nodes if n["id"] == nid), {})
        report_lines.append(f"| {i} | {node.get('label','?')} | {score} | {node.get('type','?')} |")

    (REPORTS_DIR / "ecosystem_influence_ranking.md").write_text(
        "\n".join(report_lines), encoding="utf-8")

    print(f"[Ecosystem] Top influencer: {node_labels.get(top[0][0],'?')} (score={top[0][1]})")

    return {
        "nodes": len(all_nodes),
        "edges": len(all_edges),
        "top_influencer": node_labels.get(top[0][0], "?") if top else "",
        "mermaid_file": str(VIZ_DIR / "ecosystem_full_2026.mmd"),
        "graph_file": str(kg_file),
    }


if __name__ == "__main__":
    run_ecosystem_agent()
