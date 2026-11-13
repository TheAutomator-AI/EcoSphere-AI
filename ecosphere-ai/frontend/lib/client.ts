import { createBrowserClient } from '@supabase/ssr';
let client:ReturnType<typeof createBrowserClient>|null=null;
export const devMode=process.env.NEXT_PUBLIC_DEV_AUTH_MODE==='true';
export const supabaseConfigured=Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL&&process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY);
export function supabase(){
 if(!supabaseConfigured)return null;
 if(!client)client=createBrowserClient(process.env.NEXT_PUBLIC_SUPABASE_URL!,process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!);
 return client;
}
export async function authToken(){
 if(devMode)return '';
 const sup=supabase(); if(!sup)throw new Error('Supabase Auth is not configured. Enable local dev mode for local testing.');
 const {data,error}=await sup.auth.getSession();
 if(error||!data.session)throw new Error('Please sign in to access real audits.');
 return data.session.access_token;
}
const base=process.env.NEXT_PUBLIC_API_URL||'http://127.0.0.1:8000';
export async function api<T>(path:string,opts:RequestInit={}){
 const token=await authToken();
 const headers=new Headers(opts.headers);
 if(token)headers.set('Authorization',`Bearer ${token}`);
 if(opts.body&&!(opts.body instanceof FormData))headers.set('Content-Type','application/json');
 const res=await fetch(base+path,{...opts,headers,cache:'no-store'});
 if(!res.ok){let reason=`API error ${res.status}`;try{const data=await res.json();reason=typeof data.detail==='string'?data.detail:JSON.stringify(data.detail)}catch{}throw new Error(reason)}
 return (await res.json()) as T;
}
export async function downloadReport(path:string,filename:string){
 const token=await authToken();const res=await fetch(base+path,{headers:token?{Authorization:`Bearer ${token}`}:{},cache:'no-store'});
 if(!res.ok)throw new Error('Report could not be generated. Confirm that the API is available.');
 const blob=await res.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=filename;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),5000);
}
export async function evidenceBlob(path:string){const token=await authToken();const res=await fetch(base+path,{headers:token?{Authorization:`Bearer ${token}`}:{}});if(!res.ok)throw new Error('Evidence inaccessible');return URL.createObjectURL(await res.blob())}
