import os
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    gspread = None


DEFAULT_FRAMEWORK = [
    {
        "name": "Tone & Empathy",
        "description": "Assesses whether the counselor maintains a respectful, human-centered tone and expresses empathy toward student or family concerns.",
        "measures": "tone shifts, empathy words, politeness decline, harsh or overly promotional language.",
        "why": "Edoofa's brand depends on counselors feeling supportive, not transactional, especially during sensitive decisions about education and finance.",
    },
    {
        "name": "Consistency & Follow-through",
        "description": "Checks if promises, next steps, or commitments are delivered consistently and if follow-up questions are answered.",
        "measures": "unanswered questions, contradicted promises, missing follow-up, date or fee mismatch.",
        "why": "Inconsistent guidance erodes trust, causes confusion, and can make families feel misled after an initial commitment.",
    },
    {
        "name": "Clarity & Transparency",
        "description": "Evaluates whether program details, fees, and payment information are communicated clearly without ambiguity.",
        "measures": "unclear fee descriptions, vague benefits, missing terms, indirect language around costs.",
        "why": "Transparent fee communication reduces future disputes and supports Edoofa's reputation for honest advisory services.",
    },
    {
        "name": "Student-Centric Focus",
        "description": "Measures whether the counselor centers the student's goals, questions, and preferences instead of pushing a single solution.",
        "measures": "student questions ignored, one-sided sales language, insufficient probe into goals, overemphasis on enrollment.",
        "why": "Counseling is effective when the student's needs are prioritized; a strong student focus is a key marker of quality service.",
    },
    {
        "name": "Pressure & Sales Intensity",
        "description": "Detects whether the conversation includes high-pressure tactics, urgency framing, or repeated insistence that may feel coercive.",
        "measures": "hard-sell phrases, repeated pushiness, false urgency, emotional triggers aimed at quick decisions.",
        "why": "Edoofa wants disciplined, ethical enrollment conversations rather than pressure-driven signups that can damage long-term trust.",
    },
]


PRESSURE_PHRASES = [
    "last seat",
    "few spots",
    "today only",
    "need to decide",
    "if you don't",
    "must enroll",
    "only available",
    "final chance",
    "deadline",
    "payment link now",
    "book your seat",
]

EMPATHY_PHRASES = [
    "I understand",
    "I know",
    "happy to help",
    "no worries",
    "totally",
    "that makes sense",
    "we can",
    "feel free",
    "here to support",
]

QUESTION_WORDS = ["what", "when", "how", "why", "which", "where", "who"]

PROMISE_PHRASES = [
    "I will",
    "we will",
    "you will",
    "I'll",
    "we'll",
    "we can",
    "will share",
    "send the details",
]

FEE_KEYWORDS = ["fee", "installment", "payment", "cost", "price", "programme", "program", "scholarship", "discount"]


