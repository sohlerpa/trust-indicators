import {useEffect, useState} from "react";
import {getArticleC2PA} from "../api/endpoints";
import type {C2PATrust} from "../api/types";

export default function C2PACard({
    articleId,
    compact = false,
}: {
    articleId: string;
    compact?: boolean;
}) {
    const [data, setData] = useState<C2PATrust | null>(null);

    useEffect(() => {
        getArticleC2PA(articleId).then(setData);
    }, [articleId]);

    if (!data) {
        return (
            <div className="card metaCard">
                <h2>C2PA</h2>
                <p className="loading">Analyzing media provenance…</p>
            </div>
        );
    }

    if (compact) {
        const first = data.c2pa_info?.[0];
        if (!first) return null;

        return (
            <div className="c2paOverlay">
                <div className="c2paMeta">
                    {first.c2pa_present ? (
                        <>
                            <div className="c2paStatus ok">
                                ✓ C2PA Manifest present
                            </div>
                            <div><strong>Title:</strong> {first.title ?? "-"}</div>
                            <div><strong>Issuer:</strong> {first.issuer ?? "-"}</div>
                            <div>
                                <strong>AI generated:</strong>{" "}
                                {first.is_ai_generated ? "yes" : "no"}
                            </div>
                        </>
                    ) : (
                        <div className="c2paStatus error">
                            ✕ No C2PA data
                        </div>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="card metaCard">
            <h2>C2PA</h2>

            {data.c2pa_info?.length ? (
                <ul className="c2paList">
                    {data.c2pa_info.map((i) => {
                        const ytId = i.src.includes("youtube.com/embed/")
                            ? i.src.split("youtube.com/embed/")[1]?.split("?")[0]
                            : null;

                        const thumbSrc = ytId
                            ? `https://img.youtube.com/vi/${ytId}/hqdefault.jpg`
                            : i.src;

                        return (
                            <li key={i.src} className="c2paItem">
                                <div className="c2paThumbWrap">
                                    <img
                                        src={thumbSrc}
                                        alt={i.title ?? (ytId ? "Video" : "Image")}
                                        className="c2paThumb"
                                    />
                                    {ytId && (
                                        <div className="playOverlay">▶</div>
                                    )}
                                </div>

                                {i.c2pa_present ? (
                                    <div className="c2paMeta">
                                        <div className="c2paStatus ok">
                                            ✓ C2PA Manifest present
                                        </div>
                                        <div>
                                            <strong>Title:</strong>{" "}
                                            {i.title ?? "-"}
                                        </div>
                                        <div>
                                            <strong>Issuer:</strong>{" "}
                                            {i.issuer ?? "-"}
                                        </div>
                                        <div>
                                            <strong>AI generated:</strong>{" "}
                                            {i.is_ai_generated ? "yes" : "no"}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="c2paMeta">
                                        <div className="c2paStatus error">
                                            ✕ No C2PA data
                                        </div>
                                    </div>
                                )}
                            </li>
                        );
                    })}
                </ul>
            ) : (
                <p>-</p>
            )}
        </div>
    );
}