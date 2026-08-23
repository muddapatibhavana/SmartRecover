import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models.entities import (
    Customer, Subscription, Mandate, PaymentAttempt, RecoveryCase,
    RecoveryAction, GuardrailEvent, AuditLog, CustomerEvent, HumanReview
)
from app.schemas.dtos import StateConstants, StopReasonConstants
from app.core.intelligence_engine import RuleBasedIntelligenceEngine
from app.core.guardrail_engine import GuardrailEngine
from app.core.audit_service import AuditService

def seed_database(db: Session = None):
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    # Drop all and recreate
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    now = datetime.now(timezone.utc)
    ai_engine = RuleBasedIntelligenceEngine()

    print("[SEED] Seeding SmartRecover core demo scenarios...")

    # ----------------------------------------------------
    # SCENARIO A: High Recovery (Customer A - ABC Technologies)
    # ----------------------------------------------------
    cust_a = Customer(
        id="CUST-1001",
        name="ABC Technologies",
        email="billing@abctechnologies.io",
        phone="+91 98765 43210",
        is_active=True,
        has_dispute=False,
        is_opted_out=False,
        historical_success_count=14,
        historical_failure_count=1,
        last_active_at=now - timedelta(days=2),
        created_at=now - timedelta(days=420)
    )
    db.add(cust_a)

    sub_a = Subscription(
        id="SUB-2001",
        customer_id=cust_a.id,
        plan_name="Enterprise Platform Annual",
        amount=14999.0,
        currency="INR",
        interval="MONTHLY",
        status="ACTIVE",
        created_at=now - timedelta(days=420)
    )
    db.add(sub_a)

    mand_a = Mandate(
        id="MAND-3001",
        subscription_id=sub_a.id,
        mandate_type="ENACH",
        bank_name="HDFC Bank",
        status="ACTIVE",
        max_amount=50000.0,
        created_at=now - timedelta(days=420)
    )
    db.add(mand_a)

    case_a = RecoveryCase(
        id="SR-1024",
        customer_id=cust_a.id,
        subscription_id=sub_a.id,
        mandate_id=mand_a.id,
        amount=14999.0,
        currency="INR",
        failure_reason="Temporary payment failure (Bank switch timeout)",
        failure_code="BANK_NETWORK_TIMEOUT",
        attempt_count=0,
        current_status=StateConstants.FAILED,
        initial_failure_at=now - timedelta(hours=3),
        created_at=now - timedelta(hours=3)
    )
    db.add(case_a)
    db.flush()

    AuditService.record_event(
        db=db,
        recovery_case_id=case_a.id,
        event_type="PAYMENT_FAILED",
        description="Recurring mandate debit failed: Temporary payment failure",
        actor="PAYMENT_SIMULATOR",
        state_after=StateConstants.FAILED,
        metadata={"amount": 14999.0, "failure_code": "BANK_NETWORK_TIMEOUT"}
    )

    # ----------------------------------------------------
    # SCENARIO B: Low Recovery Score (Customer B - BlueWave Dynamics)
    # ----------------------------------------------------
    cust_b = Customer(
        id="CUST-1002",
        name="BlueWave Dynamics",
        email="finance@bluewavedynamics.com",
        phone="+91 98111 22233",
        is_active=False,
        has_dispute=False,
        is_opted_out=False,
        historical_success_count=2,
        historical_failure_count=5,
        last_active_at=now - timedelta(days=62),
        created_at=now - timedelta(days=210)
    )
    db.add(cust_b)

    sub_b = Subscription(
        id="SUB-2002",
        customer_id=cust_b.id,
        plan_name="Growth Pro Tier",
        amount=9999.0,
        currency="INR",
        interval="MONTHLY",
        status="ACTIVE",
        created_at=now - timedelta(days=210)
    )
    db.add(sub_b)

    mand_b = Mandate(
        id="MAND-3002",
        subscription_id=sub_b.id,
        mandate_type="UPI_AUTOPAY",
        bank_name="State Bank of India",
        status="ACTIVE",
        max_amount=25000.0,
        created_at=now - timedelta(days=210)
    )
    db.add(mand_b)

    case_b = RecoveryCase(
        id="SR-1025",
        customer_id=cust_b.id,
        subscription_id=sub_b.id,
        mandate_id=mand_b.id,
        amount=9999.0,
        currency="INR",
        failure_reason="Persistent authorization failure / Inactive account",
        failure_code="UNAUTHORIZED",
        attempt_count=1,
        recovery_score=35.0,
        recovery_probability=0.35,
        ai_recommendation="HUMAN_REVIEW",
        ai_explanation="Low recovery score (35/100) due to 5 prior failures and 62 days customer inactivity. Direct automated retry is discouraged.",
        ai_decision_factors=[
            "Poor payment history (5 previous failures, 28% reliability)",
            "Customer inactive for 62 days (high churn risk)",
            "1 prior recovery attempt already failed in current cycle"
        ],
        guardrail_status="ALLOWED",
        current_status=StateConstants.HUMAN_REVIEW,
        stop_reason=StopReasonConstants.HUMAN_REVIEW_REQUIRED,
        initial_failure_at=now - timedelta(days=2),
        created_at=now - timedelta(days=2)
    )
    db.add(case_b)
    db.flush()

    AuditService.record_event(
        db=db,
        recovery_case_id=case_b.id,
        event_type="HUMAN_REVIEW_TRIGGERED",
        description="Low recovery score (35%) routed to operational review",
        actor="RECOVERY_INTELLIGENCE",
        state_after=StateConstants.HUMAN_REVIEW
    )

    review_b = HumanReview(
        id="REV-1002",
        recovery_case_id=case_b.id,
        customer_id=cust_b.id,
        trigger_reason="AI Recovery score below threshold (35/100) - Inactive account",
        status="PENDING",
        created_at=now - timedelta(days=2)
    )
    db.add(review_b)

    # ----------------------------------------------------
    # SCENARIO C: Customer Dispute (Customer C - Apex Retail Logistics)
    # ----------------------------------------------------
    cust_c = Customer(
        id="CUST-1003",
        name="Apex Retail Logistics",
        email="ops@apexlogistics.in",
        phone="+91 97777 88899",
        is_active=True,
        has_dispute=True,
        is_opted_out=False,
        historical_success_count=10,
        historical_failure_count=0,
        last_active_at=now - timedelta(days=1),
        created_at=now - timedelta(days=300)
    )
    db.add(cust_c)

    sub_c = Subscription(
        id="SUB-2003",
        customer_id=cust_c.id,
        plan_name="Supply Chain Enterprise",
        amount=14999.0,
        currency="INR",
        interval="MONTHLY",
        status="ACTIVE",
        created_at=now - timedelta(days=300)
    )
    db.add(sub_c)

    mand_c = Mandate(
        id="MAND-3003",
        subscription_id=sub_c.id,
        mandate_type="ENACH",
        bank_name="ICICI Bank",
        status="ACTIVE",
        max_amount=50000.0,
        created_at=now - timedelta(days=300)
    )
    db.add(mand_c)

    case_c = RecoveryCase(
        id="SR-1026",
        customer_id=cust_c.id,
        subscription_id=sub_c.id,
        mandate_id=mand_c.id,
        amount=14999.0,
        currency="INR",
        failure_reason="Mandate debit contested with card issuing bank",
        failure_code="CUSTOMER_DISPUTE_RAISED",
        attempt_count=0,
        recovery_score=85.0,
        recovery_probability=0.85,
        ai_recommendation="RETRY",
        ai_explanation="Customer has high historical payment reliability. AI recommends retry.",
        ai_decision_factors=[
            "10 successful previous payments (100% historical reliability)",
            "Customer active recently (1 day ago)",
            "High-value subscription (INR 14,999.00)"
        ],
        guardrail_status="BLOCKED",
        guardrail_block_reason="Customer dispute detected. Automatic retries strictly prohibited.",
        guardrail_rules_checked=["attempt_limit", "retry_interval", "recovery_window", "customer_opt_out", "customer_dispute"],
        current_status=StateConstants.HUMAN_REVIEW,
        stop_reason=StopReasonConstants.CUSTOMER_DISPUTED,
        initial_failure_at=now - timedelta(hours=12),
        created_at=now - timedelta(hours=12)
    )
    db.add(case_c)
    db.flush()

    AuditService.record_event(
        db=db,
        recovery_case_id=case_c.id,
        event_type="GUARDRAIL_BLOCKED",
        description="AI recommended RETRY but Guardrail BLOCKED action due to active customer dispute",
        actor="GUARDRAIL_ENGINE",
        state_before=StateConstants.AI_RECOMMENDED,
        state_after=StateConstants.HUMAN_REVIEW,
        metadata={"blocked_reason": "Customer dispute detected"}
    )

    review_c = HumanReview(
        id="REV-1003",
        recovery_case_id=case_c.id,
        customer_id=cust_c.id,
        trigger_reason="Customer disputed recurring charge - Mandate locked",
        status="PENDING",
        created_at=now - timedelta(hours=12)
    )
    db.add(review_c)

    # ----------------------------------------------------
    # SCENARIO D: Successful Recovery (Customer D - CloudScale Analytics)
    # ----------------------------------------------------
    cust_d = Customer(
        id="CUST-1004",
        name="CloudScale Analytics",
        email="billing@cloudscale.ai",
        phone="+91 99000 11223",
        is_active=True,
        has_dispute=False,
        is_opted_out=False,
        historical_success_count=12,
        historical_failure_count=1,
        last_active_at=now - timedelta(days=1),
        created_at=now - timedelta(days=360)
    )
    db.add(cust_d)

    sub_d = Subscription(
        id="SUB-2004",
        customer_id=cust_d.id,
        plan_name="DataOps Scale Tier",
        amount=9999.0,
        currency="INR",
        interval="MONTHLY",
        status="ACTIVE",
        created_at=now - timedelta(days=360)
    )
    db.add(sub_d)

    mand_d = Mandate(
        id="MAND-3004",
        subscription_id=sub_d.id,
        mandate_type="UPI_AUTOPAY",
        bank_name="Axis Bank",
        status="ACTIVE",
        max_amount=30000.0,
        created_at=now - timedelta(days=360)
    )
    db.add(mand_d)

    case_d = RecoveryCase(
        id="SR-1027",
        customer_id=cust_d.id,
        subscription_id=sub_d.id,
        mandate_id=mand_d.id,
        amount=9999.0,
        currency="INR",
        failure_reason="Temporary NPCI switch timeout",
        failure_code="PROCESSING_TIMEOUT",
        attempt_count=0,
        current_status=StateConstants.FAILED,
        initial_failure_at=now - timedelta(hours=4),
        created_at=now - timedelta(hours=4)
    )
    db.add(case_d)

    # ----------------------------------------------------
    # SCENARIO E: Max Attempts Reached (Customer E - Horizon Media Labs)
    # ----------------------------------------------------
    cust_e = Customer(
        id="CUST-1005",
        name="Horizon Media Labs",
        email="accounts@horizonmedia.tv",
        phone="+91 98450 12345",
        is_active=True,
        has_dispute=False,
        is_opted_out=False,
        historical_success_count=8,
        historical_failure_count=3,
        last_active_at=now - timedelta(days=5),
        created_at=now - timedelta(days=240)
    )
    db.add(cust_e)

    sub_e = Subscription(
        id="SUB-2005",
        customer_id=cust_e.id,
        plan_name="Studio Pro Cloud",
        amount=8499.0,
        currency="INR",
        interval="MONTHLY",
        status="ACTIVE",
        created_at=now - timedelta(days=240)
    )
    db.add(sub_e)

    mand_e = Mandate(
        id="MAND-3005",
        subscription_id=sub_e.id,
        mandate_type="ENACH",
        bank_name="Kotak Mahindra Bank",
        status="ACTIVE",
        max_amount=25000.0,
        created_at=now - timedelta(days=240)
    )
    db.add(mand_e)

    case_e = RecoveryCase(
        id="SR-1028",
        customer_id=cust_e.id,
        subscription_id=sub_e.id,
        mandate_id=mand_e.id,
        amount=8499.0,
        currency="INR",
        failure_reason="Insufficient balance on consecutive retries",
        failure_code="INSUFFICIENT_FUNDS",
        attempt_count=2,
        recovery_score=78.0,
        recovery_probability=0.78,
        ai_recommendation="RETRY",
        ai_explanation="Customer has good history, AI suggested retry.",
        guardrail_status="BLOCKED",
        guardrail_block_reason="Maximum retry attempts limit (2) reached.",
        guardrail_rules_checked=["attempt_limit", "retry_interval", "recovery_window", "customer_opt_out", "customer_dispute"],
        current_status=StateConstants.STOPPED,
        stop_reason=StopReasonConstants.MAX_ATTEMPTS_REACHED,
        initial_failure_at=now - timedelta(days=3),
        created_at=now - timedelta(days=3)
    )
    db.add(case_e)

    att_e1 = PaymentAttempt(
        id="ATT-8001",
        recovery_case_id=case_e.id,
        mandate_id=mand_e.id,
        attempt_number=1,
        amount=8499.0,
        status="FAILED",
        failure_code="INSUFFICIENT_FUNDS",
        failure_reason="Insufficient balance",
        created_at=now - timedelta(days=2)
    )
    att_e2 = PaymentAttempt(
        id="ATT-8002",
        recovery_case_id=case_e.id,
        mandate_id=mand_e.id,
        attempt_number=2,
        amount=8499.0,
        status="FAILED",
        failure_code="INSUFFICIENT_FUNDS",
        failure_reason="Insufficient balance",
        created_at=now - timedelta(days=1)
    )
    db.add(att_e1)
    db.add(att_e2)

    # ----------------------------------------------------
    # SCENARIO F: Customer Opt-Out (Customer F - FinPulse Systems)
    # ----------------------------------------------------
    cust_f = Customer(
        id="CUST-1006",
        name="FinPulse Systems",
        email="billing@finpulse.co",
        phone="+91 99887 66554",
        is_active=True,
        has_dispute=False,
        is_opted_out=True,
        historical_success_count=15,
        historical_failure_count=1,
        last_active_at=now - timedelta(days=3),
        created_at=now - timedelta(days=400)
    )
    db.add(cust_f)

    sub_f = Subscription(
        id="SUB-2006",
        customer_id=cust_f.id,
        plan_name="Enterprise Analytics",
        amount=12500.0,
        currency="INR",
        interval="MONTHLY",
        status="ACTIVE",
        created_at=now - timedelta(days=400)
    )
    db.add(sub_f)

    mand_f = Mandate(
        id="MAND-3006",
        subscription_id=sub_f.id,
        mandate_type="ENACH",
        bank_name="HDFC Bank",
        status="ACTIVE",
        max_amount=50000.0,
        created_at=now - timedelta(days=400)
    )
    db.add(mand_f)

    case_f = RecoveryCase(
        id="SR-1029",
        customer_id=cust_f.id,
        subscription_id=sub_f.id,
        mandate_id=mand_f.id,
        amount=12500.0,
        currency="INR",
        failure_reason="Customer opted out of payment recovery automation",
        failure_code="OPT_OUT_RECORDED",
        attempt_count=0,
        recovery_score=88.0,
        recovery_probability=0.88,
        ai_recommendation="RETRY",
        ai_explanation="Customer has high payment history; AI recommends retry.",
        guardrail_status="BLOCKED",
        guardrail_block_reason="Customer has opted out of automated payment retries.",
        guardrail_rules_checked=["attempt_limit", "retry_interval", "recovery_window", "customer_opt_out"],
        current_status=StateConstants.STOPPED,
        stop_reason=StopReasonConstants.CUSTOMER_OPTED_OUT,
        initial_failure_at=now - timedelta(hours=18),
        created_at=now - timedelta(hours=18)
    )
    db.add(case_f)

    # ----------------------------------------------------
    # Additional background volume for dynamic metrics
    # To match target demo values:
    # Recovered revenue: ~27.8L
    # Revenue at risk: ~42.6L
    # Failed mandates: 1,248
    # AI Eligible: ~937
    # Automation stopped: 311 (142 max attempts, 83 disputes, 51 opt outs, 35 human review)
    # ----------------------------------------------------
    print("[SEED] Generating dynamic volume for metrics...")

    # 1. Recovered cohort (approx 550 cases summing to ~27.8L)
    # 550 * 5055 = 2,780,250 INR
    for i in range(1, 551):
        amt = 4000.0 + (i % 25) * 85.0
        c_id = f"CUST-REC-{i:04d}"
        s_id = f"SUB-REC-{i:04d}"
        m_id = f"MAND-REC-{i:04d}"
        case_id = f"SR-REC-{i:04d}"

        cust = Customer(
            id=c_id,
            name=f"Enterprise Client #{i}",
            email=f"client{i}@enterprise-rec.com",
            is_active=True,
            historical_success_count=6 + (i % 10),
            historical_failure_count=1,
            created_at=now - timedelta(days=30 + (i % 60))
        )
        sub = Subscription(id=s_id, customer_id=c_id, plan_name="Business Tier", amount=amt)
        mand = Mandate(id=m_id, subscription_id=s_id, max_amount=amt * 2)
        rc = RecoveryCase(
            id=case_id,
            customer_id=c_id,
            subscription_id=s_id,
            mandate_id=m_id,
            amount=amt,
            failure_reason="Temporary bank debit retry success",
            failure_code="INSUFFICIENT_FUNDS",
            attempt_count=1,
            recovery_score=88.0,
            recovery_probability=0.88,
            ai_recommendation="RETRY",
            guardrail_status="ALLOWED",
            current_status=StateConstants.RECOVERED,
            stop_reason=StopReasonConstants.PAYMENT_RECOVERED,
            initial_failure_at=now - timedelta(days=5 + (i % 20)),
            created_at=now - timedelta(days=5 + (i % 20))
        )
        db.add(cust)
        db.add(sub)
        db.add(mand)
        db.add(rc)

    # 2. Stopped cohort (approx 311 cases: 142 max attempts, 83 disputes, 51 opt outs, 35 human reviews)
    # Stop 1: Max Attempts (141 + case_e = 142)
    for i in range(1, 142):
        amt = 3500.0 + (i % 20) * 100.0
        c_id = f"CUST-MAX-{i:04d}"
        s_id = f"SUB-MAX-{i:04d}"
        m_id = f"MAND-MAX-{i:04d}"
        case_id = f"SR-MAX-{i:04d}"

        cust = Customer(id=c_id, name=f"Subscriber #{i+200}", email=f"sub{i}@maxatt.com", historical_failure_count=4)
        sub = Subscription(id=s_id, customer_id=c_id, plan_name="Growth Tier", amount=amt)
        mand = Mandate(id=m_id, subscription_id=s_id, max_amount=amt * 2)
        rc = RecoveryCase(
            id=case_id,
            customer_id=c_id,
            subscription_id=s_id,
            mandate_id=m_id,
            amount=amt,
            failure_reason="Insufficient balance on retries",
            failure_code="INSUFFICIENT_FUNDS",
            attempt_count=2,
            recovery_score=45.0,
            recovery_probability=0.45,
            ai_recommendation="RETRY",
            guardrail_status="BLOCKED",
            guardrail_block_reason="Maximum retry attempts limit reached",
            current_status=StateConstants.STOPPED,
            stop_reason=StopReasonConstants.MAX_ATTEMPTS_REACHED,
            created_at=now - timedelta(days=4 + (i % 10))
        )
        db.add(cust)
        db.add(sub)
        db.add(mand)
        db.add(rc)

    # Stop 2: Disputes (82 + case_c = 83)
    for i in range(1, 83):
        amt = 4200.0 + (i % 15) * 120.0
        c_id = f"CUST-DISP-{i:04d}"
        s_id = f"SUB-DISP-{i:04d}"
        m_id = f"MAND-DISP-{i:04d}"
        case_id = f"SR-DISP-{i:04d}"

        cust = Customer(id=c_id, name=f"Disputed Account #{i}", email=f"disp{i}@acct.com", has_dispute=True)
        sub = Subscription(id=s_id, customer_id=c_id, plan_name="Pro Tier", amount=amt)
        mand = Mandate(id=m_id, subscription_id=s_id, max_amount=amt * 2)
        rc = RecoveryCase(
            id=case_id,
            customer_id=c_id,
            subscription_id=s_id,
            mandate_id=m_id,
            amount=amt,
            failure_reason="Customer dispute on recurring mandate",
            failure_code="DISPUTED",
            attempt_count=0,
            recovery_score=75.0,
            recovery_probability=0.75,
            ai_recommendation="RETRY",
            guardrail_status="BLOCKED",
            guardrail_block_reason="Customer dispute detected",
            current_status=StateConstants.HUMAN_REVIEW,
            stop_reason=StopReasonConstants.CUSTOMER_DISPUTED,
            created_at=now - timedelta(days=2 + (i % 10))
        )
        rev = HumanReview(
            id=f"REV-DISP-{i:04d}",
            recovery_case_id=case_id,
            customer_id=c_id,
            trigger_reason="Customer dispute detected",
            status="PENDING"
        )
        db.add(cust)
        db.add(sub)
        db.add(mand)
        db.add(rc)
        db.add(rev)

    # Stop 3: Opt-Outs (50 + case_f = 51)
    for i in range(1, 51):
        amt = 3800.0 + (i % 10) * 90.0
        c_id = f"CUST-OPT-{i:04d}"
        s_id = f"SUB-OPT-{i:04d}"
        m_id = f"MAND-OPT-{i:04d}"
        case_id = f"SR-OPT-{i:04d}"

        cust = Customer(id=c_id, name=f"Opted-Out User #{i}", email=f"opt{i}@user.io", is_opted_out=True)
        sub = Subscription(id=s_id, customer_id=c_id, plan_name="Basic Tier", amount=amt)
        mand = Mandate(id=m_id, subscription_id=s_id, max_amount=amt * 2)
        rc = RecoveryCase(
            id=case_id,
            customer_id=c_id,
            subscription_id=s_id,
            mandate_id=m_id,
            amount=amt,
            failure_reason="Customer unsubscribed from recovery automation",
            failure_code="OPT_OUT",
            attempt_count=0,
            recovery_score=60.0,
            recovery_probability=0.60,
            ai_recommendation="NOTIFY",
            guardrail_status="BLOCKED",
            guardrail_block_reason="Customer opted out",
            current_status=StateConstants.STOPPED,
            stop_reason=StopReasonConstants.CUSTOMER_OPTED_OUT,
            created_at=now - timedelta(days=3 + (i % 15))
        )
        db.add(cust)
        db.add(sub)
        db.add(mand)
        db.add(rc)

    # Stop 4: Human Review Required (33 + case_b = 34 + 1 = 35)
    for i in range(1, 34):
        amt = 6000.0 + (i % 10) * 150.0
        c_id = f"CUST-HREV-{i:04d}"
        s_id = f"SUB-HREV-{i:04d}"
        m_id = f"MAND-HREV-{i:04d}"
        case_id = f"SR-HREV-{i:04d}"

        cust = Customer(id=c_id, name=f"Review Candidate #{i}", email=f"hrev{i}@ops.com", is_active=False)
        sub = Subscription(id=s_id, customer_id=c_id, plan_name="Custom Tier", amount=amt)
        mand = Mandate(id=m_id, subscription_id=s_id, max_amount=amt * 2)
        rc = RecoveryCase(
            id=case_id,
            customer_id=c_id,
            subscription_id=s_id,
            mandate_id=m_id,
            amount=amt,
            failure_reason="Low recovery probability / Inactive mandate",
            failure_code="LOW_SCORE",
            attempt_count=1,
            recovery_score=32.0,
            recovery_probability=0.32,
            ai_recommendation="HUMAN_REVIEW",
            guardrail_status="ALLOWED",
            current_status=StateConstants.HUMAN_REVIEW,
            stop_reason=StopReasonConstants.HUMAN_REVIEW_REQUIRED,
            created_at=now - timedelta(days=1 + (i % 5))
        )
        rev = HumanReview(
            id=f"REV-HREV-{i:04d}",
            recovery_case_id=case_id,
            customer_id=c_id,
            trigger_reason="AI score < 40, customer inactive",
            status="PENDING"
        )
        db.add(cust)
        db.add(sub)
        db.add(mand)
        db.add(rc)
        db.add(rev)

    # 3. Active in-flight cases (approx 380 active cases summing up to ~42.6L total revenue at risk)
    # Total cases: 6 + 550 + 141 + 82 + 50 + 33 + 386 = 1,248
    for i in range(1, 387):
        amt = 8500.0 + (i % 40) * 150.0
        c_id = f"CUST-ACT-{i:04d}"
        s_id = f"SUB-ACT-{i:04d}"
        m_id = f"MAND-ACT-{i:04d}"
        case_id = f"SR-ACT-{i:04d}"

        cust = Customer(
            id=c_id,
            name=f"Active Account #{i}",
            email=f"active{i}@company.in",
            is_active=True,
            historical_success_count=5 + (i % 8),
            historical_failure_count=(i % 2),
            last_active_at=now - timedelta(days=i % 10),
            created_at=now - timedelta(days=90 + (i % 180))
        )
        sub = Subscription(id=s_id, customer_id=c_id, plan_name="Enterprise Cloud", amount=amt)
        mand = Mandate(id=m_id, subscription_id=s_id, bank_name="HDFC Bank", max_amount=amt * 2)

        # AI eligible or analyzing
        score = 82.0 if (i % 4 != 0) else 48.0
        rec = "RETRY" if score >= 80 else "NOTIFY"

        rc = RecoveryCase(
            id=case_id,
            customer_id=c_id,
            subscription_id=s_id,
            mandate_id=m_id,
            amount=amt,
            failure_reason="Temporary payment failure / Insufficient balance",
            failure_code="INSUFFICIENT_FUNDS",
            attempt_count=0,
            recovery_score=score,
            recovery_probability=round(score / 100.0, 2),
            ai_recommendation=rec,
            guardrail_status="ALLOWED",
            current_status=StateConstants.AI_RECOMMENDED if (i % 2 == 0) else StateConstants.FAILED,
            initial_failure_at=now - timedelta(hours=1 + (i % 48)),
            created_at=now - timedelta(hours=1 + (i % 48))
        )
        db.add(cust)
        db.add(sub)
        db.add(mand)
        db.add(rc)

    db.commit()
    print(f"[SEED] Successfully seeded database with 1,248 recovery cases!")

    if should_close:
        db.close()

if __name__ == "__main__":
    seed_database()
