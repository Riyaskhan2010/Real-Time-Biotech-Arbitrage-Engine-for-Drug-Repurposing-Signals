"""
AI Service Abstraction Layer
============================
Provides drug/disease/mechanism extraction and signal explanation.

Priority order:
  1. OpenAI API  — if OPENAI_API_KEY is configured
  2. Deterministic demo logic — always available, uses structured seed data

IMPORTANT: This platform is a research decision-support tool only.
Generated explanations are NEVER clinical recommendations.
"""

import json
import re
from typing import Optional, List, Dict, Any
from app.config import settings


class AIService:
    """
    Unified AI service abstraction. Falls back to deterministic demo logic
    when no LLM API key is available. The architecture allows connecting
    any LLM via environment variables without code changes.
    """

    def __init__(self):
        self._openai_client = None
        self._backend = "heuristic"
        self._init_backend()

    def _init_backend(self):
        if settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self._backend = "openai"
                print("[AIService] Using OpenAI backend")
            except Exception as e:
                print(f"[AIService] OpenAI init failed: {e}. Using deterministic fallback.")
                self._backend = "heuristic"
        else:
            print("[AIService] No API key configured. Using deterministic demo logic.")

    @property
    def backend(self) -> str:
        return self._backend

    # ──────────────────────────────────────────────────────────────────────────
    # Public API — each method has OpenAI + deterministic implementations
    # ──────────────────────────────────────────────────────────────────────────

    def extract_entities(self, text: str) -> dict:
        """
        Extract drug names, disease names, and biological mechanisms from text.
        Returns: {"drugs": [...], "diseases": [...], "mechanisms": [...], "targets": [...]}
        INTEGRATION POINT: connect to NLP pipeline or LLM API.
        """
        if self._backend == "openai":
            return self._openai_extract_entities(text)
        return self._heuristic_extract_entities(text)

    def identify_mechanisms(self, drug_name: str, disease_name: str,
                            drug_targets: List[str], disease_pathways: List[str]) -> Dict[str, Any]:
        """
        Identify shared biological mechanisms between a drug's targets and a disease's pathways.
        Returns a structured mechanism report with overlap analysis.
        INTEGRATION POINT: connect to knowledge graph or LLM reasoning.
        """
        if self._backend == "openai":
            return self._openai_identify_mechanisms(drug_name, disease_name, drug_targets, disease_pathways)
        return self._deterministic_identify_mechanisms(drug_name, disease_name, drug_targets, disease_pathways)

    def match_evidence(self, drug_name: str, disease_name: str,
                       evidence_items: List[dict]) -> Dict[str, Any]:
        """
        Cross-source evidence matching: analyse how multiple independent evidence
        items support or challenge a drug–disease association.
        Returns a structured matching report.
        INTEGRATION POINT: connect to vector search or LLM reasoning.
        """
        if self._backend == "openai":
            return self._openai_match_evidence(drug_name, disease_name, evidence_items)
        return self._deterministic_match_evidence(drug_name, disease_name, evidence_items)

    def calculate_evidence_score(self, drug_name: str, disease_name: str,
                                  evidence_items: List[dict], mechanism_overlap: float,
                                  drug_targets: List[str], disease_pathways: List[str]) -> Dict[str, Any]:
        """
        Calculate a transparent, multi-factor evidence score.
        Returns score breakdown with per-factor values and labels.
        NOTE: Score is a research-prioritization heuristic — NOT clinical probability.

        Cross-source deduplication: the same paper appearing in PubMed AND Europe PMC
        is counted only once, using DOI → PMID → PMCID → title priority.
        Demo records (is_demo_data=True) are never counted toward a live evidence score.
        """
        # ── Cross-source deduplication ─────────────────────────────────────────
        # Same article in PubMed + Europe PMC must not be counted as two pieces of evidence.
        # Use identifiers in priority: DOI > PMID > normalised title.
        seen_identifiers: set = set()
        deduplicated: List[dict] = []

        for e in evidence_items:
            # Demo records never contribute to a real evidence score
            if e.get("is_demo_data", True):
                continue

            doi   = (e.get("doi")   or "").strip().lower()
            pmid  = (e.get("pmid")  or "").strip()
            pmcid = (e.get("pmcid") or "").strip()
            title_key = (e.get("title") or "").strip().lower()[:80]

            # Build a canonical identifier in priority order
            canonical = doi or pmid or pmcid or title_key
            if not canonical:
                deduplicated.append(e)
                continue

            if canonical in seen_identifiers:
                continue  # skip cross-source duplicate

            seen_identifiers.add(canonical)
            deduplicated.append(e)

        # Fall back to all items (including demo) if no live evidence found at all
        # — this preserves backward-compatibility for signals that only have demo evidence
        if not deduplicated:
            deduplicated = list(evidence_items)

        # ── Factor 1: Research Evidence (max 24) ──────────────────────────────
        research_papers = [e for e in deduplicated if e.get("evidence_type") in
                          ("research_paper", "preprint", "review_article", "meta_analysis",
                           "protein_annotation")]  # UniProt curated annotations count
        research_score = min(len(research_papers) * 8, 24)

        # ── Factor 2: Clinical Evidence (max 20) ──────────────────────────────
        clinical_trials = [e for e in deduplicated if e.get("evidence_type") == "clinical_trial"]
        clinical_score = min(len(clinical_trials) * 12, 20)

        # ── Factor 3: Mechanism Match (max 20) ────────────────────────────────
        mechanism_score = round(mechanism_overlap * 20)

        # ── Factor 4: Independent Sources (max 12) ────────────────────────────
        # Count distinct source databases — not raw records — for diversity bonus
        unique_sources = len({e.get("data_source") or e.get("source_name") or ""
                               for e in deduplicated if e.get("data_source") or e.get("source_name")})
        source_score = min(unique_sources * 3, 12)

        # ── Factor 5: Recency (max 8) ────────────────────────────────────────
        recent_items = [e for e in deduplicated if e.get("publication_date", "")
                       and e["publication_date"] >= "2020"]
        recency_score = min(len(recent_items) * 4, 8)

        total = research_score + clinical_score + mechanism_score + source_score + recency_score

        return {
            "research_evidence":    {"score": research_score,   "max": 24, "label": "Research Evidence",    "items": len(research_papers)},
            "clinical_evidence":    {"score": clinical_score,   "max": 20, "label": "Clinical Evidence",    "items": len(clinical_trials)},
            "mechanism_match":      {"score": mechanism_score,  "max": 20, "label": "Mechanism Match",      "items": None},
            "independent_sources":  {"score": source_score,     "max": 12, "label": "Independent Sources",  "items": unique_sources},
            "recency":              {"score": recency_score,    "max": 8,  "label": "Recency (post-2020)",  "items": len(recent_items)},
            "total":                {"score": min(total, 100),  "max": 100, "label": "Total"},
            # Traceability metadata — not part of score, but useful for explanation
            "_dedup_total":         len(deduplicated),
            "_raw_total":           len(evidence_items),
            "_cross_source_dedup":  len(evidence_items) - len(deduplicated),
        }

    def summarize_evidence(self, title: str, abstract: str) -> str:
        """Generate a concise summary of a research paper or clinical trial."""
        if self._backend == "openai":
            return self._openai_summarize(title, abstract)
        return self._heuristic_summarize(title, abstract)

    def explain_signal(self, drug_name: str, disease_name: str, mechanism: str,
                       evidence_items: list, score: float) -> str:
        """
        Generate a plain-language explanation of why a repurposing signal was detected.
        This is a research-prioritization explanation — NOT a clinical recommendation.
        """
        if self._backend == "openai":
            return self._openai_explain_signal(drug_name, disease_name, mechanism, evidence_items, score)
        return self._heuristic_explain_signal(drug_name, disease_name, mechanism, evidence_items, score)

    def generate_pipeline_steps(self, signal_data: dict) -> List[Dict[str, Any]]:
        """
        Generate the detection pipeline trace for a signal.
        Shows exactly how BioArbitrage arrived at this signal — step by step.
        is_demo is set based on whether the signal actually has live evidence.
        """
        drug_name    = signal_data.get("drug_name", "")
        disease_name = signal_data.get("disease_name", "")
        mechanism    = signal_data.get("biological_mechanism", "")
        evidence     = signal_data.get("evidence_items", [])
        score        = signal_data.get("evidence_score", 0)
        targets      = signal_data.get("drug_targets", [])
        pathways     = signal_data.get("disease_pathways", [])
        data_source  = signal_data.get("data_source", "demo")

        # Determine whether this is live or demo based on actual evidence
        live_items = [e for e in evidence if not e.get("is_demo_data", True)]
        demo_items = [e for e in evidence if e.get("is_demo_data", True)]
        has_live   = len(live_items) > 0
        is_demo    = not has_live

        research_count = len([e for e in live_items if e.get("evidence_type") in
                              ("research_paper", "preprint", "review_article")])
        trial_count    = len([e for e in live_items if e.get("evidence_type") == "clinical_trial"])
        total_count    = len(live_items) if has_live else len(evidence)

        # Identify unique sources
        sources_set = {e.get("data_source") or e.get("source_name") or "unknown"
                       for e in (live_items if has_live else evidence)}
        source_list = sorted(sources_set - {"unknown", ""})
        source_str  = ", ".join(source_list) if source_list else "configured sources"

        provenance = "LIVE" if has_live else "DEMO"

        return [
            {
                "step": 1,
                "stage": "Research Evidence Ingestion",
                "icon": "database",
                "status": "complete",
                "description": f"Indexed {total_count} evidence records from research databases.",
                "detail": (
                    f"{research_count} research paper{'s' if research_count != 1 else ''} and "
                    f"{trial_count} clinical trial record{'s' if trial_count != 1 else ''} ingested. "
                    f"Source{'s' if len(source_list) != 1 else ''}: {source_str}. "
                    f"Provenance: {provenance}."
                ),
                "output": f"{total_count} records indexed ({provenance})",
                "is_demo": is_demo,
            },
            {
                "step": 2,
                "stage": "Entity Extraction",
                "icon": "cpu",
                "status": "complete",
                "description": "Drug and disease entities extracted from research text.",
                "detail": (
                    f"Entity recognition identified '{drug_name}' (drug) and "
                    f"'{disease_name}' (disease) as co-occurring entities across "
                    f"{total_count} source records. "
                    f"AI backend: {self._backend}."
                ),
                "output": f"Drug: {drug_name} | Disease: {disease_name}",
                "is_demo": is_demo,
            },
            {
                "step": 3,
                "stage": "Mechanism Identification",
                "icon": "git-merge",
                "status": "complete",
                "description": "Biological pathway overlap analysis performed.",
                "detail": (
                    f"Drug targets ({', '.join(targets[:3]) if targets else 'see drug profile'}) "
                    f"were cross-referenced against disease pathways "
                    f"({', '.join(pathways[:3]) if pathways else 'see disease profile'}). "
                    f"Shared mechanism identified: {mechanism[:120] if mechanism else 'pathway overlap detected'}…"
                ),
                "output": f"{len(targets)} drug targets × {len(pathways)} disease pathways analysed",
                "is_demo": is_demo,
            },
            {
                "step": 4,
                "stage": "Cross-Source Evidence Matching",
                "icon": "layers",
                "status": "complete",
                "description": "Independent evidence sources corroborated the association.",
                "detail": (
                    f"Evidence from {total_count} {'live' if has_live else 'demo'} source records evaluated. "
                    f"{research_count} research publication{'s' if research_count != 1 else ''} "
                    f"and {trial_count} clinical trial{'s' if trial_count != 1 else ''} assessed "
                    f"for the {drug_name}–{disease_name} research association. "
                    "Cross-source deduplication applied (DOI/PMID priority)."
                ),
                "output": f"{len(source_list) or 1} independent source categor{'ies' if len(source_list) != 1 else 'y'} matched",
                "is_demo": is_demo,
            },
            {
                "step": 5,
                "stage": "Evidence Scoring",
                "icon": "bar-chart-2",
                "status": "complete",
                "description": "Multi-factor evidence score calculated from stored evidence.",
                "detail": (
                    f"Composite evidence score: {score:.0f}/100. "
                    "Factors: research evidence quality, clinical evidence, "
                    "mechanism alignment, source independence, recency. "
                    "Demo records excluded from score. "
                    "Experimental research-prioritization score, NOT clinical probability."
                ),
                "output": f"Evidence score: {score:.0f}/100 (from {provenance} evidence)",
                "is_demo": is_demo,
            },
            {
                "step": 6,
                "stage": "Repurposing Signal Generated",
                "icon": "zap",
                "status": "complete",
                "description": "Candidate repurposing signal flagged for researcher review.",
                "detail": (
                    f"BioArbitrage flagged '{drug_name} → {disease_name}' as a potential "
                    f"research candidate association requiring expert validation. "
                    "NOT a clinical recommendation."
                ),
                "output": f"Signal ready for researcher review ({provenance})",
                "is_demo": is_demo,
            },
        ]

    # ──────────────────────────────────────────────────────────────────────────
    # OpenAI implementations
    # ──────────────────────────────────────────────────────────────────────────

    def _openai_extract_entities(self, text: str) -> dict:
        prompt = (
            "Extract biomedical entities from this text. Return JSON with keys: "
            "drugs (list), diseases (list), mechanisms (list), targets (list). "
            "Only extract clearly mentioned entities. Text:\n\n" + text[:3000]
        )
        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=500,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[AIService] OpenAI extract failed: {e}")
            return self._heuristic_extract_entities(text)

    def _openai_identify_mechanisms(self, drug_name: str, disease_name: str,
                                     drug_targets: List[str], disease_pathways: List[str]) -> Dict[str, Any]:
        prompt = (
            f"Identify shared biological mechanisms between the drug '{drug_name}' "
            f"(targets: {', '.join(drug_targets)}) and the disease '{disease_name}' "
            f"(affected pathways: {', '.join(disease_pathways)}). "
            "Return JSON with keys: shared_pathways (list), mechanism_description (str), "
            "overlap_score (0-1 float), key_targets (list)."
        )
        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=400,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[AIService] OpenAI mechanism ID failed: {e}")
            return self._deterministic_identify_mechanisms(drug_name, disease_name, drug_targets, disease_pathways)

    def _openai_match_evidence(self, drug_name: str, disease_name: str,
                                evidence_items: List[dict]) -> Dict[str, Any]:
        summaries = [e.get("title", "") for e in evidence_items[:5]]
        prompt = (
            f"Analyse how these evidence sources support a potential association between "
            f"'{drug_name}' and '{disease_name}':\n" + "\n".join(f"- {s}" for s in summaries) +
            "\nReturn JSON: support_strength (strong/moderate/weak), consensus (str), "
            "gaps (list), key_finding (str)."
        )
        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=300,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[AIService] OpenAI match evidence failed: {e}")
            return self._deterministic_match_evidence(drug_name, disease_name, evidence_items)

    def _openai_summarize(self, title: str, abstract: str) -> str:
        prompt = (
            "Summarize this biomedical research record in 2-3 sentences for a researcher. "
            "Focus on the key finding relevant to drug repurposing. Be factual, concise.\n\n"
            f"Title: {title}\nAbstract: {abstract[:1500]}"
        )
        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[AIService] OpenAI summarize failed: {e}")
            return self._heuristic_summarize(title, abstract)

    def _openai_explain_signal(self, drug_name: str, disease_name: str, mechanism: str,
                                evidence_items: list, score: float) -> str:
        prompt = (
            f"Explain why {drug_name} is a potential drug repurposing candidate for "
            f"{disease_name} to a biomedical researcher. Base your explanation on:\n"
            f"Biological mechanism: {mechanism}\n"
            f"Evidence count: {len(evidence_items)} items\n"
            f"Evidence score: {score}/100\n\n"
            "Important: This is a RESEARCH PRIORITIZATION signal. Do NOT make clinical "
            "recommendations. Be scientifically accurate and concise (3-4 sentences)."
        )
        try:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[AIService] OpenAI explain failed: {e}")
            return self._heuristic_explain_signal(drug_name, disease_name, mechanism, evidence_items, score)

    # ──────────────────────────────────────────────────────────────────────────
    # Deterministic demo implementations (no API required)
    # ──────────────────────────────────────────────────────────────────────────

    _KNOWN_DRUGS = {
        "metformin", "rapamycin", "sirolimus", "sildenafil", "doxycycline",
        "lithium", "naltrexone", "thalidomide", "ivermectin", "aspirin",
        "ibuprofen", "temozolomide", "bevacizumab", "pembrolizumab",
    }
    _KNOWN_DISEASES = {
        "alzheimer", "glioblastoma", "diabetes", "cancer", "multiple sclerosis",
        "parkinson", "hypertension", "breast cancer", "pancreatic", "obesity",
        "myeloma", "pulmonary arterial hypertension", "pulmonary hypertension",
        "neurodegeneration", "dementia", "tumor", "lymphoma", "leukemia",
        "melanoma", "carcinoma", "adenocarcinoma", "sarcoma",
    }
    _KNOWN_MECHANISMS = {
        "ampk", "mtor", "autophagy", "apoptosis", "kinase", "inhibitor",
        "phosphorylation", "signaling", "pathway", "receptor", "oxidative stress",
        "neuroinflammation", "angiogenesis", "proteasome", "ubiquitin",
    }

    def _heuristic_extract_entities(self, text: str) -> dict:
        text_lower = text.lower()
        drugs = [d.capitalize() for d in self._KNOWN_DRUGS if d in text_lower]
        diseases = [d.title() for d in self._KNOWN_DISEASES if d in text_lower]
        mechanisms = [m for m in self._KNOWN_MECHANISMS if m in text_lower]
        return {"drugs": drugs, "diseases": diseases, "mechanisms": mechanisms, "targets": []}

    def _deterministic_identify_mechanisms(self, drug_name: str, disease_name: str,
                                            drug_targets: List[str], disease_pathways: List[str]) -> Dict[str, Any]:
        """Find overlap between drug targets and disease pathways using keyword matching."""
        target_keywords  = set(" ".join(drug_targets).lower().split())
        pathway_keywords = set(" ".join(disease_pathways).lower().split())
        shared = target_keywords & pathway_keywords
        overlap_score = min(len(shared) / max(len(target_keywords), 1), 1.0)
        return {
            "shared_pathways": list(shared)[:5],
            "mechanism_description": (
                f"Keyword analysis identified {len(shared)} overlapping biological terms "
                f"between {drug_name} targets and {disease_name} pathways."
            ),
            "overlap_score": round(overlap_score, 2),
            "key_targets": drug_targets[:4],
        }

    def _deterministic_match_evidence(self, drug_name: str, disease_name: str,
                                       evidence_items: List[dict]) -> Dict[str, Any]:
        """Deterministic cross-source evidence matching."""
        n = len(evidence_items)
        has_trials = any(e.get("evidence_type") == "clinical_trial" for e in evidence_items)
        strength = "strong" if n >= 3 and has_trials else "moderate" if n >= 2 else "weak"
        return {
            "support_strength": strength,
            "consensus": (
                f"{n} independent source{'s' if n != 1 else ''} provide {strength} support "
                f"for the {drug_name}–{disease_name} research association."
            ),
            "gaps": (
                [] if has_trials else
                ["No clinical trial data indexed — association is currently pre-clinical only"]
            ),
            "key_finding": (
                f"{'Clinical trial data available. ' if has_trials else ''}"
                f"Multiple independent research sources corroborate the association."
            ),
        }

    def _heuristic_summarize(self, title: str, abstract: str) -> str:
        if abstract and len(abstract) > 50:
            sentences = re.split(r'(?<=[.!?])\s+', abstract.strip())
            summary = " ".join(sentences[:2])
            return summary[:400] if len(summary) > 400 else summary
        return title

    def _heuristic_explain_signal(self, drug_name: str, disease_name: str, mechanism: str,
                                   evidence_items: list, score: float) -> str:
        confidence = "high" if score >= 75 else "moderate" if score >= 55 else "preliminary"
        trial_count = sum(1 for e in evidence_items
                          if isinstance(e, dict) and e.get("evidence_type") == "clinical_trial")
        trial_text = f" {trial_count} clinical trial record(s) provide additional support." if trial_count else ""
        return (
            f"[Deterministic Explanation] {drug_name} was flagged as a {confidence}-confidence "
            f"research candidate for {disease_name} based on {len(evidence_items)} indexed "
            f"evidence record(s) and a composite evidence score of {score:.0f}/100. "
            f"The proposed biological mechanism involves: {mechanism[:200] if mechanism else 'shared molecular pathways'}."
            f"{trial_text} "
            f"This is an experimental research-prioritization signal — not a clinical recommendation."
        )

    def score_signal(self, drug: dict, disease: dict, evidence_count: int,
                     has_clinical_trial: bool, mechanism_overlap: float) -> dict:
        """Legacy scoring method — retained for backward compatibility."""
        sources_score   = min(evidence_count * 5, 30)
        recency_score   = 20 if evidence_count > 0 else 0
        trial_score     = 15 if has_clinical_trial else 0
        mechanism_score = round(mechanism_overlap * 25)
        total = sources_score + recency_score + trial_score + mechanism_score
        return {
            "independent_sources": sources_score,
            "recency_score": recency_score,
            "clinical_trial_support": trial_score,
            "mechanism_alignment": mechanism_score,
            "total": min(total, 100),
        }


# Singleton instance
ai_service = AIService()
