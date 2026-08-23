# Walkthrough: SmartRecover Platform

**SmartRecover** is an AI-powered failed recurring payment and mandate recovery system with deterministic safe stopping.

> **"AI recommends. Guardrails control. Automation stops safely."**

---

## 1. What Was Built

### Core Backend Modules (`backend/app/core/`)
1. **`RecoveryWorkflowEngine`**: Authoritative 12-state machine orchestrator managing state transitions, execution safety, and safe stopping triggers.
2. **`RecoveryIntelligenceEngine`**: Explainable multi-factor scoring (0–100) and probability estimator providing advisory recommendations (`RETRY`, `NOTIFY`, `HUMAN_REVIEW`, `STOP`).
3. **`GuardrailEngine`**: Authoritative deterministic engine evaluating 10 safety invariants (max 2 attempts, 24h cooldown, 7-day recovery window, customer opt-out, dispute locks, human review locks, etc.).
4. **`PaymentSimulator`**: Deterministic payment lifecycle simulation generating mock NPCI / E-NACH bank transaction references (Zero real payment credentials used).
5. **`AuditService`**: Immutable chronological audit event logging.
6. **`HumanReviewService`**: Operational queue management for manual reviews, resolutions, and escalations.

### Database Architecture (`backend/app/models/entities.py`)
Normalized database models for:
- `customers` (loyalty metrics, dispute flags, opt-out flags)
- `subscriptions` & `mandates` (recurring plans, e-NACH/UPI AutoPay references)
- `payment_attempts` (attempt sequences, failure codes, idempotency keys)
- `recovery_cases` (state machine, AI scores, guardrail status, stop reasons)
- `recovery_actions` & `guardrail_events` (action execution tracking, rule evaluation logs)
- `audit_logs` & `customer_events` (immutable event trails)
- `human_reviews` (operational escalation records)

### Frontend Dashboard (`frontend/src/`)
- **Executive KPI Cards**: Dynamic calculation of Revenue At Risk (₹42.6L), Recovered Revenue (₹27.8L), Recovery Rate (65.3%), AI Eligible Cases (937), and Stopped Automations (311).
- **"Why Did SmartRecover Stop?" Widget**: Visual breakdown with exact rationale for Maximum Attempts, Disputes, Opt-Outs, and Success Stops.
- **AI Decision vs. Guardrail Decision Hero Panel**: Clear side-by-side comparison illustrating why AI is advisory and Guardrails are authoritative.
- **Immutable Audit Timeline**: Chronological event logs with actor badges, timestamps, and state transitions.
- **Interactive Payment Simulator**: Safe testing harness for failure injection, retry simulation, disputes, and opt-outs.
- **1-Click Hackathon Demo Scenarios**: Instant playable journeys for Customers A through F.

---

## 2. Automated Test Verification Results

All **17 pytest automated backend tests** passed with 100% success:

```
tests/test_health.py::test_health_check PASSED                           [  5%]
tests/test_health.py::test_root_endpoint PASSED                          [ 11%]
tests/test_smartrecover.py::test_successful_recovery_stops_workflow PASSED [ 17%]
tests/test_smartrecover.py::test_max_retry_attempts_blocks_retry PASSED  [ 23%]
tests/test_smartrecover.py::test_retry_before_24_hours_blocks_retry PASSED [ 29%]
tests/test_smartrecover.py::test_recovery_window_expiration_stops_automation PASSED [ 35%]
tests/test_smartrecover.py::test_customer_opt_out_blocks_recovery PASSED [ 41%]
tests/test_smartrecover.py::test_customer_dispute_blocks_recovery PASSED [ 47%]
tests/test_smartrecover.py::test_ai_recommendation_cannot_bypass_guardrail PASSED [ 52%]
tests/test_smartrecover.py::test_low_recovery_score_routes_to_human_review PASSED [ 58%]
tests/test_smartrecover.py::test_successful_retry_creates_audit_event PASSED [ 64%]
tests/test_smartrecover.py::test_blocked_action_creates_guardrail_event PASSED [ 70%]
tests/test_smartrecover.py::test_frontend_cannot_bypass_backend_guardrails PASSED [ 76%]
tests/test_smartrecover.py::test_execute_revalidates_guardrails PASSED   [ 82%]
tests/test_smartrecover.py::test_idempotency_duplicate_action_rejected PASSED [ 88%]
tests/test_smartrecover.py::test_invalid_state_transitions_are_rejected PASSED [ 94%]
tests/test_smartrecover.py::test_recovered_revenue_metric_calculation PASSED [100%]

======================== 17 passed, 1 warning in 1.36s ========================
```

---

## 3. Frontend Production Build

The TypeScript compilation and Vite build succeeded with zero errors:
```
dist/index.html                   0.95 kB │ gzip:  0.54 kB
dist/assets/index-DiBsNSQj.css   30.73 kB │ gzip:  5.95 kB
dist/assets/index-DT2fL1Mk.js   217.40 kB │ gzip: 61.36 kB
✓ built in 2.47s
```

---

## 4. Demo Scenarios & Test Matrix

- **Customer A (ABC Technologies - #SR-1024)**: High historical loyalty (14 successes, 1 temp fail) → AI score 91% (`RETRY`) → Guardrails PASS → Ready for execution.
- **Customer B (BlueWave Dynamics - #SR-1025)**: Low payment history (5 fails) → AI score 35% (`HUMAN_REVIEW`) → Safely routed to Human Review queue.
- **Customer C (Apex Retail Logistics - #SR-1026)**: Perfect historical record → AI recommends `RETRY` (85%) → Active dispute detected → Guardrail BLOCKS action → Routed to Human Review.
- **Customer D (CloudScale Analytics - #SR-1027)**: 1-click primary demo loop (Fail → Analyze → Retry → Recovered → Safe Stop).
- **Customer E (Horizon Media Labs - #SR-1028)**: 2 attempts reached → Guardrail BLOCKS action → Safe Stop on `MAX_ATTEMPTS_REACHED`.
- **Customer F (FinPulse Systems - #SR-1029)**: Customer opted out → Guardrail BLOCKS action → Safe Stop on `CUSTOMER_OPTED_OUT`.
