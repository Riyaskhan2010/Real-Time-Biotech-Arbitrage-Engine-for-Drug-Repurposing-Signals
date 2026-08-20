import client from './client'
import type {
  AuthToken, DashboardData, Signal, SignalListItem,
  Drug, Disease, Evidence, Alert, SignalExplanation,
} from '../types'

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  login: async (username: string, password: string): Promise<AuthToken> => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    const { data } = await client.post<AuthToken>('/auth/token', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },
  me: async () => {
    const { data } = await client.get('/auth/me')
    return data
  },
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export const dashboardApi = {
  get: async (): Promise<DashboardData> => {
    const { data } = await client.get<DashboardData>('/dashboard')
    return data
  },
}

// ── Signals ───────────────────────────────────────────────────────────────────

export const signalsApi = {
  list: async (params?: {
    confidence?: string
    drug_id?: number
    disease_id?: number
    search?: string
    sort_by?: string
    include_demo?: boolean
    limit?: number
    offset?: number
  }): Promise<SignalListItem[]> => {
    const { data } = await client.get<SignalListItem[]>('/signals', { params })
    return data
  },

  get: async (id: number): Promise<Signal> => {
    const { data } = await client.get<Signal>(`/signals/${id}`)
    return data
  },

  explain: async (id: number): Promise<SignalExplanation> => {
    const { data } = await client.get<SignalExplanation>(`/signals/${id}/explain`)
    return data
  },
}

// ── Drugs ─────────────────────────────────────────────────────────────────────

export const drugsApi = {
  list: async (params?: { search?: string; drug_class?: string }): Promise<Drug[]> => {
    const { data } = await client.get<Drug[]>('/drugs', { params })
    return data
  },

  get: async (id: number): Promise<Drug> => {
    const { data } = await client.get<Drug>(`/drugs/${id}`)
    return data
  },

  signals: async (id: number): Promise<SignalListItem[]> => {
    const { data } = await client.get<SignalListItem[]>(`/drugs/${id}/signals`)
    return data
  },
}

// ── Diseases ──────────────────────────────────────────────────────────────────

export const diseasesApi = {
  list: async (params?: { search?: string; category?: string }): Promise<Disease[]> => {
    const { data } = await client.get<Disease[]>('/diseases', { params })
    return data
  },

  get: async (id: number): Promise<Disease> => {
    const { data } = await client.get<Disease>(`/diseases/${id}`)
    return data
  },

  signals: async (id: number): Promise<SignalListItem[]> => {
    const { data } = await client.get<SignalListItem[]>(`/diseases/${id}/signals`)
    return data
  },
}

// ── Evidence ──────────────────────────────────────────────────────────────────

export const evidenceApi = {
  list: async (params?: {
    evidence_type?: string
    data_source?: string
    is_demo?: boolean
    search?: string
    signal_id?: number
    limit?: number
    offset?: number
  }): Promise<Evidence[]> => {
    const { data } = await client.get<Evidence[]>('/evidence', { params })
    return data
  },

  get: async (id: number): Promise<Evidence> => {
    const { data } = await client.get<Evidence>(`/evidence/${id}`)
    return data
  },

  sources: async (): Promise<{ source: string; count: number }[]> => {
    const { data } = await client.get<{ source: string; count: number }[]>('/evidence/sources')
    return data
  },
}

// ── Alerts ────────────────────────────────────────────────────────────────────

export const alertsApi = {
  list: async (): Promise<Alert[]> => {
    const { data } = await client.get<Alert[]>('/alerts')
    return data
  },

  unreadCount: async (): Promise<number> => {
    const { data } = await client.get<{ unread_count: number }>('/alerts/unread-count')
    return data.unread_count
  },

  markRead: async (id: number) => client.patch(`/alerts/${id}/read`),
  dismiss: async (id: number) => client.patch(`/alerts/${id}/dismiss`),
  markAllRead: async () => client.patch('/alerts/mark-all-read'),
}

// ── Signal Pipeline (new) ─────────────────────────────────────────────────────

import type { SignalPipelineData, ResearchMonitorData } from '../types'

export const pipelineApi = {
  get: async (signalId: number): Promise<SignalPipelineData> => {
    const { data } = await client.get<SignalPipelineData>(`/signals/${signalId}/pipeline`)
    return data
  },
}

// ── Source Breakdown (new) ────────────────────────────────────────────────────

import type { SignalSourceBreakdown } from '../types'

export const sourceBreakdownApi = {
  get: async (signalId: number): Promise<SignalSourceBreakdown> => {
    const { data } = await client.get<SignalSourceBreakdown>(`/signals/${signalId}/source-breakdown`)
    return data
  },
}

// ── Live Evidence (new) ───────────────────────────────────────────────────────

import type { LiveEvidenceResponse } from '../types'

export const liveEvidenceApi = {
  get: async (
    signalId: number,
    opts?: { evidenceType?: string; source?: string },
  ): Promise<LiveEvidenceResponse> => {
    const params: Record<string, string> = {}
    if (opts?.evidenceType) params.evidence_type = opts.evidenceType
    if (opts?.source) params.source = opts.source
    const { data } = await client.get<LiveEvidenceResponse>(
      `/signals/${signalId}/live-evidence`,
      { params },
    )
    return data
  },
}

// ── Research Monitor (new) ────────────────────────────────────────────────────

export const researchMonitorApi = {
  get: async (): Promise<ResearchMonitorData> => {
    const { data } = await client.get<ResearchMonitorData>('/research-monitor')
    return data
  },
}

// ── Ingestion (new) ───────────────────────────────────────────────────────────

import type { IngestionRunOut, IngestionRunStatus, SourceStatusItem } from '../types'

export const ingestionApi = {
  /** Trigger a full ingestion run — may take 5–30 s depending on source latency */
  run: async (queryTerms?: string[]): Promise<IngestionRunOut> => {
    const body = queryTerms && queryTerms.length > 0 ? { query_terms: queryTerms } : undefined
    const { data } = await client.post<IngestionRunOut>('/ingestion/run', body)
    return data
  },

  /**
   * On-demand search for a specific drug + disease combination.
   * Searches ALL connected sources dynamically.
   */
  search: async (drug: string, disease: string, extraTerms?: string[]): Promise<IngestionRunOut> => {
    const { data } = await client.post<IngestionRunOut>('/ingestion/search', {
      drug,
      disease,
      extra_terms: extraTerms,
    })
    return data
  },

  /** Poll run status by id */
  status: async (runId: number): Promise<IngestionRunStatus> => {
    const { data } = await client.get<IngestionRunStatus>(`/ingestion/status/${runId}`)
    return data
  },

  /** Latest run summary */
  latest: async (): Promise<IngestionRunStatus | null> => {
    try {
      const { data } = await client.get<IngestionRunStatus>('/ingestion/latest')
      return data
    } catch {
      return null
    }
  },

  /** Connectivity probe for all configured sources */
  sourceStatus: async (): Promise<SourceStatusItem[]> => {
    const { data } = await client.get<SourceStatusItem[]>('/ingestion/source-status')
    return data
  },

  /** Is a run currently in progress? */
  isRunning: async (): Promise<boolean> => {
    try {
      const { data } = await client.get<{ running: boolean }>('/ingestion/running')
      return data.running
    } catch {
      return false
    }
  },

  /** List configured background query terms */
  queryTerms: async (): Promise<{ query_terms: string[]; note: string }> => {
    const { data } = await client.get<{ query_terms: string[]; note: string }>('/ingestion/query-terms')
    return data
  },
}
