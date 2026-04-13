// Types mirroring backend schemas.py

export type InputType = "url" | "text";

export interface AEORequest {
  input_type: InputType;
  input_value: string;
}

export interface DirectAnswerDetails {
  word_count: number;
  threshold: number;
  is_declarative: boolean;
  has_hedge_phrase: boolean;
}

export interface HTagHierarchyDetails {
  violations: string[];
  h_tags_found: string[];
}

export interface ReadabilityDetails {
  fk_grade_level: number;
  target_range: string;
  complex_sentences: string[];
}

export type CheckDetails =
  | DirectAnswerDetails
  | HTagHierarchyDetails
  | ReadabilityDetails
  | Record<string, unknown>;

export interface CheckResult {
  check_id: string;
  name: string;
  passed: boolean;
  score: number;
  max_score: number;
  details: CheckDetails;
  recommendation: string | null;
}

export interface AEOResponse {
  aeo_score: number;
  band: string;
  checks: CheckResult[];
}

export type SubQueryType =
  | "comparative"
  | "feature_specific"
  | "use_case"
  | "trust_signals"
  | "how_to"
  | "definitional";

export interface FanoutRequest {
  target_query: string;
  existing_content?: string;
}

export interface SubQuery {
  type: SubQueryType;
  query: string;
  covered: boolean | null;
  similarity_score: number | null;
}

export interface GapSummary {
  covered: number;
  total: number;
  coverage_percent: number;
  covered_types: string[];
  missing_types: string[];
}

export interface FanoutResponse {
  target_query: string;
  model_used: string;
  total_sub_queries: number;
  sub_queries: SubQuery[];
  gap_summary: GapSummary | null;
}

export interface StreamMeta {
  target_query: string;
  model_used: string;
}

export interface StreamError {
  error: string;
  detail: string;
}
