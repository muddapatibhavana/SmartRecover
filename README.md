# SmartRecover ⚡

> **"AI-powered payment recovery with safe stopping."**  
> *Recover more revenue without giving AI unlimited control.*

SmartRecover is an enterprise-grade fintech platform engineered specifically for **recurring subscription payment and mandate recovery** (e-NACH, UPI AutoPay, recurring cards).

---

## 1. Core Product Principle

SmartRecover is **not** a simple automatic retry script. Its foundational architecture guarantees:

> **"AI recommends. Guardrails control. Automation stops safely."**

- **The AI layer is strictly advisory**: It analyzes multi-factor customer history and failure telemetry to output an explainable Recovery Score (0–100), recovery probability, and recommended action (`RETRY`, `NOTIFY`, `HUMAN_REVIEW`, `STOP`).
- **The AI NEVER executes transactions directly**, NEVER modifies guardrail rules, and NEVER bypasses the authoritative backend engine.
- **The GuardrailEngine is authoritative and deterministic**: Every proposed recovery action must pass 10 immutable fintech safety rules before execution.

```
Payment Event
    ↓
Recovery Case
    ↓
Customer Context
    ↓
Recovery Intelligence (AI Advisory)
    ↓
AI Recommendation & Explainable Factors
    ↓
Deterministic Guardrail Engine
    ↓
Allowed / Blocked
    ↓
Recovery Workflow Engine (State Machine)
    ↓
Simulated Retry / Notify / Human Review
    ↓
Payment Result
    ↓
Immutable Audit Log
    ↓
Automatic Stop (when payment succeeds or stopping rule triggers)
```

---

## 2. Recovery State Machine

SmartRecover enforces an explicit 12-state machine:

```
FAILED → ANALYZING → AI_RECOMMENDED → GUARDRAIL_CHECK → ACTION_ALLOWED → RETRY_SCHEDULED → RETRYING → RECOVERED → STOPPED
                                                    ↘
                                                      ACTION_BLOCKED → HUMAN_REVIEW → STOPPED
```

### Valid States:
1. `FAILED`: Initial mandate failure detected.
2. `ANALYZING`: Extracting customer context & telemetry.
3. `AI_RECOMMENDED`: Explainable recovery score & recommendation generated.
4. `GUARDRAIL_CHECK`: Authoritative safety invariant verification.
5. `ACTION_ALLOWED`: Guardrails verified and action permitted.
6. `ACTION_BLOCKED`: Guardrails detected violation (e.g. dispute, max attempts).
7. `RETRY_SCHEDULED`: Retry cooldown queued (minimum 24-hour interval).
8. `RETRYING`: Simulated mandate debit in execution.
9. `NOTIFICATION_SENT`: Customer notified via email/SMS.
10. `RECOVERED` *(Terminal)*: Mandate successfully debited and revenue captured.
11. `HUMAN_REVIEW` *(Terminal / Flagged)*: Escrowed for manual operator resolution.
12. `STOPPED` *(Terminal)*: Safe stop applied.

---

## 3. 10 Authoritative Deterministic Guardrail Rules

| Rule # | Rule Identifier | Policy Enforcement | Safe Stopping Trigger |
| :--- | :--- | :--- | :--- |
| **Rule 1** | `attempt_limit` | Maximum 2 retry attempts per recovery cycle | `MAX_ATTEMPTS_REACHED` |
| **Rule 2** | `retry_interval` | Minimum 24 hours cooldown between retry attempts | Blocked until cooldown expires |
| **Rule 3** | `recovery_window` | Maximum 7 days from initial failure timestamp | `RECOVERY_WINDOW_EXPIRED` |
| **Rule 4** | `customer_opt_out` | Opt-out request immediately blocks retries | `CUSTOMER_OPTED_OUT` |
| **Rule 5** | `customer_dispute` | Active chargeback/dispute locks mandate | `CUSTOMER_DISPUTED` → Human Review |
| **Rule 6** | `repeated_failures` | Hard decline failures trigger immediate stop | `RECOVERY_FAILED` |
| **Rule 7** | `payment_success` | Already recovered mandates prohibit duplicate debits | `PAYMENT_RECOVERED` |
| **Rule 8** | `ai_override_prohibition`| AI recommendations cannot override any guardrail | Block enforced regardless of AI score |
| **Rule 9** | `human_review_lock` | Cases in Human Review cannot be auto-retried | Manual resolution required |
| **Rule 10**| `expired_window_lock` | Expired recovery windows strictly prohibit execution | Permanent Safe Stop |

---

## 4. Why Did SmartRecover Stop?

Safe stopping is a first-class feature in SmartRecover:

