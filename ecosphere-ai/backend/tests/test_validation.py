from datetime import date, timedelta
import pytest
from pydantic import ValidationError
from app.schemas import AuditInput

base={'submission_id':'A-001','audit_date':date.today(),'department_id':'d','zone_id':'z','auditor_name':'Audit Lead','category_id':'c','item_type':'PET Bottle','item_count':2,'weight_kg':'0.25','single_use':True,'recyclable':True,'disposal_method':'segregated'}

def test_weight_must_be_positive():
    with pytest.raises(ValidationError):AuditInput(**{**base,'weight_kg':'-1'})

def test_future_date_rejected():
    with pytest.raises(ValidationError):AuditInput(**{**base,'audit_date':date.today()+timedelta(days=1)})
