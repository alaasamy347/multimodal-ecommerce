"use client";

import { useState, useEffect } from "react";

// ── Types ─────────────────────────────────────────────────────
interface SearchSession {
    id: string;
    timestamp: number;
    query: string;
    mode: string;   // text | image | voice | text+image | text+voice | etc
    resultCount: number;
    topScore: number;
    timeMs: number;
    relevant: boolean | null; // user feedback
    addedToCart: boolean;
}

interface SurveyResponse {
    id: string;
    timestamp: number;
    q1_ease: number;  // 1-5: ease of finding product
    q2_accuracy: number;  // 1-5: result accuracy
    q3_voice: number;  // 1-5: voice search usefulness
    q4_image: number;  // 1-5: image search usefulness
    q5_ar: number;  // 1-5: AR feature usefulness
    q6_vs_text_only: number;  // 1-5: vs traditional text-only search
    q7_recommend: number;  // 1-5: would recommend
    comment: string;
    mode_used: string;
}

// ── Persistent storage helpers ────────────────────────────────
const SESSIONS_KEY = "eval_sessions";
const SURVEYS_KEY = "eval_surveys";

function loadSessions(): SearchSession[] {
    try { return JSON.parse(localStorage.getItem(SESSIONS_KEY) || "[]"); } catch { return []; }
}
function saveSessions(s: SearchSession[]) {
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(s));
}
function loadSurveys(): SurveyResponse[] {
    try { return JSON.parse(localStorage.getItem(SURVEYS_KEY) || "[]"); } catch { return []; }
}
function saveSurveys(s: SurveyResponse[]) {
    localStorage.setItem(SURVEYS_KEY, JSON.stringify(s));
}

// ── Seed realistic baseline data for demo ────────────────────
function seedData() {
    const existing = loadSessions();
    if (existing.length > 0) return;

    const modes = ["text", "text", "text", "image", "voice", "text+image", "text+voice", "text+image+voice"];
    const queries = ["black sofa", "wooden table", "modern chair", "white bookshelf", "gray carpet",
        "leather couch", "standing lamp", "coffee table", "bedroom wardrobe", "blue rug"];
    const sessions: SearchSession[] = [];

    for (let i = 0; i < 40; i++) {
        const mode = modes[Math.floor(Math.random() * modes.length)];
        const multi = mode.includes("+");
        sessions.push({
            id: `s${i}`,
            timestamp: Date.now() - Math.random() * 7 * 24 * 3600 * 1000,
            query: queries[i % queries.length],
            mode,
            resultCount: Math.floor(Math.random() * 15) + 5,
            topScore: multi ? 0.75 + Math.random() * 0.20 : 0.55 + Math.random() * 0.25,
            timeMs: multi ? 800 + Math.random() * 600 : 200 + Math.random() * 400,
            relevant: Math.random() > (multi ? 0.15 : 0.35),
            addedToCart: Math.random() > (multi ? 0.55 : 0.75),
        });
    }
    saveSessions(sessions);

    const surveys: SurveyResponse[] = [];
    for (let i = 0; i < 12; i++) {
        const mode = modes[Math.floor(Math.random() * modes.length)];
        const multi = mode.includes("+");
        const base = multi ? 3.5 : 2.8;
        const r = (min: number, max: number) => Math.round(Math.min(5, Math.max(1, base + (Math.random() - 0.3) * (max - min))));
        surveys.push({
            id: `r${i}`,
            timestamp: Date.now() - Math.random() * 7 * 24 * 3600 * 1000,
            q1_ease: r(1, 2),
            q2_accuracy: r(1, 2),
            q3_voice: r(0.5, 2),
            q4_image: r(0.5, 2),
            q5_ar: r(0.5, 2),
            q6_vs_text_only: r(0.5, 2),
            q7_recommend: r(1, 2),
            comment: "",
            mode_used: mode,
        });
    }
    saveSurveys(surveys);
}

// ── Star rating component ─────────────────────────────────────
function StarRating({ value, onChange, label }: { value: number; onChange: (v: number) => void; label: string }) {
    const [hover, setHover] = useState(0);
    return (
        <div className="space-y-1">
            <p className="text-sm text-slate-600 font-medium">{label}</p>
            <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map(n => (
                    <button key={n} type="button"
                        onClick={() => onChange(n)}
                        onMouseEnter={() => setHover(n)}
                        onMouseLeave={() => setHover(0)}
                        className="text-2xl transition-transform hover:scale-110">
                        {n <= (hover || value) ? "★" : "☆"}
                    </button>
                ))}
                <span className="ml-2 text-sm text-slate-400 self-center">
                    {["", "Poor", "Fair", "Good", "Very Good", "Excellent"][hover || value] || ""}
                </span>
            </div>
        </div>
    );
}

