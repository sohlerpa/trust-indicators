import {StyleTrust} from "../api/types";
import {getArticleStyle} from "../api/endpoints";
import {useEffect, useState} from "react";

export default function StyleCard({articleId}: {articleId: string}) {
    const [data, setData] = useState<StyleTrust | null>(null);

    useEffect(() => {
        getArticleStyle(articleId).then(setData);
    }, [articleId]);

    if (!data) {
        return (
            <div className="card metaCard">
                <h2>Style</h2>
                <p className="loading">Analyzing article tone…</p>
            </div>
        );
    }

    return (
        <div className="card metaCard">
            <h2>Style</h2>

            <div className="metaBox">
                <div className="metaRow">
                    <div className="metaLeft">
                        <span className="metaDot"/>
                        <span className="metaLabel capitalize">
                            {data.tone ?? "-"}
                        </span>
                    </div>

                    <span className="pill">
                        {data.content_type ?? "-"}
                    </span>
                </div>

                <p className="metaExplanation">
                    {data.tone_type_rationale ?? "-"}
                </p>
            </div>
        </div>
    );
}