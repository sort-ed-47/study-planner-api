from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import json
import numpy as np
import pandas as pd
from engine import generate_realistic_plan_v2

app = FastAPI(title="SortED Realistic Study Planner API v2")


# ------------------------------
# LOAD SPDM MODELS
# ------------------------------
weakness_model = joblib.load("spdm_weakness.pkl")
slope_model = joblib.load("spdm_slope.pkl")
speed_model = joblib.load("spdm_speed.pkl")
features = joblib.load("spdm_features.pkl")


# ------------------------------
# LOAD COMBINED SYLLABUS (Maths + Science)
# ------------------------------
with open("syllabus.json") as f:
    SYLLABUS = json.load(f)


# ------------------------------
# INPUT MODEL
# ------------------------------
class FullPlanInput(BaseModel):
    subject: str               # <--- FIXED
    exam_date: str
    study_mode: str

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

    # -----------------------------------
    # STEP 1 — FEATURE ENGINEERING
    # -----------------------------------
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

    # SPDM feature row
    X = pd.DataFrame([[
        data.marks, past_mean, past_std,
        quiz_mean, quiz_std,
        data.attendance, data.assignment_rate, data.events_participation,
        data.cluster_id, improvement_slope, discipline_score
    ]], columns=features)

    # -----------------------------------
    # STEP 2 — RUN SPDM MODELS
    # -----------------------------------
    weakness_score = float(weakness_model.predict(X)[0])
    speed_category = int(speed_model.predict(X)[0])
    predicted_slope = float(slope_model.predict(X)[0])

    # -----------------------------------
    # STEP 3 — PREPARE SUBJECT-SPECIFIC MAPS
    # -----------------------------------
    subject_key = None
    sub = data.subject.lower().strip()

    # Match subject with keys in syllabus file
    for key in SYLLABUS.keys():
        if key.lower() == sub:
            subject_key = key
            break

    # If subject doesn't exist
    if not subject_key:
        return {
            "status": "error",
            "message": f"Subject '{data.subject}' not found in syllabus.json"
        }

    # Weakness & speed maps MUST use the subject key
    weakness_map = {subject_key: weakness_score}
    speed_map = {subject_key: speed_category}

    # -----------------------------------
    # STEP 4 — GENERATE STUDY PLAN
    # -----------------------------------
    plan = generate_realistic_plan_v2(
        syllabus_json=SYLLABUS,
        weakness_map=weakness_map,
        speed_map=speed_map,
        study_mode=data.study_mode,
        exam_date=data.exam_date,
        discipline_score=discipline_score,
        subject=subject_key  # <-- FIXED
    )

    # -----------------------------------
    # STEP 5 — RETURN FULL RESPONSE
    # -----------------------------------
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
    return {"message": "SortED Realistic Study Planner API v2 is running 🚀"}
