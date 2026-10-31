"""Draft evaluation report and decision log, built only from reviewed findings."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from .findings import Decision, Finding, final_points


def scores(findings: list[Finding], decisions: dict[str, Decision], criteria: dict[str, dict]) -> dict[str, dict[str, float]]:
    """Score per subject and criterion, computed by code from decided findings only.

    Each criterion has a `max` and an optional `base` (points a subject starts with, from which
    deductions are made). The result is kept between 0 and the maximum.
    """
    table: dict[str, dict[str, float]] = {}
    for f in findings:
        if f.criterion not in criteria:
            continue
        row = table.setdefault(f.subject, {c: float(v.get("base", 0)) for c, v in criteria.items()})
        pts = final_points(f, decisions.get(f.id))
        if pts is not None:
            row[f.criterion] += pts
    for row in table.values():
        for c, v in criteria.items():
            row[c] = max(0.0, min(row[c], float(v["max"])))
    return table


def undecided(findings: list[Finding], decisions: dict[str, Decision]) -> list[Finding]:
    return [f for f in findings if f.id not in decisions]


def decision_log(findings: list[Finding], decisions: dict[str, Decision]) -> list[dict]:
    by_id = {f.id: f for f in findings}
    return [{"finding": d.finding_id, "subject": by_id[d.finding_id].subject, "title": by_id[d.finding_id].title,
             "proposed_points": by_id[d.finding_id].proposed_points, "action": d.action,
             "final_points": final_points(by_id[d.finding_id], d), "reason": d.reason,
             "evaluator": d.evaluator, "at": d.at.isoformat(), "modified_detail": d.modified_detail}
            for d in sorted(decisions.values(), key=lambda d: d.at)]


def build_markdown(*, context: dict, signoff: dict, findings: list[Finding], decisions: dict[str, Decision],
                   criteria: dict[str, dict], not_assessed: list[str], inputs: list[dict],
                   model_calls: list[dict], methods: set[str]) -> str:
    pending = undecided(findings, decisions)
    if pending:
        raise ValueError(f"{len(pending)} findings have not been reviewed; every finding needs a decision before the report is produced")
    table = scores(findings, decisions, criteria)
    now = datetime.now(timezone.utc).strftime("%d %B %Y %H:%M UTC")
    L = [f"# Draft evaluation: {context['title']}", "",
         f"Tender {context['reference']} · {context['owner']} · produced {now}", "",
         "> **Draft for the evaluation panel.** Evalia proposed the findings below; a named evaluator accepted, rejected or "
         "modified every one. Scores are computed by code from those decisions under the criteria the client signed off. "
         "The panel is responsible for the evaluation and any award.", "",
         "## Criteria sign-off", "",
         f"Criteria confirmed by **{signoff['by']}** on {signoff['at']}, before any submission was read.", "",
         "## Scores (computed from reviewed findings)", "",
         "| Tenderer | " + " | ".join(f"{v['title']} (max {v['max']:g})" for v in criteria.values()) + " | Total |",
         "|---|" + "---:|" * (len(criteria) + 1)]
    for subject, row in sorted(table.items(), key=lambda kv: -sum(kv[1].values())):
        L.append(f"| {subject} | " + " | ".join(f"{row[c]:g}" for c in criteria) + f" | **{sum(row.values()):g}** |")
    L += ["", "## Findings by tenderer", ""]
    for subject in sorted({f.subject for f in findings}):
        L += [f"### {subject}", ""]
        for f in [x for x in findings if x.subject == subject]:
            d = decisions[f.id]
            mark = {"accept": "Accepted", "reject": "Rejected", "modify": "Modified", "score": "Scored"}[d.action]
            L.append(f"- **{f.title}** ({f.basis}; {f.severity}) — {mark} by {d.evaluator}"
                     + (f": {d.reason}" if d.reason else ""))
            L.append(f"  - {d.modified_detail or f.detail}")
            for e in f.evidence:
                L.append(f"  - Evidence: {e.doc_id}, p.{e.page}: \"{e.quote}\" — {'verified on page' if e.verified else 'NOT VERIFIED'}")
        L.append("")
    L += ["## Decision log", "", "| Time (UTC) | Evaluator | Finding | Action | Proposed | Final | Reason |", "|---|---|---|---|---:|---:|---|"]
    for r in decision_log(findings, decisions):
        L.append(f"| {r['at'][:19]} | {r['evaluator']} | {r['title']} | {r['action']} | "
                 f"{'' if r['proposed_points'] is None else r['proposed_points']} | {'' if r['final_points'] is None else r['final_points']} | {r['reason']} |")
    L += ["", "## Not assessed", ""] + [f"- {x}" for x in not_assessed]
    L += ["", "## Method and use of AI", "",
          "- Extraction methods used: " + "; ".join(sorted(methods)) + ".",
          "- Every quote was checked against the page it cites; unverified evidence is marked.",
          "- Arithmetic, thresholds and scores are computed by code, never by a model.",
          "- AI models can produce plausible but false output. The reviewing evaluator acknowledged this risk before export.",
          f"- Model calls: {len(model_calls)}" + (f" ({', '.join(sorted({c['model_returned'] for c in model_calls}))})" if model_calls else " (none)") + ".",
          "", "## Inputs", "", "| Document | SHA-256 |", "|---|---|"]
    L += [f"| {i['doc_id']} | `{i['sha256']}` |" for i in inputs]
    body = "\n".join(L)
    digest = hashlib.sha256(body.encode()).hexdigest()
    return body + f"\n\nReport SHA-256: `{digest}`\n"


def save_record(path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=1, default=str))
