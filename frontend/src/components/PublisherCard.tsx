import {useEffect, useState} from "react";
import {getArticlePublisher} from "../api/endpoints";
import type {PublisherTrust} from "../api/types";
import CountryFlag from "./CountryFlag";

export default function PublisherCard({
    articleId,
    source,
}: {
    articleId: string;
    source: string;
}) {
    const [data, setData] = useState<PublisherTrust | null>(null);

    useEffect(() => {
        getArticlePublisher(articleId).then(setData);
    }, [articleId]);

    if (!data) {
        return (
            <div className="card metaCard">
                <h2>Publisher</h2>
                <p className="loading">Loading publisher info…</p>
            </div>
        );
    }

    const cc = data.publisher_country
        ? data.publisher_country.toUpperCase()
        : "-";

    return (
        <div className="card metaCard">
            <h2>Publisher</h2>

            <div className="metaRow">
                <div className="metaLeft">
                    <span
                        className="metaFlag"
                        title={cc}
                        aria-label={cc}
                    >
                        <CountryFlag code={data.publisher_country}/>
                    </span>

                    <span className="metaLabel">
                        {source}
                    </span>
                </div>

                <span className="pill">
                    {data.publisher_type ?? "-"}
                </span>
            </div>
        </div>
    );
}