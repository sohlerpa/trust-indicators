import {useEffect, useRef, useState} from "react";
import {ingestArticleFromUrl} from "../api/endpoints";

export default function ArticleIngest({
                                          onInserted,
                                          onOpenChange,
                                      }: {
    onInserted?: (id: string) => void;
    onOpenChange?: (open: boolean) => void;
}) {
    const [open, setOpen] = useState(false);
    const [url, setUrl] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [err, setErr] = useState<string | null>(null);
    const [okMsg, setOkMsg] = useState<string | null>(null);
    const COLLAPSE_MS = 260;
    const closeTimer = useRef<number | null>(null);

    function reset() {
        setUrl("");
        setErr(null);
        setOkMsg(null);
        setSubmitting(false);
    }

    async function submit() {
        setErr(null);
        setOkMsg(null);

        const trimmed = url.trim();
        if (!trimmed) {
            setErr("Please enter a URL.");
            return;
        }

        try {
            new URL(trimmed);
        } catch {
            setErr("This is not a valid URL.");
            return;
        }

        setSubmitting(true);
        try {
            const res = await ingestArticleFromUrl(trimmed);
            setOkMsg(`Inserted article: ${res.id}`);
            onInserted?.(res.id);
            setTimeout(() => {
                setOpen(false);
                scheduleParentClosed();
            }, 5000);
        } catch (e: unknown) {
            setErr(e instanceof Error ? e.message : "Insert failed");
        } finally {
            setSubmitting(false);
        }
    }

    useEffect(() => {
        return () => {
            if (closeTimer.current) window.clearTimeout(closeTimer.current);
        };
    }, []);

    function scheduleParentClosed() {
        if (closeTimer.current) window.clearTimeout(closeTimer.current);
        closeTimer.current = window.setTimeout(() => {
            onOpenChange?.(false);
            closeTimer.current = null;
        }, COLLAPSE_MS);
    }

    return (
        <div className={`card ingestCard ${open ? "open" : ""}`}>
            <div className="ingestHeader">
                <div>
                    <h3 style={{marginBottom: 4}}>Add your own article</h3>
                    <div className="metaSmall">Insert an article by URL and run preprocessing on the backend.</div>
                </div>

                <button
                    className={`factButton ingestToggle ${open ? "open" : ""}`}
                    onClick={() => {
                        setOpen((o) => {
                            const next = !o;
                            if (next) {
                                if (closeTimer.current) window.clearTimeout(closeTimer.current);
                                reset();
                                onOpenChange?.(true);
                            } else {
                                scheduleParentClosed();
                            }
                            return next;
                        });
                    }}
                    aria-expanded={open}
                    aria-controls="ingestPanel"
                >
                    Add <span className="ingestChevron" aria-hidden>▾</span>
                </button>
            </div>

            <div
                id="ingestPanel"
                className={`ingestPanel ${open ? "open" : ""}`}
                aria-hidden={!open}
            >
                <div className="ingestInner stack" style={{gap: 8}}>
                    <label className="metaSmall" htmlFor="articleUrl">Article URL</label>
                    <input
                        id="articleUrl"
                        className="input"
                        placeholder="https://example.com/news/article"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        disabled={submitting || !open}
                    />

                    <div style={{display: "flex", gap: 8}}>
                        <button className="factButton" onClick={submit} disabled={submitting || !open}>
                            {submitting ? "Inserting…" : "Insert article"}
                        </button>
                    </div>

                    {err && <div className="error">Error: {err}</div>}
                    {okMsg && <div className="hint">{okMsg}</div>}
                </div>
            </div>
        </div>
    );
}