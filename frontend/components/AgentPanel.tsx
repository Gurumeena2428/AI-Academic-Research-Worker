"use client";

import { useState } from "react";
import { CheckCircle2, CircleAlert, Loader2, Play, RotateCcw, ShieldCheck, Wrench } from "lucide-react";
import { AgentResponse } from "@/lib/types";
import { runAgent } from "@/lib/agent";

interface AgentPanelProps {
  hasDocuments: boolean;
}

export default function AgentPanel({ hasDocuments }: AgentPanelProps) {
  const [task, setTask] = useState(
    "Compare the methodology and evaluation metrics of the most relevant papers in my uploaded documents and prepare a cited comparison."
  );
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function execute() {
    if (!task.trim() || running) return;
    setRunning(true);
    setError(null);
    try {
      setResult(await runAgent(task));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agent execution failed.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="flex h-full flex-1 flex-col bg-slate-100 overflow-y-auto">
      <div className="mx-auto w-full max-w-5xl px-6 py-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Wrench className="h-5 w-5 text-brand-600" />
                <h1 className="text-lg font-semibold text-slate-900">Autonomous Research Worker</h1>
              </div>
              <p className="mt-1 text-sm text-slate-500">
                Give the agent a multi-step research objective. It plans research subtasks, searches evidence, retries weak retrieval, and verifies the final report.
              </p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">Research mode</span>
          </div>

          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            rows={4}
            disabled={running}
            className="mt-5 w-full resize-y rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 disabled:bg-slate-50"
            placeholder="Example: Find the relevant papers, compare their methods and evaluation metrics, and produce a cited report."
          />
          <div className="mt-3 flex items-center justify-between">
            <p className="text-xs text-slate-400">
              {hasDocuments ? "The agent can search all uploaded PDFs." : "Upload PDFs first so the agent has evidence to work with."}
            </p>
            <button
              onClick={execute}
              disabled={running || !hasDocuments || !task.trim()}
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              {running ? "Agent running…" : "Run autonomous task"}
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 flex gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <CircleAlert className="mt-0.5 h-4 w-4 shrink-0" /> {error}
          </div>
        )}

        {result && (
          <div className="mt-5 space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              <Metric title="Status" value={result.status} />
              <Metric title="Retries" value={String(result.retries)} />
              <Metric title="Verification" value={result.verified ? "Verified" : "Needs review"} />
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <h2 className="font-semibold text-slate-900">Agent plan</h2>
              <ol className="mt-3 space-y-2">
                {result.plan.map((item, i) => (
                  <li key={i} className="flex gap-3 text-sm text-slate-700">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold">{i + 1}</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-slate-900">Execution trace</h2>
                <span className="text-xs text-slate-400">{result.steps.length} actions</span>
              </div>
              <div className="mt-3 space-y-3">
                {result.steps.map((step) => (
                  <div key={`${step.step}-${step.tool}`} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                    <div className="flex items-start gap-3">
                      {step.success ? <CheckCircle2 className="mt-0.5 h-4 w-4 text-emerald-600" /> : <CircleAlert className="mt-0.5 h-4 w-4 text-amber-600" />}
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xs font-semibold text-slate-500">STEP {step.step}</span>
                          <span className="rounded-md bg-white px-2 py-0.5 text-xs font-medium text-slate-600">{step.tool}</span>
                          {step.retry > 0 && <span className="inline-flex items-center gap-1 text-xs text-amber-700"><RotateCcw className="h-3 w-3" /> retry {step.retry}</span>}
                        </div>
                        <p className="mt-1 text-sm font-medium text-slate-800">{step.action}</p>
                        <p className="mt-1 whitespace-pre-wrap text-xs leading-5 text-slate-500">{step.observation}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-600" />
                <h2 className="font-semibold text-slate-900">Final report</h2>
              </div>
              <div className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-700">{result.report}</div>
              <div className="mt-5 border-t border-slate-100 pt-4 text-xs text-slate-400">
                Run ID: {result.run_id} · Evidence sources: {result.sources.length}
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{title}</p>
      <p className="mt-1 text-lg font-semibold capitalize text-slate-900">{value}</p>
    </div>
  );
}
