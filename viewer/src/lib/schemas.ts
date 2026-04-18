/**
 * TypeScript mirror of src/rlm_logger/schemas.py.
 * Any change here MUST be kept in sync with the Python side.
 * Zod schemas validate case files loaded from URL / drag-drop at runtime.
 */
import { z } from "zod";

export const ModelInfo = z.object({
  provider: z.string(),
  name: z.string(),
  temperature: z.number().default(0.2),
});
export type ModelInfo = z.infer<typeof ModelInfo>;

export const LogFileEntry = z.object({
  path: z.string(),
  bytes: z.number().int(),
  rows: z.number().int(),
  sha256: z.string(),
});

export const TimeWindow = z.object({
  start: z.string(),
  end: z.string(),
});

export const LogsManifest = z.object({
  files: z.array(LogFileEntry),
  time_window: TimeWindow,
  total_rows: z.number().int(),
});
export type LogsManifest = z.infer<typeof LogsManifest>;

export const EvidenceLine = z.object({
  event_id: z.string().nullable().optional(),
  file: z.string(),
  line: z.number().int(),
  ts: z.string(),
  service: z.string(),
  level: z.string(),
  text_redacted: z.string(),
  context_before: z.array(z.string()).max(3).default([]),
  context_after: z.array(z.string()).max(3).default([]),
  why: z.string(),
  is_key: z.boolean().default(false),
});
export type EvidenceLine = z.infer<typeof EvidenceLine>;

export const BlastRadius = z.object({
  duration_minutes: z.number().nullable().optional(),
  window_start: z.string().nullable().optional(),
  window_end: z.string().nullable().optional(),
}).passthrough();

export const IncidentReport = z.object({
  root_cause: z.string(),
  blast_radius: z.union([z.string(), BlastRadius]),
  evidence: z.array(EvidenceLine),
  remediation: z.string(),
  confidence: z.number().min(0).max(1),
  confidence_rationale: z.string(),
  unknowns: z.array(z.string()).default([]),
});
export type IncidentReport = z.infer<typeof IncidentReport>;

export const ToolName = z.enum([
  "schema",
  "top_errors",
  "search",
  "around",
  "trace",
  "submit_incident_report",
  "llm_query",
]);
export type ToolName = z.infer<typeof ToolName>;

export const Step = z.object({
  step: z.number().int(),
  tool: ToolName,
  args: z.record(z.unknown()).default({}),
  stdout_excerpt: z.string().default(""),
  stderr_excerpt: z.string().default(""),
  elapsed_ms: z.number().int().default(0),
  report_delta: z.record(z.unknown()).nullable().optional(),
});
export type Step = z.infer<typeof Step>;

export const Usage = z.object({
  llm_calls: z.number().int().default(0),
  tool_calls: z.number().int().default(0),
  wall_clock_s: z.number().default(0),
  input_tokens: z.number().int().default(0),
  output_tokens: z.number().int().default(0),
});

export const GroundTruth = z.object({
  incident_id: z.string().nullable().optional(),
  root_cause: z.string(),
  evidence_event_ids: z.array(z.string()).default([]),
  blast_radius: z.union([z.record(z.unknown()), z.string()]).nullable().optional(),
  remediation: z.union([z.record(z.unknown()), z.string()]).nullable().optional(),
  distractors: z.array(z.record(z.unknown())).default([]),
}).passthrough();
export type GroundTruth = z.infer<typeof GroundTruth>;

export const TerminationReason = z.enum([
  "submitted",
  "max_iterations",
  "max_llm_calls",
  "max_wall_clock",
  "aborted",
  "error",
]);

export const CaseFile = z.object({
  version: z.literal("0.1"),
  question: z.string(),
  model: ModelInfo,
  logs_manifest: LogsManifest,
  trajectory: z.array(Step),
  report: IncidentReport.nullable().optional(),
  termination_reason: TerminationReason,
  usage: Usage.default({}),
  ground_truth: GroundTruth.nullable().optional(),
});
export type CaseFile = z.infer<typeof CaseFile>;
