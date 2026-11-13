import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from ..auth import current_user, campus_user, permit
from ..models import User, Campus, Department, CampusZone, PlasticCategory, SustainabilityGoal
from ..schemas import CampusCreate, NameCreate, ScoringInput, GoalInput

router = APIRouter(prefix='/api', tags=['workspace'])
DEFAULT_CATEGORIES = ['PET bottles','Plastic bags','Food packaging','Disposable cups','Plastic straws','Plastic cutlery','Wrappers','Stationery plastics','Other plastic waste']

@router.get('/me')
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    campus = db.get(Campus, user.campus_id) if user.campus_id else None
    return {'id': user.id, 'email':user.email, 'role':user.role, 'campus': {'id':campus.id,'name':campus.name} if campus else None}

@router.post('/campuses', status_code=201)
def create_campus(body: CampusCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.campus_id: raise HTTPException(409,'You already belong to a campus')
    campus = Campus(name=body.name.strip(), owner_auth_sub=user.auth_sub)
    db.add(campus)
    db.flush()
    user.campus_id, user.role = campus.id, 'admin'
    for n in DEFAULT_CATEGORIES:
        db.add(PlasticCategory(name=n, campus_id=campus.id))
    db.commit()
    return {'id':campus.id,'name':campus.name}

@router.get('/workspace')
def workspace(user: User = Depends(campus_user), db: Session = Depends(get_db)):
    zones = db.query(CampusZone).filter(CampusZone.campus_id==user.campus_id).order_by(CampusZone.name).all()
    deps = db.query(Department).filter(Department.campus_id==user.campus_id).order_by(Department.name).all()
    categories = db.query(PlasticCategory).filter(or_(PlasticCategory.campus_id==user.campus_id, PlasticCategory.campus_id.is_(None))).order_by(PlasticCategory.name).all()
    return {'campus_id':user.campus_id,
            'zones':[{'id':z.id,'name':z.name,'kind':z.kind,'threshold_low_kg':float(z.threshold_low_kg),'threshold_high_kg':float(z.threshold_high_kg)} for z in zones],
            'departments':[{'id':d.id,'name':d.name} for d in deps],
            'categories':[{'id':c.id,'name':c.name} for c in categories],
            'scoring':{'audit_target_weekly':db.get(Campus,user.campus_id).audit_target_weekly, 'score_weights':json.loads(db.get(Campus,user.campus_id).score_weights_json)}}

@router.post('/departments', status_code=201)
def create_department(body: NameCreate, user: User = Depends(campus_user), db: Session = Depends(get_db)):
    permit(user,'admin')
    name = body.name.strip()
    if db.query(Department).filter_by(campus_id=user.campus_id,name=name).first(): raise HTTPException(409,'Department already exists')
    entity = Department(campus_id=user.campus_id, name=name)
    db.add(entity); db.commit(); return {'id':entity.id,'name':entity.name}

@router.post('/zones', status_code=201)
def create_zone(body: NameCreate, user: User = Depends(campus_user), db: Session = Depends(get_db)):
    permit(user,'admin')
    if body.threshold_high_kg <= body.threshold_low_kg: raise HTTPException(422,'Upper threshold must be greater than lower threshold')
    name=body.name.strip()
    if db.query(CampusZone).filter_by(campus_id=user.campus_id,name=name).first():raise HTTPException(409,'Zone already exists')
    entity=CampusZone(campus_id=user.campus_id,name=name,kind=body.kind,threshold_low_kg=body.threshold_low_kg, threshold_high_kg=body.threshold_high_kg)
    db.add(entity); db.commit(); return {'id':entity.id,'name':entity.name}

@router.post('/categories', status_code=201)
def create_category(body: NameCreate,user: User=Depends(campus_user),db:Session=Depends(get_db)):
    permit(user,'admin')
    name=body.name.strip()
    if db.query(PlasticCategory).filter_by(campus_id=user.campus_id,name=name).first():raise HTTPException(409,'Category already exists')
    c=PlasticCategory(campus_id=user.campus_id,name=name);db.add(c);db.commit();return {'id':c.id,'name':c.name}

@router.put('/scoring')
def update_scoring(body: ScoringInput, user: User = Depends(campus_user), db: Session = Depends(get_db)):
    permit(user,'admin')
    campus = db.get(Campus,user.campus_id)
    campus.audit_target_weekly=body.audit_target_weekly
    campus.score_weights_json=json.dumps(body.score_weights,sort_keys=True)
    db.commit()
    return {'audit_target_weekly':campus.audit_target_weekly,'score_weights':body.score_weights}


@router.get('/goals')
def list_goals(user: User = Depends(campus_user), db: Session = Depends(get_db)):
    goals = db.query(SustainabilityGoal).filter_by(campus_id=user.campus_id).order_by(SustainabilityGoal.created_at.desc()).all()
    return [{'id':goal.id,'name':goal.name,'target_kg':float(goal.target_kg),
             'target_date':goal.target_date.isoformat(),'created_at':goal.created_at.isoformat()} for goal in goals]

@router.post('/goals', status_code=201)
def create_goal(body: GoalInput, user: User = Depends(campus_user), db: Session = Depends(get_db)):
    permit(user,'admin','auditor')
    goal = SustainabilityGoal(campus_id=user.campus_id,name=body.name.strip(),
                              target_kg=body.target_kg,target_date=body.target_date)
    db.add(goal)
    db.commit()
    return {'id':goal.id,'name':goal.name,'target_kg':float(goal.target_kg),
            'target_date':goal.target_date.isoformat(),'created_at':goal.created_at.isoformat()}
