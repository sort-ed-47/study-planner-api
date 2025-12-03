from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import json
import numpy as np
import pandas as pd
from engine import generate_realistic_plan_v2

app = FastAPI(title="SortED Study Planner API v2 (Topic Range Ready)")


# ------------------------------
# LOAD SPDM MODELS
# ------------------------------
weakness_model = joblib.load("spdm_weakness.pkl")
slope_model = joblib.load("spdm_slope.pkl")
speed_model = joblib.load("spdm_speed.pkl")
features = joblib.load("spdm_features.pkl")


# ------------------------------
# LOAD COMBINED SYLLABUS
# ------------------------------
with open("syllabus.json") as f:
    SYLLABUS = json.load(f)


# ------------------------------
# INPUT MODEL
# ------------------------------
class FullPlanInput(BaseModel):
    subject: str
    exam_date: str
    study_mode: str

    start_topic: str | None = None
    end_topic: str | None = None

    marks: float
    past_marks: list
    quiz_scores: list
    attendance: float
    assignment_rate: float
    events_participation: int
    cluster_id: int


# ------------------------------
# ENDPOINT
# ------------------------------
@app.post("/generate_study_plan")
def generate_study_plan(data: FullPlanInput):

    # FEATURE CALCULATIONS
    past_mean = np.mean(data.past_marks) if data.past_marks else 0
    past_std = np.std(data.past_marks) if data.past_marks else 0

    quiz_mean = np.mean(data.quiz_scores) if data.quiz_scores else 0
    quiz_std = np.std(data.quiz_scores) if data.quiz_scores else 0

    improvement_slope = (
        (data.past_marks[-1] - data.past_marks[0]) / len(data.past_marks)
        if len(data.past_marks) > 1 else 0
    )

    discipline_score = (
        0.4 * data.attendance +
        0.4 * data.assignment_rate +
        0.2 * (data.events_participation / 10)
    )

    X = pd.DataFrame([[
        data.marks, past_mean, past_std,
        quiz_mean, quiz_std,
        data.attendance, data.assignment_rate, data.events_participation,
        data.cluster_id, improvement_slope, discipline_score
    ]], columns=features)

    weakness_score = float(weakness_model.predict(X)[0])
    speed_category = int(speed_model.predict(X)[0])
    predicted_slope = float(slope_model.predict(X)[0])

    # SUBJECT MAPS
    sub = None
    for key in SYLLABUS.keys():
        if key.lower() == data.subject.lower():
            sub = key
            break

    if not sub:
        return {"status": "error", "message": "Subject not found in syllabus"}

    weakness_map = {sub: weakness_score}
    speed_map = {sub: speed_category}

    # GENERATE PLAN
    plan = generate_realistic_plan_v2(
        syllabus_json=SYLLABUS,
        weakness_map=weakness_map,
        speed_map=speed_map,
        study_mode=data.study_mode,
        exam_date=data.exam_date,
        discipline_score=discipline_score,
        subject=sub,
        start_topic=data.start_topic,
        end_topic=data.end_topic
    )

    return {
        "status": "success",
        "analysis": {
            "weakness_score": weakness_score,
            "learning_speed_category": speed_category,
            "predicted_improvement_slope": predicted_slope,
            "discipline_score": discipline_score
        },
        "plan": plan
    }


@app.get("/")
def home():
    return {"message": "Topic-Range Enabled Study Planner API Running 🚀"}
