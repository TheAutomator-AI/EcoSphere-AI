import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, Date, DateTime, Integer, Boolean, Numeric, Text, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


def uid(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc)

def pk(): return mapped_column(String(36), primary_key=True, default=uid)
def ts(): return mapped_column(DateTime(timezone=True), default=now, nullable=False)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = pk()
    auth_sub: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, default='')
    full_name: Mapped[str] = mapped_column(String(120), default='')
    campus_id: Mapped[str | None] = mapped_column(ForeignKey('campuses.id'), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default='auditor', nullable=False)
    created_at: Mapped[datetime] = ts()
    __table_args__ = (CheckConstraint("role IN ('admin','auditor','reviewer','viewer')", name='valid_user_role'),)

class Campus(Base):
    __tablename__ = 'campuses'
    id: Mapped[str] = pk()
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    owner_auth_sub: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    audit_target_weekly: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    score_weights_json: Mapped[str] = mapped_column(Text, default='{"reduction":30,"recycling":25,"single_use_reduction":15,"audit_completion":15,"evidence_quality":15}', nullable=False)
    created_at: Mapped[datetime] = ts()
    __table_args__ = (CheckConstraint('audit_target_weekly > 0', name='target_positive'),)

class Department(Base):
    __tablename__ = 'departments'
    id: Mapped[str] = pk()
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = ts()
    __table_args__ = (UniqueConstraint('campus_id', 'name'),)

class CampusZone(Base):
    __tablename__ = 'campus_zones'
    id: Mapped[str] = pk()
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(60), default='building')
    threshold_low_kg: Mapped[float] = mapped_column(Numeric(12, 4), default=5)
    threshold_high_kg: Mapped[float] = mapped_column(Numeric(12, 4), default=20)
    created_at: Mapped[datetime] = ts()
    __table_args__ = (UniqueConstraint('campus_id', 'name'), CheckConstraint('threshold_low_kg >= 0 AND threshold_high_kg > threshold_low_kg', name='threshold_order'),)

class PlasticCategory(Base):
    __tablename__ = 'plastic_categories'
    id: Mapped[str] = pk()
    campus_id: Mapped[str | None] = mapped_column(ForeignKey('campuses.id'), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = ts()

class AuditRecord(Base):
    __tablename__ = 'audit_records'
    id: Mapped[str] = pk()
    submission_id: Mapped[str] = mapped_column(String(90), nullable=False)
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), nullable=False, index=True)
    department_id: Mapped[str] = mapped_column(ForeignKey('departments.id'), nullable=False)
    zone_id: Mapped[str] = mapped_column(ForeignKey('campus_zones.id'), nullable=False)
    audit_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    auditor_name: Mapped[str] = mapped_column(String(120), nullable=False)
    observations: Mapped[str] = mapped_column(Text, default='')
    corrective_action: Mapped[str] = mapped_column(Text, default='')
    created_by: Mapped[str] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = ts()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (UniqueConstraint('campus_id','submission_id', name='uq_campus_submission'), Index('ix_audit_campus_date', 'campus_id', 'audit_date'),)

class AuditItem(Base):
    __tablename__ = 'audit_items'
    id: Mapped[str] = pk()
    audit_id: Mapped[str] = mapped_column(ForeignKey('audit_records.id'), nullable=False, index=True)
    category_id: Mapped[str] = mapped_column(ForeignKey('plastic_categories.id'), nullable=False)
    item_type: Mapped[str] = mapped_column(String(160), nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    single_use: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    recyclable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disposal_method: Mapped[str] = mapped_column(String(60), nullable=False)
    __table_args__ = (CheckConstraint('weight_kg > 0', name='positive_weight'), CheckConstraint('item_count > 0', name='positive_items'),)

class RecyclingRecord(Base):
    __tablename__ = 'recycling_records'
    id: Mapped[str] = pk()
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), nullable=False, index=True)
    audit_item_id: Mapped[str] = mapped_column(ForeignKey('audit_items.id'), nullable=False, index=True)
    confirmed_weight_kg: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    confirmed_by: Mapped[str | None] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = ts()
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (CheckConstraint('confirmed_weight_kg > 0', name='positive_recycled'), CheckConstraint("status IN ('pending','confirmed','rejected')", name='valid_recycle_status'),)

class ReductionAction(Base):
    __tablename__ = 'reduction_actions'
    id: Mapped[str] = pk()
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), index=True)
    zone_id: Mapped[str | None] = mapped_column(ForeignKey('campus_zones.id'))
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, default='')
    implemented_on: Mapped[datetime | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(25), default='planned')
    created_at: Mapped[datetime] = ts()

class ImpactMeasurement(Base):
    __tablename__ = 'impact_measurements'
    id: Mapped[str] = pk()
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), index=True)
    action_id: Mapped[str] = mapped_column(ForeignKey('reduction_actions.id'))
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    measured_on: Mapped[datetime] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Numeric(12,4), nullable=False)
    measurement_notes: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = ts()
    __table_args__ = (CheckConstraint('weight_kg >= 0', name='nonnegative_impact'),)

class EvidenceFile(Base):
    __tablename__ = 'evidence_files'
    id: Mapped[str] = pk()
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), index=True)
    audit_id: Mapped[str | None] = mapped_column(ForeignKey('audit_records.id'), index=True)
    action_id: Mapped[str | None] = mapped_column(ForeignKey('reduction_actions.id'))
    stage: Mapped[str] = mapped_column(String(16),default='supporting',nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(60), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default='pending')
    uploaded_by: Mapped[str] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = ts()
    __table_args__ = (CheckConstraint("status IN ('pending','reviewed','approved','rejected')", name='valid_evidence_status'),)

class VerificationReview(Base):
    __tablename__ = 'verification_reviews'
    id: Mapped[str] = pk()
    evidence_id: Mapped[str] = mapped_column(ForeignKey('evidence_files.id'), index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = ts()

class SustainabilityGoal(Base):
    __tablename__ = 'sustainability_goals'
    id: Mapped[str] = pk()
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    target_kg: Mapped[float | None] = mapped_column(Numeric(12,4))
    target_date: Mapped[datetime | None] = mapped_column(Date)
    created_at: Mapped[datetime] = ts()
    __table_args__ = (CheckConstraint('target_kg IS NULL OR target_kg > 0', name='positive_goal_target'),)

class LeaderboardScore(Base):
    __tablename__ = 'leaderboard_scores'
    id: Mapped[str] = pk()
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), index=True)
    department_id: Mapped[str] = mapped_column(ForeignKey('departments.id'), index=True)
    period_start: Mapped[datetime] = mapped_column(Date)
    score: Mapped[float] = mapped_column(Numeric(6,2))
    calculation_details: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = ts()

class AIInsight(Base):
    __tablename__ = 'ai_insights'
    id: Mapped[str] = pk()
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), index=True)
    period_start: Mapped[datetime] = mapped_column(Date)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str] = mapped_column(String(60), default='deterministic')
    created_at: Mapped[datetime] = ts()

class ReportHistory(Base):
    __tablename__ = 'report_history'
    id: Mapped[str] = pk()
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), index=True)
    period_start: Mapped[datetime] = mapped_column(Date)
    period_end: Mapped[datetime] = mapped_column(Date)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = ts()

class AuditActivityLog(Base):
    __tablename__ = 'audit_activity_logs'
    id: Mapped[str] = pk()
    campus_id: Mapped[str] = mapped_column(ForeignKey('campuses.id'), index=True)
    audit_id: Mapped[str] = mapped_column(ForeignKey('audit_records.id'), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    before_json: Mapped[str] = mapped_column(Text, default='')
    after_json: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = ts()
