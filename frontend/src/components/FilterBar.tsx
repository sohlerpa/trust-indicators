import { useMemo, useState } from "react";
import type { FeedFilters } from "../api/types";

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
const PUBLISHERS = ["public", "private", "unknown"] as const;

type Publisher = (typeof PUBLISHERS)[number];
type AuthorExpert = "field_expert" | "not_field_expert" | "unknown";

type BoolMulti = Array<true | false>;
type AuthorMulti = AuthorExpert[];
type PublisherMulti = Publisher[];

function toggleIn<T>(list: T[] | undefined, item: T): T[] {
    const s = new Set(list ?? []);
    if (s.has(item)) s.delete(item);
    else s.add(item);
    return Array.from(s);
}

function uniq<T>(arr: T[]): T[] {
    return Array.from(new Set(arr));
}

/**
 * Store multi-select booleans in the existing backend shape (boolean | undefined)
 * by encoding multi selection as:
 *  - [] => undefined
 *  - [true] => true
 *  - [false] => false
 *  - [true,false] => undefined (treat as no filter OR "both")
 *
 * This is the only lossy part because your API currently supports only tri-state.
 * If you want true multi-select semantics on the backend, we should change the API
 * to accept repeated params (e.g. no_false_facts=true&no_false_facts=false).
 */
function boolMultiToTri(xs: BoolMulti): boolean | undefined {
    const u = uniq(xs);
    if (u.length === 0) return undefined;
    if (u.length === 2) return undefined;
    return u[0];
}

function triToBoolMulti(v: boolean | undefined): BoolMulti {
    if (v === undefined) return [];
    return [v];
}

function authorMultiToSingle(xs: AuthorMulti): AuthorExpert | undefined {
    const u = uniq(xs);
    if (u.length === 0) return undefined;
    if (u.length >= 2) return undefined; // can't represent in current API
    return u[0];
}

function singleToAuthorMulti(v: AuthorExpert | undefined): AuthorMulti {
    return v ? [v] : [];
}

