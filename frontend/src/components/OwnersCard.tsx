import {useEffect, useState} from "react";
import {getArticleOwners} from "../api/endpoints";
import type {OwnershipTrust} from "../api/types";

const COLORS = [
    "#4C6EF5",
    "#15AABF",
    "#40C057",
    "#FAB005",
    "#FA5252",
    "#7950F2",
];

function OwnershipDonut({owners}: {owners: {owner: string; percent: number}[]}) {
    const size = 120;
    const stroke = 32;
    const r = (size - stroke) / 2;
    const c = size / 2;
    const circumference = 2 * Math.PI * r;

    let offset = 0;

    return (
        <svg width={size} height={size}>
            {/* background */}
            <circle
                cx={c}
                cy={c}
                r={r}
                stroke="#eee"
                strokeWidth={stroke}
                fill="none"
            />

            {owners.map((o, i) => {
                const length = (o.percent / 100) * circumference;

                const el = (
                    <circle
                        key={o.owner}
                        cx={c}
                        cy={c}
                        r={r}
                        stroke={COLORS[i % COLORS.length]}
                        strokeWidth={stroke}
                        fill="none"
                        strokeDasharray={`${length} ${circumference}`}
                        strokeDashoffset={-offset}
                        transform={`rotate(-90 ${c} ${c})`}
                    />
                );

                offset += length;
                return el;
            })}
        </svg>
    );
}

export default function OwnersCard({articleId}: {articleId: string}) {
    const [data, setData] = useState<OwnershipTrust | null>(null);

    useEffect(() => {
        getArticleOwners(articleId).then(setData);
    }, [articleId]);

    if (!data) {
        return (
            <div className="card metaCard">
                <h2>Main Owners</h2>
                <p className="loading">Loading ownership…</p>
            </div>
        );
    }

    if (!data.owners?.length) {
        return (
            <div className="card metaCard">
                <h2>Main Owners</h2>
                <p>-</p>
            </div>
        );
    }

    return (
        <div className="card metaCard">
            <h2>Main Owners</h2>

            <div
                style={{
                    display: "grid",
                    gridTemplateColumns: "auto 1fr",
                    columnGap: 20,
                    alignItems: "center",
                }}
            >
                <OwnershipDonut owners={data.owners} />

                <div>
                    {data.owners.map((o, i) => (
                        <div
                            key={o.owner}
                            className="metaRow"
                            style={{marginBottom: 6}}
                        >
                            <span
                                style={{
                                    width: 10,
                                    height: 10,
                                    borderRadius: 2,
                                    background: COLORS[i % COLORS.length],
                                    display: "inline-block",
                                    marginRight: 8,
                                }}
                            />
                            <span style={{flex: 1}}>{o.owner}</span>
                            <span className="pill">
                                {o.percent.toFixed(1)}%
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}