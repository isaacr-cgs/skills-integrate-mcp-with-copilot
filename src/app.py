"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from datetime import date

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "days": ["Friday"],
        "start_time": "15:30",
        "end_time": "17:00",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "days": ["Tuesday", "Thursday"],
        "start_time": "15:30",
        "end_time": "16:30",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "days": ["Monday", "Wednesday", "Friday"],
        "start_time": "14:00",
        "end_time": "15:00",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "days": ["Tuesday", "Thursday"],
        "start_time": "16:00",
        "end_time": "17:30",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "days": ["Wednesday", "Friday"],
        "start_time": "15:30",
        "end_time": "17:00",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "days": ["Thursday"],
        "start_time": "15:30",
        "end_time": "17:00",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "days": ["Monday", "Wednesday"],
        "start_time": "16:00",
        "end_time": "17:30",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "days": ["Tuesday"],
        "start_time": "15:30",
        "end_time": "16:30",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "days": ["Friday"],
        "start_time": "16:00",
        "end_time": "17:30",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# One-time events use a date instead of recurring weekdays.
events = {
    "Fall Activities Fair": {
        "description": "Meet activity leaders and discover new ways to get involved",
        "date": "2026-09-25",
        "schedule": "Friday, September 25, 3:30 PM - 5:00 PM",
        "start_time": "15:30",
        "end_time": "17:00",
        "max_participants": 100,
        "participants": []
    },
    "Inter-school Chess Tournament": {
        "description": "Compete against chess players from neighboring schools",
        "date": "2026-10-09",
        "schedule": "Friday, October 9, 4:00 PM - 6:00 PM",
        "start_time": "16:00",
        "end_time": "18:00",
        "max_participants": 40,
        "participants": []
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.get("/events")
def get_events():
    return events


def get_conflicts(email: str, item: dict, current_name: str):
    """Return registered activities or events that overlap with an item."""
    conflicts = []
    item_days = set(item.get("days", []))
    item_date = item.get("date")

    def overlaps(other):
        if item_date:
            event_day = date.fromisoformat(item_date).strftime("%A")
            if event_day not in other.get("days", []):
                return False
        elif other.get("date"):
            if date.fromisoformat(other["date"]).strftime("%A") not in item_days:
                return False
        elif not item_days.intersection(other.get("days", [])):
            return False

        return item["start_time"] < other["end_time"] and other["start_time"] < item["end_time"]

    for name, activity in activities.items():
        if name != current_name and email in activity["participants"] and overlaps(activity):
            conflicts.append(name)

    for name, event in events.items():
        if name != current_name and email in event["participants"] and overlaps(event):
            conflicts.append(name)

    return conflicts


def add_participant(collection: dict, name: str, email: str):
    if name not in collection:
        raise HTTPException(status_code=404, detail="Activity or event not found")

    item = collection[name]
    if email in item["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    item["participants"].append(email)
    response = {"message": f"Signed up {email} for {name}"}
    conflicts = get_conflicts(email, item, name)
    if conflicts:
        response["warning"] = f"This overlaps with: {', '.join(conflicts)}"
    return response


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    return add_participant(activities, activity_name, email)


@app.post("/events/{event_name}/signup")
def signup_for_event(event_name: str, email: str):
    """Sign up a student for a one-time event."""
    return add_participant(events, event_name, email)


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
