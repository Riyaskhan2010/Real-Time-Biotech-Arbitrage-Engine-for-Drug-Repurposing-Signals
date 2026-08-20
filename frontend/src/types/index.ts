// ── Auth ──────────────────────────────────────────────────────────────────────

export interface User {
  id: number
  email: string
  username: string
  full_name: string | null
  role: string
  institution: string | null
  is_active: boolean
}

export interface AuthToken {
  access_token: string
  token_type: string
  user: User
}

// ── Drug ──────────────────────────────────────────────────────────────────────

export interface Drug {
  id: number
  name: string
  generic_name: string | null
  drug_class: string | null
  mechanism_of_action: string | null
  approved_indications: string[]
  molecular_targets: string[]
  pathways: string[]
  fda_status: string | null
  approval_year: number | null
  description: string | null
  pubchem_cid: string | null
  chembl_id: string | null
  atc_code: string | null
  created_at: string | null
  signal_count: number
}

// ── Disease ───────────────────────────────────────────────────────────────────

export interface Disease {
  id: number
  name: string
  icd10_code: string | null
  category: string | null
  description: string | null
  affected_pathways: string[]
  molecular_markers: string[]
  current_treatments: string[]
  unmet_needs: string | null
  prevalence: string | null
  mondo_id: string | null
  mesh_id: string | null
  created_at: string | null
  signal_count: number
}

// ── Evidence ──────────────────────────────────────────────────────────────────

export interface Evidence {
  id: number
  signal_id: number
  evidence_type: string
  title: string
  authors: string[]
  abstract: string | null
  summary: string | null
  publication_date: string | null
  journal: string | null
  source_name: string | null
  source_url: string | null
  doi: string | null
  pmid: string | null
  pmcid: string | null
  nct_id: string | null
  relevance_score: number
  relevance_explanation: string | null
  supports_mechanism: boolean
  is_demo_data: boolean
  data_source: string
  // Explorer extras
  drug_name?: string | null
  disease_name?: string | null
  signal_title?: string | null
}

// ── Signal ────────────────────────────────────────────────────────────────────

export interface ExplanationFactor {
  factor: string
  detail: string
  strength: 'strong' | 'moderate' | 'weak' | 'negative' | 'supportive' | 'complex'
}

export interface ScoreBreakdown {
  independent_sources: number
  recency_score: number
  clinical_trial_support: number
  mechanism_alignment: number
  total: number
}

export interface SignalListItem {
  id: number
  title: string
  drug_id: number
  disease_id: number
  evidence_score: number
  confidence_level: 'high' | 'medium' | 'low'
  source_count: number
  status: string
  is_novel: boolean
  detected_at: string | null
  drug_name: string | null
  disease_name: string | null
  biological_mechanism: string | null
  // Source traceability — populated from stored evidence
  unique_evidence_count?: number | null
  live_evidence_count?: number | null
  source_names?: string[] | null
}

export interface Signal extends SignalListItem {
  summary: string | null
  biological_mechanism: string | null
  score_breakdown: ScoreBreakdown | null
  ai_explanation: string | null
  explanation_factors: ExplanationFactor[]
  data_source: string
  drug: Drug | null
  disease: Disease | null
  evidence_items: Evidence[]
}

// ── Alert ─────────────────────────────────────────────────────────────────────

