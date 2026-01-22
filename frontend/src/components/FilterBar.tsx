import {useMemo, useState} from "react";
import type {FeedFilters} from "../api/types";

type Props = {
    value: FeedFilters;
    onChange: (next: FeedFilters) => void;
    counts: {
        tone: Record<string, number>;
        content_type: Record<string, number>;
        publisher_type: Record<string, number>;
    };
};

const TONES = [
    "neutral",
    "analytical",
    "speculative",
    "conspiratorial",
    "sensational",
    "alarmist",
    "angry",
    "critical",
    "supportive",
    "skeptical",
    "humorous",
    "ironic",
    "promotional",
    "error",
];

const TYPES = ["news", "opinion", "analysis", "satire", "gossip", "review", "sponsored", "other", "error"];
const PUBLISHERS = ["public", "private", "unknown"];

type Tri = undefined | boolean; // Any | true | false

function toggleMulti(list: string[] | undefined, item: string) {
    const s = new Set(list ?? []);
    if (s.has(item)) s.delete(item);
    else s.add(item);
    return Array.from(s);
}

function triToKey(v: Tri): "any" | "true" | "false" {
    if (v === undefined) return "any";
    return v ? "true" : "false";
}

function keyToTri(k: "any" | "true" | "false"): Tri {
    if (k === "any") return undefined;
    return k === "true";
}

export default function FilterBar({value, onChange, counts}: Props) {
    const [advancedOpen, setAdvancedOpen] = useState(false);

    const hasAnyAdvanced = useMemo(() => {
        const t = (value.tone ?? []).length > 0;
        const ct = (value.content_type ?? []).length > 0;
        return t || ct;
    }, [value.tone, value.content_type, value.publisher_type]);

    const selectedCount = useMemo(() => {
        const parts = [
            value.no_false_facts !== undefined ? 1 : 0,
            value.c2pa_present !== undefined ? 1 : 0,
            value.author_expert !== undefined ? 1 : 0,
            (value.tone ?? []).length,
            (value.content_type ?? []).length,
            (value.publisher_type ?? []).length,
        ];
        return parts.reduce((a, b) => a + b, 0);
    }, [value]);

    const resetAll = () => {
        onChange({
            ...value,
            no_false_facts: undefined,
            author_expert: undefined,
            c2pa_present: undefined,
            tone: [],
            content_type: [],
            publisher_type: [],
        });
    };

    return (
        <div className="filters filtersModern">
            <div className="filtersHeader">
                <div className="filtersTitleRow">
                    <div className="filtersTitle">Filters</div>

                    <div className="filtersActions">
                        {selectedCount > 0 && (
                            <span className="filtersCountPill" title="Active filters">
                {selectedCount}
              </span>
                        )}
                        <button
                            type="button"
                            className="filtersReset"
                            onClick={resetAll}
                            disabled={selectedCount === 0}
                            title="Reset all filters"
                        >
                            Reset
                        </button>
                    </div>
                </div>

                <div className="filtersGrid">

                    {/* Publisher */}
                    <FilterRow
                        label="Publisher"
                        right={
                            <Segmented
                                value={(value.publisher_type?.[0] ?? "any") as "any" | "public" | "private" | "unknown"}
                                onChange={(k) =>
                                    onChange({
                                        ...value,
                                        publisher_type: k === "any" ? [] : [k],
                                    })
                                }
                                options={[
                                    {key: "any", label: "Any"},
                                    {key: "public", label: "Public"},
                                    {key: "private", label: "Private"},
                                    {key: "unknown", label: "Unknown"},
                                ]}
                            />
                        }
                    />

                    {/* No “false” facts */}
                    <FilterRow
                        label="Fact Checking"
                        right={
                            <Segmented<"any" | "true" | "false">
                                value={triToKey(value.no_false_facts)}
                                onChange={(k) => onChange({...value, no_false_facts: keyToTri(k)})}
                                options={[
                                    {key: "any", label: "Any"},
                                    {key: "true", label: "No false facts"},
                                    {key: "false", label: "False facts"},
                                ]}
                            />
                        }
                    />

                    {/* Author expert */}
                    <FilterRow
                        label="Author expert"
                        right={
                            <Segmented
                                value={value.author_expert ?? "any"}
                                onChange={(k) =>
                                    onChange({
                                        ...value,
                                        author_expert: k === "any" ? undefined : (k as "field_expert" | "not_field_expert" | "unknown"),
                                    })
                                }
                                options={[
                                    {key: "any", label: "Any"},
                                    {key: "field_expert", label: "Expert"},
                                    {key: "not_field_expert", label: "Not Expert"},
                                    {key: "unknown", label: "Unknown"},
                                ]}
                            />
                        }
                    />

                    {/* C2PA */}
                    <FilterRow
                        label="Includes C2PA"
                        right={
                            <SegmentedTri
                                value={triToKey(value.c2pa_present)}
                                onChange={(k) => onChange({...value, c2pa_present: keyToTri(k)})}
                            />
                        }
                    />
                </div>

                {/* Advanced toggle */}
                <button
                    type="button"
                    className={`advancedToggle ${advancedOpen ? "open" : ""}`}
                    onClick={() => setAdvancedOpen((o) => !o)}
                    aria-expanded={advancedOpen}
                >
          <span className="advancedLabel">
            Advanced filters
              {hasAnyAdvanced && <span className="advancedDot" title="Some advanced filters are active"/>}
          </span>
                    <span className="advancedChevron" aria-hidden="true">
            ▾
          </span>
                </button>
            </div>

            {/* Advanced content */}
            <div className={`advancedPanel ${advancedOpen ? "open" : ""}`}>
                <div className="advancedInner">
                    <ChipGroup
                        title="Tone"
                        items={TONES}
                        selected={value.tone ?? []}
                        getCount={(k) => counts.tone[k] ?? 0}
                        onToggle={(k) => onChange({...value, tone: toggleMulti(value.tone, k)})}
                        onClear={() => onChange({...value, tone: []})}
                    />

                    <ChipGroup
                        title="Type"
                        items={TYPES}
                        selected={value.content_type ?? []}
                        getCount={(k) => counts.content_type[k] ?? 0}
                        onToggle={(k) => onChange({...value, content_type: toggleMulti(value.content_type, k)})}
                        onClear={() => onChange({...value, content_type: []})}
                    />
                </div>
            </div>
        </div>
    );
}