- **SUCCESS**: *"Workflow stopped automatically because payment was successfully recovered."*
- **MAX ATTEMPTS**: *"Workflow stopped because the maximum number of retry attempts (2) was reached."*
- **DISPUTE**: *"Automation stopped because customer disputed the payment. Human review is required."*
- **OPT-OUT**: *"Automation stopped because the customer opted out of payment recovery."*
- **RECOVERY WINDOW**: *"Automation stopped because the maximum 7-day recovery window has expired."*

---

## 5. Technology Stack & Architecture

- **Backend**: Python 3.14 + FastAPI + Pydantic v2 + SQLAlchemy (PostgreSQL / SQLite test mode)
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + Lucide Icons
- **Simulation Harness**: Deterministic payment simulator generating mock NPCI / E-NACH transaction IDs and bank references (Zero real payment credentials used)
- **Testing**: Pytest automated suite covering all 15 core safety and stopping invariants

```
smartrecover/
├── backend/
│   ├── app/
│   │   ├── api/             # REST Endpoints (Dashboard, Recovery Cases, Audit, Human Review, Simulator, Demo)
│   │   ├── core/            # Engines: Workflow, Intelligence, Guardrails, Simulator, Audit, Human Review
│   │   ├── models/          # 10 Normalized SQLAlchemy Database Models
│   │   ├── schemas/         # Pydantic v2 Request/Response DTOs
│   │   ├── config.py        # Environment Configuration
│   │   ├── database.py      # SQLAlchemy Session Factory
│   │   ├── seed.py          # Realistic Demo Dataset Seeder (1,248 cases)
│   │   └── main.py          # FastAPI Application Entry Point
│   └── tests/
│       └── test_smartrecover.py # 17 Automated Backend Tests (100% passing)
├── frontend/
│   ├── src/
│   │   ├── components/      # UI: KPICards, AIDecisionVsGuardrailPanel, AuditTimeline, StopReasonAnalytics, etc.
│   │   ├── services/        # Typed API client
│   │   ├── types/           # TypeScript DTO mappings
│   │   └── App.tsx          # Main Fintech SaaS Dashboard
│   └── vite.config.ts
└── README.md
```

---

## 6. Preloaded Demo Scenarios (Customers A – F)

| Scenario | Customer | Amount | Initial State | AI Recommendation | Guardrail Decision | Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Customer A** | ABC Technologies | ₹14,999 | FAILED | `RETRY` (91% score) | `ALLOWED` | Ready for retry execution |
| **Customer B** | BlueWave Dynamics | ₹9,999 | HUMAN_REVIEW | `HUMAN_REVIEW` (35% score) | `ALLOWED` | Routed to human review |
| **Customer C** | Apex Retail Logistics | ₹14,999 | HUMAN_REVIEW | `RETRY` (85% score) | `BLOCKED` (Dispute) | AI overridden; routed to Review |
| **Customer D** | CloudScale Analytics | ₹9,999 | FAILED | `RETRY` (90% score) | `ALLOWED` | 1-Click Complete Recovery Loop |
| **Customer E** | Horizon Media Labs | ₹8,499 | STOPPED | `RETRY` (78% score) | `BLOCKED` (Max 2 Attempts) | Safely stopped |
| **Customer F** | FinPulse Systems | ₹12,500 | STOPPED | `RETRY` (88% score) | `BLOCKED` (Opted Out) | Safely stopped |

---

## 7. How to Run Locally

### Prerequisites
- Python 3.10+ (or `uv`)
- Node.js 18+ and `npm`

### 1. Run the Backend API
```powershell
cd backend
# Using uv (recommended)
uv run uvicorn app.main:app --reload --port 8000

# Or using standard python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/api/docs`
- Health Check: `http://localhost:8000/api/health`

### 2. Run the Frontend Dashboard
```powershell
cd frontend
npm install
npm run dev
```
- Dashboard UI: `http://localhost:3000`

### 3. Run Automated Safety Tests
```powershell
cd backend
uv run pytest -v
```
All 17 tests verify:
- Successful recovery auto-stops workflow
- Maximum 2 retry attempts limit
- 24-hour retry cooldown invariant
- 7-day recovery window expiration
- Customer opt-out & dispute safe stops
- AI inability to bypass GuardrailEngine
- Execution re-validation and idempotency
- Dynamic KPI calculations

---

## 8. Security and Compliance

- **No Real Payment Credentials**: The system operates exclusively with mock transaction identifiers and realistic simulated bank responses.
- **Backend-Authoritative Security**: Client-provided states or bypass flags are strictly rejected. The backend re-evaluates database state at execution time.
- **Immutable Audit Trail**: All AI recommendations, guardrail checks, state transitions, and operator interventions are permanently recorded with timestamps.
