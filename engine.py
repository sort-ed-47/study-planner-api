# import json
# from datetime import datetime, timedelta


# # -----------------------
# #  TIME & DIFFICULTY LOGIC
# # -----------------------
# def adjusted_time(base, difficulty, speed, weakness):

#     # adjust by difficulty
#     if difficulty == "easy":
#         t = base
#     elif difficulty == "medium":
#         t = base * 1.5
#     else:  # hard
#         t = base * 2

#     # adjust by learning speed
#     if speed == 0:  # slow learner
#         t *= 1.3
#     elif speed == 2:  # fast learner
#         t *= 0.8

#     # adjust by weakness
#     if weakness > 0.6:
#         t *= 1.2

#     return round(t)


# def daily_study_minutes(mode):
#     return {
#         "light": 90,
#         "moderate": 150,
#         "aggressive": 240
#     }[mode]


# # -----------------------
# #        PLANNER
# # -----------------------
# def generate_study_plan(syllabus_json,
#                         weakness_map,
#                         speed_map,
#                         study_mode,
#                         exam_date,
#                         discipline_score):

#     syllabus = syllabus_json["Science"]

#     tasks = []

#     # BUILD TASK LIST
#     for chapter, topics in syllabus.items():
#         for item in topics:
#             topic_name = item["topic"]
#             difficulty = item["difficulty"]
#             base_time = item["estimated_time"]

#             weakness = weakness_map.get("Science", 0.4)
#             speed = speed_map.get("Science", 1)

#             time_needed = adjusted_time(base_time, difficulty, speed, weakness)

#             tasks.append({
#                 "chapter": chapter,
#                 "topic": topic_name,
#                 "difficulty": difficulty,
#                 "time": time_needed
#             })

#     # SORT TASKS — weak subjects & harder topics first
#     tasks = sorted(
#         tasks,
#         key=lambda t: (
#             -weakness_map.get("Science", 0.4),
#             2 if t["difficulty"] == "hard" else
#             1 if t["difficulty"] == "medium" else 0
#         )
#     )

#     # SCHEDULING
#     today = datetime.now().date()
#     exam = datetime.strptime(exam_date, "%Y-%m-%d").date()
#     days_left = (exam - today).days

#     daily_minutes = daily_study_minutes(study_mode)

#     plan = {}
#     current_day = today
#     minutes_left = daily_minutes

#     for task in tasks:

#         if current_day not in plan:
#             plan[current_day] = []

#         if minutes_left < task["time"]:
#             current_day += timedelta(days=1)
#             minutes_left = daily_minutes
#             plan[current_day] = []

#         plan[current_day].append(task)
#         minutes_left -= task["time"]

#     # REVISION CYCLES
#     revision = {}

#     for day in plan:
#         for task in plan[day]:

#             topic = task["topic"]

#             # spaced repetition pattern
#             revision_days = [
#                 day + timedelta(days=2),
#                 day + timedelta(days=4),
#                 day + timedelta(days=7),
#                 day + timedelta(days=14),
#                 exam - timedelta(days=2)
#             ]

#             for r in revision_days:
#                 if r not in revision:
#                     revision[r] = []
#                 revision[r].append(topic)

#     return {
#         "days_left": days_left,
#         "daily_minutes": daily_minutes,
#         "daily_plan": {str(day): plan[day] for day in plan},
#         "revision_plan": {str(day): revision[day] for day in revision if day >= today}
#     }

# # -------------------------------
# # TEST RUNNER (FOR VSCode OUTPUT)
# # -------------------------------
# if __name__ == "__main__":
    
#     print("Loading syllabus...")
#     with open("science_syllabus.json") as f:
#         syllabus = json.load(f)

#     print("Generating plan...")

#     plan = generate_study_plan(
#         syllabus_json=syllabus,
#         weakness_map={"Science": 0.7},
#         speed_map={"Science": 1},
#         study_mode="moderate",
#         exam_date="2025-03-10",
#         discipline_score=0.5
#     )

#     print("Plan generated!\n")
#     print(json.dumps(plan, indent=2))

import json
from datetime import datetime, timedelta
import random


# ---------------------------------------------------
# DAILY LIMIT SETTINGS BASED ON STUDY MODE
# ---------------------------------------------------
DAILY_LIMITS = {
    "light":   {"easy": 2, "medium": 1, "hard": 0, "max_topics": 3, "time": 90},
    "moderate": {"easy": 2, "medium": 1, "hard": 1, "max_topics": 4, "time": 150},
    "aggressive": {"easy": 3, "medium": 2, "hard": 1, "max_topics": 6, "time": 240}
}

# ---------------------------------------------------
# MOTIVATIONAL MESSAGES
# ---------------------------------------------------
MOTIVATION = [
    "🔥 Consistency beats intensity — just show up today!",
    "📚 Every small step today builds your future.",
    "⚡ Stay sharp! You’re improving faster than you think.",
    "💪 Hard topics don't scare you anymore.",
    "🌱 1% improvement today = 100% growth ahead.",
    "🚀 Believe in your daily effort — it compounds."
]


