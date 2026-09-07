"""
AI Learning Navigator — V5
Public platform front-end (Streamlit).

This is a SELF-CONTAINED file (all logic from V2/V3 is copied in directly,
not imported) so it runs correctly no matter how the other project files
are saved -- this avoids the .ipynb import issues from earlier.

HOW TO RUN THIS FILE (different from Jupyter!):
1. Make sure this file is saved with a .py extension (not .ipynb).
2. Make sure topics.json is in the same folder.
3. Open a terminal in that folder and run:
       streamlit run app.py
4. A browser tab opens automatically with the live app.
"""

import json
import re
from pathlib import Path

import streamlit as st

TOPICS_PATH = "topics.json"
USERS_PATH = "users.json"


# ---------- Core engine (same logic as V2/V3, copied in directly) ----------

def load_topics():
    data = json.loads(Path(TOPICS_PATH).read_text(encoding="utf-8"))
    return data["topics"]


def depth(topics, topic_id, _cache={}):
    if topic_id in _cache:
        return _cache[topic_id]
    prereqs = topics[topic_id]["prerequisites"]
    d = 0 if not prereqs else 1 + max(depth(topics, p) for p in prereqs)
    _cache[topic_id] = d
    return d


def goal_topic(topics, goal):
    matches = [tid for tid, info in topics.items() if goal in info["goals"]]
    return max(matches, key=lambda tid: depth(topics, tid))


def collect_needed(topics, target, completed):
    needed = set()
    stack = [target]
    while stack:
        current = stack.pop()
        if current in completed or current in needed:
            continue
        needed.add(current)
        stack.extend(topics[current]["prerequisites"])
    return needed


def topological_sort(topics, needed):
    visited, order = set(), []

    def visit(topic_id):
        if topic_id in visited:
            return
        visited.add(topic_id)
        for prereq in topics[topic_id]["prerequisites"]:
            if prereq in needed:
                visit(prereq)
        order.append(topic_id)

    for topic_id in needed:
        visit(topic_id)
    return order


def build_path(topics, completed, goal):
    completed_set = set(completed)
    target = goal_topic(topics, goal)
    if target in completed_set:
        return {"target": topics[target]["name"], "path": []}
    needed = collect_needed(topics, target, completed_set)
    ordered_ids = topological_sort(topics, needed)
    path = [{"id": tid, "name": topics[tid]["name"], "level": topics[tid]["level"]} for tid in ordered_ids]
    return {"target": topics[target]["name"], "path": path}


def infer_from_text(topics, text):
    text_lower = text.lower()
    inferred = {}
    for topic_id, info in topics.items():
        for kw in info.get("keywords", []):
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                inferred[topic_id] = kw
                break
    return inferred


# ---------- Streamlit UI ----------

st.set_page_config(page_title="AI Learning Navigator", page_icon="🧭")
st.title("🧭 AI Learning Navigator")
st.caption("Personalized AI/ML learning roadmap generator — V5 public version")

topics = load_topics()

st.subheader("1. Tell us what you've already learned")
selected_topics = st.multiselect(
    "Select completed topics (or describe them below instead):",
    options=list(topics.keys()),
    format_func=lambda tid: topics[tid]["name"],
)

free_text = st.text_area(
    "Or describe your progress in your own words (optional):",
    placeholder="e.g. I built my first ML prediction model.",
)

st.subheader("2. Your career goal")
goal = st.selectbox("Goal:", options=["ai", "robotics", "research"])

if st.button("Generate my roadmap"):
    completed = set(selected_topics)
    if free_text.strip():
        inferred = infer_from_text(topics, free_text)
        completed.update(inferred.keys())
        if inferred:
            st.info("Detected from your text: " + ", ".join(topics[t]["name"] for t in inferred))

    result = build_path(topics, list(completed), goal)

    st.subheader("🎯 Your Personalized Roadmap")
    st.write(f"**Target:** {result['target']}")

    if not result["path"]:
        st.success("You've already reached this goal! 🎉")
    else:
        for i, step in enumerate(result["path"], start=1):
            st.markdown(f"**{i}. {step['name']}** — *{step['level']}*")
            idea = topics[step["id"]].get("project_idea")
            if idea:
                st.caption(f"💡 Project idea: {idea}")
