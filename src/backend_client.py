"""Backend client  —  the integration seam with Person B's FastAPI.

The UI calls these functions. Generation backend is chosen at call time:

  1. FIELD_REPORT_API set  -> POST to Person B's hosted FastAPI service.
  2. GEMINI_API_KEY set    -> generate in-process with Google Gemini.
                              (lets this Streamlit app run the real LLM on
                              hosts like Streamlit Community Cloud, which
                              can't run a separate FastAPI service).
  3. neither set           -> deterministic mock so the UI + eval harness
                              run with no external dependencies.

Contract (lock in week 1):
  POST /generate  { notes, transcript, ocr_text }  ->  report dict
"""
from __future__ import annotations

import json
import os
from typing import Any

import requests

API_URL = os.environ.get("FIELD_REPORT_API", "").rstrip("/")

# Override with the GEMINI_MODEL env var if this one is unavailable to your key.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

_GEMINI_SYSTEM_PROMPT = """\
You are an expert aviation field inspector generating professional site inspection reports.

Given observations from a site inspection (typed notes, voice transcript, and/or OCR text \
from photos), generate a comprehensive, regulation-grounded field report with 3-4 sections.

Guidelines:
- Title: clear, descriptive (e.g. "Runway Lighting Infrastructure Inspection Report")
- Metadata: inspector "Auto-generated", status "DRAFT"
- Sections: cover Observations, Compliance Assessment, Findings & Risk, Recommendations
- Each section body: 2-4 sentences, professional tone, specific to the observations given
- Citations: reference relevant aviation standards (e.g. CAAS-AIC.pdf, ICAO-Annex14.pdf,
  FAR-Part139.pdf, CAP168.pdf). Assign sequential IDs starting at 1.
- References array: every citation ID must have a matching entry with a realistic snippet
  (quoted regulatory text, 10-20 words)
- All citation IDs in sections must appear in the references array

Be specific to the actual content in the observations — do not generate generic filler.

You MUST respond with ONLY valid JSON in exactly this structure, no markdown, no extra text:
{
  "title": "string",
  "metadata": {"inspector": "string", "status": "string"},
  "sections": [
    {
      "heading": "string",
      "body": "string",
      "citations": [{"id": 1, "source": "string", "chunk_id": "string"}]
    }
  ],
  "references": [
    {"id": 1, "source": "string", "chunk_id": "string", "snippet": "string"}
  ]
}\
"""


def _gemini_generate(inputs: dict[str, str]) -> dict[str, Any]:
    """Generate a report in-process with Google Gemini (no separate service)."""
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(GEMINI_MODEL)

    parts = [
        f"Field Notes:\n{inputs.get('notes', '')}" if inputs.get("notes", "").strip() else "",
        f"Voice Transcript:\n{inputs.get('transcript', '')}" if inputs.get("transcript", "").strip() else "",
        f"OCR Text from Photos:\n{inputs.get('ocr_text', '')}" if inputs.get("ocr_text", "").strip() else "",
    ]
    combined = "\n\n".join(p for p in parts if p).strip()
    if not combined:
        raise ValueError("At least one input field is required.")

    prompt = (
        _GEMINI_SYSTEM_PROMPT
        + "\n\nGenerate a field inspection report based on these observations:\n\n"
        + combined
    )

    text = model.generate_content(prompt).text.strip()

    # Strip markdown code fences if Gemini wraps the JSON.
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    return json.loads(text)


def _mock_generate(inputs: dict[str, str]) -> dict[str, Any]:
    """Deterministic mock report so the UI is runnable without the backend."""
    notes = inputs.get("notes", "")
    transcript = inputs.get("transcript", "")
    ocr = inputs.get("ocr_text", "")
    combined = " ".join(x for x in [notes, transcript, ocr] if x).strip()

    return {
        "title": "Site Inspection Field Report",
        "metadata": {"inspector": "R. (auto)", "status": "DRAFT"},
        "sections": [
            {
                "heading": "Observations",
                "body": combined or "No observations captured.",
                "citations": [{"id": 1, "source": "Reg-Standard-A.pdf",
                               "chunk_id": "c12"}],
            },
            {
                "heading": "Compliance Assessment",
                "body": ("Structural elements were inspected per the quarterly "
                         "requirement. Non-conforming items must be logged "
                         "within 24 hours; the flagged item was logged for "
                         "review per clause 4.2."),
                "citations": [
                    {"id": 1, "source": "Reg-Standard-A.pdf", "chunk_id": "c12"},
                    {"id": 2, "source": "Reg-Standard-A.pdf", "chunk_id": "c08"},
                ],
            },
        ],
        "references": [
            {"id": 1, "source": "Reg-Standard-A.pdf", "chunk_id": "c12",
             "snippet": "All structural elements shall be inspected quarterly."},
            {"id": 2, "source": "Reg-Standard-A.pdf", "chunk_id": "c08",
             "snippet": "Non-conforming items must be logged within 24 hours."},
        ],
    }


def generate_report(inputs: dict[str, str]) -> dict[str, Any]:
    """Pick a backend: hosted FastAPI, in-process Gemini, or mock (in that order)."""
    if API_URL:
        resp = requests.post(f"{API_URL}/generate", json=inputs, timeout=60)
        resp.raise_for_status()
        return resp.json()
    if os.environ.get("GEMINI_API_KEY"):
        return _gemini_generate(inputs)
    return _mock_generate(inputs)
