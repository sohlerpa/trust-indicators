import { useEffect, useMemo, useRef, useState } from "react";
import type { FactCheckTrust, C2PATrust } from "../api/types";
import { getArticleC2PA } from "../api/endpoints";

type Claim = FactCheckTrust["claims"][number];

// --- Helpers from OLD Code (Text & Date Formatting) ---

function formatReviewDate(date?: string) {
    if (!date) return null;
    const d = new Date(date);
    if (isNaN(d.getTime())) return date;
    return d.toLocaleDateString("en-US", {
        month: "short",
        year: "numeric",
    });
}

function escapeRegExp(s: string) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function normalizeWs(s: string) {
    return s.replace(/\s+/g, " ").trim();
}

// --- Helpers from NEW Code (Image C2PA) ---

function normalize(url: string) {
    try {
        const u = new URL(url, window.location.origin);
        return u.pathname.replace(/\/+/g, "/");
    } catch {
        return url;
    }
}

function findC2PAMatch(src: string, list: NonNullable<C2PATrust["c2pa_info"]>) {
    const norm = normalize(src);

    let m = list.find((i) => i.src === src);
    if (m) return m;

    m = list.find((i) => normalize(i.src) === norm);
    if (m) return m;

    const file = norm.split("/").pop();
    if (!file) return null;

    return list.find((i) => normalize(i.src).endsWith(file)) ?? null;
}

function getMediaSrc(el: Element): string | null {
    if (el instanceof HTMLImageElement) return el.src;
    if (el instanceof HTMLIFrameElement) return el.src || null;
    return null;
}

function enhanceInlineImages(html: string, c2pa: C2PATrust | null) {
    if (!c2pa?.c2pa_info?.length) return html;

    const doc = new DOMParser().parseFromString(html, "text/html");
    const used = new Set<string>();

    doc.querySelectorAll("img, iframe").forEach((el) => {
        const src = getMediaSrc(el);
        if (!src) return;

        const match = findC2PAMatch(src, c2pa.c2pa_info!);
        if (!match || used.has(match.src)) return;

        used.add(match.src);

        const wrapTarget = el.closest(".videoWrapper") ?? el;
        const wrapper = doc.createElement("div");
        wrapper.className = "inlineImageWrap";

        wrapTarget.parentNode?.insertBefore(wrapper, wrapTarget);
        wrapper.appendChild(wrapTarget);

        const overlay = doc.createElement("div");
        overlay.className = "c2paOverlay";

        overlay.innerHTML = match.c2pa_present
            ? `
                <div class="c2paMeta">
                    <div class="c2paStatus ok">✓ C2PA Manifest present</div>
                    <div><strong>Title:</strong> ${match.title ?? "-"}</div>
                    <div><strong>Issuer:</strong> ${match.issuer ?? "-"}</div>
                    <div><strong>AI generated:</strong> ${match.is_ai_generated ? "yes" : "no"}</div>
                </div>
            `
            : `
                <div class="c2paMeta">
                    <div class="c2paStatus error">✕ No C2PA data</div>
                </div>
            `;

        wrapper.appendChild(overlay);
    });

    return doc.body.innerHTML;
}

// --- Shared Helpers (Math & DOM) ---

function clamp(n: number, min: number, max: number) {
    return Math.max(min, Math.min(max, n));
}

function computePopoverPos(anchor: DOMRect, popW = 420, popH = 360) {
    const margin = 10;

    // Aligned to left edge of highlight, below text
    let left = anchor.left;
    let top = anchor.bottom + 8;

    // Flip to top if it would overflow bottom
    if (top + popH > window.innerHeight - margin) {
        top = anchor.top - 8 - popH;
    }

    left = clamp(left, margin, window.innerWidth - margin - popW);
    top = clamp(top, margin, window.innerHeight - margin - popH);

    return { left, top };
}

function verdictClass(verdict: string) {
    if (verdict === "true") return "factSpan isTrue";
    if (verdict === "false") return "factSpan isFalse";
    return "factSpan isUnclear";
}

// Used the OLD version of wrapRange as it handles node boundaries/offsets more robustly
function wrapRange(
    root: HTMLElement,
    start: number,
    end: number,
    className: string,
    claimId: string
) {
    if (end <= start) return;

    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node: Text | null = walker.nextNode() as Text | null;

    let pos = 0;
    let startNode: Text | null = null;
    let endNode: Text | null = null;
    let startOffset = 0;
    let endOffset = 0;

    while (node) {
        const len = node.nodeValue?.length ?? 0;
        const nextPos = pos + len;

        if (!startNode && start >= pos && start < nextPos) {
            startNode = node;
            startOffset = start - pos;
        }
        if (!endNode && end > pos && end <= nextPos) {
            endNode = node;
            endOffset = end - pos;
            break;
        }

        pos = nextPos;
        node = walker.nextNode() as Text | null;
    }

    if (!startNode || !endNode) return;

    const range = document.createRange();
    range.setStart(startNode, startOffset);
    range.setEnd(endNode, endOffset);

    const mark = document.createElement("mark");
    mark.className = className;
    mark.dataset.claimId = claimId;

    try {
        range.surroundContents(mark);
    } catch {
        const frag = range.extractContents();
        mark.appendChild(frag);
        range.insertNode(mark);
    } finally {
        range.detach();
    }
}

