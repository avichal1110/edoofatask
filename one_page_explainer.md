# Edoofa Conversation Audit — One-Page Explainer

## What the tool measures

- **Pressure / urgency language**
  - Finds sales pressure like `last seat`, `deadline`, `must enroll`, `book your seat`.
  - Why it matters: pressure can make families feel rushed and damage trust.

- **Tone consistency**
  - Flags mixed language such as empathy words alongside hard-sell phrases.
  - Why it matters: inconsistent tone weakens the counselor’s credibility.

- **Unanswered questions**
  - Detects student/family questions and checks if later counselor replies address them.
  - Why it matters: unanswered questions show weak follow-through.

- **Fee clarity**
  - Marks fee/program mentions with no numeric detail.
  - Why it matters: unclear pricing leads to confusion and distrust.

- **Student-centric focus**
  - Sees whether student/family questions get a counselor response.
  - Why it matters: good counseling prioritizes the student’s needs, not just enrollment.

- **Promises without follow-up**
  - Notes commitment phrases like `I will`, `we will`, `send the details`.
  - Why it matters: promises must be backed by a clear next step.

## How it works

1. Users upload WhatsApp-style text files.
2. `analysis.py` parses each line as `Sender: Message`.
3. `ConversationAnalysis` applies rule-based checks to every message.
4. The app generates findings, evidence, and severity scores.
5. Results are shown in Streamlit and can optionally be exported to Google Sheets.

## Audit categories

- **Tone & Empathy**: checks for supportive vs. pressure language.
- **Consistency & Follow-through**: finds unanswered questions and vague promises.
- **Clarity & Transparency**: flags unclear fee/program descriptions.
- **Student-Centric Focus**: detects whether student/family concerns are ignored.
- **Pressure & Sales Intensity**: identifies urgency and coercive wording.

## Tools and workflows

- The prototype is a **rule-based analyzer** only.
- It does not use external AI models or machine learning.
- It uses Python keyword matching and message heuristics.
- Optional Google Sheets export is supported with `gspread` and `oauth2client`.

## Key design choices

- **Rule-based simplicity**: chosen for speed, transparency, and easy customization.
- **Structured input format**: requires `Sender: Message` text for reliable parsing.
- **Actionable evidence**: each finding includes message excerpts.
- **Streamlit UI**: used for a quick demo experience, not large-scale production.
- **Optional exports**: Google Sheets support is added but not required.

## Trade-offs

- Easier to inspect, but less nuanced than NLP.
- Works best with clean transcripts.
- May produce false positives from keyword-only rules.

## Bottom line

This tool is a fast, practical first-pass audit for counselor conversations. It helps identify pressure, tone inconsistency, unclear fees, weak follow-up, and student-focused gaps.
