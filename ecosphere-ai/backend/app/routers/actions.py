"""Interventions and directly measured before/after impact observations."""
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import campus_user, permit
from ..models import User, ReductionAction, ImpactMeasurement, CampusZone
from ..schemas import ActionInput

router=APIRouter(prefix='/api',tags=['actions'])
class MeasurementInput(BaseModel):
    label: str = Field(pattern='^(before|after)$')
    measured_on: date
    weight_kg: Decimal = Field(ge=0,max_digits=12,decimal_places=4)
    measurement_notes: str = Field(default='',max_length=1500)
    @field_validator('measured_on')
    @classmethod
    def date_ok(cls,v):
        if v > date.today() or v.year < 2000:raise ValueError('Invalid measurement date')
        return v

def action_view(action):return {'id':action.id,'title':action.title,'description':action.description,'zone_id':action.zone_id,'implemented_on':action.implemented_on.isoformat() if action.implemented_on else None,'status':action.status,'created_at':action.created_at.isoformat()}

@router.get('/actions')
def list_actions(user:User=Depends(campus_user),db:Session=Depends(get_db)):
    return [action_view(x) for x in db.query(ReductionAction).filter_by(campus_id=user.campus_id).order_by(ReductionAction.created_at.desc()).all()]

@router.post('/actions',status_code=201)
def add_action(body:ActionInput,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    permit(user,'admin','auditor')
    if body.zone_id and not db.query(CampusZone).filter_by(id=body.zone_id,campus_id=user.campus_id).first():raise HTTPException(422,'Zone does not belong to campus')
    if body.implemented_on and body.implemented_on>date.today():raise HTTPException(422,'Implementation date cannot be in the future')
    a=ReductionAction(campus_id=user.campus_id,**body.model_dump());db.add(a);db.commit();return action_view(a)

@router.get('/actions/{action_id}/measurements')
def action_measurements(action_id:str,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    a=db.query(ReductionAction).filter_by(id=action_id,campus_id=user.campus_id).first()
    if not a:raise HTTPException(404,'Action not found')
    entries=db.query(ImpactMeasurement).filter_by(action_id=a.id,campus_id=user.campus_id).order_by(ImpactMeasurement.measured_on).all()
    rows=[{'id':v.id,'label':v.label,'measured_on':v.measured_on.isoformat(),'weight_kg':float(v.weight_kg),'measurement_notes':v.measurement_notes} for v in entries]
    before=[x for x in rows if x['label']=='before']
    after=[x for x in rows if x['label']=='after']
    # A reduction is only meaningful when the observation durations and conditions match.
    return {'entries':rows,'comparison':{'before_kg':before[-1]['weight_kg'] if before else None,'after_kg':after[-1]['weight_kg'] if after else None,'reduction_kg':round(before[-1]['weight_kg']-after[-1]['weight_kg'],4) if before and after else None,'caution':'Measure equal time periods with the same collection method before claiming impact.'}}

@router.post('/actions/{action_id}/measurements',status_code=201)
def add_measurement(action_id:str,body:MeasurementInput,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    permit(user,'admin','auditor')
    a=db.query(ReductionAction).filter_by(id=action_id,campus_id=user.campus_id).first()
    if not a:raise HTTPException(404,'Action not found')
    entry=ImpactMeasurement(campus_id=user.campus_id,action_id=a.id,**body.model_dump())
    db.add(entry);db.commit();return {'id':entry.id,'label':entry.label,'weight_kg':float(entry.weight_kg)}
