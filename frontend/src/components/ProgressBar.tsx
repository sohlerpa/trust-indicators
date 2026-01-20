import { useEffect, useState } from "react";
import { getProgress } from "../api/endpoints";

type Props = {
    runId?: string;
};

const STEP_LABELS: Record<string, string> = {
    start: "Starting analysis",

    analyze_author: "Evaluating author expertise",
    analyzing_author: "Evaluating author background",
    saving_result: "Saving result",

    extract_claims: "Extracting factual claims",
    search_fact_checks: "Searching fact-check databases",
    asserting_claims: "Verifying claims with LLM",

    done: "Analysis complete",
};

export default function ProgressBar({ runId }: Props) {
    const [pct, setPct] = useState(0);
    const [step, setStep] = useState("starting");
    const [done, setDone] = useState(false);

    // polling
    useEffect(() => {
        if (!runId) return;

        let alive = true;

        const poll = async () => {
            try {
                const data = await getProgress(runId);
                if (!alive) return;

                setPct(data.progress);
                setStep(data.step);

                if (data.progress < 1) {
                    setTimeout(poll, 1000);
                }
            } catch {
                setTimeout(poll, 2000);
            }
        };

        poll();

        return () => {
            alive = false;
        };
    }, [runId]);

    // fade-out after completion
    useEffect(() => {
        if (pct >= 1) {
            const t = setTimeout(() => setDone(true), 600);
            return () => clearTimeout(t);
        }
    }, [pct]);

    if (!runId || done) return null;

    const label = STEP_LABELS[step] ?? step.replaceAll("_", " ");

    return (
        <div className="progressWrapper">
            <div className="progress">
                <div
                    className="progressFill"
                    style={{ width: `${Math.round(pct * 100)}%` }}
                />
            </div>

            <span className="progressLabel">
                {Math.round(pct * 100)}% · {label}
            </span>
        </div>
    );
}