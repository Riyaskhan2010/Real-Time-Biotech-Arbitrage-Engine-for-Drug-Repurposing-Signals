from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserOut"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    institution: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


# ── Drug ──────────────────────────────────────────────────────────────────────

class DrugBase(BaseModel):
    name: str
    generic_name: Optional[str] = None
    drug_class: Optional[str] = None
    mechanism_of_action: Optional[str] = None
    approved_indications: List[str] = []
    molecular_targets: List[str] = []
    pathways: List[str] = []
    fda_status: Optional[str] = None
    approval_year: Optional[int] = None
    description: Optional[str] = None
    pubchem_cid: Optional[str] = None
    chembl_id: Optional[str] = None
    atc_code: Optional[str] = None


class DrugOut(DrugBase):
    id: int
    created_at: Optional[datetime] = None
    signal_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ── Disease ───────────────────────────────────────────────────────────────────

class DiseaseBase(BaseModel):
    name: str
    icd10_code: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    affected_pathways: List[str] = []
    molecular_markers: List[str] = []
    current_treatments: List[str] = []
    unmet_needs: Optional[str] = None
    prevalence: Optional[str] = None
    mondo_id: Optional[str] = None
    mesh_id: Optional[str] = None


class DiseaseOut(DiseaseBase):
    id: int
    created_at: Optional[datetime] = None
    signal_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ── Evidence ──────────────────────────────────────────────────────────────────

class EvidenceOut(BaseModel):
    id: int
    signal_id: int
    evidence_type: str
    title: str
    authors: List[str] = []
    abstract: Optional[str] = None
    summary: Optional[str] = None
    publication_date: Optional[str] = None
    journal: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    nct_id: Optional[str] = None
    relevance_score: float = 0.0
    relevance_explanation: Optional[str] = None
    supports_mechanism: bool = False
    is_demo_data: bool = True
    data_source: str = "demo"

    class Config:
        from_attributes = True


# ── Signal ────────────────────────────────────────────────────────────────────

class ExplanationFactor(BaseModel):
    factor: str
    detail: str
    strength: str  # strong, moderate, weak, negative, supportive, complex


class SignalOut(BaseModel):
    id: int
    drug_id: int
    disease_id: int
    title: str
    summary: Optional[str] = None
    biological_mechanism: Optional[str] = None
    evidence_score: float
    confidence_level: str
    source_count: int
    score_breakdown: Optional[dict] = None
    status: str
    is_novel: bool
    ai_explanation: Optional[str] = None
    explanation_factors: List[Any] = []
    detected_at: Optional[datetime] = None
    data_source: str = "demo"
    drug: Optional[DrugOut] = None
    disease: Optional[DiseaseOut] = None
    evidence_items: Optional[List[EvidenceOut]] = None

    class Config:
        from_attributes = True


class SignalListItem(BaseModel):
    id: int
    title: str
    drug_id: int
    disease_id: int
    evidence_score: float
    confidence_level: str
    source_count: int
    status: str
    is_novel: bool
    detected_at: Optional[datetime] = None
    drug_name: Optional[str] = None
    disease_name: Optional[str] = None
    biological_mechanism: Optional[str] = None
    # Source traceability — populated when include_sources=true
    unique_evidence_count: Optional[int] = None
    live_evidence_count: Optional[int] = None
    source_names: Optional[List[str]] = None

    class Config:
        from_attributes = True


# ── Alert ─────────────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    id: int
    alert_type: str
    entity_type: str
    entity_id: int
    entity_name: str
    title: str
    message: Optional[str] = None
    is_read: bool
    is_dismissed: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_research_sources: int
    drugs_monitored: int
    diseases_tracked: int
    total_signals: int
    high_confidence_signals: int
    recent_updates: int


class SignalTrendPoint(BaseModel):
    date: str
    total: int
    high_confidence: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    signal_trend: List[SignalTrendPoint]
    recent_signals: List[SignalListItem]
    high_confidence_signals: List[SignalListItem]


# ── Evidence Explorer ─────────────────────────────────────────────────────────

class EvidenceExplorerItem(EvidenceOut):
    drug_name: Optional[str] = None
    disease_name: Optional[str] = None
    signal_title: Optional[str] = None


# ── Ingestion ─────────────────────────────────────────────────────────────────

class SourceStatusItem(BaseModel):
    source: str
    status: str          # connected | error | timeout | disabled
    enabled: bool = True
    error: Optional[str] = None


class SourceRunResult(BaseModel):
    source: str
    status: str
    records_fetched: int = 0
    records_new: int = 0
    records_duplicate: int = 0
    records_matched: int = 0
    records_novel: int = 0
    elapsed_seconds: float = 0.0
    errors: List[str] = []


class IngestionRunOut(BaseModel):
    id: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    source_results: List[Any] = []
    total_fetched: int = 0
    total_new: int = 0
    total_duplicates: int = 0
    total_errors: int = 0
    signals_updated: int = 0
    signals_created: int = 0
    alerts_created: int = 0
    summary: Optional[str] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


class IngestionRunStatus(BaseModel):
    """Lightweight status check — used by frontend polling."""
    id: int
    status: str
    summary: Optional[str] = None
    total_new: int = 0
    signals_updated: int = 0
    signals_created: int = 0
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True
