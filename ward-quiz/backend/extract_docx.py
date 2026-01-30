import json
import re
from pathlib import Path
from typing import List, Dict, Optional

from docx import Document

DOCX_PATH = Path("data/Ward Conversation Jan 26.docx")
OUT_JSON_PATH = Path("data/questions.json")

QUESTION_RE = re.compile(r"^\s*(Opening Question|Question\s+\w+|Question\s+\d+)\s*[:\-]?\s*(.*)\s*$", re.IGNORECASE)
ANSWER_RE = re.compile(r"^\s*Answer\s*[:\-]?\s*(.*)\s*$", re.IGNORECASE)

def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def paragraph_text(p) -> str:
    # Preserve paragraph boundaries; strip only outer whitespace.
    return (p.text or "").strip()

def extract_qa(docx_path: Path) -> List[Dict]:
    doc = Document(str(docx_path))
    paras = [paragraph_text(p) for p in doc.paragraphs]
    # Filter empty lines but keep spacing by paragraph join later
    indexed = [(i, t) for i, t in enumerate(paras) if t and t.strip()]

    items: List[Dict] = []
    current = None
    mode = None  # "question" or "answer"

    def start_new(q_title: str, q_rest: str):
        nonlocal current, mode
        if current:
            items.append(finalize(current))
        current = {
            "id": f"q{len(items)+1:03d}",
            "title": normalize_ws(q_title),
            "question_text_paras": [],
            "answer_text_paras": [],
            # Game fields you can tune later:
            "choices": [
                "Classical orthodox: God intervenes directly; traditional doctrines as stated.",
                "Liberal/demythologizing: mostly symbolic language; ethics-first; minimal metaphysics.",
                "Ward-like metaphysical theism/idealist: ultimate reality is Mind/Spirit; nuanced, not crude supernaturalism.",
                "Materialist/skeptical: only matter exists; religion is human projection.",
                "Non-theistic spiritual: ultimate reality is impersonal; 'God' language is too anthropomorphic."
            ],
            "correct_choice": "C",     # default; edit later per question
            "hint_wrong": "Not quite right—Ward typically takes a nuanced metaphysical position rather than a purely literalist or purely reductionist one.",
            "explanation_right": "Yes—this aligns with Ward's characteristic approach in this answer."
        }
        mode = "question"
        if q_rest:
            current["question_text_paras"].append(q_rest.strip())

    def finalize(item: Dict) -> Dict:
        # Join paras into readable blocks
        q = "\n\n".join([p.strip() for p in item["question_text_paras"] if p.strip()]).strip()
        a = "\n\n".join([p.strip() for p in item["answer_text_paras"] if p.strip()]).strip()
        item["question_text"] = q
        item["answer_text"] = a
        # remove internal lists
        item.pop("question_text_paras", None)
        item.pop("answer_text_paras", None)
        return item

    for _, text in indexed:
        # Detect question header
        qm = QUESTION_RE.match(text)
        if qm:
            q_title = qm.group(1).strip()
            q_rest = (qm.group(2) or "").strip()
            start_new(q_title, q_rest)
            continue

        # Detect answer marker
        am = ANSWER_RE.match(text)
        if am and current:
            mode = "answer"
            rest = (am.group(1) or "").strip()
            if rest:
                current["answer_text_paras"].append(rest)
            continue

        # Content lines
        if current is None:
            # Ignore prologue text before first recognized question
            continue

        if mode == "answer":
            current["answer_text_paras"].append(text)
        else:
            current["question_text_paras"].append(text)

    if current:
        items.append(finalize(current))

    # Guardrail: if no items found, fail loudly with hint
    if not items:
        raise RuntimeError(
            "No Q/A blocks detected. The parser expects paragraphs beginning with "
            "'Opening Question' or 'Question ...' and answers beginning with 'Answer'."
        )

    return items

def main():
    if not DOCX_PATH.exists():
        raise FileNotFoundError(f"Missing DOCX at: {DOCX_PATH.resolve()}")

    items = extract_qa(DOCX_PATH)

    OUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON_PATH.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(items)} questions to {OUT_JSON_PATH}")

if __name__ == "__main__":
    main()