export default function FilterBar({ value, onChange, counts }: Props) {
    const [advancedOpen, setAdvancedOpen] = useState(false);

    // map existing (single-value) API fields into multi-select UI state
    const publisherSel = (value.publisher_type ?? []) as PublisherMulti;

    const factSel = triToBoolMulti(value.no_false_facts);
    const c2paSel = triToBoolMulti(value.c2pa_present);
    const authorSel = singleToAuthorMulti(value.author_expert as AuthorExpert | undefined);

    const hasAnyAdvanced = useMemo(() => {
        return (value.tone ?? []).length > 0 || (value.content_type ?? []).length > 0;
    }, [value.tone, value.content_type]);

    const selectedCount = useMemo(() => {
        const parts = [
            (publisherSel ?? []).length,
            factSel.length,
            authorSel.length,
            c2paSel.length,
            (value.tone ?? []).length,
            (value.content_type ?? []).length,
        ];
        return parts.reduce((a, b) => a + b, 0);
    }, [publisherSel, factSel, authorSel, c2paSel, value.tone, value.content_type]);

    const resetAll = () => {
        onChange({
            ...value,
            // top filters
            publisher_type: [],
            no_false_facts: undefined,
            author_expert: undefined,
            c2pa_present: undefined,
            // advanced
            tone: [],
            content_type: [],
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
                    {/* Publisher (multi) */}
                    <FilterRow
                        label="Publisher"
                        right={
                            <SegMulti
                                selected={publisherSel}
                                options={[
                                    { key: "public", label: "Public", count: counts.publisher_type.public ?? 0 },
                                    { key: "private", label: "Private", count: counts.publisher_type.private ?? 0 },
                                    { key: "unknown", label: "Unknown", count: counts.publisher_type.unknown ?? 0 },
                                ]}
                                onToggle={(k) => onChange({ ...value, publisher_type: toggleIn(publisherSel, k) })}
                            />
                        }
                    />

                    {/* Fact Checking (multi UI -> tri API) */}
                    <FilterRow
                        label="Fact Checking"
                        right={
                            <SegMulti
                                selected={factSel}
                                options={[
                                    { key: true as const, label: "No false facts" },
                                    { key: false as const, label: "False facts" },
                                ]}
                                onToggle={(k) => {
                                    const next = toggleIn(factSel, k);
                                    onChange({ ...value, no_false_facts: boolMultiToTri(next) });
                                }}
                            />
                        }
                    />

                    {/* Author Expertise (multi UI -> single API) */}
                    <FilterRow
                        label="Author Field Expertise"
                        right={
                            <SegMulti
                                selected={authorSel}
                                options={[
                                    { key: "field_expert" as const, label: "Expert" },
                                    { key: "not_field_expert" as const, label: "Not expert" },
                                    { key: "unknown" as const, label: "Unknown" },
                                ]}
                                onToggle={(k) => {
                                    const next = toggleIn(authorSel, k);
                                    onChange({ ...value, author_expert: authorMultiToSingle(next) as any });
                                }}
                            />
                        }
                    />

                    {/* C2PA (multi UI -> tri API) */}
                    <FilterRow
                        label="Includes C2PA"
                        right={
                            <SegMulti
                                selected={c2paSel}
                                options={[
                                    { key: true as const, label: "Has C2PA" },
                                    { key: false as const, label: "No C2PA" },
                                ]}
                                onToggle={(k) => {
                                    const next = toggleIn(c2paSel, k);
                                    onChange({ ...value, c2pa_present: boolMultiToTri(next) });
                                }}
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
              {hasAnyAdvanced && <span className="advancedDot" title="Some advanced filters are active" />}
          </span>
                    <span className="advancedChevron" aria-hidden="true">
            ▾
          </span>
                </button>
            </div>

            {/* Advanced content (same style rows) */}
            <div className={`advancedPanel ${advancedOpen ? "open" : ""}`}>
                <div className="advancedInner">
                    <FilterRow
                        label="Tone"
                        right={
                            <SegMulti
                                selected={value.tone ?? []}
                                options={TONES.map((t) => ({ key: t, label: t, count: counts.tone[t] ?? 0 }))}
                                onToggle={(k) => onChange({ ...value, tone: toggleIn(value.tone, k) })}
                                wrap
                            />
                        }
                    />

                    <FilterRow
                        label="Type"
                        right={
                            <SegMulti
                                selected={value.content_type ?? []}
                                options={TYPES.map((t) => ({ key: t, label: t, count: counts.content_type[t] ?? 0 }))}
                                onToggle={(k) => onChange({ ...value, content_type: toggleIn(value.content_type, k) })}
                                wrap
                            />
                        }
                    />
                </div>
            </div>
        </div>
    );
}

/* -----------------------------
   Small presentational helpers
------------------------------ */

function FilterRow({ label, right }: { label: string; right: React.ReactNode }) {
    return (
        <div className="filterRow">
            <div className="filterRowLabel">{label}</div>
            <div className="filterRowControl">{right}</div>
        </div>
    );
}

function SegMulti<T extends string | boolean>({
                                                  selected,
                                                  options,
                                                  onToggle,
                                                  wrap = false,
                                              }: {
    selected: T[];
    options: Array<{ key: T; label: string; count?: number }>;
    onToggle: (k: T) => void;
    wrap?: boolean;
}) {

    return (
        <div className={`segmented segmentedMulti ${wrap ? "wrap" : ""}`} role="group">
            {options.map((o) => {
                const active = selected.includes(o.key);
                const c = o.count ?? 0;
                return (
                    <button
                        key={String(o.key)}
                        type="button"
                        className={`segBtn ${active ? "active" : ""}`}
                        onClick={() => onToggle(o.key)}
                        title={c > 0 ? `${c}` : undefined}
                    >
                        <span>{o.label}</span>
                        <span
                            className={`segCount ${c > 0 ? "show" : "isZero"}`}
                            aria-label={`${o.label}: ${c}`}
                        >
                          {c}
                        </span>
                    </button>
                );
            })}
        </div>
    );
}