class ConversationAnalysis:
    def __init__(self, framework: List[Dict[str, Any]]):
        self.framework = framework

    def analyze_conversations(self, conversations: List[Dict[str, str]]) -> Dict[str, Any]:
        records = []
        findings = []
        evidence = []

        for conversation in conversations:
            parsed = self.parse_whatsapp_text(conversation["content"], conversation["name"])
            records.extend(parsed)
            conversation_findings = self.analyze_messages(parsed, conversation["name"])
            findings.extend(conversation_findings)

        summary = self.build_summary(findings)

        return {
            "summary": summary,
            "findings": sorted(findings, key=lambda f: f["severity_score"], reverse=True),
        }

    def parse_whatsapp_text(self, text: str, source_name: str) -> List[Dict[str, Any]]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        messages = []
        current = None

        header_pattern = re.compile(r"^(?P<sender>[^:]+):\s*(?P<body>.*)$")

        for raw in lines:
            match = header_pattern.match(raw)
            if match:
                if current:
                    messages.append(current)
                sender = match.group("sender").strip()
                body = match.group("body").strip()
                current = {
                    "source": source_name,
                    "sender": sender,
                    "text": body,
                    "timestamp": None,
                    "raw": raw,
                }
            elif current:
                current["text"] += " " + raw

        if current:
            messages.append(current)

        return messages

    def analyze_messages(self, messages: List[Dict[str, Any]], conversation_name: str) -> List[Dict[str, Any]]:
        findings = []
        question_map = self.collect_questions(messages)
        promise_map = self.collect_promises(messages)
        fee_mentions = self.collect_fee_mentions(messages)
        tone_issues = self.detect_tone_shifts(messages)
        pressure_issues = self.detect_pressure(messages)
        clarity_issues = self.detect_clarity(messages)
        student_focus_issues = self.detect_student_focus(messages)
        consistency_issues = self.detect_consistency(messages, promise_map)

        findings.extend(tone_issues)
        findings.extend(pressure_issues)
        findings.extend(clarity_issues)
        findings.extend(student_focus_issues)
        findings.extend(consistency_issues)

        if question_map["unanswered"]:
            findings.append({
                "title": "Unanswered student/family questions",
                "category": "Consistency & Follow-through",
                "description": (
                    "Some questions from the student or parent were not answered, which can create confusion or leave the family feeling ignored. "
                    "The counselor should explicitly address all open queries before moving to enrollment steps."
                ),
                "evidence": question_map["unanswered"],
                "severity": "High" if len(question_map["unanswered"]) >= 2 else "Medium",
                "severity_score": 8 if len(question_map["unanswered"]) >= 2 else 6,
            })

        if fee_mentions["unclear"]:
            findings.append({
                "title": "Fee communication lacks clarity",
                "category": "Clarity & Transparency",
                "description": (
                    "The conversation includes program or fee mentions that are vague or incomplete. "
                    "Unclear pricing can lead to mistrust and later disputes after enrollment."
                ),
                "evidence": fee_mentions["evidence"],
                "severity": "Medium",
                "severity_score": 6,
            })

        # Deduplicate
        unique = { (f["title"], tuple(f["evidence"])): f for f in findings }
        return list(unique.values())

    def collect_questions(self, messages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        unanswered = []
        answered = []
        question_messages = []

        for index, msg in enumerate(messages):
            text = msg["text"].lower()
            if text.endswith("?") or any(text.startswith(q + " ") for q in QUESTION_WORDS):
                question_messages.append((index, msg["sender"], msg["text"], msg))

        for index, sender, question, msg in question_messages:
            if not any(keyword in sender.lower() for keyword in ["parent", "student", "family"]):
                continue

            answered_flag = False
            for later_msg in messages[index + 1:]:
                if "counselor" in later_msg["sender"].lower() and not later_msg["text"].strip().endswith("?"):
                    answered_flag = True
                    break

            if answered_flag:
                answered.append(question)
            else:
                unanswered.append(f"{sender}: {msg["text"]}")

        return {"unanswered": unanswered, "answered": answered}

    def collect_promises(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        promises = []
        for msg in messages:
            text = msg["text"]
            if any(phrase.lower() in text.lower() for phrase in PROMISE_PHRASES):
                promises.append(msg)
        return {"promises": promises}

    def collect_fee_mentions(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        evidence = []
        unclear = []
        for msg in messages:
            text = msg["text"].lower()
            if any(keyword in text for keyword in FEE_KEYWORDS):
                evidence.append(f"{msg['sender']}: {msg['text']}")
                if not re.search(r"\d", text):
                    unclear.append(f"{msg['sender']}: {msg['text']}")
        return {"evidence": evidence, "unclear": unclear}

    def detect_pressure(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        evidence = []
        for msg in messages:
            text = msg["text"].lower()
            if any(phrase in text for phrase in PRESSURE_PHRASES):
                evidence.append(f"{msg['sender']}: {msg['text']}")

        if evidence:
            return [
                {
                    "title": "Pressure or urgency language detected",
                    "category": "Pressure & Sales Intensity",
                    "description": (
                        "The counselor uses urgency or scarcity language that may pressure the family into a quick decision rather than allowing them to evaluate the program calmly."
                    ),
                    "evidence": evidence,
                    "severity": "High" if len(evidence) >= 2 else "Medium",
                    "severity_score": 7 if len(evidence) >= 2 else 5,
                }
            ]
        return []

    def detect_tone_shifts(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        evidence = []
        counselor_messages = [m for m in messages if "counselor" in m["sender"].lower()]
        markers = [m for m in counselor_messages if any(word in m["text"].lower() for word in ["sorry", "understand", "happy to help", "no worries"])]
        pushy = [m for m in counselor_messages if any(word in m["text"].lower() for word in ["must", "need to decide", "last seat", "book your seat"])]

        if markers and pushy:
            evidence.extend([f"{m['sender']}: {m['text']}" for m in markers + pushy])
            return [
                {
                    "title": "Tone shifts between empathetic and pressuring",
                    "category": "Tone & Empathy",
                    "description": (
                        "The conversation alternates between empathetic language and strong sales pressure, which can feel inconsistent and undermine trust."
                    ),
                    "evidence": evidence,
                    "severity": "Medium",
                    "severity_score": 6,
                }
            ]
        return []

    def detect_clarity(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        evidence = []
        for msg in messages:
            text = msg["text"].lower()
            if any(keyword in text for keyword in FEE_KEYWORDS) and not any(num in text for num in "0123456789"):
                evidence.append(f"{msg['sender']}: {msg['text']}")

        if evidence:
            return [
                {
                    "title": "Unclear fee or program details",
                    "category": "Clarity & Transparency",
                    "description": (
                        "The counselor mentions fees or program information without concrete numbers or clear terms, which can cause misaligned expectations."
                    ),
                    "evidence": evidence,
                    "severity": "Medium",
                    "severity_score": 5,
                }
            ]
        return []

    def detect_student_focus(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        evidence = []
        student_questions = [
            (index, m)
            for index, m in enumerate(messages)
            if ("student" in m["sender"].lower() or "parent" in m["sender"].lower() or "family" in m["sender"].lower())
            and m["text"].strip().endswith("?")
        ]

        for index, q in student_questions:
            later_counselor = next(
                (m for m in messages[index + 1 :] if "counselor" in m["sender"].lower()),
                None,
            )
            if later_counselor is None:
                evidence.append(f"{q['sender']}: {q['text']}")

        if evidence:
            return [
                {
                    "title": "Student questions are not addressed directly",
                    "category": "Student-Centric Focus",
                    "description": (
                        "Important questions from the student or parent appear to be ignored or only partially addressed, which can make the conversation feel one-sided."
                    ),
                    "evidence": evidence,
                    "severity": "High" if len(evidence) >= 2 else "Medium",
                    "severity_score": 7,
                }
            ]
        return []

    def detect_consistency(self, messages: List[Dict[str, Any]], promise_map: Dict[str, Any]) -> List[Dict[str, Any]]:
        evidence = []
        if promise_map["promises"]:
            for promise in promise_map["promises"]:
                evidence.append(f"{promise['sender']}: {promise['text']}")
            return [
                {
                    "title": "Promise or commitment issued without clear follow-up",
                    "category": "Consistency & Follow-through",
                    "description": (
                        "The counselor makes commitments or indicates next steps, but the conversation lacks an explicit delivery point or schedule for that follow-up."
                    ),
                    "evidence": evidence,
                    "severity": "Medium",
                    "severity_score": 6,
                }
            ]
        return []

    def build_summary(self, findings: List[Dict[str, Any]]) -> str:
        if not findings:
            return "No concerning patterns detected. The conversation appears consistent with Edoofa's quality expectations."
        categories = sorted({finding["category"] for finding in findings})
        top = sorted(findings, key=lambda f: f["severity_score"], reverse=True)[:3]
        summary_lines = [f"Detected {len(findings)} issues across categories: {', '.join(categories)}."]
        summary_lines.append("Top concerns:")
        for finding in top:
            summary_lines.append(f"- {finding['title']} ({finding['severity']})")
        return "\n".join(summary_lines)

    def push_to_google_sheet(self, report: Dict[str, Any], sheet_id: str) -> str:
        if gspread is None:
            raise RuntimeError("gspread is not installed. Install requirements with Google Sheets support.")

        credentials_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
        if not credentials_path:
            raise RuntimeError("Environment variable GOOGLE_SHEETS_CREDENTIALS is not set.")

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.sheet1

        rows = [
            [
                "Category",
                "Title",
                "Severity",
                "Evidence",
                "Description",
                "Generated At",
            ]
        ]
        now = datetime.utcnow().isoformat()
        for finding in report["findings"]:
            rows.append([
                finding["category"],
                finding["title"],
                finding["severity"],
                " | ".join(finding["evidence"]),
                finding["description"],
                now,
            ])

        worksheet.clear()
        worksheet.update(rows)
        return sheet.url
