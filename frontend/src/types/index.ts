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

export interface RuleCheckDetail {
  rule_name: string;
  passed: boolean;
  description: string;
  details?: string;
}

export interface AIDecision {
  score: number;
  probability: number;
  recommended_action: string;
  recommended_delay_hours: number;
  explanation: string;
  factors: string[];
}

export interface GuardrailDecision {
  allowed: boolean;
  status: 'ALLOWED' | 'BLOCKED';
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
