"""Atomic CSV import: strict field mapping, full-file validation, no partial writes."""
import csv
import io
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from ..auth import campus_user, permit
from ..database import get_db
from ..models import User, Department, CampusZone, PlasticCategory, AuditRecord, AuditItem, AuditActivityLog
from ..schemas import AuditInput

router=APIRouter(prefix='/api',tags=['csv import'])
REQUIRED=['submission_id','audit_date','department','zone','auditor_name','category','item_type','item_count','weight_kg','single_use','recyclable','disposal_method']

def bool_value(x):
    v=str(x).strip().lower()
    if v in ('yes','y','true','1'):return True
    if v in ('no','n','false','0'):return False
    raise ValueError(f'Invalid boolean value: {x}')

@router.post('/audits/import',status_code=201)
async def import_csv(file:UploadFile=File(...),user:User=Depends(campus_user),db:Session=Depends(get_db)):
    permit(user,'admin','auditor')
    if not (file.filename or '').lower().endswith('.csv'):raise HTTPException(415,'Select a CSV file')
    raw=await file.read(1024*1024+1)
    if len(raw)>1024*1024:raise HTTPException(413,'Maximum CSV size is 1 MB')
    try:
        text=raw.decode('utf-8-sig')
        reader=csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or not set(REQUIRED).issubset(set(reader.fieldnames)):
            raise ValueError('CSV columns required: '+', '.join(REQUIRED))
        records=list(reader)
        if not records or len(records)>500:raise ValueError('Import must contain 1–500 records')
        deps={d.name.casefold():d.id for d in db.query(Department).filter_by(campus_id=user.campus_id)}
        zones={z.name.casefold():z.id for z in db.query(CampusZone).filter_by(campus_id=user.campus_id)}
        cats={c.name.casefold():c.id for c in db.query(PlasticCategory).filter(or_(PlasticCategory.campus_id==user.campus_id,PlasticCategory.campus_id.is_(None)))}
        prepared=[];seen=set()
        for i,row in enumerate(records,2):
            try:
                if None in row:raise ValueError('Unexpected extra CSV fields')
                d=deps.get((row['department'] or '').strip().casefold())
                z=zones.get((row['zone'] or '').strip().casefold())
                c=cats.get((row['category'] or '').strip().casefold())
                if not d or not z or not c:raise ValueError('Unknown department, zone or category; create them in Settings first')
                value=AuditInput(submission_id=row['submission_id'].strip(),audit_date=date.fromisoformat(row['audit_date'].strip()),
                    department_id=d,zone_id=z,category_id=c,auditor_name=row['auditor_name'].strip(),item_type=row['item_type'].strip(),
                    item_count=int(row['item_count']),weight_kg=row['weight_kg'],single_use=bool_value(row['single_use']),
                    recyclable=bool_value(row['recyclable']),disposal_method=row['disposal_method'].strip(),
                    observations=(row.get('observations') or '').strip(),corrective_action=(row.get('corrective_action') or '').strip())
                if value.submission_id in seen:raise ValueError('Duplicate submission ID within this import')
                seen.add(value.submission_id);prepared.append(value)
            except (KeyError,ValueError,TypeError,ValidationError) as exc:
                raise HTTPException(422,f'Row {i}: {exc}') from exc
    except HTTPException:raise
    except (UnicodeError,csv.Error,ValueError) as exc:raise HTTPException(422,str(exc)) from exc
    # Import as a single transaction; rollback every row if any DB uniqueness fails.
    try:
        for v in prepared:
            a=AuditRecord(submission_id=v.submission_id,campus_id=user.campus_id,department_id=v.department_id,zone_id=v.zone_id,
                audit_date=v.audit_date,auditor_name=v.auditor_name,observations=v.observations,corrective_action=v.corrective_action,created_by=user.id)
            db.add(a);db.flush()
            db.add(AuditItem(audit_id=a.id,category_id=v.category_id,item_type=v.item_type,item_count=v.item_count,weight_kg=v.weight_kg,
                single_use=v.single_use,recyclable=v.recyclable,disposal_method=v.disposal_method))
            db.add(AuditActivityLog(campus_id=user.campus_id,audit_id=a.id,actor_id=user.id,action='csv_import',after_json=v.model_dump_json()))
        db.commit()
    except IntegrityError as exc:
        db.rollback();raise HTTPException(409,'CSV contains submission IDs already present in this campus; no records were imported') from exc
    return {'imported':len(prepared),'status':'validated and committed atomically'}
