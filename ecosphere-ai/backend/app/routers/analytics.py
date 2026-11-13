from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import campus_user
from ..models import User
from ..services.metrics import calculate
from ..schemas import AskInput

router=APIRouter(prefix='/api',tags=['analytics'])

def period(start:date|None,end:date|None):
    today=date.today()
    e=end or today
    s=start or (e-timedelta(days=29))
    if s>e or e>today or (e-s).days>366:raise HTTPException(422,'Invalid reporting period')
    return s,e

@router.get('/analytics')
def analytics(start:date|None=None,end:date|None=None,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    s,e=period(start,end)
    return calculate(db,user.campus_id,s,e)

@router.post('/assistant')
def assistant(body:AskInput,user:User=Depends(campus_user),db:Session=Depends(get_db)):
    s,e=period(body.start,body.end)
    report=calculate(db,user.campus_id,s,e)
    m=report['metrics']; q=body.question.lower()
    if not m['audits']:
        return {'method':'deterministic','answer':'No recorded audits exist in this date range. Enter measured plastic weights, audit dates and campus zones to receive evidence-based analysis.','confidence':'insufficient data'}
    zone=report['by_zone'][0] if report['by_zone'] else None
    cat=report['by_category'][0] if report['by_category'] else None
    if 'zone' in q or 'area' in q or 'where' in q or 'highest' in q:
        answer=f"{zone['name']} has the highest recorded plastic waste: {zone['value']:.2f} kg during {s} to {e}. This reflects recorded audits, not continuous monitoring." if zone else 'No zone-level data is available.'
    elif 'recycl' in q:
        answer=f"Confirmed recycling: {m['recycled_kg']:.2f} kg of {m['total_kg']:.2f} kg ({m['recycling_rate']:.1f}%). Only confirmed recycling entries count." if m['recycling_rate'] is not None else 'No measured weight is available to calculate a recycling rate.'
    elif 'reduc' in q or 'baseline' in q or 'compar' in q:
        delta=m['reduction_kg']
        answer=(f"Recorded waste {'decreased' if delta>=0 else 'increased'} by {abs(delta):.2f} kg versus the equally long prior period ({report['baseline']['start']} to {report['baseline']['end']})." if delta is not None else 'A comparable baseline and current period with recorded audits are required to calculate reduction.')
    elif 'plan' in q or 'action' in q or 'recommend' in q or 'cafeteria' in q:
        target=f"{cat['name']} ({cat['value']:.2f} kg)" if cat else 'the leading measured category'
        answer=f"Priority: target {target}. (1) Verify major single-use items through a 7-day audit. (2) Introduce refill/reuse options in the affected zones. (3) Document the implementation date and repeat the same sampling method in the next period. (4) Upload weighing and recycling receipts for reviewer approval. These are rule-based suggestions, not verified outcomes."
    elif 'forecast' in q or 'predict' in q:
        points=report['by_day']
        if len(points)<7:
            answer='A forecast requires at least 7 separate days with audit observations. The current sample is insufficient.'
        else:
            import numpy as np
            from sklearn.linear_model import LinearRegression
            vals=np.array([p['weight_kg'] for p in points]);xs=np.arange(len(vals)).reshape(-1,1)
            model=LinearRegression().fit(xs,vals)
            next_est=max(0,float(model.predict([[len(vals)]])[0]))
            error=float(np.std(vals-model.predict(xs)))
            answer=f"Exploratory next-observation forecast: {next_est:.2f} kg, indicative range {max(0,next_est-1.96*error):.2f}–{next_est+1.96*error:.2f} kg (1.96× in-sample residual SD, NOT a calibrated confidence interval). Gaps in audit dates and changes in sampling make this projection unreliable."
    else:
        answer=f"Between {s} and {e}, {m['audits']} audits recorded {m['total_kg']:.2f} kg plastic, including {m['single_use_kg']:.2f} kg single-use. The largest recorded category is {cat['name']} ({cat['value']:.2f} kg)." if cat else 'No category measurements available.'
    return {'method':'deterministic', 'answer':answer, 'confidence':'based on recorded audits; not independently verified'}
