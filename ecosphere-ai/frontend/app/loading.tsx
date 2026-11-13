import { Leaf } from 'lucide-react';

export default function Loading() {
  return <main className="route-state" role="status" aria-live="polite">
    <div className="route-state-card"><span className="route-loading-mark"><Leaf size={34}/></span>
      <h1>Preparing EcoSphere AI.</h1><p>Loading your sustainability workspace…</p>
      <div className="route-loading-bar" aria-hidden="true"/>
    </div>
  </main>;
}
