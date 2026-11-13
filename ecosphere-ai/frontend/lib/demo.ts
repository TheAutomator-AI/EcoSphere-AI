/** DEMONSTRATION ONLY — fixed simulated observations, never sent to the API. */
import type { Analytics, Audit, Workspace } from './types';
const categories=['PET bottles','Plastic bags','Food packaging','Disposable cups','Plastic straws','Plastic cutlery','Wrappers','Stationery plastics','Other plastic waste'];
const zoneNames=['Cafeteria','Academic Block','Library','Hostel','Innovation Lab','Campus Garden'];
const depNames=['Computer Science','Mechanical Engineering','Electrical Engineering','Business Studies'];
export const demoWorkspace:Workspace={campus_id:'SIMULATED-DEMO',zones:zoneNames.map((name,i)=>({id:`z-${i}`,name,kind:'building',threshold_low_kg:4,threshold_high_kg:12})),
 departments:depNames.map((name,i)=>({id:`d-${i}`,name})),categories:categories.map((name,i)=>({id:`c-${i}`,name})),scoring:{audit_target_weekly:5,score_weights:{reduction:30,recycling:25,single_use_reduction:15,audit_completion:15,evidence_quality:15}}};
function iso(offset:number){const d=new Date();d.setHours(12,0,0,0);d.setDate(d.getDate()+offset);return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-')}
export const demoAudits:Audit[]=Array.from({length:78},(_,i)=>{
 const day=-Math.floor(i/2),zone=i%6,cat=(i*5+Math.floor(i/6))%9,dep=i%4;
 const weight=Math.round((0.65+((i*17)%19)*0.15+zone*0.24+(day<-30?0.6:0))*100)/100;
 return {id:`sim-${i}`,submission_id:`DEMO-${String(i+1).padStart(4,'0')}`,audit_date:iso(day),campus_id:'SIMULATED-DEMO',department_id:`d-${dep}`,department:depNames[dep],zone_id:`z-${zone}`,zone:zoneNames[zone],auditor_name:'Simulated Auditor',category_id:`c-${cat}`,category:categories[cat],item_id:`sim-item-${i}`,item_type:categories[cat],item_count:Math.round(6+((i*13)%70)),weight_kg:weight,
 single_use:cat<7,recyclable:[0,2,3,7].includes(cat),disposal_method:i%3===0?'segregated':'collection',confirmed_recycled_kg:i%4===0?Math.round(weight*0.6*100)/100:0,
 observations:'Simulation for interface exploration only.',corrective_action:'',created_by:'simulated-user',created_at:iso(day),updated_at:iso(day)}
});
const round=(x:number)=>Math.round(x*100)/100;
export function computeDemo(rows:Audit[],start:string,end:string):Analytics {
 const filtered=rows.filter(r=>r.audit_date>=start&&r.audit_date<=end);
 const span=Math.round((new Date(end+'T12:00:00').getTime()-new Date(start+'T12:00:00').getTime())/86400000)+1;
 const s0=new Date(start+'T12:00:00');s0.setDate(s0.getDate()-span);
 const e0=new Date(start+'T12:00:00');e0.setDate(e0.getDate()-1);
 const format=(d:Date)=>[d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');
 const prev=rows.filter(r=>r.audit_date>=format(s0)&&r.audit_date<=format(e0));
 const sum=(arr:Audit[])=>round(arr.reduce((s,r)=>s+r.weight_kg,0));
 const total=sum(filtered),prior=sum(prev),single=sum(filtered.filter(r=>r.single_use)),recycled=round(filtered.reduce((s,r)=>s+r.confirmed_recycled_kg,0));
 const uniq=(arr:Audit[])=>new Set(arr.map(r=>r.id)).size;
 const reduce=prev.length&&filtered.length?round(prior-total):null;
 const reductionPct=reduce!==null&&prior>0?round(100*reduce/prior):null;
 const rate=total?round(100*recycled/total):null;
 const singleRate=total?round(100*single/total):null;
 const group=(field:'audit_date'|'category'|'zone'|'department')=>Object.entries(filtered.reduce((acc,r)=>({...acc,[r[field]]:(acc[r[field]]||0)+r.weight_kg}),{} as Record<string,number>)).map(([name,value])=>({name,value:round(value)})).sort((a,b)=>b.value-a.value);
 const byDay=group('audit_date').map(({name,value})=>({date:name,weight_kg:value})).sort((a,b)=>a.date.localeCompare(b.date));
 const baseSingle=sum(prev.filter(r=>r.single_use)); const baseRate=prior?100*baseSingle/prior:0;
 const components=reduce!==null&&prior>0?{reduction:Math.max(0,Math.min(100,reductionPct||0)),recycling:rate||0,single_use_reduction:baseRate?Math.max(0,100*(baseRate-(singleRate||0))/baseRate):0,audit_completion:Math.min(100,uniq(filtered)/(5*span/7)*100),evidence_quality:0}:null;
 const score=components?round(components.reduction*.3+components.recycling*.25+components.single_use_reduction*.15+components.audit_completion*.15):null;
 const reduction_trend=reduce===null?[]:Array.from({length:span},(_,i)=>{const d=new Date(start+'T12:00:00');d.setDate(d.getDate()+i);const bd=new Date(s0);bd.setDate(bd.getDate()+i);const bc=prev.filter(r=>r.audit_date<=format(bd)).reduce((s,r)=>s+r.weight_kg,0);const cc=filtered.filter(r=>r.audit_date<=format(d)).reduce((s,r)=>s+r.weight_kg,0);return {date:format(d),relative_day:i+1,cumulative_reduction_kg:round(bc-cc)}});
 return {reduction_trend,period:{start,end},baseline:{start:format(s0),end:format(e0),available:!!prev.length,total_kg:prior,audits:uniq(prev),single_use_kg:baseSingle},
 metrics:{total_kg:total,single_use_kg:single,recycled_kg:recycled,single_use_pct:singleRate,recycling_rate:rate,audits:uniq(filtered),reduction_kg:reduce,reduction_pct:reductionPct,sustainability_score:score},
 score_components:components,score_weights:{reduction:30,recycling:25,single_use_reduction:15,audit_completion:15,evidence_quality:15},score_disclaimer:'Simulated provisional index — not a certified rating.',
 by_day:byDay,by_category:group('category'),by_zone:group('zone'),by_department:group('department'),rows:filtered};
}
export function initialDates(){return {end:iso(0),start:iso(-29)}}
