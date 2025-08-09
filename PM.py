# Project Scorecard Tracker – Streamlit UI
# Usage:
#   python -m streamlit run project_tracker_ui.py

import json
import datetime
from pathlib import Path
import streamlit as st

PROJECT_FILE = Path(__file__).with_name("projects.json")

def load_projects():
    if PROJECT_FILE.exists():
        with open(PROJECT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []
    for p in data:
        p.setdefault("tasks", [])
        if "urgency" not in p:
            ub = p.get("urgency_buffer")
            mapping = {1: 5, 2: 3, 3: 1}
            p["urgency"] = mapping.get(ub, 3)
        p.setdefault("category", "Uncategorized")
    return data


def save_projects(projects):
    with open(PROJECT_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2)


def utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def calculate_score(impact, alignment, momentum, effort, urgency):
    return round((impact * alignment * momentum * urgency) / effort, 2)


def update_next_action(project):
    for t in project["tasks"]:
        if not t["done"]:
            project["next_action"] = t["text"]
            return
    project["next_action"] = ""

st.set_page_config(page_title="Project Scorecard Tracker", layout="wide")
st.title("📊 Project Scorecard Tracker")
st.markdown("Rank, track, and finish projects with weighted scoring and task lists.")

st.markdown(
    """
    <style>
    .badge{display:inline-block;padding:0.2rem 0.55rem;border-radius:999px;font-weight:600;font-size:0.80rem;border:1px solid rgba(255,255,255,.18);margin-left:.35rem}
    .status-inprogress{background:rgba(59,130,246,.15);color:#93c5fd;border-color:#3b82f6}
    .status-blocked{background:rgba(239,68,68,.15);color:#fca5a5;border-color:#ef4444}
    .status-notstarted{background:rgba(148,163,184,.15);color:#cbd5e1;border-color:#94a3b8}
    .status-done{background:rgba(16,185,129,.15);color:#86efac;border-color:#10b981}
    .cat-chip{background:rgba(124,58,237,.15);color:#d8b4fe;border-color:#7c3aed}
    .next-chip{background:rgba(34,197,94,.12);color:#bbf7d0;border-color:#22c55e;padding:.3rem .6rem;border-radius:10px;display:inline-block}
    .card{border:1px solid rgba(148,163,184,.35);border-radius:14px;padding:1rem 1.25rem;background:linear-gradient(180deg, rgba(124,58,237,.06), rgba(59,130,246,.05));}
    .score{font-size:1.5rem;font-weight:800}
    </style>
    """,
    unsafe_allow_html=True,
)

STATUS_CLASS = {"In Progress": "inprogress", "Blocked": "blocked", "Not Started": "notstarted", "Done": "done"}
STATUS_COLOR = {"In Progress": "#3b82f6", "Blocked": "#ef4444", "Not Started": "#64748b", "Done": "#10b981"}
STATUS_BG = {"In Progress": "rgba(59,130,246,.10)", "Blocked": "rgba(239,68,68,.10)", "Not Started": "rgba(148,163,184,.10)", "Done": "rgba(16,185,129,.10)"}

projects = load_projects()
status_order = ["In Progress", "Blocked", "Not Started", "Done"]
status_icons = {"In Progress": "🚧", "Blocked": "⛔", "Not Started": "📝", "Done": "✅"}

for p in projects:
    p["score"] = calculate_score(
        p.get("impact", 3), p.get("alignment", 3), p.get("momentum", 1), p.get("effort", 3), p.get("urgency", 3)
    )
save_projects(projects)

content_col, form_col = st.columns((3, 1), gap="large")

with form_col:
    st.header("➕ Add New Project")
    with st.form("add_project", border=True):
        name = st.text_input("Project name")
        impact = st.slider("Impact", 1, 5, 3)
        alignment = st.slider("Alignment", 1, 5, 3)
        momentum = st.slider("Momentum", 1, 5, 1)
        effort = st.slider("Effort", 1, 5, 3)
        urgency = st.slider("Urgency (5 = urgent)", 1, 5, 3)
        cat_options = ["Work", "Farm", "House", "Personal", "Uncategorized", "Custom…"]
        cat_choice = st.selectbox("Category", cat_options, index=0)
        custom_cat = st.text_input("Custom category", value="", disabled=(cat_choice != "Custom…"))
        category = custom_cat.strip() if cat_choice == "Custom…" else cat_choice
        if st.form_submit_button("Add Project") and name.strip():
            score = calculate_score(impact, alignment, momentum, effort, urgency)
            projects.append(
                {
                    "name": name.strip(),
                    "impact": impact,
                    "alignment": alignment,
                    "momentum": momentum,
                    "effort": effort,
                    "urgency": urgency,
                    "category": category or "Uncategorized",
                    "score": score,
                    "status": "Not Started" if momentum <= 2 else "In Progress",
                    "next_action": "",
                    "created": utc_iso(),
                    "updated": utc_iso(),
                    "tasks": [],
                }
            )
            save_projects(projects)
            st.rerun()

with content_col:
    projects_sorted = sorted(projects, key=lambda p: p["score"], reverse=True)
    active = [p for p in projects_sorted if p["status"] != "Done"]

    st.subheader("🎯 Focus for Next Project Night")
    if active:
        fp = active[0]
        status_cls = STATUS_CLASS.get(fp["status"], "notstarted")
        st.markdown(
            f"""
            <div class='card'>
              <div style='display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;'>
                <div style='font-size:1.1rem;font-weight:700'>{fp['name']}</div>
                <span class='badge status-{status_cls}'>{fp['status']}</span>
                <span class='badge cat-chip'>{fp.get('category','Uncategorized')}</span>
              </div>
              <div style='margin-top:.4rem'>Score: <span class='score'>{fp['score']}</span></div>
              <div style='margin-top:.6rem'><span class='next-chip'>Next: {fp['next_action'] or 'Add a task below'}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("All projects complete or none available.")

    st.markdown("---")

    if not projects:
        st.info("No projects yet. Use the form on the right to add one.")
    else:
        st.subheader("📋 Projects")
        group_mode = st.selectbox(
            "Group by",
            [
                "Grouped by Status",
                "Grouped by Category",
                "Grouped by Completed vs Not",
                "Grouped by Impact",
                "Grouped by Alignment",
                "Grouped by Momentum",
                "Grouped by Effort",
                "Grouped by Urgency",
            ],
            index=0,
            key="group_mode_main",
        )

        def group_projects(projects_list, mode):
            if mode == "Grouped by Status":
                order = ["In Progress", "Blocked", "Not Started", "Done"]
                groups = {k: [] for k in order}
                for p in projects_list:
                    groups.setdefault(p["status"], []).append(p)
                return [(k, groups[k]) for k in order if groups.get(k)]
            if mode == "Grouped by Category":
                cats = sorted({p.get("category", "Uncategorized") for p in projects_list})
                groups = {c: [] for c in cats}
                for p in projects_list:
                    groups.setdefault(p.get("category", "Uncategorized"), []).append(p)
                return [(c, groups[c]) for c in cats]
            if mode == "Grouped by Completed vs Not":
                groups = {"Active": [], "Completed": []}
                for p in projects_list:
                    label = "Completed" if p["status"] == "Done" else "Active"
                    groups[label].append(p)
                return [("Active", groups["Active"]), ("Completed", groups["Completed"])]
            metric_map = {
                "Grouped by Impact": ("impact", [5, 4, 3, 2, 1]),
                "Grouped by Alignment": ("alignment", [5, 4, 3, 2, 1]),
                "Grouped by Momentum": ("momentum", [5, 4, 3, 2, 1]),
                "Grouped by Effort": ("effort", [5, 4, 3, 2, 1]),
                "Grouped by Urgency": ("urgency", [5, 4, 3, 2, 1]),
            }
            key_name, order_vals = metric_map[mode]
            buckets = {v: [] for v in order_vals}
            for p in projects_list:
                buckets.setdefault(int(p.get(key_name, 0)), []).append(p)
            return [(f"{key_name.capitalize()} = {v}", buckets[v]) for v in order_vals if buckets.get(v)]

        grouped = group_projects(projects_sorted, group_mode)

        idx = 1
        for label, group in grouped:
            if not group:
                continue
            heading_icon = status_icons.get(label, "") if group_mode == "Grouped by Status" else ""
            st.markdown(
                f"<h3>{heading_icon} {label} <span class='badge cat-chip'>{len(group)}</span></h3>",
                unsafe_allow_html=True,
            )
            group_sorted = sorted(group, key=lambda p: p["score"], reverse=True)
            for p in group_sorted:
                pid = p.get("created", p["name"])  # stable per-project key
                exp_label = f"{idx}. {p['name']} (score {p['score']} | next: {p['next_action'] or 'N/A'})"
                idx += 1
                with st.expander(exp_label):
                    bar_color = STATUS_COLOR.get(p["status"], "#64748b")
                    bar_bg = STATUS_BG.get(p["status"], "rgba(148,163,184,.10)")
                    st.markdown(
                        f"""
                        <div style='background:{bar_bg};border-left:6px solid {bar_color};padding:.5rem .75rem;border-radius:10px;margin-bottom:.5rem'>
                          <span class='badge status-{STATUS_CLASS.get(p['status'],'notstarted')}'>{p['status']}</span>
                          <span class='badge cat-chip'>{p.get('category','Uncategorized')}</span>
                          <span class='badge' style='background:rgba(250,204,21,.12);color:#fde68a;border-color:#f59e0b'>Urgency {p.get('urgency',3)}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.form(f"meta_{pid}"):
                        cols = st.columns(6)
                        imp_u = cols[0].slider("Impact", 1, 5, p["impact"], key=f"imp_{pid}")
                        ali_u = cols[1].slider("Align", 1, 5, p["alignment"], key=f"ali_{pid}")
                        mom_u = cols[2].slider("Momentum", 1, 5, p["momentum"], key=f"mom_{pid}")
                        eff_u = cols[3].slider("Effort", 1, 5, p["effort"], key=f"eff_{pid}")
                        urg_u = cols[4].slider("Urgency", 1, 5, p["urgency"], key=f"urg_{pid}")
                        cat_u = cols[5].text_input("Category", value=p.get("category", "Uncategorized"), key=f"cat_{pid}")
                        status_u = st.selectbox(
                            "Status",
                            ["In Progress", "Blocked", "Not Started", "Done"],
                            index=["In Progress", "Blocked", "Not Started", "Done"].index(p["status"]),
                            key=f"stat_{pid}",
                        )
                        if st.form_submit_button("Save Meta"):
                            p.update(
                                {
                                    "impact": imp_u,
                                    "alignment": ali_u,
                                    "momentum": mom_u,
                                    "effort": eff_u,
                                    "urgency": urg_u,
                                    "category": cat_u.strip() or "Uncategorized",
                                    "status": status_u,
                                    "updated": utc_iso(),
                                }
                            )
                            p["score"] = calculate_score(imp_u, ali_u, mom_u, eff_u, urg_u)
                            save_projects(projects)
                            st.rerun()

                    st.divider()
                    st.markdown("#### 📋 Tasks")

                    for i, task in enumerate(p["tasks"]):
                        dot = "#10b981" if task["done"] else "#3b82f6"
                        cols = st.columns([0.04, 0.06, 0.62, 0.09, 0.09, 0.10])
                        cols[0].markdown(
                            f"<div style='width:12px;height:12px;border-radius:3px;background:{dot};margin-top:.55rem'></div>",
                            unsafe_allow_html=True,
                        )
                        done = cols[1].checkbox("Done", value=task["done"], key=f"done_{pid}_{i}", label_visibility="hidden")
                        text = cols[2].text_input("Task", value=task["text"], key=f"txt_{pid}_{i}", label_visibility="hidden")
                        up = cols[3].button("↑", key=f"up_{pid}_{i}") if i > 0 else False
                        down = cols[4].button("↓", key=f"down_{pid}_{i}") if i < len(p["tasks"]) - 1 else False
                        delete = cols[5].button("✕", key=f"del_{pid}_{i}")

                        if done != task["done"] or text != task["text"]:
                            task["done"], task["text"] = done, text
                            update_next_action(p)
                            save_projects(projects)
                            st.rerun()
                        if up:
                            p["tasks"][i - 1], p["tasks"][i] = p["tasks"][i], p["tasks"][i - 1]
                            update_next_action(p)
                            save_projects(projects)
                            st.rerun()
                        if down:
                            p["tasks"][i + 1], p["tasks"][i] = p["tasks"][i], p["tasks"][i + 1]
                            update_next_action(p)
                            save_projects(projects)
                            st.rerun()
                        if delete:
                            p["tasks"].pop(i)
                            update_next_action(p)
                            save_projects(projects)
                            st.rerun()

                    new_task = st.text_input("New task", key=f"new_{pid}")
                    if st.button("Add Task", key=f"add_{pid}") and new_task.strip():
                        p["tasks"].append({"text": new_task.strip(), "done": False})
                        update_next_action(p)
                        save_projects(projects)
                        st.rerun()
