import csv
import io
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Campus, ReportHistory, ReductionAction, ImpactMeasurement, EvidenceFile
from ..auth import campus_user
from ..services.metrics import calculate
from .analytics import period

router=APIRouter(prefix='/api',tags=['reports'])

def record(db,user,start,end,typ):
    db.add(ReportHistory(campus_id=user.campus_id,period_start=start,period_end=end,file_type=typ,created_by=user.id));db.commit()

@router.get('/reports/csv')
def csv_report(start:date|None=None,end:date|None=None,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    s,e=period(start,end);rows=calculate(db,user.campus_id,s,e)['rows']
    buffer=io.StringIO();cols=['submission_id','audit_date','department','zone','auditor_name','category','item_type','item_count','weight_kg','single_use','recyclable','disposal_method','confirmed_recycled_kg','observations','corrective_action','created_at','updated_at']
    writer=csv.DictWriter(buffer,fieldnames=cols,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    # Escape spreadsheet formula injection for imported free-text cells.
    # Numeric fields are controlled by schemas; escape only text to keep numeric values usable.
    buffer2=io.StringIO();writer2=csv.DictWriter(buffer2,fieldnames=cols);writer2.writeheader()
    buffer.seek(0)
    for r in csv.DictReader(buffer):
        for col in ['department','zone','auditor_name','category','item_type','disposal_method','observations','corrective_action','submission_id']:
            if r[col].lstrip().startswith(('=','+','-','@')):r[col]="'"+r[col]
        writer2.writerow(r)
    record(db,user,s,e,'csv')
    return StreamingResponse(iter([buffer2.getvalue().encode('utf-8-sig')]),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="ecosphere-audits-{s}-{e}.csv"','Cache-Control':'no-store'})

@router.get('/reports/pdf')
def pdf_report(start:date|None=None,end:date|None=None,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    s,e=period(start,end);data=calculate(db,user.campus_id,s,e);m=data['metrics'];b=data['baseline']
    campus=db.get(Campus,user.campus_id)
    from xml.sax.saxutils import escape
    out=io.BytesIO()
    doc=SimpleDocTemplate(out,pagesize=(595.28,841.89),rightMargin=48,leftMargin=48,topMargin=48,bottomMargin=48,title='EcoSphere AI Environmental Audit Report',author='Raja')
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='EcoTitle',parent=styles['Title'],textColor=colors.HexColor('#087f5b'),fontSize=21,leading=27,spaceAfter=13))
    styles.add(ParagraphStyle(name='EcoSection',parent=styles['Heading2'],textColor=colors.HexColor('#087f5b'),spaceBefore=16))
    story=[Paragraph('ECOSPHERE AI | PLASTIC-FREE CAMPUS AUDIT',styles['EcoTitle']),Paragraph('Intelligence for a Plastic-Free Tomorrow.',styles['Normal']),Spacer(1,16)]
    def section(title,text):story.extend([Paragraph(title,styles['EcoSection']),Paragraph(escape(str(text)),styles['BodyText']),Spacer(1,8)])
    section('01 · Project details',f'Campus: {campus.name}. Project Developer: Raja. Platform: EcoSphere AI. Year: 2026. SDG 12 (primary); SDGs 11, 13, 14, 15 (supporting).')
    section('02 · Executive summary',f"{m['audits']} audits recorded {m['total_kg']:.3f} kg plastic waste. Single-use: {m['single_use_kg']:.3f} kg. Confirmed recycled: {m['recycled_kg']:.3f} kg. Recycling rate: {str(m['recycling_rate'])+'%' if m['recycling_rate'] is not None else 'not available'}.")
    section('03 · Environmental problem','Single-use plastic consumption and inconsistent waste segregation create campus waste streams that must be measured before improvements can be evaluated.')
    section('04 · Project objectives','Document sources of plastic waste, reduce avoidable single-use items, verify recycling outcomes, and compare measured waste over consistent periods.')
    section('05 · Audit methodology','Auditors enter item counts, weighed kilograms, category, campus zone, date and disposal route. Measurements are user-reported; photographs and recycling receipts have a separate human-review status. Collection methods may vary.')
    section('06 · Data collection period',f'{s} through {e} inclusive; {m["audits"]} unique audits in the selected campus. No unrecorded days are assumed to have zero real waste.')
    section('07 · Baseline measurements',f"Prior matched period {b['start']} through {b['end']}: {b['total_kg']:.3f} kg from {b['audits']} audits." if b['available'] else 'No comparable previous-period audit data. Baseline reduction and reduction percentage cannot be calculated.')
    section('08 · Current measurements',f"Recorded plastic: {m['total_kg']:.3f} kg; single-use plastic: {m['single_use_kg']:.3f} kg; confirmed recycled: {m['recycled_kg']:.3f} kg.")
    section('09 · Plastic waste analysis','Weights by plastic category (kilograms); these categories reflect observed measurements only.')
    if data['by_category']:
        cells=[['Category','Recorded weight (kg)']]+[[escape(c['name']),f"{c['value']:.3f}"] for c in data['by_category']]
        table=Table(cells,colWidths=[310,185],repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0b4737')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#edf7f1')]),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8)]))
        story.append(table)
        top=data['by_category'][:6];chart=Drawing(495,25+len(top)*29)
        highest=max(x['value'] for x in top)
        for i,item in enumerate(top):
            y=23+(len(top)-1-i)*29
            chart.add(String(2,y+3,item['name'][:24],fontSize=9,fillColor=colors.HexColor('#314b3c')))
            chart.add(Rect(175,y,250*item['value']/highest,13,fillColor=colors.HexColor('#16a87b'),strokeColor=None))
            chart.add(String(min(455,181+250*item['value']/highest),y+3,f"{item['value']:.2f}",fontSize=8,fillColor=colors.HexColor('#286644')))
        story.extend([Spacer(1,13),chart])
    else:
        story.append(Paragraph('No measured plastic categories were recorded in the report period.',styles['BodyText']))
    actions=db.query(ReductionAction).filter_by(campus_id=user.campus_id).order_by(ReductionAction.created_at.desc()).limit(25).all()
    section('10 · Corrective actions',f'{len(actions)} recorded intervention(s) are listed here. These do not automatically constitute verified environmental benefits.')
    for a in actions[:12]:
        story.append(Paragraph(escape(f"{a.title} — {a.status}. {a.description[:220]}"),styles['BodyText']))
        story.append(Spacer(1,5))
    reduction=m['reduction_kg']
    section('11 · Measured environmental impact',f"Observed plastic waste {'decreased' if reduction>=0 else 'increased'} by {abs(reduction):.3f} kg ({m['reduction_pct']}%) versus a matched prior period." if reduction is not None else 'Impact unavailable: both baseline and current-period audit records are required for a comparable difference.')
    evidence=db.query(EvidenceFile).filter_by(campus_id=user.campus_id).order_by(EvidenceFile.created_at.desc()).limit(25).all()
    before=sum(1 for x in evidence if x.stage=='before');after=sum(1 for x in evidence if x.stage=='after');approved=sum(1 for x in evidence if x.status=='approved')
    section('12 · Before-and-after evidence',f'{before} before images/documents; {after} after images/documents; {approved} approved evidence file(s) among the {len(evidence)} most recent file(s) checked. Files not marked approved must not be presented as verified.')
    for a in actions[:8]:
        measures=db.query(ImpactMeasurement).filter_by(action_id=a.id,campus_id=user.campus_id).order_by(ImpactMeasurement.measured_on).all()
        pre=[x for x in measures if x.label=='before'];post=[x for x in measures if x.label=='after']
        if pre or post:
            text=f"{a.title}: BEFORE {float(pre[-1].weight_kg):.3f} kg ({pre[-1].measured_on})" if pre else f'{a.title}: BEFORE missing'
            text+=f" / AFTER {float(post[-1].weight_kg):.3f} kg ({post[-1].measured_on})" if post else ' / AFTER missing'
            story.append(Paragraph(escape(text+' — compare collection effort before interpreting the difference.'),styles['BodyText']))
    section('13 · Limitations','These values reflect self-reported observations, not certified whole-campus waste totals or continuous sensor monitoring. Sampling and weighing conditions may differ. Recycling requires an authorized confirmation. No carbon or ecological savings are inferred here.')
    section('14 · Recommendations','Prioritize high-weight categories and zones; establish refill and reuse choices; document implementation dates; repeat audits with comparable effort; request independent review of weighing and recycling evidence.')
    section('15 · Conclusion','The campus can use recorded audit trends and approved documentation to guide its next intervention. The provisional EcoSphere index is not an externally certified environmental rating.')
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#6b7280'))
        canvas.drawString(48,30,'EcoSphere AI | Designed & Developed by Raja © 2026')
        canvas.drawRightString(548,30,str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    out.seek(0);record(db,user,s,e,'pdf')
    return StreamingResponse(out,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="ecosphere-audit-{s}-{e}.pdf"','Cache-Control':'no-store'})
