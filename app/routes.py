from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId
from app.database import get_database
from app.models import (
    ChildCreate, ChildResponse, DoctorCreate, DoctorResponse,
    ParentCreate, ParentResponse, TherapyLogCreate, Token, LoginRequest,
    WeeklyReport, MonthlyReport
)
from app.auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_doctor, get_current_parent,
    generate_random_password, TokenData
)
from app.email_service import send_parent_credentials, send_child_code_email

router = APIRouter()

# Helper function to generate child code
def generate_child_code() -> str:
    import random
    year = datetime.now().year
    number = random.randint(1000, 9999)
    return f"P-{year}-{number}"

# ==================== AUTH ROUTES ====================

@router.post("/auth/login", response_model=Token)
async def login(request: LoginRequest):
    db = get_database()
    
    if request.user_type == "doctor":
        user = await db.doctors.find_one({"email": request.email})
    else:
        user = await db.parents.find_one({"email": request.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "user_type": request.user_type}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_type=request.user_type,
        user_id=str(user["_id"]),
        user_name=user["name"]
    )

@router.post("/auth/register/doctor", response_model=DoctorResponse)
async def register_doctor(doctor: DoctorCreate):
    db = get_database()
    
    # Check if email already exists
    existing = await db.doctors.find_one({"email": doctor.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    doctor_doc = {
        "name": doctor.name,
        "email": doctor.email,
        "password_hash": get_password_hash(doctor.password),
        "specialization": doctor.specialization,
        "assigned_children": [],
        "created_at": datetime.utcnow()
    }
    
    result = await db.doctors.insert_one(doctor_doc)
    doctor_doc["_id"] = result.inserted_id
    
    return DoctorResponse(
        id=str(doctor_doc["_id"]),
        name=doctor_doc["name"],
        email=doctor_doc["email"],
        specialization=doctor_doc["specialization"],
        assigned_children=[],
        created_at=doctor_doc["created_at"]
    )

@router.post("/auth/register/parent", response_model=ParentResponse)
async def register_parent(parent: ParentCreate):
    db = get_database()
    
    # Check if email already exists
    existing = await db.parents.find_one({"email": parent.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    parent_doc = {
        "name": parent.name,
        "email": parent.email,
        "phone": parent.phone,
        "password_hash": get_password_hash(parent.password),
        "children": [],
        "created_by_system": False,
        "created_at": datetime.utcnow()
    }
    
    # If child code provided, verify and link
    if parent.child_code:
        child_code_doc = await db.child_codes.find_one({
            "code": parent.child_code,
            "status": "active"
        })
        
        if not child_code_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired child code"
            )
        
        # Insert parent first
        result = await db.parents.insert_one(parent_doc)
        parent_id = result.inserted_id
        
        # Link child to parent
        await db.children.update_one(
            {"_id": child_code_doc["child_id"]},
            {"$addToSet": {"parent_ids": parent_id}}
        )
        
        # Add child to parent's children list
        await db.parents.update_one(
            {"_id": parent_id},
            {"$addToSet": {"children": child_code_doc["child_id"]}}
        )
        
        parent_doc["children"] = [str(child_code_doc["child_id"])]
    else:
        result = await db.parents.insert_one(parent_doc)
    
    parent_doc["_id"] = result.inserted_id
    
    return ParentResponse(
        id=str(parent_doc["_id"]),
        name=parent_doc["name"],
        email=parent_doc["email"],
        phone=parent_doc.get("phone"),
        children=[str(c) for c in parent_doc.get("children", [])],
        created_at=parent_doc["created_at"]
    )

# ==================== DOCTOR ROUTES ====================

@router.post("/doctor/create-child", response_model=dict)
async def create_child(child: ChildCreate, current_user: TokenData = Depends(get_current_doctor)):
    db = get_database()
    
    # Generate unique child code
    child_code = generate_child_code()
    while await db.child_codes.find_one({"code": child_code}):
        child_code = generate_child_code()
    
    child_doc = {
        "child_code": child_code,
        "name": child.name,
        "age": child.age,
        "gender": child.gender,
        "diagnosis": child.diagnosis,
        "assigned_doctor_id": ObjectId(current_user.user_id),
        "parent_ids": [],
        "created_at": datetime.utcnow()
    }
    
    # Insert child
    result = await db.children.insert_one(child_doc)
    child_id = result.inserted_id
    
    # Create child code record
    await db.child_codes.insert_one({
        "child_id": child_id,
        "code": child_code,
        "status": "active",
        "created_at": datetime.utcnow()
    })
    
    # Update doctor's assigned children
    await db.doctors.update_one(
        {"_id": ObjectId(current_user.user_id)},
        {"$addToSet": {"assigned_children": child_id}}
    )
    
    parent_created = False
    parent_email_sent = False
    
    # Handle parent linking/creation
    if child.parent_email:
        existing_parent = await db.parents.find_one({"email": child.parent_email})
        
        if existing_parent:
            # Link existing parent
            await db.children.update_one(
                {"_id": child_id},
                {"$addToSet": {"parent_ids": existing_parent["_id"]}}
            )
            await db.parents.update_one(
                {"_id": existing_parent["_id"]},
                {"$addToSet": {"children": child_id}}
            )
        else:
            # Auto-create parent account
            random_password = generate_random_password()
            parent_name = child.parent_name or f"Parent of {child.name}"
            
            parent_doc = {
                "name": parent_name,
                "email": child.parent_email,
                "phone": child.parent_phone,
                "password_hash": get_password_hash(random_password),
                "children": [child_id],
                "created_by_system": True,
                "created_at": datetime.utcnow()
            }
            
            parent_result = await db.parents.insert_one(parent_doc)
            parent_id = parent_result.inserted_id
            
            # Link parent to child
            await db.children.update_one(
                {"_id": child_id},
                {"$addToSet": {"parent_ids": parent_id}}
            )
            
            parent_created = True
            
            # Send email with credentials
            try:
                parent_email_sent = await send_parent_credentials(
                    child.parent_email,
                    random_password,
                    child.name
                )
            except Exception as e:
                print(f"Failed to send email: {e}")
    
    return {
        "success": True,
        "child_id": str(child_id),
        "child_code": child_code,
        "parent_created": parent_created,
        "email_sent": parent_email_sent,
        "message": "Child profile created successfully"
    }

@router.get("/doctor/children", response_model=List[dict])
async def get_doctor_children(current_user: TokenData = Depends(get_current_doctor)):
    db = get_database()
    
    children = await db.children.find({
        "assigned_doctor_id": ObjectId(current_user.user_id)
    }).to_list(100)
    
    return [{
        "id": str(child["_id"]),
        "child_code": child["child_code"],
        "name": child["name"],
        "age": child["age"],
        "gender": child["gender"],
        "diagnosis": child["diagnosis"],
        "created_at": child["created_at"].isoformat()
    } for child in children]

@router.get("/doctor/dashboard-stats")
async def get_doctor_dashboard_stats(current_user: TokenData = Depends(get_current_doctor)):
    db = get_database()
    
    # Get total children
    total_children = await db.children.count_documents({
        "assigned_doctor_id": ObjectId(current_user.user_id)
    })
    
    # Get today's sessions
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    todays_sessions = await db.therapy_logs.count_documents({
        "doctor_id": ObjectId(current_user.user_id),
        "session_date": {"$gte": today_start, "$lt": today_end}
    })
    
    # Get this week's sessions
    week_start = today_start - timedelta(days=today_start.weekday())
    weeks_sessions = await db.therapy_logs.count_documents({
        "doctor_id": ObjectId(current_user.user_id),
        "session_date": {"$gte": week_start}
    })
    
    # Get recent activity
    recent_logs = await db.therapy_logs.find({
        "doctor_id": ObjectId(current_user.user_id)
    }).sort("created_at", -1).limit(5).to_list(5)
    
    recent_activity = []
    for log in recent_logs:
        child = await db.children.find_one({"_id": log["child_id"]})
        if child:
            recent_activity.append({
                "child_name": child["name"],
                "date": log["session_date"].isoformat(),
                "duration": log.get("duration_minutes", 0)
            })
    
    return {
        "total_children": total_children,
        "todays_sessions": todays_sessions,
        "weeks_sessions": weeks_sessions,
        "recent_activity": recent_activity
    }

@router.get("/doctor/profile")
async def get_doctor_profile(current_user: TokenData = Depends(get_current_doctor)):
    db = get_database()
    doctor = await db.doctors.find_one({"_id": ObjectId(current_user.user_id)})
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    return {
        "id": str(doctor["_id"]),
        "name": doctor["name"],
        "email": doctor["email"],
        "specialization": doctor["specialization"],
        "total_children": len(doctor.get("assigned_children", []))
    }

# ==================== THERAPY LOG ROUTES ====================

@router.post("/therapy/add-log")
async def add_therapy_log(log: TherapyLogCreate, current_user: TokenData = Depends(get_current_doctor)):
    db = get_database()
    
    # Verify child exists and belongs to doctor
    child = await db.children.find_one({
        "_id": ObjectId(log.child_id),
        "assigned_doctor_id": ObjectId(current_user.user_id)
    })
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found or not assigned to you"
        )
    
    log_doc = {
        "child_id": ObjectId(log.child_id),
        "doctor_id": ObjectId(current_user.user_id),
        "session_date": log.session_date,
        "duration_minutes": log.duration_minutes,
        "activities_performed": log.activities_performed,
        "notes": log.notes,
        "communication_skills": log.communication_skills.dict() if log.communication_skills else None,
        "emotional_development": log.emotional_development.dict() if log.emotional_development else None,
        "social_skills": log.social_skills.dict() if log.social_skills else None,
        "behavior": log.behavior.dict() if log.behavior else None,
        "cognitive_skills": log.cognitive_skills.dict() if log.cognitive_skills else None,
        "sensory_processing": log.sensory_processing.dict() if log.sensory_processing else None,
        "daily_living_skills": log.daily_living_skills.dict() if log.daily_living_skills else None,
        "therapy_participation": log.therapy_participation.dict() if log.therapy_participation else None,
        "created_at": datetime.utcnow()
    }
    
    result = await db.therapy_logs.insert_one(log_doc)
    
    return {
        "success": True,
        "log_id": str(result.inserted_id),
        "message": "Therapy log added successfully"
    }

@router.get("/therapy/session/{session_id}")
async def get_therapy_session(session_id: str, current_user: TokenData = Depends(get_current_user)):
    db = get_database()
    
    # Get single session
    session = await db.therapy_logs.find_one({"_id": ObjectId(session_id)})
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Build domain scores
    domain_scores = {}
    domain_mapping = {
        "communication_skills": "communication",
        "emotional_development": "emotional",
        "social_skills": "social",
        "behavior": "behavior",
        "cognitive_skills": "cognitive",
        "sensory_processing": "sensory",
        "daily_living_skills": "daily_living",
        "therapy_participation": "social_participation"
    }
    
    for db_field, domain_key in domain_mapping.items():
        if session.get(db_field):
            domain_data = session[db_field]
            if isinstance(domain_data, dict):
                # Calculate percentage based on ratings
                ratings = list(domain_data.values())
                score_map = {"good": 100, "average": 60, "no_improvement": 20}
                scores = [score_map.get(r, 50) for r in ratings if r in score_map]
                if scores:
                    domain_scores[domain_key] = round(sum(scores) / len(scores))
    
    return {
        "id": str(session["_id"]),
        "session_date": session["session_date"].isoformat(),
        "duration_minutes": session["duration_minutes"],
        "activities_performed": session.get("activities_performed", ""),
        "goals_addressed": session.get("goals_addressed", ""),
        "notes": session.get("notes", ""),
        "recommendations": session.get("recommendations", ""),
        "domain_scores": domain_scores if domain_scores else None,
        "communication_skills": session.get("communication_skills"),
        "emotional_development": session.get("emotional_development"),
        "social_skills": session.get("social_skills"),
        "behavior": session.get("behavior"),
        "cognitive_skills": session.get("cognitive_skills"),
        "sensory_processing": session.get("sensory_processing"),
        "daily_living_skills": session.get("daily_living_skills"),
        "therapy_participation": session.get("therapy_participation"),
        "created_at": session["created_at"].isoformat()
    }

@router.get("/therapy/logs/{child_id}")
async def get_therapy_logs(child_id: str, current_user: TokenData = Depends(get_current_user)):
    db = get_database()
    
    # Get logs for child
    logs = await db.therapy_logs.find({
        "child_id": ObjectId(child_id)
    }).sort("session_date", -1).to_list(100)
    
    return [{
        "id": str(log["_id"]),
        "session_date": log["session_date"].isoformat(),
        "duration_minutes": log["duration_minutes"],
        "activities_performed": log["activities_performed"],
        "notes": log["notes"],
        "communication_skills": log.get("communication_skills"),
        "emotional_development": log.get("emotional_development"),
        "social_skills": log.get("social_skills"),
        "behavior": log.get("behavior"),
        "cognitive_skills": log.get("cognitive_skills"),
        "sensory_processing": log.get("sensory_processing"),
        "daily_living_skills": log.get("daily_living_skills"),
        "therapy_participation": log.get("therapy_participation"),
        "created_at": log["created_at"].isoformat()
    } for log in logs]

# ==================== REPORT ROUTES ====================

def calculate_domain_score(domain_data: dict) -> dict:
    """Calculate average score for a domain"""
    if not domain_data:
        return {"score": 0, "good": 0, "average": 0, "no_improvement": 0}
    
    scores = {"good": 0, "average": 0, "no_improvement": 0}
    total = 0
    
    def process_value(value):
        nonlocal total
        if value == "good":
            scores["good"] += 1
            total += 1
        elif value == "average":
            scores["average"] += 1
            total += 1
        elif value == "no_improvement":
            scores["no_improvement"] += 1
            total += 1
    
    def process_dict(d):
        for key, value in d.items():
            if isinstance(value, dict):
                process_dict(value)
            elif value:
                process_value(value)
    
    process_dict(domain_data)
    
    if total == 0:
        return {"score": 0, "good": 0, "average": 0, "no_improvement": 0, "total": 0}
    
    # Calculate weighted score (good=3, average=2, no_improvement=1)
    weighted_score = ((scores["good"] * 3) + (scores["average"] * 2) + (scores["no_improvement"] * 1)) / (total * 3) * 100
    
    return {
        "score": round(weighted_score, 1),
        "good": scores["good"],
        "average": scores["average"],
        "no_improvement": scores["no_improvement"],
        "total": total
    }

@router.get("/reports/weekly/{child_id}")
async def get_weekly_report(child_id: str, current_user: TokenData = Depends(get_current_user)):
    db = get_database()
    
    # Get child info
    child = await db.children.find_one({"_id": ObjectId(child_id)})
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    # Get last 7 days of logs
    week_end = datetime.utcnow()
    week_start = week_end - timedelta(days=7)
    
    logs = await db.therapy_logs.find({
        "child_id": ObjectId(child_id),
        "session_date": {"$gte": week_start, "$lte": week_end}
    }).to_list(100)
    
    # Calculate domain averages
    domain_totals = {
        "communication_skills": [],
        "emotional_development": [],
        "social_skills": [],
        "behavior": [],
        "cognitive_skills": [],
        "sensory_processing": [],
        "daily_living_skills": [],
        "therapy_participation": []
    }
    
    session_summaries = []
    total_duration = 0
    
    for log in logs:
        total_duration += log.get("duration_minutes", 0)
        
        session_summaries.append({
            "date": log["session_date"].isoformat(),
            "duration": log.get("duration_minutes", 0),
            "activities": log.get("activities_performed", ""),
            "notes": log.get("notes", "")
        })
        
        for domain in domain_totals.keys():
            if log.get(domain):
                score = calculate_domain_score(log[domain])
                if score["total"] > 0:
                    domain_totals[domain].append(score["score"])
    
    # Calculate averages
    domain_averages = {}
    for domain, scores in domain_totals.items():
        if scores:
            domain_averages[domain] = round(sum(scores) / len(scores), 1)
        else:
            domain_averages[domain] = 0
    
    # Calculate improvement trends
    improvement_trends = {}
    for domain in domain_totals.keys():
        if len(domain_totals[domain]) >= 2:
            first_half = domain_totals[domain][:len(domain_totals[domain])//2]
            second_half = domain_totals[domain][len(domain_totals[domain])//2:]
            
            if first_half and second_half:
                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)
                
                if second_avg > first_avg:
                    improvement_trends[domain] = "improving"
                elif second_avg < first_avg:
                    improvement_trends[domain] = "declining"
                else:
                    improvement_trends[domain] = "stable"
            else:
                improvement_trends[domain] = "stable"
        else:
            improvement_trends[domain] = "insufficient_data"
    
    return {
        "child_id": child_id,
        "child_name": child["name"],
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "total_sessions": len(logs),
        "total_duration": total_duration,
        "domain_averages": domain_averages,
        "session_summaries": session_summaries,
        "improvement_trends": improvement_trends
    }

@router.get("/reports/monthly/{child_id}")
async def get_monthly_report(child_id: str, month: Optional[int] = None, year: Optional[int] = None, current_user: TokenData = Depends(get_current_user)):
    db = get_database()
    
    # Get child info
    child = await db.children.find_one({"_id": ObjectId(child_id)})
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    # Default to current month
    now = datetime.utcnow()
    if not month:
        month = now.month
    if not year:
        year = now.year
    
    # Get month date range
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, month + 1, 1)
    
    logs = await db.therapy_logs.find({
        "child_id": ObjectId(child_id),
        "session_date": {"$gte": month_start, "$lt": month_end}
    }).sort("session_date", 1).to_list(500)
    
    # Calculate weekly trends
    weekly_trends = []
    current_week_start = month_start
    
    while current_week_start < month_end:
        week_end = current_week_start + timedelta(days=7)
        if week_end > month_end:
            week_end = month_end
        
        week_logs = [log for log in logs if current_week_start <= log["session_date"] < week_end]
        
        if week_logs:
            week_domain_scores = {}
            for domain in ["communication_skills", "emotional_development", "social_skills", 
                          "behavior", "cognitive_skills", "sensory_processing", 
                          "daily_living_skills", "therapy_participation"]:
                scores = []
                for log in week_logs:
                    if log.get(domain):
                        score = calculate_domain_score(log[domain])
                        if score["total"] > 0:
                            scores.append(score["score"])
                
                week_domain_scores[domain] = round(sum(scores) / len(scores), 1) if scores else 0
            
            weekly_trends.append({
                "week_start": current_week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "sessions": len(week_logs),
                "domain_scores": week_domain_scores
            })
        
        current_week_start = week_end
    
    # Calculate overall domain averages
    domain_averages = {}
    for domain in ["communication_skills", "emotional_development", "social_skills", 
                  "behavior", "cognitive_skills", "sensory_processing", 
                  "daily_living_skills", "therapy_participation"]:
        scores = []
        for log in logs:
            if log.get(domain):
                score = calculate_domain_score(log[domain])
                if score["total"] > 0:
                    scores.append(score["score"])
        
        domain_averages[domain] = round(sum(scores) / len(scores), 1) if scores else 0
    
    # Generate recommendations based on scores
    recommendations = []
    behavior_alerts = []
    
    for domain, score in domain_averages.items():
        domain_name = domain.replace("_", " ").title()
        if score < 40:
            recommendations.append(f"Focus more on {domain_name} - current progress is below expectations")
            if domain == "behavior":
                behavior_alerts.append(f"Behavioral concerns detected - score: {score}%")
        elif score < 60:
            recommendations.append(f"Continue working on {domain_name} - showing some progress")
        elif score >= 80:
            recommendations.append(f"Excellent progress in {domain_name} - maintain current approach")
    
    total_duration = sum(log.get("duration_minutes", 0) for log in logs)
    
    return {
        "child_id": child_id,
        "child_name": child["name"],
        "month": month,
        "year": year,
        "total_sessions": len(logs),
        "total_duration": total_duration,
        "domain_averages": domain_averages,
        "weekly_trends": weekly_trends,
        "recommendations": recommendations,
        "behavior_alerts": behavior_alerts
    }

# ==================== PARENT ROUTES ====================

@router.get("/parent/children")
async def get_parent_children(current_user: TokenData = Depends(get_current_parent)):
    db = get_database()
    
    parent = await db.parents.find_one({"_id": ObjectId(current_user.user_id)})
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    
    children = []
    for child_id in parent.get("children", []):
        # Handle both ObjectId and string formats
        if isinstance(child_id, str):
            child_id = ObjectId(child_id)
        child = await db.children.find_one({"_id": child_id})
        if child:
            children.append({
                "id": str(child["_id"]),
                "child_code": child["child_code"],
                "name": child["name"],
                "age": child["age"],
                "gender": child["gender"],
                "diagnosis": child["diagnosis"],
                "created_at": child["created_at"].isoformat()
            })
    
    return children

@router.get("/parent/dashboard-stats")
async def get_parent_dashboard_stats(current_user: TokenData = Depends(get_current_parent)):
    db = get_database()
    
    parent = await db.parents.find_one({"_id": ObjectId(current_user.user_id)})
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    
    children_ids = parent.get("children", [])
    
    # Get total sessions this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_sessions = await db.therapy_logs.count_documents({
        "child_id": {"$in": children_ids},
        "session_date": {"$gte": month_start}
    })
    
    # Get recent sessions
    recent_sessions = await db.therapy_logs.find({
        "child_id": {"$in": children_ids}
    }).sort("session_date", -1).limit(5).to_list(5)
    
    recent_activity = []
    for session in recent_sessions:
        child = await db.children.find_one({"_id": session["child_id"]})
        if child:
            recent_activity.append({
                "child_name": child["name"],
                "date": session["session_date"].isoformat(),
                "duration": session.get("duration_minutes", 0),
                "activities": session.get("activities_performed", "")[:100]
            })
    
    return {
        "total_children": len(children_ids),
        "monthly_sessions": monthly_sessions,
        "recent_activity": recent_activity
    }

