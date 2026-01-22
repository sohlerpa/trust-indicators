import {useState} from "react";
import {ingestArticleFromUrl} from "../api/endpoints";

export default function ArticleIngest({onInserted}: { onInserted?: (id: string) => void }) {
    const [open, setOpen] = useState(false);
    const [url, setUrl] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [err, setErr] = useState<string | null>(null);
    const [okMsg, setOkMsg] = useState<string | null>(null);

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
            }, 5000);
        } catch (e: unknown) {
            setErr(e instanceof Error ? e.message : "Insert failed");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="card">
            <div style={{display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12}}>
                <div>
                    <h3 style={{marginBottom: 4}}>Add your own article</h3>
                    <div className="metaSmall">Insert an article by URL and run preprocessing on the backend.</div>
                </div>

                <button
                    className="factButton"
                    onClick={() => {
                        setOpen(true);
                        reset();
                    }}
                >
                    Add
                </button>
            </div>

            {open && (
                <div style={{marginTop: 12}}>
                    <div className="stack" style={{gap: 8}}>
                        <label className="metaSmall" htmlFor="articleUrl">Article URL</label>
                        <input
                            id="articleUrl"
                            className="input"
                            placeholder="https://example.com/news/article"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            disabled={submitting}
                        />

                        <div style={{display: "flex", gap: 8}}>
                            <button
                                className="factButton"
                                onClick={submit}
                                disabled={submitting}
                            >
                                {submitting ? "Inserting…" : "Insert article"}
                            </button>

                            <button
                                className="factButton"
                                onClick={() => {
                                    setOpen(false);
                                    reset();
                                }}
                                disabled={submitting}
                            >
                                Close
                            </button>
                        </div>

                        {err && <div className="error">Error: {err}</div>}
                        {okMsg && <div className="hint">{okMsg}</div>}
                    </div>
                </div>
            )}
        </div>
    );
}