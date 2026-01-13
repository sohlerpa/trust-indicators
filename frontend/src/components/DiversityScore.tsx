import {useEffect, useMemo, useState} from "react";
import {getFeedDiversity, type DiversityRow} from "../api/endpoints";

export default function DiversityScore({domains}: {domains: string[]}) {
    const [score, setScore] = useState<number | null>(null);

    const uniqueDomains = useMemo(
        () => Array.from(new Set(domains)),
        [domains]
    );

    function diversityLabel(score: number) {
        if (score >= 0.7) return {text: "High diversity", level: "high"};
        if (score >= 0.4) return {text: "Moderate diversity", level: "medium"};
        return {text: "Low diversity", level: "low"};
    }

    useEffect(() => {
        if (uniqueDomains.length === 0) {
            setScore(null);
            return;
        }

        getFeedDiversity(uniqueDomains).then((rows: DiversityRow[]) => {
            const total = rows.reduce((s, r) => s + r.influence, 0);
            if (total === 0) {
                setScore(null);
                return;
            }

            const hhi = rows.reduce(
                (s, r) => s + Math.pow(r.influence / total, 2),
                0
            );

            setScore(1 - hhi);
        });
    }, [uniqueDomains]);

    if (score === null) return null;

    const pct = Math.round(score * 100);
    const label = diversityLabel(score);

    return (
        <div className="card diversityCard">
            <div className="diversityHeader">
                <span>Diversity</span>
                <span className={`diversityTag ${label.level}`}>
                    {label.text}
                </span>
            </div>

            <div className="diversityValue">{pct}%</div>

            <div className="diversityBar">
                <div
                    className={`diversityFill ${label.level}`}
                    style={{width: `${pct}%`}}
                />
            </div>

            <div className="metaSmall">
                Ownership concentration across sources
            </div>
        </div>
    );
}