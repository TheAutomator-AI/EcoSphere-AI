import json
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..auth import campus_user, permit
from ..database import get_db
from ..models import User, AuditRecord, AuditItem, Department, CampusZone, PlasticCategory, AuditActivityLog, RecyclingRecord
from ..schemas import AuditInput, RecyclingInput
from ..services.metrics import load_rows

router = APIRouter(prefix='/api', tags=['audits'])

def validate_references(db, campus, value):
    if not db.query(Department).filter_by(id=value.department_id,campus_id=campus).first(): raise HTTPException(422,'Department is not in your campus')
    if not db.query(CampusZone).filter_by(id=value.zone_id,campus_id=campus).first(): raise HTTPException(422,'Zone is not in your campus')
    c = db.get(PlasticCategory, value.category_id)
    if not c or c.campus_id not in (None,campus): raise HTTPException(422,'Invalid plastic category')

def log(db, record, user, event, before='', after=''):
    db.add(AuditActivityLog(campus_id=record.campus_id,audit_id=record.id,actor_id=user.id,action=event,before_json=before,after_json=after))

def one_record(db, user, audit_id):
    a = db.query(AuditRecord).filter(AuditRecord.id == audit_id, AuditRecord.campus_id == user.campus_id, AuditRecord.deleted_at.is_(None)).first()
    if not a: raise HTTPException(404,'Audit not found')
    return a

@router.get('/audits')
def list_audits(start: date | None = None, end: date | None = None, search: str = Query(default='', max_length=120), user: User = Depends(campus_user), db: Session = Depends(get_db)):
    if start and end and start > end: raise HTTPException(422,'Invalid date range')
    rows = load_rows(db, user.campus_id, start, end)
    needle = search.casefold().strip()
    if needle:
        rows = [r for r in rows if needle in ' '.join(str(r[k]) for k in ('submission_id','category','department','zone','item_type','auditor_name')).casefold()]
    return rows[:5000]

@router.post('/audits', status_code=201)
def create_audit(body: AuditInput, user: User = Depends(campus_user), db: Session = Depends(get_db)):
    permit(user,'admin','auditor')
    validate_references(db,user.campus_id,body)
    a=AuditRecord(submission_id=body.submission_id, campus_id=user.campus_id,department_id=body.department_id,zone_id=body.zone_id,
        audit_date=body.audit_date,auditor_name=body.auditor_name,observations=body.observations,corrective_action=body.corrective_action,created_by=user.id)
    db.add(a)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409,'Submission ID already exists for this campus') from exc
    item=AuditItem(audit_id=a.id,category_id=body.category_id,item_type=body.item_type,item_count=body.item_count,
        weight_kg=body.weight_kg,single_use=body.single_use,recyclable=body.recyclable,disposal_method=body.disposal_method)
    db.add(item);log(db,a,user,'create',after=body.model_dump_json())
    try:db.commit()
    except IntegrityError as exc:
        db.rollback();raise HTTPException(409,'Submission ID already exists for this campus') from exc
    return {'id':a.id,'submission_id':a.submission_id}

@router.get('/audits/{audit_id}')
def read_audit(audit_id:str,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    a=one_record(db,user,audit_id)
    return next((r for r in load_rows(db,user.campus_id) if r['id']==a.id), None)

@router.put('/audits/{audit_id}')
def edit_audit(audit_id:str,body:AuditInput,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    permit(user,'admin','auditor')
    a=one_record(db,user,audit_id)
    if a.created_by!=user.id and user.role!='admin':raise HTTPException(403,'Only the author or administrator can edit this audit')
    validate_references(db,user.campus_id,body)
    before=json.dumps({'submission_id':a.submission_id, 'audit_date':a.audit_date.isoformat(),'observations':a.observations})
    for k in ('submission_id','audit_date','department_id','zone_id','auditor_name','observations','corrective_action'):setattr(a,k,getattr(body,k))
    item=db.query(AuditItem).filter_by(audit_id=a.id).first()
    for k in ('category_id','item_type','item_count','weight_kg','single_use','recyclable','disposal_method'):setattr(item,k,getattr(body,k))
    # Changing the measured weight cannot invalidate an already confirmed recycling receipt.
    confirmed = sum(float(x.confirmed_weight_kg) for x in db.query(RecyclingRecord).filter_by(audit_item_id=item.id,status='confirmed').all())
    if confirmed > float(body.weight_kg):raise HTTPException(422,'New weight would be lower than already confirmed recycled weight')
    log(db,a,user,'update',before=before,after=body.model_dump_json())
    try:db.commit()
    except IntegrityError as exc:
        db.rollback();raise HTTPException(409,'Submission ID already exists for this campus') from exc
    return {'id':a.id, 'updated':True}

@router.delete('/audits/{audit_id}')
def delete_audit(audit_id:str,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    permit(user,'admin','auditor')
    a=one_record(db,user,audit_id)
    if a.created_by!=user.id and user.role!='admin':raise HTTPException(403,'Only the author or administrator can delete this audit')
    from ..models import now
    a.deleted_at=now();log(db,a,user,'soft_delete',before=json.dumps({'submission_id':a.submission_id}))
    db.commit();return {'deleted':True, 'archived':True}

@router.post('/recycling', status_code=201)
def add_recycling(body:RecyclingInput,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    permit(user,'admin','reviewer')
    item=(db.query(AuditItem).join(AuditRecord, AuditRecord.id==AuditItem.audit_id)
         .filter(AuditItem.id==body.audit_item_id,AuditRecord.campus_id==user.campus_id,AuditRecord.deleted_at.is_(None)).first())
    if not item:raise HTTPException(404,'Audit item not found')
    current=sum(float(r.confirmed_weight_kg) for r in db.query(RecyclingRecord).filter_by(audit_item_id=item.id,status='confirmed'))
    if current+float(body.confirmed_weight_kg) > float(item.weight_kg)+0.0000001:
        raise HTTPException(422,'Confirmed recycled mass cannot exceed measured item mass')
    from ..models import now
    r=RecyclingRecord(campus_id=user.campus_id,audit_item_id=item.id,confirmed_weight_kg=body.confirmed_weight_kg,status='confirmed',confirmed_by=user.id,confirmed_at=now())
    db.add(r);db.commit();return {'id':r.id,'status':'confirmed'}

@router.get('/audits/{audit_id}/history')
def audit_history(audit_id:str,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    a=db.query(AuditRecord).filter_by(id=audit_id,campus_id=user.campus_id).first()
    if not a:raise HTTPException(404,'Audit not found in campus')
    entries=db.query(AuditActivityLog).filter_by(audit_id=a.id,campus_id=user.campus_id).order_by(AuditActivityLog.created_at.desc()).all()
    return [{'action':x.action,'created_at':x.created_at.isoformat(),'actor_id':x.actor_id} for x in entries]
