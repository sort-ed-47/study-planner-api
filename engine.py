import json
from datetime import datetime, timedelta
import random


DAILY_LIMITS = {
    "light":   {"easy": 2, "medium": 1, "hard": 0, "max_topics": 3, "time": 90},
    "moderate": {"easy": 2, "medium": 1, "hard": 1, "max_topics": 4, "time": 150},
    "aggressive": {"easy": 3, "medium": 2, "hard": 1, "max_topics": 6, "time": 240}
}

MOTIVATION = [
    "🔥 Consistency beats intensity — just show up today!",
    "📚 Every small step today builds your future.",
    "⚡ Stay sharp! You’re improving faster than you think.",
    "💪 Hard topics don't scare you anymore.",
    "🌱 1% improvement today = 100% growth ahead.",
    "🚀 Believe in your daily effort — it compounds."
]


def adjusted_time(base, difficulty, speed, weakness):
    t = base
    if speed == 0: t *= 1.3
    if speed == 2: t *= 0.8
    if weakness > 0.6: t *= 1.2
    return round(t)


def generate_realistic_plan_v2(
    syllabus_json,
    weakness_map,
    speed_map,
    study_mode,
    exam_date,
    discipline_score
):

    today = datetime.now().date()
    exam = datetime.strptime(exam_date, "%Y-%m-%d").date()

    # FIX: if exam date is in the past → auto assign 45 days study cycle
    if exam <= today:
        exam = today + timedelta(days=45)

    days_left = (exam - today).days
    limits = DAILY_LIMITS[study_mode]
    time_budget = limits["time"]

    syllabus = syllabus_json["Science"]

    # -------------------------
    # Build tasks in chapter order
    # -------------------------
    tasks = []
    for chapter, topics in syllabus.items():
        for item in topics:
            t = adjusted_time(
                item["estimated_time"],
                item["difficulty"],
                speed_map.get("Science", 1),
                weakness_map.get("Science", 0.4)
            )
            tasks.append({
                "chapter": chapter,
                "topic": item["topic"],
                "difficulty": item["difficulty"],
                "time": t
            })

    # -------------------------
    # Daily planning
    # -------------------------
    plan = {}
    current_day = today

    i = 0
    while i < len(tasks):
        plan[current_day] = {
            "topics": [],
            "message": random.choice(MOTIVATION)
        }

        used = {"easy": 0, "medium": 0, "hard": 0, "topics": 0, "time": 0}

        while i < len(tasks) and used["topics"] < limits["max_topics"]:
            task = tasks[i]
            diff = task["difficulty"]

            # difficulty limits
            if used[diff] >= limits[diff]:
                break

            # time limit
            if used["time"] + task["time"] > time_budget:
                break

            # assign task
            plan[current_day]["topics"].append(task)
            used[diff] += 1
            used["topics"] += 1
            used["time"] += task["time"]

            i += 1

        current_day += timedelta(days=1)

    # -------------------------
    # Weekly Overview
    # -------------------------
    weekly = {}
    week = 1
    week_start = today

    for day, detail in plan.items():
        if day >= week_start + timedelta(days=7):
            week += 1
            week_start += timedelta(days=7)
        if week not in weekly:
            weekly[week] = []
        weekly[week].extend([t["chapter"] for t in detail["topics"]])

    # Remove duplicates per week
    for wk in weekly:
        weekly[wk] = list(dict.fromkeys(weekly[wk]))

    # -------------------------
    # Human-friendly Revision
    # -------------------------
    revision = {}

    for day, detail in plan.items():
        todays_topics = detail["topics"]

        if not todays_topics:
            continue

        # Day+1 → last 2 topics
        rd1 = day + timedelta(days=1)
        if rd1 <= exam:
            revision.setdefault(rd1, [])
            revision[rd1].extend([t["topic"] for t in todays_topics[-2:]])

        # Day+3 → only medium/hard
        rd3 = day + timedelta(days=3)
        if rd3 <= exam:
            revision.setdefault(rd3, [])
            revision[rd3].extend([
                t["topic"] for t in todays_topics if t["difficulty"] in ("medium", "hard")
            ])

        # Day+7 → chapter summary (first 3 topics of chapter)
        rd7 = day + timedelta(days=7)
        if rd7 <= exam:
            revision.setdefault(rd7, [])
            chapters = list(dict.fromkeys([t["chapter"] for t in todays_topics]))
            for chap in chapters:
                # Add *key topics* (first 3 topics of chapter)
                ch_topics = []
                for c, topic_list in syllabus.items():
                    if c == chap:
                        ch_topics = topic_list[:3]
                        break
                revision[rd7].extend([t["topic"] for t in ch_topics])

    # Clean revision (max 5 topics/day)
    for day in revision:
        revision[day] = revision[day][:5]

    # -------------------------
    # RETURN FINAL PLAN
    # -------------------------
    return {
        "days_left": days_left,
        "daily_minutes": time_budget,
        "daily_plan": {
            str(day): plan[day] for day in plan
        },
        "revision_plan": {
            str(day): revision[day] for day in revision
        },
        "weekly_overview": weekly
    }
