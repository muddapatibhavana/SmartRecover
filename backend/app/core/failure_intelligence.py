from typing import Dict, List, Optional
from app.schemas.dtos import FailureClassificationDetail, RecoveryStrategyConstants

class FailureIntelligenceService:
    """
    Failure-Reason Intelligence:
    Categorizes payment failure codes, calculates historical recovery likelihood,
    and maps failure types to optimal recovery strategies and communication guidelines.
    """

    CATALOG: Dict[str, FailureClassificationDetail] = {
        "BANK_NETWORK_TIMEOUT": FailureClassificationDetail(
            code="BANK_NETWORK_TIMEOUT",
            name="Bank Network Timeout",
            category="INFRASTRUCTURE",
            description="Transient network timeout or switch latency between sponsor bank and issuing bank switch.",
            retry_suitable=True,
            preferred_strategy=RecoveryStrategyConstants.RETRY_AFTER_24H,
            recommended_delay_hours=24,
            communication_recommendation="Silent automated retry. No customer friction necessary.",
            risk_level="LOW",
            human_review_required=False,
            historical_recovery_rate=0.88,
            explanation_template="Temporary bank switch timeout. High historical recovery probability (88%) on next-day retry."
        ),
        "PROCESSING_TIMEOUT": FailureClassificationDetail(
            code="PROCESSING_TIMEOUT",
            name="Processing Gateway Timeout",
            category="INFRASTRUCTURE",
            description="NPCI or payment gateway internal queue timeout during mandate batch processing.",
            retry_suitable=True,
            preferred_strategy=RecoveryStrategyConstants.RETRY_AFTER_24H,
            recommended_delay_hours=24,
            communication_recommendation="Silent retry. System will retry automatically during off-peak processing hours.",
            risk_level="LOW",
            human_review_required=False,
            historical_recovery_rate=0.85,
            explanation_template="Gateway batch processing timeout. Standard 24h retry window delivers optimal clearance."
        ),
        "INSUFFICIENT_FUNDS": FailureClassificationDetail(
            code="INSUFFICIENT_FUNDS",
            name="Insufficient Balance",
            category="CUSTOMER_FINANCIAL",
            description="Customer account balance below recurring mandate debit requirement.",
            retry_suitable=True,
            preferred_strategy=RecoveryStrategyConstants.SEND_PAYMENT_REMINDER,
            recommended_delay_hours=48,
            communication_recommendation="Send gentle payment reminder via SMS & WhatsApp prompting balance top-up prior to retry.",
            risk_level="MEDIUM",
            human_review_required=False,
            historical_recovery_rate=0.68,
            explanation_template="Customer balance shortfall. Recommending payment reminder followed by a 48-hour retry to allow salary/fund deposit."
        ),
        "MANDATE_EXPIRED": FailureClassificationDetail(
            code="MANDATE_EXPIRED",
            name="Mandate Expired / Revoked",
            category="MANDATE_LIFECYCLE",
            description="E-NACH or UPI AutoPay mandate validity period has elapsed or authorization has expired.",
            retry_suitable=False,
            preferred_strategy=RecoveryStrategyConstants.REQUEST_MANDATE_REAUTHORIZATION,
            recommended_delay_hours=0,
            communication_recommendation="Send mandate re-authentication link (UPI AutoPay / NetBanking) to customer.",
            risk_level="HIGH",
            human_review_required=True,
            historical_recovery_rate=0.45,
            explanation_template="Mandate is legally expired. Automated retries will fail. Re-authorization link required."
        ),
        "PAYMENT_METHOD_INVALID": FailureClassificationDetail(
            code="PAYMENT_METHOD_INVALID",
            name="Payment Method Invalid / Closed",
            category="CREDENTIAL",
            description="Underlying card expired or bank account flagged as frozen / closed.",
            retry_suitable=False,
            preferred_strategy=RecoveryStrategyConstants.REQUEST_PAYMENT_METHOD_UPDATE,
            recommended_delay_hours=0,
            communication_recommendation="Send urgent notification to update billing instrument before subscription termination.",
            risk_level="HIGH",
            human_review_required=True,
            historical_recovery_rate=0.40,
            explanation_template="Payment method invalid or inactive. Automatic retries prohibited until credentials are updated."
        ),
        "CUSTOMER_DISPUTE": FailureClassificationDetail(
            code="CUSTOMER_DISPUTE",
            name="Customer Charge Dispute",
            category="DISPUTE_FRAUD",
            description="Customer raised a chargeback or dispute contesting recurring mandate authorization.",
            retry_suitable=False,
            preferred_strategy=RecoveryStrategyConstants.STOP_RECOVERY,
            recommended_delay_hours=0,
            communication_recommendation="Prohibit automated recovery. Escalate immediately to Billing Operations & Legal.",
            risk_level="CRITICAL",
            human_review_required=True,
            historical_recovery_rate=0.0,
            explanation_template="Active customer dispute detected. Guardrail safety rules strictly prohibit automated debit."
        ),
        "FRAUD_OR_RISK_SIGNAL": FailureClassificationDetail(
            code="FRAUD_OR_RISK_SIGNAL",
            name="Fraud or High Risk Anomaly",
            category="DISPUTE_FRAUD",
            description="Account flagged for velocity anomalies, synthetic identity signals, or compliance sanctions.",
            retry_suitable=False,
            preferred_strategy=RecoveryStrategyConstants.STOP_RECOVERY,
            recommended_delay_hours=0,
            communication_recommendation="Lock mandate. Route to Fraud & Risk Investigation Unit.",
            risk_level="CRITICAL",
            human_review_required=True,
            historical_recovery_rate=0.0,
            explanation_template="Risk compliance anomaly. Automated execution locked; manual risk review mandated."
        ),
        "REPEATED_FAILURE": FailureClassificationDetail(
            code="REPEATED_FAILURE",
            name="Maximum Attempts Reached",
            category="CYCLE_LIMIT",
            description="Recurring payment failed multiple consecutive times within the current 7-day recovery window.",
            retry_suitable=False,
            preferred_strategy=RecoveryStrategyConstants.STOP_RECOVERY,
            recommended_delay_hours=0,
            communication_recommendation="Automated retry quota exhausted (2 attempts max). Route to account executive.",
            risk_level="HIGH",
            human_review_required=True,
            historical_recovery_rate=0.15,
            explanation_template="Maximum recovery attempts reached. Workflow stopped automatically to protect customer trust."
        ),
        "UNKNOWN_FAILURE": FailureClassificationDetail(
            code="UNKNOWN_FAILURE",
            name="Unclassified Payment Failure",
            category="GENERIC",
            description="Non-standard bank decline or unrecognized switch code.",
            retry_suitable=True,
            preferred_strategy=RecoveryStrategyConstants.RETRY_AFTER_24H,
            recommended_delay_hours=24,
            communication_recommendation="Standard payment notification with 24h retry schedule.",
            risk_level="MEDIUM",
            human_review_required=False,
            historical_recovery_rate=0.55,
            explanation_template="Unclassified decline. Conservative 24h retry cooldown recommended with monitoring."
        )
    }

    @classmethod
    def get_classification(cls, failure_code: Optional[str]) -> FailureClassificationDetail:
        if not failure_code:
            return cls.CATALOG["UNKNOWN_FAILURE"]

        normalized = failure_code.strip().upper()
        if normalized in cls.CATALOG:
            return cls.CATALOG[normalized]

        # Fuzzy mapping for partial match
        if "TIMEOUT" in normalized or "BANK" in normalized:
            return cls.CATALOG["BANK_NETWORK_TIMEOUT"]
        elif "INSUFFICIENT" in normalized or "BALANCE" in normalized:
            return cls.CATALOG["INSUFFICIENT_FUNDS"]
        elif "DISPUTE" in normalized or "CONTESTED" in normalized:
            return cls.CATALOG["CUSTOMER_DISPUTE"]
        elif "EXPIRED" in normalized or "REVOKED" in normalized:
            return cls.CATALOG["MANDATE_EXPIRED"]
        elif "FRAUD" in normalized or "RISK" in normalized or "BLOCKED" in normalized:
            return cls.CATALOG["FRAUD_OR_RISK_SIGNAL"]
        elif "INVALID" in normalized or "CLOSED" in normalized or "CARD" in normalized:
            return cls.CATALOG["PAYMENT_METHOD_INVALID"]

        return cls.CATALOG["UNKNOWN_FAILURE"]

    @classmethod
    def get_all_classifications(cls) -> List[FailureClassificationDetail]:
        return list(cls.CATALOG.values())

    @classmethod
    def generate_explanation(
        cls,
        failure_code: str,
        customer_success_count: int,
        customer_failure_count: int,
        recommended_strategy: str
    ) -> str:
        classification = cls.get_classification(failure_code)
        total = customer_success_count + customer_failure_count
        reliability = int((customer_success_count / total * 100)) if total > 0 else 0

        return (
            f"Failure classified as {classification.name} ({classification.risk_level} risk). "
            f"Customer has a track record of {customer_success_count}/{total} successful debits ({reliability}% reliability). "
            f"{classification.explanation_template} Strategy {recommended_strategy} selected."
        )