export interface Alert {
  id: number
  alert_type: string
  entity_type: string
  entity_id: number
  entity_name: string
  title: string
  message: string | null
  is_read: boolean
  is_dismissed: boolean
  created_at: string | null
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export interface DashboardStats {
  total_research_sources: number
  drugs_monitored: number
  diseases_tracked: number
  total_signals: number
  high_confidence_signals: number
  recent_updates: number
}

export interface SignalTrendPoint {
  date: string
  total: number
  high_confidence: number
}

export interface DashboardData {
  stats: DashboardStats
  signal_trend: SignalTrendPoint[]
  recent_signals: SignalListItem[]
  high_confidence_signals: SignalListItem[]
}

// ── Signal Explanation ────────────────────────────────────────────────────────

export interface SignalExplanation {
  signal_id: number
  drug_name: string | null
  disease_name: string | null
  explanation: string
  explanation_factors: ExplanationFactor[]
  score_breakdown: ScoreBreakdown
  ai_backend: string
  disclaimer: string
}

// ── Pipeline ──────────────────────────────────────────────────────────────────

export interface PipelineStep {
  step: number
  stage: string
  icon: string
  status: 'complete' | 'in_progress' | 'pending'
  description: string
  detail: string
  output: string
  is_demo: boolean
}

export interface EnrichedScoreFactor {
  score: number
  max: number
  label: string
  items: number | null
}

export interface EnrichedScoreBreakdown {
  research_evidence:   EnrichedScoreFactor
  clinical_evidence:   EnrichedScoreFactor
  mechanism_match:     EnrichedScoreFactor
  independent_sources: EnrichedScoreFactor
  recency:             EnrichedScoreFactor
  total:               EnrichedScoreFactor
}

export interface DetectionRationale {
  how_detected: string
  mechanism_summary: string
  pathway_overlap: string[]
  shared_targets: string[]
  evidence_types_found: string[]
  key_evidence_titles: string[]
  research_gaps: string[]
  validation_required: boolean
  clinical_readiness: string
}

export interface GraphNode {
  label: string
  type: 'drug' | 'target' | 'pathway' | 'disease' | 'evidence'
  approved_for?: string
  action?: string
  disease_relevance?: string
  strength?: string
  affected_by?: string
}

export interface RelationshipGraph {
  drug_node:     GraphNode
  target_nodes:  GraphNode[]
  pathway_nodes: GraphNode[]
  disease_node:  GraphNode
  evidence_nodes:GraphNode[]
}

export interface EvidenceMatching {
  support_strength: 'strong' | 'moderate' | 'weak'
  consensus: string
  gaps: string[]
  key_finding: string
}

export interface PipelineEvidenceItem {
  evidence_type: string
  title: string
  publication_date: string
  source_name: string | null
  source_url: string | null
  doi: string | null
  pmid: string | null
  nct_id: string | null
  supports_mechanism: boolean
  relevance_score: number
  relevance_explanation: string | null
  is_demo_data: boolean
}

export interface SignalPipelineData {
  signal_id: number
  drug_name: string
  disease_name: string
  evidence_score: number
  confidence_level: string
  pipeline_steps: PipelineStep[]
  enriched_score_breakdown: EnrichedScoreBreakdown
  detection_rationale: DetectionRationale
  relationship_graph: RelationshipGraph
  evidence_matching: EvidenceMatching
  evidence_items: PipelineEvidenceItem[]
  ai_backend: string
  disclaimer: string
  is_demo_data: boolean
}

// ── Research Monitor ──────────────────────────────────────────────────────────

export interface ResearchMonitorRecord {
  id: string
  title: string
  source: string
  source_type: string
  ingested_at: string
  pipeline_stage: string
  pipeline_status: string
  extracted_entities: {
    drugs: string[]
    diseases: string[]
    mechanisms: string[]
    targets: string[]
  }
  matched_signals: Array<{ drug: string; disease: string; score_delta: number }>
  evaluation_result: string
  is_demo_data: boolean
}

export interface PipelineStageInfo {
  stage: string
  label: string
  description: string
}

export interface ResearchMonitorData {
  pipeline_stages: PipelineStageInfo[]
  recent_records: ResearchMonitorRecord[]
  total_records: number
  disclaimer: string
  integration_points: Array<{ source: string; status: string; api: string }>
}

// ── Ingestion ──────────────────────────────────────────────────────────────────

export interface SourceStatusItem {
  source: string
  status: 'connected' | 'error' | 'timeout' | 'disabled' | 'loading' | 'not_configured' | 'invalid_key' | 'rate_limited'
  enabled: boolean
  error?: string | null
}

export interface SourceRunResult {
  source: string
  status: string
  records_fetched: number
  records_new: number
  records_duplicate: number
  records_matched: number
  records_novel: number
  elapsed_seconds: number
  errors: string[]
}

export interface IngestionRunStatus {
  id: number
  status: 'pending' | 'running' | 'complete' | 'partial' | 'failed'
  summary: string | null
  total_new: number
  signals_updated: number
  signals_created: number
  finished_at: string | null
}

export interface IngestionRunOut extends IngestionRunStatus {
  started_at: string | null
  source_results: SourceRunResult[]
  total_fetched: number
  total_duplicates: number
  total_errors: number
  alerts_created: number
  error: string | null
}

// ── Source Breakdown (new) ─────────────────────────────────────────────────────

export interface SourceEvidenceRecord {
  id: number
  title: string
  evidence_type: string
  authors: string[]
  publication_date: string | null
  journal: string | null
  doi: string | null
  pmid: string | null
  pmcid: string | null
  nct_id: string | null
  source_url: string | null
  relevance_score: number
  relevance_explanation: string | null
  supports_mechanism: boolean
  is_demo_data: boolean
}

export interface SourceBreakdownItem {
  count: number
  live: number
  demo: number
  records: SourceEvidenceRecord[]
}

export interface CrossSourceDuplicate {
  identifier: string
  type: 'doi' | 'pmid'
  sources: string[]
}

export interface SignalSourceBreakdown {
  signal_id: number
  drug_name: string
  disease_name: string
  evidence_score: number
  confidence_level: string
  data_source: string
  source_breakdown: Record<string, SourceBreakdownItem>
  total_evidence_records: number
  unique_evidence_records: number
  unique_live_records: number
  unique_demo_records: number
  independent_source_count: number
  has_live_evidence: boolean
  cross_source_duplicates: CrossSourceDuplicate[]
  duplicates_removed: number
  evidence_type_distribution: Record<string, number>
  score_breakdown_from_evidence: EnrichedScoreBreakdown
  score_explanation: string
  disclaimer: string
}

export interface EvidenceSourceItem {
  source: string
  count: number
}

// ── Live Evidence (new) ───────────────────────────────────────────────────────

export interface LiveEvidenceRecord {
  id: number
  source: string
  source_url: string | null
  title: string
  authors: string[]
  publication_date: string | null
  journal: string | null
  abstract: string | null
  doi: string | null
  pmid: string | null
  pmcid: string | null
  nct_id: string | null
  evidence_type: string
  is_open_access: boolean
  relevance_score: number
  relevance_explanation: string | null
  supports_mechanism: boolean
  is_demo_data: false
}

export interface LiveEvidenceResponse {
  signal_id: number
  drug_name: string
  disease_name: string
  has_live_evidence: boolean
  total_live_records: number
  per_source_counts: Record<string, number>
  per_type_counts: Record<string, number>
  sources_without_evidence: string[]
  evidence: LiveEvidenceRecord[]
  message: string
  disclaimer: string
}
