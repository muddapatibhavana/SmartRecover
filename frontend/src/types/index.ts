export interface Customer {
  id: string;
  name: string;
  email: string;
  phone?: string;
  is_active: boolean;
  has_dispute: boolean;
  is_opted_out: boolean;
  historical_success_count: number;
  historical_failure_count: number;
  last_active_at?: string;
}

export interface Subscription {
  id: string;
  customer_id: string;
  plan_name: string;
  amount: number;
  currency: string;
  interval: string;
  status: string;
}

export interface Mandate {
  id: string;
  subscription_id: string;
  mandate_type: string;
  bank_name: string;
  status: string;
  max_amount: number;
}

export interface PaymentAttempt {
  id: string;
  attempt_number: number;
  amount: number;
  status: string;
  failure_code?: string;
  failure_reason?: string;
  is_temporary: boolean;
  idempotency_key?: string;
  created_at: string;
}

export interface AIDecision {
  score: number;
  probability: number;
  recommended_action: string;
  recommended_delay_hours: number;
  explanation: string;
  factors: string[];
}

export interface RuleCheckDetail {
  rule_name: string;
  passed: boolean;
  description: string;
  details?: string;
}

export interface GuardrailDecision {
  allowed: boolean;
  status: string;
  blocked_reason?: string;
  stop_reason?: string;
  rules_checked: RuleCheckDetail[];
}

export interface DualDecisionView {
  ai_decision: AIDecision;
  guardrail_decision: GuardrailDecision;
  final_status: string;
  final_allowed: boolean;
  summary: string;
}

export interface RecoveryCaseSummary {
  id: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  subscription_plan: string;
  amount: number;
  currency: string;
  failure_reason: string;
  failure_code: string;
  attempt_count: number;
  recovery_score?: number;
  recovery_probability?: number;
  ai_recommendation?: string;
  guardrail_status: string;
  current_status: string;
  stop_reason?: string;
  next_action?: string;
  created_at: string;
  updated_at?: string;
}

export interface RecoveryCaseDetail {
  id: string;
  customer: Customer;
  subscription: Subscription;
  mandate: Mandate;
  amount: number;
  currency: string;
  failure_reason: string;
  failure_code: string;
  attempt_count: number;
  recovery_score?: number;
  recovery_probability?: number;
  ai_recommendation?: string;
  ai_recommended_delay_hours: number;
  ai_explanation?: string;
  ai_decision_factors: string[];
  guardrail_status: string;
  guardrail_block_reason?: string;
  guardrail_rules_checked: string[];
  current_status: string;
  stop_reason?: string;
  next_action?: string;
  next_action_scheduled_at?: string;
  initial_failure_at: string;
  created_at: string;
  updated_at?: string;
  payment_attempts: PaymentAttempt[];
}

export interface AuditLogEntry {
  id: string;
  recovery_case_id: string;
  event_type: string;
  description: string;
  actor: string;
  state_before?: string;
  state_after?: string;
  metadata: Record<string, any>;
  timestamp: string;
}

export interface HumanReviewItem {
  id: string;
  recovery_case_id: string;
  customer: Customer;
  case_amount: number;
  case_failure_reason: string;
  trigger_reason: string;
  status: string;
  operator_notes?: string;
  resolution_action?: string;
  ai_recommendation?: string;
  ai_score?: number;
  stop_reason?: string;
  case_status?: string;
  created_at: string;
  updated_at?: string;
}

export interface StopReasonCount {
  reason: string;
  label: string;
  count: number;
  percentage: number;
  amount_at_stop: number;
}

export interface DashboardMetrics {
  failed_mandates_count: number;
  revenue_at_risk: number;
  ai_eligible_count: number;
  recovered_revenue: number;
  recovery_rate: number;
  expected_recovery_revenue: number;
  automation_stopped_count: number;
  human_review_count: number;
  stop_reasons_breakdown: StopReasonCount[];
}

export interface ExecuteActionResponse {
  success: boolean;
  action_id: string;
  action_type: string;
  status: string;
  execution_result: Record<string, any>;
  current_case_status: string;
  stop_reason?: string;
  message: string;
}

// =================================================================
// 5 MAJOR FEATURE TYPES
// =================================================================

export interface StrategyOptimizerResponse {
  case_id: string;
  strategy: string;
  strategy_label: string;
  recovery_score: number;
  estimated_success_probability: number;
  expected_recovery_amount: number;
  confidence: number;
  recommended_delay_hours: number;
  reasoning: string[];
  positive_factors: string[];
  negative_factors: string[];
  risk_level: string;
  human_review_required: boolean;
  guardrail_precheck_status: string;
  guardrail_precheck_reason?: string;
}

export interface FailureClassificationDetail {
  code: string;
  name: string;
  category: string;
  description: string;
  retry_suitable: boolean;
  preferred_strategy: string;
  recommended_delay_hours: number;
  communication_recommendation: string;
  risk_level: string;
  human_review_required: boolean;
  historical_recovery_rate: number;
  explanation_template: string;
}

export interface WhatIfStrategyOption {
  strategy: string;
  label: string;
  success_probability: number;
  expected_recovery_amount: number;
  risk_level: string;
  customer_contact_risk: string;
  expected_attempts: number;
  is_recommended: boolean;
  guardrail_allowed: boolean;
  guardrail_reason?: string;
  reason: string;
}

export interface WhatIfSimulationResponse {
  case_id: string;
  amount: number;
  customer_name: string;
  failure_code: string;
  failure_reason: string;
  strategies: WhatIfStrategyOption[];
  best_strategy: string;
  why_recommended: string[];
  disclaimer: string;
}

export interface PriorityCaseSummary {
  id: string;
  customer_name: string;
  customer_email: string;
  amount: number;
  recovery_probability: number;
  expected_recovery_amount: number;
  priority_tier: 'HIGH' | 'MEDIUM' | 'LOW';
  priority_score: number;
  failure_code: string;
  failure_reason: string;
  recommended_strategy: string;
  guardrail_eligible: boolean;
  rank: number;
  explainable_factors: string[];
}

export interface RevenuePriorityMetrics {
  total_revenue_at_risk: number;
  expected_recoverable_revenue: number;
  high_priority_count: number;
  high_priority_amount: number;
  medium_priority_count: number;
  medium_priority_amount: number;
  low_priority_count: number;
  low_priority_amount: number;
  top_opportunities: PriorityCaseSummary[];
}

export interface StressTestScenario {
  id: string;
  name: string;
  description: string;
  target_customer: string;
  amount: number;
  failure_code: string;
  failure_reason: string;
  proposed_ai_recommendation: string;
  expected_guardrail_result: 'ALLOWED' | 'BLOCKED';
  expected_block_reason?: string;
  scenario_category: string;
}

export interface StressTestRunRequest {
  scenario_id?: string;
  custom_case_id?: string;
  proposed_action?: string;
  simulate_dispute?: boolean;
  simulate_max_retries?: boolean;
  simulate_opt_out?: boolean;
  simulate_high_risk?: boolean;
  simulate_stopped?: boolean;
}

export interface StressTestResult {
  scenario_id: string;
  scenario_name: string;
  ai_proposed_action: string;
  guardrail_allowed: boolean;
  guardrail_status: string;
  guardrail_blocked_reason?: string;
  stop_reason?: string;
  rules_checked: RuleCheckDetail[];
  simulation_badge: string;
  verdict_summary: string;
  execution_blocked: boolean;
}
