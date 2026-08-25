# SmartRecover ⚡

> **"AI-powered payment recovery with safe stopping."**  
> *Recover more revenue without giving AI unlimited control.*

SmartRecover is an enterprise-grade fintech platform engineered specifically for **recurring subscription payment and mandate recovery** (e-NACH, UPI AutoPay, recurring card mandates).

---

## 1. Core Product Principle

SmartRecover is **not** a simple automatic retry script. Its foundational architecture guarantees:

> **"AI RECOMMENDS. DETERMINISTIC GUARDRAILS DECIDE. AUTOMATION STOPS SAFELY."**

- **The AI layer is strictly advisory**: It analyzes multi-factor customer history, failure telemetry, and behavioral signals to compute an explainable Recovery Score (0–100), success probability, structured recovery strategy, and expected revenue retention.
- **The AI NEVER executes transactions directly**, NEVER modifies guardrail rules, and NEVER bypasses the authoritative backend engine.
- **The GuardrailEngine is authoritative and deterministic**: Every proposed recovery action must pass 10 immutable fintech safety rules before execution.
- **Simulation-Only Gateway**: No real payment credentials or real money transactions are ever executed.

```
Payment Failure Event
        ↓
Recovery Case Creation
        ↓
Customer Historical & Financial Context
        ↓
Recovery Strategy Optimizer (AI Advisory)
        ↓
AI Recommendation & Explainability Factors
        ↓
Authoritative Guardrail Engine (10 Deterministic Invariants)
   ├── ALLOWED ──→ Scheduled Delayed Execution ──→ Simulated Clearance ──→ RECOVERED ──→ STOPPED
   └── BLOCKED ──→ Safe Automatic Stop / Human Review Escalation ────────→ STOPPED
        ↓
Immutable Audit Trail (with State Diffs & SIMULATION_ONLY Badges)
```

---

## 2. Five Major Capabilities

### 1. Recovery Strategy Optimizer
Computes optimal, structured recovery strategies tailored to individual customer and failure characteristics:
- **Strategies**: `RETRY_NOW`, `RETRY_AFTER_6H`, `RETRY_AFTER_24H`, `RETRY_AFTER_48H`, `SEND_PAYMENT_REMINDER`, `REQUEST_PAYMENT_METHOD_UPDATE`, `REQUEST_MANDATE_REAUTHORIZATION`, `HUMAN_REVIEW`, `STOP_RECOVERY`.
- **Metrics**: Recovery Score (0–100), estimated clearance probability, expected recovery amount ($\text{Amount} \times p$), AI confidence level, recommended delay (cooldown hours), and explainable positive/negative factors.

### 2. Failure-Reason Intelligence
Standardized classification across 9 recurring payment failure categories:
1. `BANK_NETWORK_TIMEOUT` (Infrastructure switch timeout • 24h retry • Low risk • 88% recovery rate)
2. `PROCESSING_TIMEOUT` (NPCI batch queue timeout • 24h retry • Low risk • 85% recovery rate)
3. `INSUFFICIENT_FUNDS` (Balance shortfall • SMS/WhatsApp reminder + 48h retry • Medium risk • 68% recovery rate)
4. `MANDATE_EXPIRED` (Mandate validity elapsed • Re-authorization link • High risk • Operator review)
5. `PAYMENT_METHOD_INVALID` (Card expired / account closed • Update credentials link • High risk)
6. `CUSTOMER_DISPUTE` (Chargeback filed • Immediate recovery lock • Critical risk • Zero retry)
7. `FRAUD_OR_RISK_SIGNAL` (Sanctions/velocity anomaly • Lock mandate • Critical risk)
8. `REPEATED_FAILURE` (2 attempts exhausted in cycle • Hard limit stop • Human review)
9. `UNKNOWN_FAILURE` (Unclassified decline • Conservative 24h cooldown)

### 3. What-If Recovery Simulator
Interactive, multi-pathway strategy comparison sandbox:
- Evaluates 5 recovery strategies simultaneously: **6h Retry vs 24h Retry vs 48h Retry vs Payment Reminder vs Stop Recovery**.
- Displays probability curves, expected revenue, risk levels, customer contact friction, and guardrail pre-check verifications.
- Prominently watermarked with `SIMULATION — NO PAYMENT WILL BE EXECUTED` and audited as `SIMULATION_ONLY`.

### 4. Revenue-at-Risk Prioritization
Priority ranking engine that values failed payments by **Expected Recoverable Revenue** ($\text{Amount} \times \text{Clearance Probability}$) rather than nominal face value alone:
- **Priority Tiers**: `HIGH`, `MEDIUM`, `LOW`.
- **Ranked Opportunity Queue**: Lists top revenue recovery opportunities with explainable drivers and guardrail eligibility badges.
- **KPI Metrics**: Total Revenue at Risk, Total Expected Recoverable Volume, High/Medium/Low priority volume breakdowns.

