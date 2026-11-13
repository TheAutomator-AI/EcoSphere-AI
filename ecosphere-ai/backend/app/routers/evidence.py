"""Private evidence uploads with signature checks and per-campus authorization."""
from pathlib import Path
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..auth import campus_user, permit
from ..models import User, AuditRecord, EvidenceFile, VerificationReview, ReductionAction, now
from ..schemas import ReviewInput

router=APIRouter(prefix='/api',tags=['evidence'])
SUPPORTED={'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp','application/pdf':'.pdf'}

def magic_ok(content:bytes, typ:str):
    return {'image/png':content.startswith(b'\x89PNG\r\n\x1a\n'), 'image/jpeg':content.startswith(b'\xff\xd8\xff'),
            'image/webp': content[:4]==b'RIFF' and content[8:12]==b'WEBP',
            'application/pdf':content.startswith(b'%PDF-')}.get(typ,False)

def storage_url(path):
    return settings.supabase_url.rstrip('/')+'/storage/v1/object/'+settings.supabase_storage_bucket+'/'+path

def storage_headers():
    return {'apikey':settings.supabase_service_role_key,'Authorization':'Bearer '+settings.supabase_service_role_key}

def file_view(e):
    return {'id':e.id,'audit_id':e.audit_id,'action_id':e.action_id,'stage':e.stage,'file_name':e.file_name,'content_type':e.content_type,
            'size_bytes':e.size_bytes,'status':e.status,'created_at':e.created_at.isoformat(), 'download_url':f'/api/evidence/{e.id}/file'}

@router.get('/evidence')
def list_evidence(user:User=Depends(campus_user),db:Session=Depends(get_db)):
    return [file_view(e) for e in db.query(EvidenceFile).filter_by(campus_id=user.campus_id).order_by(EvidenceFile.created_at.desc()).limit(500).all()]

@router.post('/evidence',status_code=201)
async def upload(audit_id:str|None=None,action_id:str|None=None,stage:str='supporting',file: UploadFile=File(...),user:User=Depends(campus_user),db:Session=Depends(get_db)):
    permit(user,'admin','auditor','reviewer')
    if bool(audit_id)==bool(action_id):raise HTTPException(422,'Provide an audit ID or an action ID, not both')
    if stage not in ('before','after','supporting'):raise HTTPException(422,'Invalid evidence stage')
    audit=db.query(AuditRecord).filter_by(id=audit_id,campus_id=user.campus_id,deleted_at=None).first() if audit_id else None
    action=db.query(ReductionAction).filter_by(id=action_id,campus_id=user.campus_id).first() if action_id else None
    if not audit and not action:raise HTTPException(404,'Audit/action not found in campus')
    if file.content_type not in SUPPORTED:raise HTTPException(415,'Only PNG, JPEG, WebP and PDF files are supported')
    content=await file.read(settings.max_file_bytes+1)
    if not content or len(content)>settings.max_file_bytes:raise HTTPException(413,'Empty or oversized file')
    if not magic_ok(content,file.content_type):raise HTTPException(415,'File content does not match its declared type')
    if file.content_type.startswith('image/'):
        try:
            with Image.open(BytesIO(content)) as im:
                if im.width * im.height > 25000000:raise HTTPException(413,'Image dimensions exceed the safe pixel limit')
                im.verify()
        except (UnidentifiedImageError, OSError) as exc:raise HTTPException(415,'Invalid image file') from exc
    original=Path(file.filename or 'evidence').name[:250]
    key=f'{user.campus_id}/{uuid.uuid4().hex}{SUPPORTED[file.content_type]}'
    if settings.supabase_url and settings.supabase_service_role_key:
        async with httpx.AsyncClient(timeout=30) as client:
            res=await client.post(storage_url(key),content=content,headers={**storage_headers(),'Content-Type':file.content_type,'x-upsert':'false'})
        if res.status_code>=300:raise HTTPException(502,'Private evidence storage upload failed')
    else:
        target=Path(settings.upload_dir)/key
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    e=EvidenceFile(campus_id=user.campus_id,audit_id=audit.id if audit else None,action_id=action.id if action else None,stage=stage,file_name=original,content_type=file.content_type,
        size_bytes=len(content),storage_path=key,status='pending',uploaded_by=user.id)
    db.add(e);db.commit();return file_view(e)

@router.get('/evidence/{evidence_id}/file')
async def get_file(evidence_id:str,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    e=db.query(EvidenceFile).filter_by(id=evidence_id,campus_id=user.campus_id).first()
    if not e:raise HTTPException(404,'Evidence not found')
    if settings.supabase_url and settings.supabase_service_role_key:
        async with httpx.AsyncClient(timeout=30) as client:
            res=await client.get(storage_url(e.storage_path),headers=storage_headers())
        if res.status_code!=200:raise HTTPException(502,'Evidence retrieval failed')
        content=res.content
    else:
        base=Path(settings.upload_dir).resolve()
        path=(base/e.storage_path).resolve()
        if not path.is_relative_to(base) or not path.is_file():raise HTTPException(404,'Evidence file unavailable')
        content=path.read_bytes()
    disposition='attachment' if e.content_type=='application/pdf' else 'inline'
    filename=f'{uuid.uuid4().hex}{SUPPORTED[e.content_type]}'
    return Response(content,media_type=e.content_type,headers={
        'Content-Disposition':f'{disposition}; filename="{filename}"',
        'Cache-Control':'private, no-store',
        'X-Content-Type-Options':'nosniff',
        'Content-Security-Policy':"default-src 'none'; sandbox"
    })


@router.post('/evidence/{evidence_id}/review')
def review(evidence_id:str,body:ReviewInput,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    permit(user,'admin','reviewer')
    e=db.query(EvidenceFile).filter_by(id=evidence_id,campus_id=user.campus_id).first()
    if not e:raise HTTPException(404,'Evidence not found')
    e.status=body.status
    db.add(VerificationReview(evidence_id=e.id,reviewer_id=user.id,status=body.status,notes=body.notes))
    db.commit();return file_view(e)
