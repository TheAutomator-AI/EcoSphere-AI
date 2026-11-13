import Link from 'next/link';
import { ArrowRight, Compass } from 'lucide-react';
export default function NotFound() {
  return <main className="route-state"><div className="route-state-card"><Compass size={42} color="#77eab6"/>
    <span className="eyebrow">404 · PAGE NOT FOUND</span>
    <h1>This path leads somewhere else.</h1><p>The requested EcoSphere page does not exist.</p>
    <Link href="/" className="btn btn-primary">Back to EcoSphere AI <ArrowRight size={16}/></Link>
  </div></main>;
}