// --- Main Component ---

export default function HighlightedArticleBody({
    html,
    claims,
    articleId,
}: {
    html: string;
    claims?: Claim[] | null;
    articleId: string;
}) {
    const articleRef = useRef<HTMLElement | null>(null);
    const popoverRef = useRef<HTMLDivElement | null>(null);

    // 1. C2PA Image Logic
    const [c2pa, setC2pa] = useState<C2PATrust | null>(null);

    useEffect(() => {
        getArticleC2PA(articleId).then(setC2pa);
    }, [articleId]);

    // Apply C2PA overlays to the HTML string
    const enhancedHtml = useMemo(
        () => enhanceInlineImages(html, c2pa),
        [html, c2pa]
    );

    // 2. Fact Check Logic Setup
    const claimById = useMemo(() => {
        const m = new Map<string, Claim>();
        for (const c of claims ?? []) m.set(c.id, c);
        return m;
    }, [claims]);

    const [hover, setHover] = useState<{
        open: boolean;
        left: number;
        top: number;
        claim: Claim | null;
    }>({
        open: false,
        left: 0,
        top: 0,
        claim: null,
    });

    // 3. Highlighting Effect (Restored from OLD code)
    // This now watches `enhancedHtml` so highlighting applies *after* images are wrapped
    useEffect(() => {
        const root = articleRef.current;
        if (!root) return;

        // Cleanup existing marks
        root.querySelectorAll("mark.factSpan").forEach((m) => {
            const parent = m.parentNode;
            if (!parent) return;
            while (m.firstChild) parent.insertBefore(m.firstChild, m);
            parent.removeChild(m);
            parent.normalize();
        });

        if (!claims || claims.length === 0) return;

        const fullText = root.textContent ?? "";

        // Sort claims by length (longest first) to prevent nested overlap issues
        const sorted = [...claims].sort(
            (a, b) => (b.sourceText?.length ?? 0) - (a.sourceText?.length ?? 0)
        );

        for (const c of sorted) {
            const source = c.sourceText?.trim();
            if (!source) continue;

            let idx = 0;
            // 3a. Exact match attempt
            while (true) {
                const found = fullText.indexOf(source, idx);
                if (found === -1) break;

                wrapRange(
                    root,
                    found,
                    found + source.length,
                    verdictClass(c.verdict),
                    c.id
                );

                idx = found + source.length;
            }

            // 3b. Regex/Whitespace normalized fallback attempt
            if (!fullText.includes(source)) {
                const pattern = escapeRegExp(normalizeWs(source)).replace(/\s+/g, "\\s+");
                const re = new RegExp(pattern, "g");

                let m: RegExpExecArray | null;
                while ((m = re.exec(fullText)) !== null) {
                    wrapRange(
                        root,
                        m.index,
                        m.index + m[0].length,
                        verdictClass(c.verdict),
                        c.id
                    );
                }
            }
        }
    }, [enhancedHtml, claims]);

    // 4. Interaction/Hover Logic (Restored from OLD code)
    useEffect(() => {
        const root = articleRef.current;
        if (!root) return;

        let closeTimer: number | null = null;

        const clearCloseTimer = () => {
            if (closeTimer !== null) {
                window.clearTimeout(closeTimer);
                closeTimer = null;
            }
        };

        const scheduleClose = () => {
            clearCloseTimer();
            closeTimer = window.setTimeout(() => {
                setHover((h) => ({ ...h, open: false, claim: null }));
            }, 120);
        };

        const openForMark = (mark: HTMLElement) => {
            const claimId = mark.dataset.claimId;
            if (!claimId) return;

            const claim = claimById.get(claimId);
            if (!claim) return;

            const popW = Math.min(420, window.innerWidth - 24);
            const popH = Math.min(360, window.innerHeight - 24);

            const rect = mark.getBoundingClientRect();
            const pos = computePopoverPos(rect, popW, popH);

            setHover({
                open: true,
                left: pos.left,
                top: pos.top,
                claim,
            });
        };

        const onOver = (e: MouseEvent) => {
            const mark = (e.target as HTMLElement | null)?.closest("mark.factSpan") as HTMLElement | null;
            if (!mark) return;
            clearCloseTimer();
            openForMark(mark);
        };

        const onOut = (e: MouseEvent) => {
            const leavingMark = (e.target as HTMLElement | null)?.closest("mark.factSpan");
            if (!leavingMark) return;

            const entering = e.relatedTarget as HTMLElement | null;
            if (entering?.closest(".factHoverPopover")) return;

            scheduleClose();
        };

        root.addEventListener("mouseover", onOver);
        root.addEventListener("mouseout", onOut);

        const onScrollOrResize = () => {
            setHover((h) => {
                if (!h.open || !h.claim) return h;
                const mark = root.querySelector(`mark.factSpan[data-claim-id="${h.claim.id}"]`) as HTMLElement | null;
                if (!mark) return h;

                const popW = Math.min(420, window.innerWidth - 24);
                const popH = Math.min(360, window.innerHeight - 24);

                const rect = mark.getBoundingClientRect();
                const pos = computePopoverPos(rect, popW, popH);
                return { ...h, left: pos.left, top: pos.top };
            });
        };

        window.addEventListener("scroll", onScrollOrResize, true);
        window.addEventListener("resize", onScrollOrResize);

        return () => {
            root.removeEventListener("mouseover", onOver);
            root.removeEventListener("mouseout", onOut);
            window.removeEventListener("scroll", onScrollOrResize, true);
            window.removeEventListener("resize", onScrollOrResize);
            clearCloseTimer();
        };
    }, [claimById]);

    // 5. Popover Position Refinement (Restored from OLD code)
    useEffect(() => {
        if (!hover.open || !hover.claim) return;
        const root = articleRef.current;
        const pop = popoverRef.current;
        if (!root || !pop) return;

        const mark = root.querySelector(
            `mark.factSpan[data-claim-id="${hover.claim.id}"]`
        ) as HTMLElement | null;

        if (!mark) return;

        const anchor = mark.getBoundingClientRect();
        const popRect = pop.getBoundingClientRect();

        const isAbove = popRect.bottom <= anchor.top + 2;
        if (!isAbove) return;

        const margin = 10;
        const gap = 8;

        const desiredTop = anchor.top - gap - popRect.height;
        const clampedTop = clamp(desiredTop, margin, window.innerHeight - margin - popRect.height);

        if (Math.abs(clampedTop - hover.top) > 1) {
            setHover((h) => ({ ...h, top: clampedTop }));
        }
    }, [hover.open, hover.claim?.id, hover.left, hover.top]);

    return (
        <>
            <article
                ref={articleRef as any}
                className="articleBody card"
                // Uses enhancedHtml which includes the Image Overlays
                dangerouslySetInnerHTML={{ __html: enhancedHtml }}
            />

            {/* Restored Detailed Popover Structure */}
            <div
                ref={popoverRef}
                className={`factHoverPopover ${hover.open ? "isOpen" : ""}`}
                style={{ left: hover.left, top: hover.top }}
                onMouseEnter={() => {
                    // prevent closing when moving from mark to popover
                    null;
                }}
                onMouseLeave={() =>
                    setHover((h) => ({ ...h, open: false, claim: null }))
                }
            >
                {hover.claim && (
                    <div className="card metaCard">
                        <div className="verdictLine">
                            <span className="arrow">→</span>{" "}
                            <strong className={`verdictText verdictText-${hover.claim.verdict}`}>
                                {hover.claim.verdict}
                            </strong>{" "}
                            <span className="confidenceText">
                                ({Math.round(hover.claim.confidence * 100)}%)
                            </span>
                        </div>

                        <p className="summary" style={{ marginTop: 8 }}>
                            {hover.claim.summary}
                        </p>

                        {hover.claim.sources?.length ? (
                            <>
                                <div className="sourceSectionLabel" style={{ marginTop: 10 }}>
                                    Sources
                                </div>
                                <ul className="tooltipList" style={{ marginTop: 6 }}>
                                    {hover.claim.sources.map((s, i) => (
                                        <li
                                            key={`${s.url ?? s.title ?? "src"}-${i}`}
                                            className="tooltipItem"
                                        >
                                            <span className="tooltipPublisher">
                                                {s.publisher}{" "}
                                                {formatReviewDate((s as any).review_date) && (
                                                    <span className="tooltipDate">
                                                        · {formatReviewDate((s as any).review_date)}
                                                    </span>
                                                )}
                                            </span>
                                            {s.url && (
                                                <a
                                                    className="tooltipLink"
                                                    href={s.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                >
                                                    {s.url}
                                                </a>
                                            )}
                                        </li>
                                    ))}
                                </ul>
                            </>
                        ) : null}
                    </div>
                )}
            </div>
        </>
    );
}