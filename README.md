# Multimodal Field Report Generator — Capture · Export · Eval

My slice (**Person C**) of the field-report system: the **Streamlit UI**
(capture → edit → review citations), **PDF/DOCX export**, and the
**evaluation harness** that reports faithfulness + citation-coverage metrics.

The RAG core (Person A) and multimodal generation backend (Person B) plug in
behind a single contract. A deterministic mock backend ships here so the UI
and harness run **today** without their services.

## Run the UI

```bash
pip install -r requirements.txt
streamlit run src/app.py
```

Capture inputs in the sidebar (typed notes, voice transcript, OCR text),
generate a draft, edit it, review the citation/provenance panel, and export
to PDF or DOCX.

## Run the evaluation harness

```bash
python eval/harness.py
```

Outputs per-case and aggregate metrics:

| Metric | Meaning |
|--------|---------|
| `faithfulness` | lexical grounding of claims in cited source snippets |
| `citation_coverage` | fraction of sections carrying ≥1 citation |
| `keyword_recall` | expected key facts captured in the report |

`score_faithfulness` is offline/CI-friendly; swap it for an LLM-judge later
without touching the rest of the harness.

## Connect the real backend (Person B)

```bash
export FIELD_REPORT_API=http://localhost:8000   # the FastAPI service
```

Contract (lock in week 1): `POST /generate { notes, transcript, ocr_text } -> report`.

## Layout

```
src/app.py             Streamlit capture/edit/cite/export UI
src/export.py          PDF + DOCX renderers          <-- Person C
src/backend_client.py  integration seam (+ mock)
eval/harness.py        faithfulness/coverage metrics <-- Person C headline
eval/test_set.json     test inputs + expected facts
```

## CV line

> Built the capture-to-export UI + an evaluation harness reporting faithfulness
> and citation-coverage metrics over a multimodal RAG report generator.

## Person F — Workflow Automation & Safety Testing

### Workflow Automation

`run_preflight_check` in `workflows/preflight_check.py` is a multi-step
pre-flight pipeline that runs without an LLM or MCP client:

1. Validates all inputs (coordinates, altitude, waypoint shape)
2. Queries airspace constraints at every waypoint
3. Runs route feasibility analysis via `plan_route()`
4. Returns a structured go/no-go summary with status, violations,
   per-waypoint constraints, total distance, and a human-readable recommendation

Input validation is enforced by `validators/inputs.py` before any computation
is reached, keeping `compute.py` pure and untouched.

### Safety & Reliability Testing

67 deterministic tests across four files:

| File | Focus |
|------|-------|
| `tests/test_safety.py` | Core no-fly and altitude enforcement (existing) |
| `tests/test_validators.py` | Input validation — bounds, shapes, edge values |
| `tests/test_edge_cases.py` | Zone boundaries, overlapping zones, temporal TFRs, inf/NaN inputs |
| `tests/test_workflows.py` | Full workflow schema, approved/rejected paths, error handling |

### Run the demo

```bash
python demo.py
```

Runs one approved and one rejected route end-to-end and pretty-prints the
full workflow output. No LLM or MCP client required.

### Run the test suite

```bash
pytest
```

Full suite: **67 passed**.
