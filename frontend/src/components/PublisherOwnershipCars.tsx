import {useEffect, useState} from "react";
import {getArticleOwners, getArticlePublisher} from "../api/endpoints";
import type {OwnershipTrust, PublisherTrust} from "../api/types";
import CountryFlag from "./CountryFlag";

const COLORS = [
    "#4C6EF5",
    "#15AABF",
    "#40C057",
    "#FAB005",
    "#FA5252",
    "#7950F2",
];

function OwnershipDonut({
    owners,
}: {
    owners: {owner: string; percent: number}[];
}) {
    const size = 100;
    const stroke = 25;
    const r = (size - stroke) / 2;
    const c = size / 2;
    const circumference = 2 * Math.PI * r;

    let offset = 0;

    return (
        <svg width={size} height={size}>
            <circle
                cx={c}
                cy={c}
                r={r}
                stroke="#e9ecef"
                strokeWidth={stroke}
                fill="none"
            />

            {owners.map((o, i) => {
                const len = (o.percent / 100) * circumference;

                const el = (
                    <circle
                        key={o.owner}
                        cx={c}
                        cy={c}
                        r={r}
                        stroke={COLORS[i % COLORS.length]}
                        strokeWidth={stroke}
                        fill="none"
                        strokeDasharray={`${len} ${circumference}`}
                        strokeDashoffset={-offset}
                        transform={`rotate(-90 ${c} ${c})`}
                    />
                );

                offset += len;
                return el;
            })}
        </svg>
    );
}

export default function SourceOwnershipCard({
    articleId,
    source,
}: {
    articleId: string;
    source: string;
}) {
    const [owners, setOwners] = useState<OwnershipTrust | null>(null);
    const [publisher, setPublisher] = useState<PublisherTrust | null>(null);

    useEffect(() => {
        getArticleOwners(articleId).then(setOwners);
        getArticlePublisher(articleId).then(setPublisher);
    }, [articleId]);

    if (!owners || !publisher) {
        return (
            <div className="card metaCard">
                <h2>Source</h2>
                <p className="loading">Loading source information…</p>
            </div>
        );
    }

    return (
        <div className="card metaCard sourceCard">
            {/* SOURCE HEADER */}
            <div className="sourceHeader">
                <div className="sourceTop">
                    <div className="sourceName">{source}</div>

                    <span className="metaFlag">
                        <CountryFlag code={publisher.publisher_country} />
                    </span>
                </div>

                <div
                    className={`sourceType ${
                        publisher.publisher_type ?? "unknown"
                    }`}
                >
                    {publisher.publisher_type === "public" &&
                        "Public broadcaster"}
                    {publisher.publisher_type === "private" &&
                        "Private media company"}
                    {publisher.publisher_type === "unknown" &&
                        "Publisher type unknown"}
                </div>
            </div>

            {/* OWNERSHIP */}
            <div className="sourceSectionLabel">
                Ownership structure
            </div>

            {owners.owners?.length ? (
                <div className="ownersGrid">
                    <OwnershipDonut owners={owners.owners} />

                    <ul className="ownersNiceList">
                        {owners.owners.map((o, i) => (
                            <li key={o.owner} className="metaRow">
                                <div className="metaLeft">
                                    <span
                                        className="ownerColor"
                                        style={{
                                            background:
                                                COLORS[i % COLORS.length],
                                        }}
                                    />
                                    <span className="metaLabel">
                                        {o.owner}
                                    </span>
                                </div>

                                <span className="pill ownerPercent">
                                    {o.percent.toFixed(1)}%
                                </span>
                            </li>
                        ))}
                    </ul>
                </div>
            ) : (
                <p>-</p>
            )}
        </div>
    );
}