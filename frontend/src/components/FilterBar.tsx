import type {FeedFilters} from "../api/types";

type Props = {
    value: FeedFilters;
    onChange: (next: FeedFilters) => void;
};

const TONES = ["neutral", "analytical", "speculative", "conspiratorial", "sensational", "alarmist", "angry", "critical", "supportive", "skeptical", "humorous", "ironic", "promotional", "error",];
const TYPES = ["news", "opinion", "analysis", "satire", "gossip", "review", "sponsored", "other", "error"];
const PUBLISHERS = ["public", "private", "unknown"];

export default function FilterBar({value, onChange}: Props) {
    function toggle(list: string[] | undefined, item: string) {
        const s = new Set(list ?? []);
        if (s.has(item)) s.delete(item);
        else s.add(item);
        return Array.from(s);
    }

    return (
        <div className="filters">
            <div className="filterGroup">
                <label>Fact-checked</label>
                <select
                    value={value.fact_checked === undefined ? "any" : String(value.fact_checked)}
                    onChange={(e) => {
                        const v = e.target.value;
                        onChange({...value, fact_checked: v === "any" ? undefined : v === "true"});
                    }}
                >
                    <option value="any">Any</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                </select>
            </div>

            <div className="filterGroup">
                <label>Tone</label>
                <div className="chips">
                    {TONES.map((t) => (
                        <button
                            key={t}
                            className={`chip ${value.tone?.includes(t) ? "active" : ""}`}
                            onClick={() => onChange({...value, tone: toggle(value.tone, t)})}
                            type="button"
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            <div className="filterGroup">
                <label>Type</label>
                <div className="chips">
                    {TYPES.map((t) => (
                        <button
                            key={t}
                            className={`chip ${value.content_type?.includes(t) ? "active" : ""}`}
                            onClick={() => onChange({...value, content_type: toggle(value.content_type, t)})}
                            type="button"
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            <div className="filterGroup">
                <label>Publisher</label>
                <div className="chips">
                    {PUBLISHERS.map((p) => (
                        <button
                            key={p}
                            className={`chip ${value.publisher_type?.includes(p) ? "active" : ""}`}
                            onClick={() => onChange({...value, publisher_type: toggle(value.publisher_type, p)})}
                            type="button"
                        >
                            {p}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}