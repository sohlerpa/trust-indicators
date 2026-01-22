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
    imgSrc: string,
    list: NonNullable<C2PATrust["c2pa_info"]>
) {
    const imgNorm = normalize(imgSrc);

    let match = list.find(i => i.src === imgSrc);
    if (match) return match;

    match = list.find(i =>
        normalize(i.src) === imgNorm
    );
    if (match) return match;

    const imgFile = imgNorm.split("/").pop();
    if (!imgFile) return null;

    match = list.find(i =>
        normalize(i.src).endsWith(imgFile)
    );
    if (match) return match;

    return null;
}

function getMediaSrc(el: Element): string | null {
    if (el instanceof HTMLImageElement) {
        return el.src;
    }

    if (el instanceof HTMLIFrameElement) {
        return el.src || null;
    }

    return null;
}

function enhanceInlineImages(
    html: string,
    c2pa: C2PATrust | null
) {
    if (!c2pa?.c2pa_info?.length) return html;

    const doc = new DOMParser().parseFromString(html, "text/html");

    const used = new Set<string>();

    doc.querySelectorAll("img, iframe").forEach((el) => {
        const src = getMediaSrc(el);
        if (!src) return;

        const match = findC2PAMatch(src, c2pa.c2pa_info!);
        if (!match) return;
        if (used.has(match.src)) return;

        used.add(match.src);

        const wrapTarget =
            el.closest(".videoWrapper") ?? el;

        const wrapper = doc.createElement("div");
        wrapper.className = "inlineImageWrap";

        wrapTarget.parentNode?.insertBefore(wrapper, wrapTarget);
        wrapper.appendChild(wrapTarget);

        const overlay = doc.createElement("div");
        overlay.className = "c2paOverlay";

        overlay.innerHTML = match.c2pa_present
            ? `
                <div class="c2paMeta">
                    <div class="c2paStatus ok">
                        ✓ C2PA Manifest present
                    </div>
                    <div><strong>Title:</strong> ${match.title ?? "-"}</div>
                    <div><strong>Issuer:</strong> ${match.issuer ?? "-"}</div>
                    <div><strong>AI generated:</strong> ${match.is_ai_generated ? "yes" : "no"}</div>
                </div>
            `
            : `
                <div class="c2paMeta">
                    <div class="c2paStatus error">
                        ✕ No C2PA data
                    </div>
                </div>
            `;

        wrapper.appendChild(overlay);
    });

    return doc.body.innerHTML;
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
    }>({
        open: false,
        left: 0,
        top: 0,
        claim: null,
    });

    return (
        <>
            <article
                ref={articleRef as any}
                className="articleBody card"
                dangerouslySetInnerHTML={{ __html: enhancedHtml }}
            />

            <div
                ref={popoverRef}
                className={`factHoverPopover ${hover.open ? "isOpen" : ""}`}
                style={{ left: hover.left, top: hover.top }}
                onMouseLeave={() =>
                    setHover({ open: false, left: 0, top: 0, claim: null })
                }
            />
        </>
    );
}