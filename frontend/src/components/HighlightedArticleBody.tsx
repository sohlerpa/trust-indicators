import { useEffect, useMemo, useRef, useState } from "react";
import type { FactCheckTrust } from "../api/types";
import { getArticleC2PA } from "../api/endpoints";
import type { C2PATrust } from "../api/types";

type Claim = FactCheckTrust["claims"][number];

function clamp(n: number, min: number, max: number) {
    return Math.max(min, Math.min(max, n));
}

function computePopoverPos(anchor: DOMRect, popW = 420, popH = 360) {
    const margin = 10;

    let left = anchor.left;
    let top = anchor.bottom + 8;

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

function normalize(url: string) {
    try {
        const u = new URL(url, window.location.origin);
        return u.pathname.replace(/\/+/g, "/");
    } catch {
        return url;
    }
}

function findC2PAMatch(
    src: string,
    list: NonNullable<C2PATrust["c2pa_info"]>
) {
    const norm = normalize(src);

    let m = list.find(i => i.src === src);
    if (m) return m;

    m = list.find(i => normalize(i.src) === norm);
    if (m) return m;

    const file = norm.split("/").pop();
    if (!file) return null;

    return list.find(i => normalize(i.src).endsWith(file)) ?? null;
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

    doc.querySelectorAll("img, iframe").forEach(el => {
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

function wrapRange(
    root: HTMLElement,
    start: number,
    end: number,
    className: string,
    claimId: string
) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);

    let pos = 0;
    let node: Text | null = walker.nextNode() as Text | null;

    let startNode: Text | null = null;
    let endNode: Text | null = null;
    let startOffset = 0;
    let endOffset = 0;

    while (node) {
        const len = node.nodeValue?.length ?? 0;
        const next = pos + len;

        if (!startNode && start >= pos && start < next) {
            startNode = node;
            startOffset = start - pos;
        }

        if (!endNode && end > pos && end <= next) {
            endNode = node;
            endOffset = end - pos;
            break;
        }

        pos = next;
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

    const [c2pa, setC2pa] = useState<C2PATrust | null>(null);

    const enhancedHtml = useMemo(
        () => enhanceInlineImages(html, c2pa),
        [html, c2pa]
    );

    useEffect(() => {
        getArticleC2PA(articleId).then(setC2pa);
    }, [articleId]);

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
    }>({ open: false, left: 0, top: 0, claim: null });

    useEffect(() => {
        const root = articleRef.current;
        if (!root || !claims?.length) return;

        root.querySelectorAll("mark.factSpan").forEach(m => {
            const p = m.parentNode;
            if (!p) return;
            while (m.firstChild) p.insertBefore(m.firstChild, m);
            p.removeChild(m);
            p.normalize();
        });

        const text = root.textContent ?? "";

        for (const c of claims) {
            if (!c.sourceText) continue;

            let idx = 0;
            while (true) {
                const found = text.indexOf(c.sourceText, idx);
                if (found === -1) break;

                wrapRange(
                    root,
                    found,
                    found + c.sourceText.length,
                    verdictClass(c.verdict),
                    c.id
                );

                idx = found + c.sourceText.length;
            }
        }
    }, [enhancedHtml, claims]);

    useEffect(() => {
        const root = articleRef.current;
        if (!root) return;

        const over = (e: MouseEvent) => {
            const mark = (e.target as HTMLElement | null)
                ?.closest("mark.factSpan") as HTMLElement | null;
            if (!mark) return;

            const claim = claimById.get(mark.dataset.claimId!);
            if (!claim) return;

            const rect = mark.getBoundingClientRect();
            const pos = computePopoverPos(rect);

            setHover({ open: true, left: pos.left, top: pos.top, claim });
        };

        const out = () => setHover(h => ({ ...h, open: false }));

        root.addEventListener("mouseover", over);
        root.addEventListener("mouseout", out);

        return () => {
            root.removeEventListener("mouseover", over);
            root.removeEventListener("mouseout", out);
        };
    }, [claimById]);

    return (
        <>
            <article
                ref={articleRef}
                className="articleBody card"
                dangerouslySetInnerHTML={{ __html: enhancedHtml }}
            />

            <div
                ref={popoverRef}
                className={`factHoverPopover ${hover.open ? "isOpen" : ""}`}
                style={{ left: hover.left, top: hover.top }}
            >
                {hover.claim && (
                    <div className="card metaCard">
                        <strong className={`verdictText verdictText-${hover.claim.verdict}`}>
                            {hover.claim.verdict}
                        </strong>
                        <p>{hover.claim.summary}</p>
                    </div>
                )}
            </div>
        </>
    );
}