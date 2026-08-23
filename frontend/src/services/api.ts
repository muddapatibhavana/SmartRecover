import {
  DashboardMetrics,
  RecoveryCaseSummary,
  RecoveryCaseDetail,
  DualDecisionView,
  AuditLogEntry,
  HumanReviewItem,
  ExecuteActionResponse
} from '../types';

const API_BASE = '/api';

export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  const res = await fetch(`${API_BASE}/dashboard`);
  if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
  return res.json();
}

export async function fetchRecoveryCases(status?: string, search?: string): Promise<RecoveryCaseSummary[]> {
  const params = new URLSearchParams();
  if (status && status !== 'ALL') params.append('status', status);
  if (search) params.append('search', search);

  const res = await fetch(`${API_BASE}/recovery-cases?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch recovery cases');
  return res.json();
}

export async function fetchRecoveryCaseDetail(caseId: string): Promise<RecoveryCaseDetail> {
  const res = await fetch(`${API_BASE}/recovery-cases/${caseId}`);
  if (!res.ok) throw new Error(`Failed to fetch case ${caseId}`);
  return res.json();
}

export async function analyzeCase(caseId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/recovery-cases/${caseId}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) throw new Error(`Failed to analyze case ${caseId}`);
  return res.json();
}

export async function validateAction(caseId: string, actionType = 'RETRY_PAYMENT'): Promise<DualDecisionView> {
  const res = await fetch(`${API_BASE}/recovery-cases/${caseId}/validate-action?action_type=${actionType}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) throw new Error(`Failed to validate action on case ${caseId}`);
  return res.json();
}

export async function executeRecoveryAction(
  caseId: string,
  actionType = 'RETRY_PAYMENT',
  forceOutcome?: 'SUCCESS' | 'FAILED'
): Promise<ExecuteActionResponse> {
  const res = await fetch(`${API_BASE}/recovery-cases/${caseId}/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action_type: actionType,
      force_simulation_outcome: forceOutcome
    })
  });
  if (!res.ok) throw new Error(`Failed to execute recovery action on ${caseId}`);
  return res.json();
}

export async function fetchAuditTrail(caseId: string): Promise<AuditLogEntry[]> {
  const res = await fetch(`${API_BASE}/recovery-cases/${caseId}/audit`);
  if (!res.ok) throw new Error(`Failed to fetch audit trail for ${caseId}`);
  return res.json();
}

export async function fetchHumanReviews(status?: string): Promise<HumanReviewItem[]> {
  const params = new URLSearchParams();
  if (status && status !== 'ALL') params.append('status', status);

  const res = await fetch(`${API_BASE}/human-review?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch human review queue');
  return res.json();
}

export async function updateHumanReview(
  reviewId: string,
  action: 'review' | 'resolve' | 'escalate',
  notes?: string,
  resolutionAction?: string
): Promise<HumanReviewItem> {
  const res = await fetch(`${API_BASE}/human-review/${reviewId}/${action}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes, resolution_action: resolutionAction })
  });
  if (!res.ok) throw new Error(`Failed to ${action} review item`);
  return res.json();
}

export async function simulatePaymentFailure(
  customerId: string,
  amount: number,
  failureCode: string,
  failureReason: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/simulator/payment-failure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      customer_id: customerId,
      amount,
      failure_code: failureCode,
      failure_reason: failureReason
    })
  });
  if (!res.ok) throw new Error('Failed to simulate payment failure');
  return res.json();
}

export async function simulateDispute(customerId: string, reason: string): Promise<any> {
  const res = await fetch(`${API_BASE}/simulator/dispute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_id: customerId, reason })
  });
  if (!res.ok) throw new Error('Failed to simulate dispute');
  return res.json();
}

export async function simulateOptOut(customerId: string, reason: string): Promise<any> {
  const res = await fetch(`${API_BASE}/simulator/opt-out`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_id: customerId, reason })
  });
  if (!res.ok) throw new Error('Failed to simulate opt-out');
  return res.json();
}

export async function resetDemoData(): Promise<any> {
  const res = await fetch(`${API_BASE}/demo/reset`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to reset demo data');
  return res.json();
}

export async function loadDemoScenario(scenarioKey: string): Promise<any> {
  const res = await fetch(`${API_BASE}/demo/scenario/${scenarioKey}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to load scenario ${scenarioKey}`);
  return res.json();
}
