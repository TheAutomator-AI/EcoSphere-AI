export interface Audit {
 id:string; submission_id:string; audit_date:string; campus_id?:string; department_id:string; department:string;zone_id:string;zone:string;
 auditor_name:string;category_id:string; category:string; item_id:string; item_type:string;item_count:number; weight_kg:number;
 single_use:boolean;recyclable:boolean;disposal_method:string;confirmed_recycled_kg:number;observations:string; corrective_action:string;
 created_by?:string;created_at?:string; updated_at?:string;
}
export type Lookup = {id:string;name:string};
export type Zone = Lookup & {kind:string;threshold_low_kg:number;threshold_high_kg:number};
export type Workspace = {campus_id:string; zones:Zone[];departments:Lookup[];categories:Lookup[];scoring?:{audit_target_weekly:number;score_weights:Record<string,number>}};
export interface Metrics {total_kg:number;single_use_kg:number;recycled_kg:number;single_use_pct:number|null;recycling_rate:number|null;audits:number;reduction_kg:number|null;reduction_pct:number|null;sustainability_score:number|null}
export interface Analytics {period:{start:string;end:string};baseline:{start:string;end:string;total_kg:number;audits:number;single_use_kg:number;available:boolean};metrics:Metrics;
 score_components:Record<string,number>|null;score_weights:Record<string,number>;score_disclaimer:string;
 reduction_trend?:{date:string;relative_day:number;cumulative_reduction_kg:number}[];by_day:{date:string;weight_kg:number}[];by_category:{name:string;value:number}[];by_zone:{name:string;value:number}[];by_department:{name:string;value:number}[];rows:Audit[]}
export interface Evidence {id:string;audit_id:string|null;action_id?:string|null;stage?:'before'|'after'|'supporting';file_name:string;content_type:string;size_bytes:number;status:'pending'|'reviewed'|'approved'|'rejected';created_at:string;download_url:string}
export type View = 'overview'|'twin'|'audits'|'analytics'|'intelligence'|'categories'|'recycling'|'goals'|'reports'|'evidence'|'leaderboard'|'settings';
