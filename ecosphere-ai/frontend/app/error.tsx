'use client';

import Link from 'next/link';
import { AlertTriangle, ArrowRight, RotateCcw } from 'lucide-react';

/** Next.js route-level error boundary: the audit API retains persisted data. */
export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="route-state">
      <div className="route-state-card" role="alert">
        <AlertTriangle size={42} color="#fbbf70" />
        <span className="eyebrow">ECOSPHERE AI · RECOVERY</span>
        <h1>We couldn&apos;t render this view.</h1>
        <p>Try loading this section again. Already-submitted measurements remain stored by the audit API.</p>
        <div className="route-state-actions">
          <button className="btn btn-primary" onClick={reset}><RotateCcw size={16} /> Retry</button>
          <Link href="/" className="btn btn-outline">Return home <ArrowRight size={16}/></Link>
        </div>
      </div>
    </main>
  );
}