### 5. AI Safety Guardrail Stress-Test Mode
Adversarial demonstration harness that intentionally feeds unsafe, aggressive AI recommendations into the `GuardrailEngine` to prove deterministic safety enforcement:
- **Predefined Scenarios**:
  - *Active Dispute Override Attempt*: AI proposes `RETRY_NOW` ➔ Blocked by Rule 5 (Dispute).
  - *Retry Limit Bypass Attempt*: AI proposes `RETRY_AFTER_6H` on 2-attempt case ➔ Blocked by Rule 1 (Attempt Limit).
  - *High-Risk Account Attempt*: AI proposes `RETRY_NOW` on flagged account ➔ Blocked by Risk Policy.
  - *Post-Stop Execution Attempt*: AI attempts reactivation for opted-out user ➔ Blocked by Rule 4 (Opt-Out).
  - *Compliant Baseline Case*: AI proposes `RETRY_AFTER_24H` ➔ Verified Allowed across all 10 invariants.
- **Interactive Sandbox**: Configure custom combinations of dispute, max retries, opt-out, high risk, and stopped states with zero real transaction risk.

---

## 3. The 10 Deterministic Guardrail Safety Invariants

Every recovery action is strictly evaluated against 10 immutable backend rules:

1. **Attempt Limit Rule**: Maximum 2 automated retry attempts permitted per recovery cycle.
2. **Retry Interval Rule**: Minimum 24-hour cooldown between automated retries (NPCI/RBI clearing compliance).
3. **Recovery Window Rule**: Maximum 7 calendar days from initial mandate failure.
4. **Customer Opt-Out Rule**: Mandatory immediate stop upon customer cancellation/opt-out.
5. **Dispute / Chargeback Rule**: Automated recovery strictly prohibited on active customer dispute.
6. **Payment Success State Invariant**: Recovery cannot be initiated if payment is already recovered.
7. **Human Review Lock**: Cases flagged for operator review cannot be retried without human resolution.
8. **Idempotency Rule**: Prevents duplicate executions on identical request keys.
9. **State Transition Validity**: Enforces strict mathematical state machine DAG.
10. **Zero Execution in Simulation**: All stress tests and simulations strictly prevent gateway execution.

---

## 4. API Endpoints

### Core Recovery Workflow
- `GET /api/dashboard`: Executive KPI metrics, recovery rates, and stop reasons breakdown.
- `GET /api/recovery-cases`: Filter and search recurring payment mandate failure cases.
- `GET /api/recovery-cases/{id}`: Detailed case telemetry, attempt history, and customer context.
- `POST /api/recovery-cases/{id}/analyze`: Run advisory AI recovery intelligence.
- `POST /api/recovery-cases/{id}/validate-action`: Dual decision engine validation (AI + Guardrails).
- `POST /api/recovery-cases/{id}/execute`: Execute simulated recovery action.
- `GET /api/recovery-cases/{id}/audit`: Immutable audit log with state diffs.

### Human Review & Operations
- `GET /api/human-review`: Pending, reviewed, resolved, and escalated review queue.
- `POST /api/human-review/{id}/review`: Mark case in-review with operator notes.
- `POST /api/human-review/{id}/resolve`: Operator resolution with custom actions.
- `POST /api/human-review/{id}/escalate`: Escalate case to legal or fraud team.

### Strategy Optimizer & Failure Intelligence
- `POST /api/optimizer/{case_id}/optimize`: Get structured strategy recommendation with confidence & factors.
- `GET /api/optimizer/failure-catalog`: Retrieve complete 9-category failure taxonomy matrix.

### What-If Simulator & Prioritization
- `POST /api/what-if/{case_id}`: Run multi-pathway hypothetical recovery simulation.
- `GET /api/prioritization/metrics`: Retrieve ranked top opportunities and expected value metrics.

### AI Safety Stress Test & Simulator
- `GET /api/stress-test/scenarios`: List predefined adversarial stress-test scenarios.
- `POST /api/stress-test/run`: Run adversarial recommendation verification against GuardrailEngine.
- `POST /api/simulator/payment-failure`: Trigger simulated payment failure.
- `POST /api/simulator/dispute`: Trigger simulated dispute event.
- `POST /api/simulator/opt-out`: Trigger simulated customer opt-out.
- `POST /api/demo/reset`: Reset database to initial demo state.

---

## 5. Verification & Testing

### Automated Backend Tests
Run the comprehensive 31-test suite:
```bash
cd backend
uv run pytest -v
```
*Result: 31 passed, 100% test coverage for state machine, guardrails, optimizer, what-if simulator, prioritization, and stress testing.*

### Frontend Production Build
Compile the React/TypeScript/Tailwind frontend:
```bash
cd frontend
npm run build
```
*Result: Clean compilation with 0 lint/TypeScript errors.*

---

## 6. Running Locally

### Backend:
```bash
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Docs: `http://127.0.0.1:8000/api/docs`
- Health Check: `http://127.0.0.1:8000/api/health`

### Frontend:
```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 3000
```
- Web Application: `http://127.0.0.1:3000`
