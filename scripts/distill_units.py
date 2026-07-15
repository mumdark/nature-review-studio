"""Extract concern units and resolution units from a segmented PRF.

Rule-based extractors: they do not call an LLM. They use surface heuristics
to label each reviewer comment paragraph with concern category hints.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any

CONCERN_KEYWORDS = {
    "sample_size": [r"\bsample size\b", r"\bpower(ed)?\b", r"\bunderpowered\b", r"\bn\s*=", r"\bN\s*=\s*\d"],
    "statistical": [r"\bp[-_ ]?value", r"\bmultiple (?:testing|comparisons|comparison)", r"\bbonferroni", r"\bfdr\b", r"\bconfidence interval"],
    "external_validation": [r"\bexternal(ly)?\s+validated?", r"\bin an? (independent|external) cohort", r"\bgeneraliz", r"\breproducib", r"\bextension\b"],
    "controls": [r"\bcontrol (?:group|condition|experiment)", r"\bcontrolling for\b", r"\b(compare|comparison)", r"\bcontrol experiments?\b", r"\b(?:negative|positive)\s+control"],
    "methods_detail": [r"\b(?:method|protocol|procedures?)\b.*(?:detail|describe|specify|missing)", r"\b(?:how|please)\s+describe\b"],
    "figure_quality": [r"\bfigure\b", r"\bpanel\b", r"\baxis\b", r"\blegend\b", r"\bscale bar\b"],
    "writing": [r"\bbetter (?:explained|described|motivated|clarified)", r"\bclarif(?:y|ication)\b", r"\brephrase\b", r"\b(?:over|under)[ -]?stated\b", r"\bproof[- ]?read\b", r"\b(?:grammatical|grammar|spelling)"],
    "novelty": [r"\bnovel\b", r"\bmechanism\b", r"\binnovation\b", r"\badvance\b", r"\b\bfirst\b.*\b(?:show|demonstrate|prove)"],
    "ethics": [r"\bethic", r"\birb\b", r"\binformed consent\b", r"\banimal care\b"],
    "data_availability": [r"\bdata availab", r"\braw data", r"\bdeposit", r"\baccession", r"\bsupplement"],
    "machinery": [r"\bspecificity\b", r"\bsensitivity\b", r"\baspecificit", r"\bisoform\b"],
    "clinical": [r"\bclinical\b", r"\bcohort\b", r"\bpatient", r"\bendpoint\b"],
    "long_term_or_followup": [r"\blong[- ]term", r"\bfollow[- ]up", r"\bdurability\b"],
    "comparator": [r"\bvs\.?\b", r"\bcompare with\b", r"\bhead-to-head\b"],
    "limitation": [r"\blimitations?\b", r"\bcaveat\b", r"\bcaveats\b"],
    "interpretation": [r"\bconclude?\b", r"\bclaim\b", r"\bspeculat", r"\boverinterpret", r"\binflated\b"],
}

REBUTTAL_KEYWORDS = {
    "added_analysis": [r"\bwe (?:have )?(?:now )?(?:performed|conducted|carried out|added|analy[sz]ed|re-?analy[sz]ed)\b"],
    "added_experiment": [r"\bwe (?:have )?(?:now )?(?:performed|conducted|carried out|added)\b.*\bexperiment", r"\bwe have added a (?:new )?(?:experiment|figure|panel)"],
    "added_figure": [r"\b(?:new|added|updated) (?:figure|supplementary figure|panel|table|supplementary table)\b", r"\b(?:now )?show in (?:figure|fig\.)"],
    "text_revision": [r"\bwe have (?:revised|reworded|modified|updated|clarified|rephrased|restructured|expanded)\b"],
    "added_reference": [r"\bwe have added (?:a )?(?:reference|citation|new (?:reference|citation))\b", r"\bciting\b", r"\bPMID\b"],
    "moderate_claim": [r"\bwe have (?:revised|modified|softened|tempered)\b.*\b(?:claim|conclusion|assertion)\b", r"\bwe agree\b.*\b(?:over|under)\b.*\binterpret", r"\bwe have moderated"],
    "disagree": [r"\bwe respectfully (?:disagree|do not agree|maintain|believe)\b", r"\bwe (?:do not )?(?:think|believe|consider|feel)\b.*\b(?:necessary|appropriate|required|critical)\b"],
    "feasibility_question": [r"\b(?:not feasible|infeasible|beyond the scope|out of scope|outside the scope)\b"],
    "editor_judgment": [r"\b(?:respectfully )?(?:request|seek|leave|ask)\b.*\beditor(?:ial)?\b.*\b(?:judgment|adjudication|decision)"],
    "thank_reviewer": [r"\bwe (?:thank|appreciate|are grateful)\b"],
    "data_or_code_provided": [r"\bdata are (?:now )?(?:available|deposited|public)", r"\bcode is available", r"\bwe provide (?:the )?(?:code|data|scripts?)\b"],
    "undertook_revision": [r"\bplace of change\b", r"\btrack[- ]change\b", r"\bmanuscript page\b", r"\b(?:manuscript|methods|results) page"],
}

def label_concern(text: str) -> List[str]:
    """Return list of concern keyword hits (dedup, sorted by name)."""
    if not text:
        return []
    hits = set()
    for cat, patterns in CONCERN_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                hits.add(cat)
                break
    return sorted(hits)

def label_rebuttal(text: str) -> List[str]:
    if not text:
        return []
    hits = set()
    for cat, patterns in REBUTTAL_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                hits.add(cat)
                break
    return sorted(hits)

def split_reviewer_comment_into_subs(text: str, referee: str) -> List[Dict[str, Any]]:
    """Within a single Referee report, split into atomic sub-comments.

    Heuristic: use numbered or lettered headings "1.", "Q1.", "(a)", "A.", etc.
    Fall back to newline-blank-line chunks.
    """
    if not text:
        return []
    # Common patterns: "1. xxx", "Q1 xxx", "A. xxx", "(a) xxx", "Major: xxx"
    pattern = re.compile(
        r"^\s*(?:(?:\d{1,2}|[A-Z])\.|\(\s*[a-z]\s*\)|Q\s*\d+|(?:Major|Minor)\b\s*[:\-]?)\s*(?=[A-Z\u4e00-\u9fff])",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    if matches:
        subs = []
        for i, m in enumerate(matches):
            label = m.group(0).strip(" :.\n")
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            if body:
                subs.append({
                    "referee": referee,
                    "sub_label": label,
                    "text": body,
                })
        return subs
    # Fallback: split by double newline
    blocks = [b.strip() for b in re.split(r"\n\s*\n+", text) if b.strip()]
    if not blocks:
        return [{"referee": referee, "sub_label": "GENERAL", "text": text.strip()}]
    return [
        {"referee": referee, "sub_label": f"PARA_{i+1}", "text": b}
        for i, b in enumerate(blocks) if len(b) >= 30
    ]

def distill_case(case_id: str, pdf_path: str, segmented: Dict[str, Any]) -> Dict[str, Any]:
    """Convert segmented output into a structured Case."""
    case = {
        "case_id": case_id,
        "source_pdf": pdf_path,
        "corresponding": segmented.get("corresponding", ""),
        "open_access": segmented.get("open_access_present", False),
        "review_rounds": [],
    }
    for vb in segmented["version_blocks"]:
        round_id = f"R{vb['version']}"
        reviewer_blobs = []
        for rb in vb["reviewer_comments"]:
            subs = split_reviewer_comment_into_subs(rb["text"], rb["referee"])
            reviewer_blobs.append({
                "referee": rb["referee"],
                "sub_comments": [
                    {
                        "sub_label": s["sub_label"],
                        "text": s["text"],
                        "concern_labels": label_concern(s["text"]),
                    }
                    for s in subs
                ],
            })
        case["review_rounds"].append({
            "round_id": round_id,
            "version": vb["version"],
            "reviewer_reports": reviewer_blobs,
        })

    # Attach rebuttal as "responses" round R0 in the rebuttal section
    responses = []
    for rb in segmented["rebuttal_blocks"]:
        for i, seg in enumerate(rb["rebuttal_segments"]):
            responses.append({
                "referee": seg.get("referee") or "UNLABELED",
                "para_index": i,
                "text": seg["text"],
                "response_labels": label_rebuttal(seg["text"]),
            })
    case["author_responses"] = responses
    return case

def anonymize_case(case: Dict[str, Any], fn) -> Dict[str, Any]:
    """Apply fn (str->str) to every textual field."""
    case["corresponding"] = fn(case.get("corresponding", ""))
    for r in case["review_rounds"]:
        for blob in r["reviewer_reports"]:
            for sc in blob["sub_comments"]:
                sc["text"] = fn(sc["text"])
    for r in case.get("author_responses", []):
        r["text"] = fn(r["text"])
    return case
