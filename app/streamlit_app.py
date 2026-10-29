"""Evalia demo: a local application for evaluating construction tenders.

Run from the repository root:

    streamlit run app/streamlit_app.py

The application runs on the evaluator's own machine. Documents are read locally;
they leave the machine only if the evaluator chooses an AI model profile that the
engagement's residency policy permits.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evalia.engine.documents import load_pdf  # noqa: E402
from evalia.engine.findings import Decision  # noqa: E402
from evalia.engine.llm import Gateway, GatewayError, ResidencyPolicy, load_profiles  # noqa: E402
from evalia.engine.report import build_markdown, decision_log, scores, undecided  # noqa: E402
from evalia.engine.rules import Band  # noqa: E402
from packs.construction.evaluate import evaluate_bid, load_default_criteria  # noqa: E402
from packs.construction.extract import extract_with_model, read_forms  # noqa: E402

DEMO_DIR = ROOT / "tests" / "fixtures" / "synthetic"
DATA_DIR = Path(os.environ.get("EVALIA_DATA_DIR") or Path.home() / ".evalia-demo")
STEPS = ["1. Context", "2. Tenderers", "3. Evaluation criteria", "4. Evaluate", "5. Review", "6. Draft evaluation"]

st.set_page_config(page_title="Evalia", page_icon="📄", layout="wide")
S = st.session_state
S.setdefault("criteria", load_default_criteria())
S.setdefault("signoff", None)
S.setdefault("findings", [])
S.setdefault("decisions", {})
S.setdefault("docs", {})
S.setdefault("methods", set())
S.setdefault("calls", [])
S.setdefault("evaluator", "")

CONTEXT = {"reference": "RC-2026-014", "title": "Riverbend County Light-Industrial Facility (fictional)",
           "owner": "Riverbend County Department of Public Works (fictional)"}


def engagement_dir() -> Path:
    d = DATA_DIR / "engagements" / CONTEXT["reference"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def highlight(text: str, quote: str) -> str:
    esc = html.escape(text)
    if not quote.split():
        return f"<pre>{esc}</pre>"
    pattern = re.compile(r"\s+".join(re.escape(html.escape(w)) for w in quote.split()))
    return "<pre style='white-space:pre-wrap'>" + pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", esc, count=1) + "</pre>"


# ---------------------------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("Evalia")
    st.caption("Tender evaluation support. The evaluator decides.")
    unlocked = S.signoff is not None
    step = st.radio("Steps", STEPS, index=0)
    if not unlocked:
        st.info("Steps 4 to 6 open once the criteria are signed off.")
    S.evaluator = st.text_input("Evaluator name", S.evaluator, help="Recorded with every decision")
    st.caption(f"Data folder: {DATA_DIR}")

if step in STEPS[3:] and not unlocked:
    st.warning("Sign off the evaluation criteria (step 3) before any submission is read.")
    st.stop()

# ---------------------------------------------------------------------------------------------- 1. context
if step == STEPS[0]:
    st.header("Context")
    st.markdown(f"**Tender:** {CONTEXT['reference']} — {CONTEXT['title']}  \n**Owner:** {CONTEXT['owner']}")
    st.warning("Demonstration data: the tender and all three bids are fictional documents generated for this demo.")
    tender = DEMO_DIR / "tender_ITB_RC-2026-014.pdf"
    if tender.exists():
        doc = load_pdf(tender, "ITB")
        with st.expander("Invitation to Bid, as read (text layer)"):
            for pg in doc.pages:
                st.markdown(f"**Page {pg.number}**")
                st.text(pg.text)

# ---------------------------------------------------------------------------------------------- 2. tenderers
elif step == STEPS[1]:
    st.header("Who is being assessed")
    bids = sorted(DEMO_DIR.glob("bid_*.pdf"))
    for b in bids:
        st.markdown(f"- `{b.name}`")
    st.caption("Submissions are listed but not opened until the criteria are signed off.")

# ---------------------------------------------------------------------------------------------- 3. criteria
elif step == STEPS[2]:
    st.header("Evaluation criteria")
    st.caption("Confirm how each criterion will be applied. Nothing is read from the submissions until you sign off.")
    c = S.criteria
    r = c.record_rules[0]
    locked = S.signoff is not None
    with st.container(border=True):
        st.subheader(f"{r.id}. {r.title}")
        st.markdown("Points for each completed project that is relevant, above the value threshold, rated at or above the "
                    "minimum by its owner, and (if required) performed as prime contractor.")
        kw = st.text_input("Relevant project types (comma-separated)", ", ".join(r.keywords), disabled=locked)
        a, b, v = st.columns(3)
        y0 = a.number_input("Start year", value=r.year_min, step=1, disabled=locked)
        y1 = b.number_input("End year", value=r.year_max, step=1, disabled=locked)
        val = v.number_input("Minimum contract value ($)", value=float(r.value_min), step=500000.0, disabled=locked)
        a, b, v = st.columns(3)
        rmin = a.selectbox("Minimum owner rating", r.rating_scale, index=r.rating_scale.index(r.rating_min), disabled=locked)
        mx = b.number_input("Maximum number of projects", value=r.max_records, min_value=1, step=1, disabled=locked)
        ppp = v.number_input("Points per project", value=r.points_per_record, step=0.5, disabled=locked)
        prime = st.checkbox("Tenderer must have been prime contractor", value=r.role_required is not None, disabled=locked)
    b2 = c.band_rules[0]
    with st.container(border=True):
        st.subheader(f"{b2.id}. {b2.title}")
        a, b = st.columns(2)
        t1 = a.number_input("Full points (5) if EMR is at or below", value=float(b2.bands[0].up_to), step=0.05, disabled=locked)
        t2 = b.number_input("Partial points (3) if EMR is at or below", value=float(b2.bands[1].up_to), step=0.05, disabled=locked)
    with st.container(border=True):
        st.subheader("Compliance items")
        for item in c.compliance_items:
            st.markdown(f"- {item['id']}: {item['title']}")
    if locked:
        st.success(f"Signed off by {S.signoff['by']} on {S.signoff['at']}. Criteria are locked for this evaluation.")
    else:
        if st.button("I confirm this interpretation of the criteria", type="primary", disabled=not S.evaluator.strip()):
            r.keywords = [k.strip() for k in kw.split(",") if k.strip()]
            r.year_min, r.year_max, r.value_min, r.rating_min = int(y0), int(y1), float(val), rmin
            r.max_records, r.points_per_record = int(mx), float(ppp)
            r.role_required = "Prime contractor" if prime else None
            b2.bands = [Band(up_to=t1, points=5), Band(up_to=t2, points=3), Band(up_to=None, points=0)]
            S.signoff = {"by": S.evaluator.strip(), "at": datetime.now(timezone.utc).strftime("%d %B %Y %H:%M UTC"),
                         "criteria": c.model_dump()}
            (engagement_dir() / "criteria_signoff.json").write_text(json.dumps(S.signoff, indent=1))
            st.rerun()
        if not S.evaluator.strip():
            st.caption("Enter your name in the sidebar to sign off.")

# ---------------------------------------------------------------------------------------------- 4. evaluate
elif step == STEPS[3]:
    st.header("Evaluate submissions")
    profiles = load_profiles(ROOT / "config" / "profiles.yaml")
    allowed = st.multiselect("Where may this engagement's documents be processed?", ["self_hosted", "us_api", "eu_api"],
                             default=["self_hosted", "us_api"],
                             help="Residency policy. Evalia refuses any model outside it.")
    options = ["Form reader (no AI; documents stay on this machine)"]
    gateways = {}
    for name, prof in profiles.items():
        try:
            gw = Gateway(prof, ResidencyPolicy(allowed=allowed), engagement_dir() / "llm-cache")
            label = f"AI model: {name} ({prof.residency}, {prof.region})"
            if gw.available:
                options.append(label)
                gateways[label] = gw
            else:
                st.caption(f"{name}: not configured (set EVALIA_MODEL and {prof.api_key_env}).")
        except GatewayError as e:
            st.caption(f"{name}: refused by residency policy. {e}")
    method = st.radio("Extraction method", options)
    if st.button("Read submissions and propose findings", type="primary"):
        S.findings, S.decisions, S.docs, S.methods = [], {}, {}, set()
        for path in sorted(DEMO_DIR.glob("bid_*.pdf")):
            doc = load_pdf(path)
            S.docs[doc.doc_id] = doc
            try:
                facts = (extract_with_model(doc, gateways[method], S.criteria.compliance_items) if method in gateways
                         else read_forms(doc, S.criteria.compliance_items))
            except GatewayError as e:
                st.error(f"{doc.doc_id}: {e}")
                continue
            S.methods.add(facts.method)
            S.findings += evaluate_bid(facts, doc, S.criteria)
        S.calls = [c for g in gateways.values() for c in g.calls]
        st.success(f"{len(S.findings)} findings proposed for {len(S.docs)} submissions. Go to step 5 to review them.")
    if S.findings:
        crit = sum(f.severity == "critical" for f in S.findings)
        st.metric("Findings needing particular attention", crit)

# ---------------------------------------------------------------------------------------------- 5. review
elif step == STEPS[4]:
    st.header("Review findings")
    if not S.findings:
        st.info("Run step 4 first.")
        st.stop()
    if not S.evaluator.strip():
        st.warning("Enter your name in the sidebar; every decision is recorded against it.")
        st.stop()
    pending_info = [f for f in undecided(S.findings, S.decisions) if f.severity == "info" and f.fully_verified]
    if pending_info and st.button(f"Accept all {len(pending_info)} verified, informational findings"):
        for f in pending_info:
            S.decisions[f.id] = Decision(finding_id=f.id, action="accept", evaluator=S.evaluator,
                                         reason="Accepted in bulk: verified evidence, no issue raised")
        st.rerun()
    subjects = sorted({f.subject for f in S.findings})
    for tab, subject in zip(st.tabs(subjects), subjects):
        with tab:
            for f in [x for x in S.findings if x.subject == subject]:
                d = S.decisions.get(f.id)
                icon = {"critical": "🔴", "attention": "🟠", "info": "🟢"}[f.severity]
                done = {"accept": "accepted", "reject": "rejected", "modify": "modified"}
                status = f" — {done[d.action]} by {d.evaluator}" if d else " — awaiting decision"
                with st.expander(f"{icon} {f.title}{status}", expanded=(d is None and f.severity != "info")):
                    st.markdown(f"**Basis:** {f.basis} · **Method:** {f.method}"
                                + (f" · **Proposed points:** {f.proposed_points:g}" if f.proposed_points is not None else ""))
                    st.write(f.detail)
                    for i, e in enumerate(f.evidence):
                        st.markdown(f"{'✅' if e.verified else '❌'} **{e.doc_id}, page {e.page}:** “{e.quote}”")
                        if st.toggle("Show page", key=f"pg-{f.id}-{i}"):
                            pg = S.docs[e.doc_id].page(e.page)
                            st.markdown(highlight(pg.text if pg else "", e.quote), unsafe_allow_html=True)
                    with st.form(f"dec-{f.id}"):
                        action = st.radio("Decision", ["accept", "reject", "modify"], horizontal=True,
                                          index=["accept", "reject", "modify"].index(d.action) if d else 0)
                        reason = st.text_input("Reason (required to reject or modify)", d.reason if d else "")
                        pts = (st.number_input("Points after modification", value=float(f.proposed_points), step=0.5)
                               if f.proposed_points is not None else None)
                        note = st.text_input("Amended wording (optional)", d.modified_detail if d and d.modified_detail else "")
                        if st.form_submit_button("Record decision"):
                            try:
                                S.decisions[f.id] = Decision(finding_id=f.id, action=action, reason=reason, evaluator=S.evaluator,
                                                             modified_points=pts if action == "modify" else None,
                                                             modified_detail=note or None)
                                st.rerun()
                            except ValueError as err:
                                st.error(str(err).split("\n")[-1] if "\n" in str(err) else str(err))
    st.caption(f"{len(S.decisions)} of {len(S.findings)} findings decided.")

# ---------------------------------------------------------------------------------------------- 6. report
elif step == STEPS[5]:
    st.header("Draft evaluation")
    if not S.findings:
        st.info("Run step 4 first.")
        st.stop()
    c = S.criteria
    caps = {r.id: (r.title, r.max_points) for r in c.record_rules} | {b.id: (b.title, b.max_points) for b in c.band_rules}
    table = scores(S.findings, S.decisions, caps)
    st.subheader("Scores so far (decided findings only, computed by code)")
    st.dataframe([{"Tenderer": s, **{caps[k][0]: v for k, v in row.items()}, "Total": sum(row.values())}
                  for s, row in table.items()], hide_index=True)
    pending = undecided(S.findings, S.decisions)
    if pending:
        st.warning(f"{len(pending)} findings still need a decision before the draft can be produced.")
        st.stop()
    ack = st.checkbox("I understand that AI-assisted findings can be wrong, and I have reviewed every finding above.")
    if ack:
        inputs = [{"doc_id": d.doc_id, "sha256": d.sha256} for d in S.docs.values()]
        md = build_markdown(context=CONTEXT, signoff=S.signoff, findings=S.findings, decisions=S.decisions, caps=caps,
                            not_assessed=c.not_assessed, inputs=inputs, model_calls=S.calls, methods=S.methods)
        out = engagement_dir()
        (out / "draft_evaluation.md").write_text(md)
        log = decision_log(S.findings, S.decisions)
        (out / "decision_log.json").write_text(json.dumps(log, indent=1))
        st.download_button("Download draft evaluation (Markdown)", md, file_name="draft_evaluation.md")
        st.download_button("Download decision log (JSON)", json.dumps(log, indent=1), file_name="decision_log.json")
        st.caption(f"Also saved to {out}")
        st.markdown(md)