/* -----------------------------
   Small presentational helpers
------------------------------ */

function FilterRow({label, right}: { label: string; right: React.ReactNode }) {
    return (
        <div className="filterRow">
            <div className="filterRowLabel">{label}</div>
            <div className="filterRowControl">{right}</div>
        </div>
    );
}

function SegmentedTri({
                          value,
                          onChange,
                      }: {
    value: "any" | "true" | "false";
    onChange: (v: "any" | "true" | "false") => void;
}) {
    return (
        <Segmented<"any" | "true" | "false">
            value={value}
            onChange={onChange}
            options={[
                {key: "any", label: "Any"},
                {key: "true", label: "Yes"},
                {key: "false", label: "No"},
            ]}
        />
    );
}

function Segmented<T extends string>({
                                         value,
                                         onChange,
                                         options,
                                     }: {
    value: T;
    onChange: (v: T) => void;
    options: Array<{ key: T; label: string }>;
}) {
    return (
        <div className="segmented" role="group">
            {options.map((o) => (
                <button
                    key={o.key}
                    type="button"
                    className={`segBtn ${value === o.key ? "active" : ""}`}
                    onClick={() => onChange(o.key)}
                >
                    {o.label}
                </button>
            ))}
        </div>
    );
}

function ChipGroup({
                       title,
                       items,
                       selected,
                       getCount,
                       onToggle,
                       onClear,
                   }: {
    title: string;
    items: string[];
    selected: string[];
    getCount: (key: string) => number;
    onToggle: (key: string) => void;
    onClear: () => void;
}) {
    const hasSelected = selected.length > 0;

    return (
        <div className="chipGroup">
            <div className="chipGroupHeader">
                <div className="chipGroupTitle">{title}</div>
                <button
                    type="button"
                    className="chipClear"
                    onClick={onClear}
                    disabled={!hasSelected}
                    title={`Clear ${title}`}
                >
                    Clear
                </button>
            </div>

            <div className="chips chipsModern">
                {items.map((k) => {
                    const active = selected.includes(k);
                    const c = getCount(k);
                    return (
                        <button
                            key={k}
                            type="button"
                            className={`chip chipModern ${active ? "active" : ""}`}
                            onClick={() => onToggle(k)}
                        >
                            <span className="chipLabel">{k}</span>
                            {c > 0 && <span className="chipCount">{c}</span>}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}