# ---------------------------------------------------
# TIME ADJUSTMENT BASED ON LEARNING SPEED & WEAKNESS
# ---------------------------------------------------
def adjusted_time(base, difficulty, speed, weakness):
    t = base

    # speed categories: 0 = slow, 1 = normal, 2 = fast
    if speed == 0:
        t *= 1.3
    if speed == 2:
        t *= 0.8

    # weakness > 0.6 → extra time needed
    if weakness > 0.6:
        t *= 1.2

    return round(t)



# ---------------------------------------------------
# SUBJECT SELECTION LOGIC
# ---------------------------------------------------
def select_subject(syllabus_json, subject_from_api):
    """
    syllabus_json = { "Science": {...}, "Maths": {...} }
    subject_from_api = "maths" or "science"
    """

    # Normalize subject string
    if subject_from_api:
        subject_from_api = subject_from_api.lower().strip()

        # Match subject key in JSON
        for key in syllabus_json.keys():
            if key.lower() == subject_from_api:
                return key  # exact match

    # Fallback: take FIRST key in file
    return list(syllabus_json.keys())[0]



# ---------------------------------------------------
# MAIN PLANNER ENGINE
# ---------------------------------------------------
def generate_realistic_plan_v2(
    syllabus_json,
    weakness_map,
    speed_map,
    study_mode,
    exam_date,
    discipline_score,
    subject
):

    # ---------------------------------------------------
    # DATE HANDLING
    # ---------------------------------------------------
    today = datetime.now().date()
    exam = datetime.strptime(exam_date, "%Y-%m-%d").date()

    # If exam date already passed → give 45 days
    if exam <= today:
        exam = today + timedelta(days=45)

    days_left = (exam - today).days
    limits = DAILY_LIMITS[study_mode]
    time_budget = limits["time"]

    # ---------------------------------------------------
    # SUBJECT PICKING (FULLY FIXED)
    # ---------------------------------------------------
    subject_key = select_subject(syllabus_json, subject)

    syllabus = syllabus_json[subject_key]

    # ---------------------------------------------------
    # BUILD TASK LIST
    # ---------------------------------------------------
    tasks = []

    for chapter, topics in syllabus.items():
        for item in topics:

            t = adjusted_time(
                base=item["estimated_time"],
                difficulty=item["difficulty"],
                speed=speed_map.get(subject_key, 1),
                weakness=weakness_map.get(subject_key, 0.4)
            )

            tasks.append({
                "chapter": chapter,
                "topic": item["topic"],
                "difficulty": item["difficulty"],
                "time": t
            })

    # ---------------------------------------------------
    # DAILY PLAN GENERATION
    # ---------------------------------------------------
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

            # difficulty cap
            if used[diff] >= limits[diff]:
                break

            # time cap
            if used["time"] + task["time"] > time_budget:
                break

            plan[current_day]["topics"].append(task)

            used[diff] += 1
            used["topics"] += 1
            used["time"] += task["time"]

            i += 1

        current_day += timedelta(days=1)

    # ---------------------------------------------------
    # WEEKLY OVERVIEW
    # ---------------------------------------------------
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

    # remove duplicate chapters per week
    for wk in weekly:
        weekly[wk] = list(dict.fromkeys(weekly[wk]))

    # ---------------------------------------------------
    # REVISION PLAN
    # ---------------------------------------------------
    revision = {}

    for day, detail in plan.items():
        todays_topics = detail["topics"]
        if not todays_topics:
            continue

        # Day +1 → revise last 2 topics
        rd1 = day + timedelta(days=1)
        if rd1 <= exam:
            revision.setdefault(rd1, [])
            revision[rd1].extend([t["topic"] for t in todays_topics[-2:]])

        # Day +3 → revise medium & hard topics
        rd3 = day + timedelta(days=3)
        if rd3 <= exam:
            revision.setdefault(rd3, [])
            revision[rd3].extend([
                t["topic"] for t in todays_topics if t["difficulty"] in ("medium", "hard")
            ])

        # Day +7 → chapter summary (first 3 key topics)
        rd7 = day + timedelta(days=7)
        if rd7 <= exam:
            revision.setdefault(rd7, [])
            chapters = list(dict.fromkeys([t["chapter"] for t in todays_topics]))
            for chap in chapters:
                key_topics = syllabus[chap][:3]
                revision[rd7].extend([t["topic"] for t in key_topics])

    # cap revision (max 5 topics/day)
    for day in revision:
        revision[day] = revision[day][:5]

    # ---------------------------------------------------
    # RETURN FINAL STUDY SCHEDULE
    # ---------------------------------------------------
    return {
        "subject_used": subject_key,  # for debugging
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
