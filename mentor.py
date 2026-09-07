"""
AI Learning Navigator — V4
AI Learning Mentor.

Difference from V1-V3: this is the first version with MEMORY. Instead of
passing "completed topics" manually every time, the learner logs progress
once (add_completed), and it's saved to progress.json with a timestamp.
The mentor then builds on V2 (path) + V3 (NLP) to give a single combined
report: what you've done, what's next, why, and a concrete project to try.

New in V4:
- Persistent progress log (progress.json) -- survives between sessions.
- Achievement history (what you completed, and when).
- Project suggestion attached to the next recommended step.
- A human-readable "mentor report" combining everything.

Not yet real in V4 (flagged honestly, not faked):
- Research paper suggestions -- would need a real API (e.g. arXiv) to avoid
  making up papers. Left as a clearly separate next increment.
- Course suggestions -- would need a real course catalog/API for the same
  reason. Also left as a next increment rather than invented data.
"""

import json
from datetime import datetime
from pathlib import Path

from path_builder import LearningPathBuilder
from nlp_assistant import NLPLearningAssistant


class AILearningMentor:
    def __init__(self, topics_path: str = "topics.json", progress_path: str = "progress.json"):
        data = json.loads(Path(topics_path).read_text(encoding="utf-8"))
        self.topics = data["topics"]
        self.progress_path = Path(progress_path)
        self.path_builder = LearningPathBuilder(topics_path)
        self.nlp_assistant = NLPLearningAssistant(topics_path)
        self.progress = self._load_progress()

    def _load_progress(self) -> dict:
        if self.progress_path.exists():
            return json.loads(self.progress_path.read_text(encoding="utf-8"))
        return {"goal": None, "completed": [], "history": []}

    def _save_progress(self):
        self.progress_path.write_text(
            json.dumps(self.progress, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def set_goal(self, goal: str):
        self.progress["goal"] = goal
        self._save_progress()

    def add_completed(self, topic_id: str = None, text: str = None):
        """Log a completed topic either directly by ID, or inferred from free text (via V3)."""
        newly_completed = []

        if topic_id:
            if topic_id not in self.topics:
                raise ValueError(f"Unknown topic id: {topic_id}")
            newly_completed.append(topic_id)

        if text:
            inferred = self.nlp_assistant.infer_completed_topics(text)
            newly_completed.extend(inferred.keys())

        added = []
        for tid in newly_completed:
            if tid not in self.progress["completed"]:
                self.progress["completed"].append(tid)
                self.progress["history"].append(
                    {"topic": tid, "name": self.topics[tid]["name"], "date": datetime.now().strftime("%Y-%m-%d")}
                )
                added.append(tid)

        self._save_progress()
        return added

    def mentor_report(self) -> str:
        """The main V4 output: a human-readable mentor message combining
        progress history, the recommended path, and a concrete project idea."""
        goal = self.progress.get("goal")
        completed = self.progress.get("completed", [])

        if not goal:
            return "لسا ما حددتي هدفك. استخدمي set_goal('ai' / 'robotics' / 'research') الأول."

        if not completed:
            return f"لسا ما سجّلتي أي إنجاز. استخدمي add_completed(...) لتسجيل أول topic خلصتيه نحو هدف '{goal}'."

        path_result = self.path_builder.build_path(completed=completed, goal=goal)
        lines = []

        lines.append(f"📊 عندك {len(completed)} إنجاز مسجّل نحو هدف '{goal}':")
        for entry in self.progress["history"]:
            lines.append(f"   ✓ {entry['name']}  ({entry['date']})")

        if not path_result["path"]:
            lines.append(f"\n🎉 مبروك! وصلتي للهدف: {path_result['target']}")
            return "\n".join(lines)

        next_step = path_result["path"][0]
        next_topic_info = self.topics[next_step["id"]]

        lines.append(f"\n🎯 خطوتك الجاية الموصى فيها: {next_step['name']}")
        lines.append(f"   (لأنها بتقربك من هدفك: {path_result['target']})")
        lines.append(f"\n💡 مشروع مقترح لهاي الخطوة:")
        lines.append(f"   {next_topic_info['project_idea']}")

        remaining = len(path_result["path"])
        lines.append(f"\n🗺️ باقي {remaining} خطوة/خطوات للوصول لهدفك الكامل.")

        return "\n".join(lines)


if __name__ == "__main__":
    # Fresh demo run: reset progress file for a clean example
    demo_progress_path = Path("progress.json")
    if demo_progress_path.exists():
        demo_progress_path.unlink()

    mentor = AILearningMentor("topics.json", "progress.json")
    mentor.set_goal("robotics")

    mentor.add_completed(topic_id="python")
    mentor.add_completed(topic_id="math")
    mentor.add_completed(text="I finished statistics and did a data analysis project with pandas.")
    mentor.add_completed(text="I built my first ML prediction model.")

    print(mentor.mentor_report())
