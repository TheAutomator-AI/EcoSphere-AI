'use client';
import { forwardRef, type ButtonHTMLAttributes } from 'react';
import clsx from 'clsx';
export const Button=forwardRef<HTMLButtonElement,ButtonHTMLAttributes<HTMLButtonElement>&{variant?:'primary'|'outline'|'ghost'|'danger';size?:'default'|'small'}>(({variant='primary',size='default',className,...props},ref)=><button ref={ref} {...props} className={clsx('btn',`btn-${variant}`,size==='small'&&'btn-small',className)}/>);
Button.displayName='Button';
export function Badge({children,tone='mint',className=''}:{children:React.ReactNode;tone?:'mint'|'amber'|'rose'|'muted';className?:string}){return <span className={`badge badge-${tone} ${className}`}>{children}</span>}
export function SectionHeading({eyebrow,title,description}:{eyebrow:string;title:string;description?:string}){return <div className="section-heading"><div className="eyebrow"><span className="eyebrow-dot"/>{eyebrow}</div><h2>{title}</h2>{description&&<p>{description}</p>}</div>}
export function EmptyState({title,description,action}:{title:string;description:string;action?:React.ReactNode}){return <div className="empty-state"><span className="empty-orbit">✳</span><h3>{title}</h3><p>{description}</p>{action}</div>}
export function Skeleton({height=120}:{height?:number}){return <div className="skeleton" style={{height}} aria-label="Loading content"/>}
