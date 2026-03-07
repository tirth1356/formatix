/**
 * Centralised API client.
 * Base URL is read from VITE_BACKEND_URL (set in .env.local).
 * Falls back to http://localhost:8000 for local dev without .env.
 */

export const BACKEND_URL =
  (import.meta.env.VITE_BACKEND_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000";

// ──────────────────────────────────────────────────────────────────────────────
// Generic helpers
// ──────────────────────────────────────────────────────────────────────────────

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`API ${path} → ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

// ──────────────────────────────────────────────────────────────────────────────
// Health
// ──────────────────────────────────────────────────────────────────────────────

export const apiHealth = () =>
  request<{ status: string; ai_mode: string }>("/health");

// ──────────────────────────────────────────────────────────────────────────────
// File upload  →  returns { job_id, filename }
// ──────────────────────────────────────────────────────────────────────────────

export async function apiUploadManuscript(
  file: File
): Promise<{ job_id: string; filename: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BACKEND_URL}/upload-manuscript`, {
    method: "POST",
    body: form,
    // Do NOT set Content-Type here – browser sets it with the boundary automatically
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`Upload failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export async function apiUploadText(
  text: string
): Promise<{ job_id: string; filename: string }> {
  return request<{ job_id: string; filename: string }>("/upload-text", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

// ──────────────────────────────────────────────────────────────────────────────
// Extract rules  →  tell the backend which style was chosen
// ──────────────────────────────────────────────────────────────────────────────

export const apiExtractRules = (
  job_id: string,
  style: string,
  use_cloud = false,
  guidelines = ""
) =>
  request("/extract-rules", {
    method: "POST",
    body: JSON.stringify({ job_id, style, guidelines, use_cloud }),
  });

// ──────────────────────────────────────────────────────────────────────────────
// Format a citation preview (called on card click)
// ──────────────────────────────────────────────────────────────────────────────

export interface CitationPreviewResult {
  citation: string;
  style_key: string;
  style_name: string;
  citation_type: string;
  in_text_format: string;
  formatting_rules: Record<string, unknown>;
}

export const apiFormatCitation = (
  style: string,
  source_type: "journal" | "conference" | "book" | "website",
  data: Record<string, string | number>
) =>
  request<CitationPreviewResult>("/format-citation", {
    method: "POST",
    body: JSON.stringify({ style, source_type, data }),
  });

// ──────────────────────────────────────────────────────────────────────────────
// List all citation styles
// ──────────────────────────────────────────────────────────────────────────────

export const apiCitationStyles = () =>
  request<{
    styles: Record<string, unknown>;
    title_map: Record<string, string>;
  }>("/citation-styles");

// ──────────────────────────────────────────────────────────────────────────────
// Full Pipeline Endpoints
// ──────────────────────────────────────────────────────────────────────────────

export const apiParse = (job_id: string, use_cloud = false) =>
  request<{ text: string; pages: number; raw_sections: unknown[] }>("/parse", {
    method: "POST",
    body: JSON.stringify({ job_id, use_cloud }),
  });

export const apiAnalyzeStructure = (job_id: string, use_cloud = false) =>
  request<{ title: string; sections: unknown[]; citations: unknown[] }>("/analyze-structure", {
    method: "POST",
    body: JSON.stringify({ job_id, use_cloud }),
  });

export const apiAnalyzeCorrections = (job_id: string, use_cloud = false) =>
  request<{ corrections: unknown[] }>("/analyze-corrections", {
    method: "POST",
    body: JSON.stringify({ job_id, use_cloud }),
  });

export const apiFormatDocument = (job_id: string, accepted_corrections: unknown[] = [], use_cloud = false) =>
  request<{ output_docx: string; corrections: unknown[] }>("/format-document", {
    method: "POST",
    body: JSON.stringify({ job_id, accepted_corrections, use_cloud }),
  });

export const apiValidateCitations = (job_id: string, use_cloud = false) =>
  request<{ issues: unknown[]; missing_references: unknown[]; uncited_references: unknown[] }>("/validate-citations", {
    method: "POST",
    body: JSON.stringify({ job_id, use_cloud }),
  });

export const apiValidateFormat = (job_id: string, use_cloud = false) =>
  request<{ formatting_score: number; issues: unknown[]; suggestions: unknown[] }>("/validate-format", {
    method: "POST",
    body: JSON.stringify({ job_id, use_cloud }),
  });

// ──────────────────────────────────────────────────────────────────────────────
// Get Job / Results
// ──────────────────────────────────────────────────────────────────────────────
export const apiGetJob = (job_id: string, include_parsed = false) =>
  request<any>(`/job/${job_id}${include_parsed ? "?include_parsed=true" : ""}`);
