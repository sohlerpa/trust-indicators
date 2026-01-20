import {useLayoutEffect, useMemo, useRef, useState} from "react";
import type {FactCheckTrustClaim} from "../api/types";

export default function ClaimSourcesTooltip({sources}: { sources: FactCheckTrustClaim["sources"] }) {
    const items = useMemo(() => {
        const map = new Map<string, { publisher: string; url: string; date?: string }>();
        for (const s of sources ?? []) {
            const url = s.url?.trim();
            if (!url) continue;
            const publisher = (s.publisher ?? s.publisherSite ?? "Source").trim();

            let date: string | undefined;
            const rawDate = s.reviewDate ?? (s as any).review_date ?? (s as any).claimDate ?? (s as any).claim_date;
            if (rawDate) {
                const d = new Date(rawDate);
                if (!isNaN(d.getTime())) date = d.toLocaleDateString("en-US", {month: "short", year: "numeric"});
            }

            if (!map.has(url)) map.set(url, {publisher, url, date});
        }
        return Array.from(map.values());
    }, [sources]);

    const [open, setOpen] = useState(false);
    const btnRef = useRef<HTMLSpanElement | null>(null);
    const popRef = useRef<HTMLDivElement | null>(null);

    useLayoutEffect(() => {
        if (!open) return;
        const btn = btnRef.current;
        const pop = popRef.current;
        if (!btn || !pop) return;

        const r = btn.getBoundingClientRect();
        const margin = 12;

        // measure popover
        const pr = pop.getBoundingClientRect();

        // open to the right and slightly below
        let left = r.right + 8;
        let top = r.bottom + 8;

        if (left + pr.width > window.innerWidth - margin) left = window.innerWidth - margin - pr.width;
        if (top + pr.height > window.innerHeight - margin) top = r.top - 8 - pr.height;

        left = Math.max(margin, left);
        top = Math.max(margin, top);

        pop.style.left = `${left}px`;
        pop.style.top = `${top}px`;
    }, [open]);

    if (items.length === 0) return null;

    return (
        <span
            className="sourcesWrap"
            onMouseEnter={() => setOpen(true)}
            onMouseLeave={() => setOpen(false)}
        >
      <span ref={btnRef} className="sourcesBadge" aria-label="Show sources">i</span>

      <div
          ref={popRef}
          className={`sourcesPopover ${open ? "isOpen" : ""}`}
      >
        <div className="card metaCard">
          <div className="tooltipTitle">Sources</div>
          <ul className="tooltipList">
            {items.map((it) => (
                <li key={it.url} className="tooltipItem">
                <span className="tooltipPublisher">
                  {it.publisher}
                    {it.date && <span className="tooltipDate"> · {it.date}</span>}
                </span>
                    <a href={it.url} target="_blank" rel="noopener noreferrer" className="tooltipLink">
                        {it.url}
                    </a>
                </li>
            ))}
          </ul>
        </div>
      </div>
    </span>
    );
}