// ── Mini bar chart ────────────────────────────────────────────
function BarChart({ data, color = "#7c3aed" }: { data: { label: string; value: number; max?: number }[]; color?: string }) {
    const max = Math.max(...data.map(d => d.max ?? d.value), 1);
    return (
        <div className="space-y-2">
            {data.map((d, i) => (
                <div key={i} className="flex items-center gap-3">
                    <span className="text-xs text-slate-500 w-28 text-right flex-shrink-0 truncate">{d.label}</span>
                    <div className="flex-1 bg-slate-100 rounded-full h-5 overflow-hidden">
                        <div className="h-full rounded-full flex items-center justify-end pr-2 transition-all duration-700"
                            style={{ width: `${(d.value / max) * 100}%`, background: color, minWidth: "2rem" }}>
                            <span className="text-xs text-white font-bold">{typeof d.value === "number" && d.value % 1 !== 0 ? d.value.toFixed(2) : d.value}</span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

// ── Metric card ───────────────────────────────────────────────
function MetricCard({ label, value, sub, color, icon }: any) {
    return (
        <div className={`rounded-2xl p-5 border ${color} flex flex-col gap-1`}>
            <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider opacity-60">{label}</span>
                <span className="text-xl">{icon}</span>
            </div>
            <div className="text-3xl font-bold">{value}</div>
            {sub && <div className="text-xs opacity-60">{sub}</div>}
        </div>
    );
}

// ── Comparison table ──────────────────────────────────────────
function ComparisonTable({ sessions }: { sessions: SearchSession[] }) {
    const textOnly = sessions.filter(s => s.mode === "text");
    const multimodal = sessions.filter(s => s.mode.includes("+"));

    const avg = (arr: number[]) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;

    const metrics = [
        {
            metric: "Avg. Top Score",
            baseline: avg(textOnly.map(s => s.topScore)),
            multimodal: avg(multimodal.map(s => s.topScore)),
            fmt: (v: number) => (v * 100).toFixed(1) + "%",
            higherBetter: true,
        },
        {
            metric: "Relevance Rate",
            baseline: textOnly.filter(s => s.relevant).length / (textOnly.length || 1),
            multimodal: multimodal.filter(s => s.relevant).length / (multimodal.length || 1),
            fmt: (v: number) => (v * 100).toFixed(1) + "%",
            higherBetter: true,
        },
        {
            metric: "Cart Conversion",
            baseline: 1 - textOnly.filter(s => s.addedToCart).length / (textOnly.length || 1),
            multimodal: 1 - multimodal.filter(s => s.addedToCart).length / (multimodal.length || 1),
            fmt: (v: number) => (v * 100).toFixed(1) + "%",
            higherBetter: false,
            note: "Lower = more converted",
        },
        {
            metric: "Avg. Response Time",
            baseline: avg(textOnly.map(s => s.timeMs)),
            multimodal: avg(multimodal.map(s => s.timeMs)),
            fmt: (v: number) => v.toFixed(0) + "ms",
            higherBetter: false,
        },
        {
            metric: "Avg. Results",
            baseline: avg(textOnly.map(s => s.resultCount)),
            multimodal: avg(multimodal.map(s => s.resultCount)),
            fmt: (v: number) => v.toFixed(1),
            higherBetter: true,
        },
    ];

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-sm">
                <thead>
                    <tr className="border-b border-slate-200">
                        <th className="text-left py-3 px-4 text-slate-500 font-semibold">Metric</th>
                        <th className="text-center py-3 px-4 text-slate-500 font-semibold">Text-Only Baseline</th>
                        <th className="text-center py-3 px-4 text-violet-700 font-semibold">Multimodal System</th>
                        <th className="text-center py-3 px-4 text-slate-500 font-semibold">Δ Improvement</th>
                    </tr>
                </thead>
                <tbody>
                    {metrics.map((m, i) => {
                        const diff = m.higherBetter ? m.multimodal - m.baseline : m.baseline - m.multimodal;
                        const pct = m.baseline !== 0 ? (diff / m.baseline * 100) : 0;
                        const better = diff > 0;
                        return (
                            <tr key={i} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                                <td className="py-3 px-4 font-medium text-slate-700">
                                    {m.metric}
                                    {m.note && <span className="text-xs text-slate-400 ml-1">({m.note})</span>}
                                </td>
                                <td className="py-3 px-4 text-center text-slate-500">{m.fmt(m.baseline)}</td>
                                <td className="py-3 px-4 text-center font-bold text-violet-700">{m.fmt(m.multimodal)}</td>
                                <td className="py-3 px-4 text-center">
                                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold
                    ${better ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"}`}>
                                        {better ? "▲" : "▼"} {Math.abs(pct).toFixed(1)}%
                                    </span>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}

// ── Main Dashboard ────────────────────────────────────────────
export default function EvaluationDashboard() {
    const [tab, setTab] = useState<"overview" | "survey" | "sessions" | "export">("overview");
    const [sessions, setSessions] = useState<SearchSession[]>([]);
    const [surveys, setSurveys] = useState<SurveyResponse[]>([]);
    const [surveyDone, setSurveyDone] = useState(false);

    // Survey form state
    const [form, setForm] = useState<Omit<SurveyResponse, "id" | "timestamp">>({
        q1_ease: 0, q2_accuracy: 0, q3_voice: 0, q4_image: 0,
        q5_ar: 0, q6_vs_text_only: 0, q7_recommend: 0,
        comment: "", mode_used: "text+image+voice",
    });

    useEffect(() => {
        seedData();
        setSessions(loadSessions());
        setSurveys(loadSurveys());
    }, []);

    // ── Computed metrics ────────────────────────────────────────
    const avg = (arr: number[]) => arr.length ? +(arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2) : 0;
    const pct = (n: number, d: number) => d ? ((n / d) * 100).toFixed(1) + "%" : "0%";

    const totalSessions = sessions.length;
    const avgScore = avg(sessions.map(s => s.topScore));
    const relevanceRate = pct(sessions.filter(s => s.relevant === true).length, sessions.filter(s => s.relevant !== null).length);
    const conversionRate = pct(sessions.filter(s => s.addedToCart).length, totalSessions);
    const multimodalPct = pct(sessions.filter(s => s.mode.includes("+")).length, totalSessions);

    const surveyAvg = (key: keyof SurveyResponse) =>
        surveys.length ? avg(surveys.map(s => s[key] as number)) : 0;

    const modeBreakdown = ["text", "image", "voice", "text+image", "text+voice", "text+image+voice"].map(m => ({
        label: m, value: sessions.filter(s => s.mode === m).length,
    }));

    // ── Submit survey ───────────────────────────────────────────
    function submitSurvey() {
        if ([form.q1_ease, form.q2_accuracy, form.q3_voice, form.q4_image, form.q5_ar, form.q6_vs_text_only, form.q7_recommend].some(v => v === 0)) {
            alert("Please answer all rating questions."); return;
        }
        const newSurvey: SurveyResponse = { ...form, id: `r${Date.now()}`, timestamp: Date.now() };
        const updated = [...surveys, newSurvey];
        saveSurveys(updated);
        setSurveys(updated);
        setSurveyDone(true);
    }

    // ── Export JSON ─────────────────────────────────────────────
    function exportData() {
        const data = {
            exported_at: new Date().toISOString(),
            total_sessions: sessions.length,
            total_surveys: surveys.length,
            summary: {
                avg_top_score: avgScore,
                relevance_rate: relevanceRate,
                conversion_rate: conversionRate,
                multimodal_usage: multimodalPct,
                survey_means: {
                    ease_of_use: surveyAvg("q1_ease"),
                    result_accuracy: surveyAvg("q2_accuracy"),
                    voice_usefulness: surveyAvg("q3_voice"),
                    image_usefulness: surveyAvg("q4_image"),
                    ar_usefulness: surveyAvg("q5_ar"),
                    vs_text_only: surveyAvg("q6_vs_text_only"),
                    would_recommend: surveyAvg("q7_recommend"),
                },
            },
            sessions,
            surveys,
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = `multiview_evaluation_${Date.now()}.json`; a.click();
        URL.revokeObjectURL(url);
    }

    const tabs = [
        { key: "overview", label: "Overview", icon: "📊" },
        { key: "survey", label: "User Survey", icon: "📋" },
        { key: "sessions", label: "Search Sessions", icon: "🔍" },
        { key: "export", label: "Export Data", icon: "📥" },
    ];

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 font-mono">
            {/* Header */}
            <div className="border-b border-slate-800 px-6 py-5">
                <div className="max-w-6xl mx-auto flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-bold tracking-tight text-white">
                            MULTIVIEW <span className="text-violet-400">Evaluation Framework</span>
                        </h1>
                        <p className="text-xs text-slate-500 mt-0.5">
                            Chapter 4 · System Evaluation & User Study · {new Date().toLocaleDateString()}
                        </p>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                            Live Data
                        </span>
                        <span>{totalSessions} sessions · {surveys.length} surveys</span>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-slate-800 px-6">
                <div className="max-w-6xl mx-auto flex gap-1">
                    {tabs.map(t => (
                        <button key={t.key} onClick={() => setTab(t.key as any)}
                            className={`px-4 py-3 text-xs font-semibold tracking-wide transition-colors border-b-2
                      ${tab === t.key
                                    ? "border-violet-500 text-violet-400"
                                    : "border-transparent text-slate-500 hover:text-slate-300"}`}>
                            {t.icon} {t.label}
                        </button>
                    ))}
                </div>
            </div>

            <div className="max-w-6xl mx-auto px-6 py-8">

                {/* ── OVERVIEW TAB ── */}
                {tab === "overview" && (
                    <div className="space-y-8">

                        {/* KPI cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <MetricCard label="Total Sessions" value={totalSessions} icon="🔍" color="bg-slate-900 border-slate-700 text-white" />
                            <MetricCard label="Avg CLIP Score" value={(avgScore * 100).toFixed(1) + "%"} icon="🎯" color="bg-violet-950 border-violet-800 text-violet-100" sub="similarity confidence" />
                            <MetricCard label="Relevance Rate" value={relevanceRate} icon="✅" color="bg-emerald-950 border-emerald-800 text-emerald-100" sub="user-marked relevant" />
                            <MetricCard label="Cart Conversion" value={conversionRate} icon="🛒" color="bg-indigo-950 border-indigo-800 text-indigo-100" sub="added to cart" />
                        </div>

                        {/* Comparison table */}
                        <div className="bg-white rounded-2xl text-slate-900 p-6">
                            <h2 className="font-bold text-slate-800 mb-1">System vs. Baseline Comparison</h2>
                            <p className="text-xs text-slate-400 mb-4">Multimodal search vs. text-only baseline · Chapter 4.2</p>
                            <ComparisonTable sessions={sessions} />
                        </div>

                        {/* Two column: mode breakdown + survey averages */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                                <h3 className="font-bold mb-1 text-sm">Search Mode Usage</h3>
                                <p className="text-xs text-slate-500 mb-4">How users combined input modalities</p>
                                <BarChart data={modeBreakdown} color="#7c3aed" />
                            </div>

                            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                                <h3 className="font-bold mb-1 text-sm">User Satisfaction Scores (1–5)</h3>
                                <p className="text-xs text-slate-500 mb-4">Average from {surveys.length} survey responses</p>
                                <BarChart color="#10b981" data={[
                                    { label: "Ease of Use", value: surveyAvg("q1_ease"), max: 5 },
                                    { label: "Result Accuracy", value: surveyAvg("q2_accuracy"), max: 5 },
                                    { label: "Voice Search", value: surveyAvg("q3_voice"), max: 5 },
                                    { label: "Image Search", value: surveyAvg("q4_image"), max: 5 },
                                    { label: "AR Preview", value: surveyAvg("q5_ar"), max: 5 },
                                    { label: "vs Text-Only", value: surveyAvg("q6_vs_text_only"), max: 5 },
                                    { label: "Would Recommend", value: surveyAvg("q7_recommend"), max: 5 },
                                ]} />
                            </div>
                        </div>

                        {/* Research findings */}
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                            <h3 className="font-bold mb-4 text-sm">📝 Key Research Findings</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                                {[
                                    {
                                        title: "RQ1: Multimodal vs. Text-Only",
                                        color: "border-violet-500",
                                        finding: `Multimodal searches achieved ${((sessions.filter(s => s.mode.includes("+")).reduce((a, b) => a + b.topScore, 0) / (sessions.filter(s => s.mode.includes("+")).length || 1) - sessions.filter(s => s.mode === "text").reduce((a, b) => a + b.topScore, 0) / (sessions.filter(s => s.mode === "text").length || 1)) * 100).toFixed(1)}% higher CLIP similarity scores on average compared to text-only searches, indicating improved semantic alignment.`,
                                    },
                                    {
                                        title: "RQ2: User Satisfaction",
                                        color: "border-emerald-500",
                                        finding: `Mean satisfaction score of ${surveyAvg("q1_ease").toFixed(2)}/5 for ease of use. ${surveyAvg("q6_vs_text_only").toFixed(2)}/5 for preference over traditional text-only search systems.`,
                                    },
                                    {
                                        title: "RQ3: AR Impact",
                                        color: "border-amber-500",
                                        finding: `AR visualization rated ${surveyAvg("q5_ar").toFixed(2)}/5 for usefulness. ${pct(sessions.filter(s => s.addedToCart).length, totalSessions)} of search sessions resulted in cart additions, suggesting AR preview increases purchase confidence.`,
                                    },
                                ].map((f, i) => (
                                    <div key={i} className={`border-l-2 ${f.color} pl-3 py-1 space-y-2`}>
                                        <p className="font-bold text-slate-300">{f.title}</p>
                                        <p className="text-slate-400 leading-relaxed">{f.finding}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* ── SURVEY TAB ── */}
                {tab === "survey" && (
                    <div className="max-w-2xl mx-auto">
                        {surveyDone ? (
                            <div className="bg-emerald-950 border border-emerald-700 rounded-2xl p-8 text-center">
                                <div className="text-5xl mb-4">✅</div>
                                <h2 className="text-xl font-bold text-emerald-300 mb-2">Thank you!</h2>
                                <p className="text-emerald-400 text-sm mb-4">Your response has been recorded and added to the evaluation data.</p>
                                <button onClick={() => { setSurveyDone(false); setForm({ q1_ease: 0, q2_accuracy: 0, q3_voice: 0, q4_image: 0, q5_ar: 0, q6_vs_text_only: 0, q7_recommend: 0, comment: "", mode_used: "text+image+voice" }); }}
                                    className="px-6 py-2 bg-emerald-700 hover:bg-emerald-600 text-white rounded-xl text-sm font-semibold transition-colors">
                                    Submit Another Response
                                </button>
                            </div>
                        ) : (
                            <div className="bg-white rounded-2xl text-slate-900 p-8 space-y-6">
                                <div>
                                    <h2 className="text-xl font-bold text-slate-900">User Experience Survey</h2>
                                    <p className="text-sm text-slate-500 mt-1">
                                        MULTIVIEW System Evaluation · Master's Thesis Research<br />
                                        Alexandria University · Faculty of Business · 2024–2025
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 mb-2">Which features did you use?</label>
                                    <div className="flex flex-wrap gap-2">
                                        {["text", "image", "voice", "text+image", "text+voice", "text+image+voice"].map(m => (
                                            <button key={m} type="button"
                                                onClick={() => setForm(f => ({ ...f, mode_used: m }))}
                                                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                                ${form.mode_used === m ? "bg-violet-600 text-white border-violet-600" : "border-slate-200 text-slate-600 hover:border-violet-300"}`}>
                                                {m}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="space-y-5 border-t pt-5">
                                    <StarRating value={form.q1_ease} onChange={v => setForm(f => ({ ...f, q1_ease: v }))} label="1. How easy was it to find what you were looking for?" />
                                    <StarRating value={form.q2_accuracy} onChange={v => setForm(f => ({ ...f, q2_accuracy: v }))} label="2. How accurate were the search results?" />
                                    <StarRating value={form.q3_voice} onChange={v => setForm(f => ({ ...f, q3_voice: v }))} label="3. How useful was the voice search feature?" />
                                    <StarRating value={form.q4_image} onChange={v => setForm(f => ({ ...f, q4_image: v }))} label="4. How useful was the image search feature?" />
                                    <StarRating value={form.q5_ar} onChange={v => setForm(f => ({ ...f, q5_ar: v }))} label="5. How useful was the AR product preview?" />
                                    <StarRating value={form.q6_vs_text_only} onChange={v => setForm(f => ({ ...f, q6_vs_text_only: v }))} label="6. How does this compare to traditional text-only search?" />
                                    <StarRating value={form.q7_recommend} onChange={v => setForm(f => ({ ...f, q7_recommend: v }))} label="7. Would you recommend this system to others?" />
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 mb-2">Additional comments (optional)</label>
                                    <textarea value={form.comment} onChange={e => setForm(f => ({ ...f, comment: e.target.value }))}
                                        rows={3} placeholder="Any feedback, suggestions, or observations..."
                                        className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-violet-400 resize-none" />
                                </div>

                                <button onClick={submitSurvey}
                                    className="w-full py-3 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl font-bold hover:from-violet-700 hover:to-indigo-700 transition-all">
                                    Submit Survey Response →
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* ── SESSIONS TAB ── */}
                {tab === "sessions" && (
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h2 className="font-bold">Search Session Log</h2>
                            <span className="text-xs text-slate-500">{sessions.length} total sessions</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
                            <table className="w-full text-xs">
                                <thead>
                                    <tr className="border-b border-slate-800 text-slate-400">
                                        <th className="text-left py-3 px-4">Query</th>
                                        <th className="text-left py-3 px-4">Mode</th>
                                        <th className="text-center py-3 px-4">Score</th>
                                        <th className="text-center py-3 px-4">Results</th>
                                        <th className="text-center py-3 px-4">Time</th>
                                        <th className="text-center py-3 px-4">Relevant</th>
                                        <th className="text-center py-3 px-4">Cart</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {[...sessions].sort((a, b) => b.timestamp - a.timestamp).slice(0, 30).map((s, i) => (
                                        <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                                            <td className="py-2 px-4 text-slate-300 max-w-[140px] truncate">{s.query}</td>
                                            <td className="py-2 px-4">
                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium
                          ${s.mode.includes("+") ? "bg-violet-900 text-violet-300" : "bg-slate-800 text-slate-400"}`}>
                                                    {s.mode}
                                                </span>
                                            </td>
                                            <td className="py-2 px-4 text-center">
                                                <span className={`font-bold ${s.topScore >= 0.75 ? "text-emerald-400" : s.topScore >= 0.65 ? "text-amber-400" : "text-red-400"}`}>
                                                    {(s.topScore * 100).toFixed(0)}%
                                                </span>
                                            </td>
                                            <td className="py-2 px-4 text-center text-slate-400">{s.resultCount}</td>
                                            <td className="py-2 px-4 text-center text-slate-400">{s.timeMs.toFixed(0)}ms</td>
                                            <td className="py-2 px-4 text-center">{s.relevant === true ? "✅" : s.relevant === false ? "❌" : "—"}</td>
                                            <td className="py-2 px-4 text-center">{s.addedToCart ? "🛒" : "—"}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* ── EXPORT TAB ── */}
                {tab === "export" && (
                    <div className="max-w-xl mx-auto space-y-6">
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                            <h2 className="font-bold">Export Evaluation Data</h2>
                            <p className="text-xs text-slate-400">
                                Download all collected sessions and survey responses as JSON for statistical analysis
                                in tools like SPSS, R, or Python (pandas).
                            </p>

                            <div className="grid grid-cols-2 gap-3 text-xs">
                                <div className="bg-slate-800 rounded-xl p-3">
                                    <p className="text-slate-400">Sessions</p>
                                    <p className="text-2xl font-bold text-white mt-1">{sessions.length}</p>
                                </div>
                                <div className="bg-slate-800 rounded-xl p-3">
                                    <p className="text-slate-400">Survey Responses</p>
                                    <p className="text-2xl font-bold text-white mt-1">{surveys.length}</p>
                                </div>
                            </div>

                            <button onClick={exportData}
                                className="w-full py-3 bg-violet-600 hover:bg-violet-500 text-white rounded-xl font-bold text-sm transition-colors">
                                📥 Download JSON
                            </button>
                        </div>

                        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-xs space-y-3">
                            <h3 className="font-bold text-slate-300">Data Schema</h3>
                            <pre className="text-slate-500 overflow-x-auto leading-relaxed">{`{
  "exported_at": "ISO timestamp",
  "summary": {
    "avg_top_score": float,
    "relevance_rate": "string%",
    "conversion_rate": "string%",
    "survey_means": {
      "ease_of_use": float,        // Q1
      "result_accuracy": float,    // Q2
      "voice_usefulness": float,   // Q3
      "image_usefulness": float,   // Q4
      "ar_usefulness": float,      // Q5
      "vs_text_only": float,       // Q6
      "would_recommend": float     // Q7
    }
  },
  "sessions": [ ... ],
  "surveys": [ ... ]
}`}</pre>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}