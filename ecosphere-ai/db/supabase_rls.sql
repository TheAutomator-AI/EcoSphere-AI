-- EcoSphere AI: Supabase Row Level Security (PostgreSQL)
-- Run AFTER creating schema via SQLAlchemy/Alembic. Never run on SQLite.
-- Application API also enforces campus scoping; this blocks direct Data API access.
-- public.users.auth_sub holds the authenticated Supabase subject as text.

CREATE OR REPLACE FUNCTION public.eco_user_id()
RETURNS text LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT id FROM public.users WHERE auth_sub = auth.uid()::text LIMIT 1
$$;
CREATE OR REPLACE FUNCTION public.eco_campus_id()
RETURNS text LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT campus_id FROM public.users WHERE auth_sub = auth.uid()::text LIMIT 1
$$;
CREATE OR REPLACE FUNCTION public.eco_role()
RETURNS text LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT role FROM public.users WHERE auth_sub = auth.uid()::text LIMIT 1
$$;
REVOKE ALL ON FUNCTION public.eco_user_id() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.eco_campus_id() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.eco_role() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.eco_user_id(), public.eco_campus_id(), public.eco_role() TO authenticated;

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campuses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campus_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plastic_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recycling_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reduction_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.impact_measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verification_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sustainability_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leaderboard_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_activity_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY eco_users_self_read ON public.users FOR SELECT TO authenticated USING (auth_sub = auth.uid()::text);
-- Creating/updating identities and membership is server-controlled (no client write policy).
CREATE POLICY eco_campus_read ON public.campuses FOR SELECT TO authenticated USING (id = public.eco_campus_id());
CREATE POLICY eco_departments_read ON public.departments FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id());
CREATE POLICY eco_zones_read ON public.campus_zones FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id());
CREATE POLICY eco_categories_read ON public.plastic_categories FOR SELECT TO authenticated USING (campus_id IS NULL OR campus_id = public.eco_campus_id());
CREATE POLICY eco_audits_read ON public.audit_records FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id() AND deleted_at IS NULL);
CREATE POLICY eco_items_read ON public.audit_items FOR SELECT TO authenticated USING (EXISTS(SELECT 1 FROM public.audit_records a WHERE a.id = audit_id AND a.campus_id = public.eco_campus_id() AND a.deleted_at IS NULL));
CREATE POLICY eco_recycling_read ON public.recycling_records FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id());
CREATE POLICY eco_actions_read ON public.reduction_actions FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id());
CREATE POLICY eco_impact_read ON public.impact_measurements FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id());
CREATE POLICY eco_evidence_read ON public.evidence_files FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id());
CREATE POLICY eco_reviews_read ON public.verification_reviews FOR SELECT TO authenticated USING (EXISTS(SELECT 1 FROM public.evidence_files e WHERE e.id = evidence_id AND e.campus_id = public.eco_campus_id()));
CREATE POLICY eco_goals_read ON public.sustainability_goals FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id());
CREATE POLICY eco_leaderboard_read ON public.leaderboard_scores FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id());
CREATE POLICY eco_insights_read ON public.ai_insights FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id());
CREATE POLICY eco_reports_read ON public.report_history FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id());
CREATE POLICY eco_activity_read ON public.audit_activity_logs FOR SELECT TO authenticated USING (campus_id = public.eco_campus_id());

-- Authenticated users can add audited records in their own campus, but cannot claim another author.
CREATE POLICY eco_audits_insert ON public.audit_records FOR INSERT TO authenticated
  WITH CHECK (campus_id = public.eco_campus_id() AND created_by = public.eco_user_id() AND public.eco_role() IN ('admin','auditor'));
CREATE POLICY eco_audits_update ON public.audit_records FOR UPDATE TO authenticated
  USING (campus_id = public.eco_campus_id() AND (created_by = public.eco_user_id() OR public.eco_role() = 'admin'))
  WITH CHECK (campus_id = public.eco_campus_id() AND (created_by = public.eco_user_id() OR public.eco_role() = 'admin'));
CREATE POLICY eco_items_insert ON public.audit_items FOR INSERT TO authenticated
  WITH CHECK (public.eco_role() IN ('admin','auditor') AND EXISTS(SELECT 1 FROM public.audit_records a WHERE a.id = audit_id AND a.campus_id = public.eco_campus_id() AND a.created_by = public.eco_user_id()));
CREATE POLICY eco_items_update ON public.audit_items FOR UPDATE TO authenticated
  USING (EXISTS(SELECT 1 FROM public.audit_records a WHERE a.id = audit_id AND a.campus_id = public.eco_campus_id() AND (a.created_by=public.eco_user_id() OR public.eco_role()='admin')))
  WITH CHECK (EXISTS(SELECT 1 FROM public.audit_records a WHERE a.id = audit_id AND a.campus_id = public.eco_campus_id() AND (a.created_by=public.eco_user_id() OR public.eco_role()='admin')));
CREATE POLICY eco_evidence_insert ON public.evidence_files FOR INSERT TO authenticated
  WITH CHECK (campus_id = public.eco_campus_id() AND uploaded_by = public.eco_user_id() AND public.eco_role() IN ('admin','auditor','reviewer'));
-- Review status and recycling confirmations intentionally have no direct client write policy.
-- The authenticated FastAPI routes are the sole write authority for them.
-- No DELETE policies: the API performs soft-deletes and retains a modification log.
-- Important: a DB connection using postgres/service_role may bypass RLS; the API must always
-- check campus_id and user roles, regardless of database role.
