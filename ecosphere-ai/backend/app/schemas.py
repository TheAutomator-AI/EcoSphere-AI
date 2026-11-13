from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, ConfigDict

class CampusCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)

class NameCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    kind: str = Field(default='building', max_length=60)
    threshold_low_kg: Decimal = Field(default=5, ge=0)
    threshold_high_kg: Decimal = Field(default=20, gt=0)

class AuditInput(BaseModel):
    submission_id: str = Field(min_length=3, max_length=90, pattern=r'^[A-Za-z0-9_-]+$')
    audit_date: date
    department_id: str
    zone_id: str
    auditor_name: str = Field(min_length=2, max_length=120)
    category_id: str
    item_type: str = Field(min_length=2, max_length=160)
    item_count: int = Field(gt=0, le=10000000)
    weight_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=4)
    single_use: bool
    recyclable: bool
    disposal_method: str = Field(min_length=2, max_length=60)
    observations: str = Field(default='', max_length=3000)
    corrective_action: str = Field(default='', max_length=3000)

    @field_validator('audit_date')
    @classmethod
    def realistic_date(cls, v: date):
        if v > date.today() or v.year < 2000:
            raise ValueError('Audit date must be between 2000 and today')
        return v

class RecyclingInput(BaseModel):
    audit_item_id: str
    confirmed_weight_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=4)

class ReviewInput(BaseModel):
    status: str = Field(pattern='^(reviewed|approved|rejected)$')
    notes: str = Field(default='', max_length=1500)

class AskInput(BaseModel):
    question: str = Field(min_length=3, max_length=600)
    start: date | None = None
    end: date | None = None

class ActionInput(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(default='', max_length=3000)
    zone_id: str | None = None
    implemented_on: date | None = None
    status: str = Field(default='planned', pattern='^(planned|in_progress|completed)$')

class ScoringInput(BaseModel):
    audit_target_weekly: int = Field(ge=1, le=365)
    score_weights: dict[str,int]

    @field_validator('score_weights')
    @classmethod
    def valid_weights(cls, value):
        required={'reduction','recycling','single_use_reduction','audit_completion','evidence_quality'}
        if set(value)!=required or any(type(v) is not int or not 0<=v<=100 for v in value.values()) or sum(value.values())!=100:
            raise ValueError('Five percentage weights must be integers from 0 to 100 and total exactly 100')
        return value

class GoalInput(BaseModel):
    name: str = Field(min_length=3, max_length=180)
    target_kg: Decimal = Field(gt=0, max_digits=12, decimal_places=4)
    target_date: date

    @field_validator('target_date')
    @classmethod
    def future_target(cls, value: date):
        if value < date.today():
            raise ValueError('Goal deadline cannot be in the past')
        return value
