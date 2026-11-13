"""All weights use recorded kilograms; missing baseline is NOT treated as a reduction."""
import json
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import AuditRecord, AuditItem, Campus, CampusZone, Department, PlasticCategory, RecyclingRecord, EvidenceFile


def load_rows(db: Session, campus_id: str, start: date | None = None, end: date | None = None):
    q = (db.query(AuditRecord, AuditItem, Department.name, CampusZone.name, PlasticCategory.name)
        .join(AuditItem, AuditItem.audit_id == AuditRecord.id)
        .join(Department, Department.id == AuditRecord.department_id)
        .join(CampusZone, CampusZone.id == AuditRecord.zone_id)
        .join(PlasticCategory, PlasticCategory.id == AuditItem.category_id)
        .filter(AuditRecord.campus_id == campus_id, AuditRecord.deleted_at.is_(None)))
    if start: q = q.filter(AuditRecord.audit_date >= start)
    if end: q = q.filter(AuditRecord.audit_date <= end)
    items = q.order_by(AuditRecord.audit_date.desc(), AuditRecord.created_at.desc()).all()
    # Confirmed outcomes only. Clamp to the weight of the audit item.
    confirmed = dict(db.query(RecyclingRecord.audit_item_id, func.sum(RecyclingRecord.confirmed_weight_kg))
                     .filter(RecyclingRecord.campus_id == campus_id, RecyclingRecord.status == 'confirmed')
                     .group_by(RecyclingRecord.audit_item_id).all())
    rows = []
    for a, item, dep, zone, category in items:
        weight = float(item.weight_kg)
        rows.append({
            'id': a.id, 'submission_id': a.submission_id, 'audit_date': a.audit_date.isoformat(),
            'campus_id': a.campus_id, 'department_id': a.department_id, 'department': dep,
            'zone_id': a.zone_id, 'zone': zone, 'auditor_name': a.auditor_name,
            'category_id': item.category_id, 'category': category, 'item_id': item.id,
            'item_type': item.item_type, 'item_count': item.item_count, 'weight_kg': weight,
            'single_use': item.single_use, 'recyclable': item.recyclable, 'disposal_method': item.disposal_method,
            'confirmed_recycled_kg': min(weight, float(confirmed.get(item.id) or 0)),
            'observations': a.observations, 'corrective_action': a.corrective_action,
            'created_by': a.created_by, 'created_at': a.created_at.isoformat(), 'updated_at': a.updated_at.isoformat()
        })
    return rows


def aggregates(rows: list[dict]):
    total = round(sum(r['weight_kg'] for r in rows), 4)
    single = round(sum(r['weight_kg'] for r in rows if r['single_use']), 4)
    recycled = round(sum(r['confirmed_recycled_kg'] for r in rows), 4)
    return {'total_kg': total, 'single_use_kg': single, 'recycled_kg': recycled,
            'single_use_pct': round(100 * single / total, 2) if total else None,
            'recycling_rate': round(100 * recycled / total, 2) if total else None,
            'audits': len({r['id'] for r in rows})}


def calculate(db: Session, campus_id: str, start: date, end: date):
    if start > end: raise ValueError('Start date must not exceed end date')
    rows = load_rows(db, campus_id, start, end)
    cur = aggregates(rows)
    span = (end - start).days + 1
    previous_start = start - timedelta(days=span)
    previous_end = start - timedelta(days=1)
    base_rows = load_rows(db, campus_id, previous_start, previous_end)
    base = aggregates(base_rows)
    has_baseline = base['audits'] > 0
    delta = round(base['total_kg'] - cur['total_kg'], 4) if has_baseline and cur['audits'] else None
    percent = round(100 * delta / base['total_kg'], 2) if delta is not None and base['total_kg'] > 0 else None
    by_day, by_category, by_zone, by_department = defaultdict(float), defaultdict(float), defaultdict(float), defaultdict(float)
    for r in rows:
        by_day[r['audit_date']] += r['weight_kg']
        by_category[r['category']] += r['weight_kg']
        by_zone[r['zone']] += r['weight_kg']
        by_department[r['department']] += r['weight_kg']
    campus = db.get(Campus, campus_id)
    default_weights={'reduction':30,'recycling':25,'single_use_reduction':15,'audit_completion':15,'evidence_quality':15}
    weights=json.loads(campus.score_weights_json) if campus else default_weights
    # Transparent provisional sustainability index. Reduction components require comparable baseline.
    # No score is produced if current/baseline observations are missing.
    score = None
    components = None
    if has_baseline and cur['audits'] and base['total_kg'] > 0:
        evidence = db.query(EvidenceFile).filter(EvidenceFile.campus_id == campus_id, EvidenceFile.audit_id.in_([r['id'] for r in rows])).all()
        approved = sum(1 for e in evidence if e.status == 'approved')
        evidence_quality = 100 * approved / len(evidence) if evidence else 0
        period_weekly_goal = max(1, (campus.audit_target_weekly if campus else 5) * span / 7)
        reduction_component = max(0, min(100, percent or 0))
        recycling_component = cur['recycling_rate'] or 0
        baseline_single_pct = base['single_use_pct'] or 0
        current_single_pct = cur['single_use_pct'] or 0
        single_reduction = max(0, min(100, 100 * (baseline_single_pct - current_single_pct) / baseline_single_pct)) if baseline_single_pct else 0
        audit_completion = min(100, 100 * cur['audits'] / period_weekly_goal)
        components = {'reduction': round(reduction_component,2), 'recycling': round(recycling_component,2), 'single_use_reduction': round(single_reduction,2), 'audit_completion': round(audit_completion,2), 'evidence_quality': round(evidence_quality,2)}
        score = round(sum(weights[name] * value/100 for name,value in components.items()),1)
    baseline_daily=defaultdict(float)
    current_daily=defaultdict(float)
    for r in base_rows:baseline_daily[r['audit_date']]+=r['weight_kg']
    for r in rows:current_daily[r['audit_date']]+=r['weight_kg']
    reduction_trend=[]
    if has_baseline and cur['audits']:
        baseline_cumulative=0.0;current_cumulative=0.0
        for i in range(span):
            bd=(previous_start+timedelta(days=i)).isoformat()
            cd=(start+timedelta(days=i)).isoformat()
            baseline_cumulative+=baseline_daily[bd];current_cumulative+=current_daily[cd]
            reduction_trend.append({'date':cd,'relative_day':i+1,'cumulative_reduction_kg':round(baseline_cumulative-current_cumulative,4)})
    return {'period': {'start':start.isoformat(),'end':end.isoformat()},
            'baseline': {'start': previous_start.isoformat(), 'end': previous_end.isoformat(), **base, 'available': has_baseline},
            'metrics': {**cur, 'reduction_kg':delta, 'reduction_pct':percent, 'sustainability_score':score},
            'score_components': components,
            'score_weights':weights,
            'score_disclaimer': 'Provisional EcoSphere index, not an officially certified environmental rating.',
            'reduction_trend':reduction_trend,
            'by_day': [{'date':d,'weight_kg':round(v,4)} for d,v in sorted(by_day.items())],
            'by_category': [{'name':n,'value':round(v,4)} for n,v in sorted(by_category.items(), key=lambda x:-x[1])],
            'by_zone': [{'name':n,'value':round(v,4)} for n,v in sorted(by_zone.items(), key=lambda x:-x[1])],
            'by_department': [{'name':n,'value':round(v,4)} for n,v in sorted(by_department.items(), key=lambda x:-x[1])],
            'rows': rows}
