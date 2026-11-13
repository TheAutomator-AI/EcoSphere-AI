'use client';
import { useEffect, useState, type FormEvent } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Camera, Check, FileUp, Plus, X } from 'lucide-react';
import { Button } from './ui/primitives';
import type { Audit, Workspace } from '@/lib/types';
import { api } from '@/lib/client';

type Props={open:boolean;onOpenChange:(value:boolean)=>void; workspace:Workspace; editing?:Audit|null; onSaved:()=>Promise<void>};
const isoToday=()=>{const now=new Date();return `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`};
export function AuditForm({open,onOpenChange,workspace,editing,onSaved}:Props){
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[files,setFiles]=useState<File[]>([]);
 const [values,setValues]=useState({submission_id:'',audit_date:isoToday(),auditor_name:'',department_id:'',zone_id:'',category_id:'',item_type:'',item_count:'1',weight_kg:'',single_use:true,recyclable:true,disposal_method:'segregated',observations:'',corrective_action:''});
 useEffect(()=>{if(!open)return;setError('');setFiles([]);setValues(editing?{submission_id:editing.submission_id,audit_date:editing.audit_date,auditor_name:editing.auditor_name,department_id:editing.department_id,zone_id:editing.zone_id,category_id:editing.category_id,item_type:editing.item_type,item_count:String(editing.item_count),weight_kg:String(editing.weight_kg),single_use:editing.single_use,recyclable:editing.recyclable,disposal_method:editing.disposal_method,observations:editing.observations,corrective_action:editing.corrective_action}:{submission_id:`ECO-${Date.now().toString(36).toUpperCase()}`,audit_date:isoToday(),auditor_name:'',department_id:workspace.departments[0]?.id||'',zone_id:workspace.zones[0]?.id||'',category_id:workspace.categories[0]?.id||'',item_type:'',item_count:'1',weight_kg:'',single_use:true,recyclable:true,disposal_method:'segregated',observations:'',corrective_action:''})},[open,editing,workspace]);
 function field<K extends keyof typeof values>(key:K,value:typeof values[K]){setValues(prev=>({...prev,[key]:value}))}
 async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();setBusy(true);setError('');try{
  if(!Number.isFinite(Number(values.weight_kg))||Number(values.weight_kg)<=0)throw Error('Enter a measured weight greater than zero.');
  if(Number(values.item_count)<1)throw Error('Item count must be at least 1.');
  const payload={...values,item_count:Number(values.item_count),weight_kg:Number(values.weight_kg)};
  const result=await api<{id:string}>(editing?`/api/audits/${editing.id}`:'/api/audits',{method:editing?'PUT':'POST',body:JSON.stringify(payload)});
  for(const file of files){const data=new FormData();data.set('file',file);await api(`/api/evidence?audit_id=${encodeURIComponent(result.id)}`,{method:'POST',body:data})}
  await onSaved();onOpenChange(false);
 }catch(err){setError(err instanceof Error?err.message:'Could not save audit')}finally{setBusy(false)}}
 return <Dialog.Root open={open} onOpenChange={onOpenChange}><Dialog.Portal><Dialog.Overlay className="dialog-overlay"/><Dialog.Content className="audit-dialog"><div className="modal-heading"><div><span className="eyebrow"><span className="eyebrow-dot"/> REAL ENVIRONMENTAL RECORD</span><Dialog.Title>{editing?'Edit audit record':'New plastic waste audit'}</Dialog.Title><Dialog.Description>Record weighed observations. All measurements are validated and attributed to this campus.</Dialog.Description></div><Dialog.Close aria-label="Close audit form" className="icon-button"><X size={19}/></Dialog.Close></div><form onSubmit={submit} className="audit-form"><div className="form-grid">
  <label>Audit ID<input required maxLength={90} pattern="[A-Za-z0-9_-]+" value={values.submission_id} onChange={e=>field('submission_id',e.target.value)}/></label>
  <label>Audit date<input required type="date" max={isoToday()} value={values.audit_date} onChange={e=>field('audit_date',e.target.value)}/></label>
  <label>Auditor name<input required minLength={2} value={values.auditor_name} placeholder="Full name" onChange={e=>field('auditor_name',e.target.value)}/></label>
  <label>Department<select required value={values.department_id} onChange={e=>field('department_id',e.target.value)}>{workspace.departments.map(d=><option value={d.id} key={d.id}>{d.name}</option>)}</select></label>
  <label>Campus zone<select required value={values.zone_id} onChange={e=>field('zone_id',e.target.value)}>{workspace.zones.map(z=><option value={z.id} key={z.id}>{z.name}</option>)}</select></label>
  <label>Waste category<select required value={values.category_id} onChange={e=>field('category_id',e.target.value)}>{workspace.categories.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
  <label>Plastic item type<input required minLength={2} value={values.item_type} placeholder="e.g. 500 mL PET bottle" onChange={e=>field('item_type',e.target.value)}/></label>
  <label>Number of items<input required type="number" min={1} step={1} value={values.item_count} onChange={e=>field('item_count',e.target.value)}/></label>
  <label>Measured weight (kg)<input required type="number" min="0.0001" max="99999999" step="0.0001" value={values.weight_kg} placeholder="0.0000" onChange={e=>field('weight_kg',e.target.value)}/></label>
  <label>Disposal method<select value={values.disposal_method} onChange={e=>field('disposal_method',e.target.value)}><option value="segregated">Segregated collection</option><option value="mixed_waste">Mixed waste</option><option value="recycling_pending">Sent for recycling (unconfirmed)</option><option value="landfill">Landfill</option><option value="reuse">Reuse</option><option value="other">Other</option></select></label>
  </div><div className="form-checks"><label><input type="checkbox" checked={values.single_use} onChange={e=>field('single_use',e.target.checked)}/> Single-use plastic</label><label><input type="checkbox" checked={values.recyclable} onChange={e=>field('recyclable',e.target.checked)}/> Recyclable material</label></div>
  <div className="form-grid"><label>Observations<textarea value={values.observations} placeholder="Waste source, collection context, weighing method..." onChange={e=>field('observations',e.target.value)} rows={3}/></label><label>Corrective action<textarea value={values.corrective_action} placeholder="Proposed or completed improvement..." onChange={e=>field('corrective_action',e.target.value)} rows={3}/></label></div>
  <label className="upload-well"><FileUp size={20}/><span>Before / after photos, weighing records, supporting evidence</span><small>PNG · JPG · WebP · PDF · max 8 MB each</small><input type="file" multiple accept=".png,.jpg,.jpeg,.webp,.pdf" onChange={e=>setFiles(Array.from(e.target.files||[]))}/>{files.length>0&&<strong>{files.length} file(s) selected</strong>}</label>
  <p className="form-note"><Check size={14}/> Files begin as PENDING, not verified. A reviewer must approve evidence. Recycling requires a separate confirmed-weight entry.</p>
  {error&&<div role="alert" className="form-error">{error}</div>}<div className="modal-actions"><Button type="button" variant="ghost" onClick={()=>onOpenChange(false)}>Cancel</Button><Button type="submit" disabled={busy||!workspace.zones.length||!workspace.departments.length}>{busy?'Saving measurement…':editing?'Save changes':'Submit audit'} <Plus size={15}/></Button></div>
 </form></Dialog.Content></Dialog.Portal></Dialog.Root>
}