@router.get("/parent/profile")
async def get_parent_profile(current_user: TokenData = Depends(get_current_parent)):
    db = get_database()
    parent = await db.parents.find_one({"_id": ObjectId(current_user.user_id)})
    
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    
    return {
        "id": str(parent["_id"]),
        "name": parent["name"],
        "email": parent["email"],
        "phone": parent.get("phone"),
        "total_children": len(parent.get("children", []))
    }

@router.post("/parent/link-child")
async def link_child_to_parent(request: dict, current_user: TokenData = Depends(get_current_parent)):
    db = get_database()
    child_code = request.get("child_code")
    
    if not child_code:
        raise HTTPException(status_code=400, detail="Child code is required")
    
    # Find the child code in database
    child_code_doc = await db.child_codes.find_one({
        "code": child_code,
        "status": "active"
    })
    
    if not child_code_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired child code"
        )
    
    child_id = child_code_doc["child_id"]
    
    # Get parent document
    parent = await db.parents.find_one({"_id": ObjectId(current_user.user_id)})
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    
    # Check if child is already linked to this parent (handle both ObjectId and string)
    existing_children = parent.get("children", [])
    already_linked = False
    for existing_id in existing_children:
        if isinstance(existing_id, str):
            existing_id = ObjectId(existing_id)
        if existing_id == child_id:
            already_linked = True
            break
    
    # Get child details
    child = await db.children.find_one({"_id": child_id})
    
    if already_linked:
        # Return success anyway - child is already linked
        return {
            "message": "Child is already linked to your account",
            "child_id": str(child_id),
            "child_name": child["name"] if child else "Unknown"
        }
    
    # Link child to parent
    await db.parents.update_one(
        {"_id": ObjectId(current_user.user_id)},
        {"$addToSet": {"children": child_id}}
    )
    
    return {
        "message": "Child linked successfully",
        "child_id": str(child_id),
        "child_name": child["name"] if child else "Unknown"
    }

# ==================== CHILD CODE ROUTES ====================

@router.post("/child/verify-code")
async def verify_child_code(code: str):
    db = get_database()
    
    child_code = await db.child_codes.find_one({
        "code": code,
        "status": "active"
    })
    
    if not child_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired child code"
        )
    
    child = await db.children.find_one({"_id": child_code["child_id"]})
    
    return {
        "valid": True,
        "child_name": child["name"] if child else "Unknown"
    }

@router.get("/child/{child_id}")
async def get_child_details(child_id: str, current_user: TokenData = Depends(get_current_user)):
    db = get_database()
    
    child = await db.children.find_one({"_id": ObjectId(child_id)})
    
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    return {
        "id": str(child["_id"]),
        "child_code": child["child_code"],
        "name": child["name"],
        "age": child["age"],
        "gender": child["gender"],
        "diagnosis": child["diagnosis"],
        "created_at": child["created_at"].isoformat()
    }
