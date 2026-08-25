from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.schemas.dtos import (
    AIDecisionResponse,
    StrategyOptimizerResponse,
    RecoveryStrategyConstants
)
from app.core.failure_intelligence import FailureIntelligenceService

class RecoveryDecisionEngine(ABC):
    """
    Abstract interface for Recovery Intelligence.
    Can be implemented deterministically, via classical ML, or with an LLM.
    The AI layer is strictly advisory and NEVER executes transactions.
    """
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> AIDecisionResponse:
        pass

    @abstractmethod
    def optimize_strategy(self, context: Dict[str, Any]) -> StrategyOptimizerResponse:
        pass

class RuleBasedIntelligenceEngine(RecoveryDecisionEngine):
    """
    Deterministic, fully explainable Recovery Intelligence & Strategy Optimizer Engine.
    Computes multi-factor recovery scores (0-100), structured strategies, and expected revenue.
    """

    def evaluate(self, context: Dict[str, Any]) -> AIDecisionResponse:
        """
        Advisory AI evaluation based on customer historical track record and failure telemetry.
        The AI is purely advisory; deterministic policy checks are enforced by GuardrailEngine.
        """
        customer = context.get("customer", {})
        attempts = context.get("attempts", [])
        failure_code = context.get("failure_code", "GENERIC_ERROR")
        is_temporary = context.get("is_temporary", True)
        amount = float(context.get("amount", 0.0))
        last_active_days_ago = context.get("last_active_days_ago", 0)

        # Baseline score calculation
        score = 50.0
        factors: List[str] = []

        # 1. Historical payment track record (up to +30 or -30)
        success_count = int(customer.get("historical_success_count", 0))
        failure_count = int(customer.get("historical_failure_count", 0))
        total_hist = success_count + failure_count

        if total_hist > 0:
            success_ratio = success_count / total_hist
            if success_ratio >= 0.9 and success_count >= 5:
                score += 30.0
                factors.append(f"{success_count} successful previous payments (high loyalty, {int(success_ratio*100)}% reliability)")
            elif success_ratio >= 0.7:
                score += 15.0
                factors.append(f"Consistent payment history ({success_count} of {total_hist} successful)")
            elif success_ratio < 0.4 or failure_count >= 4:
                score -= 30.0
                factors.append(f"Poor payment history ({failure_count} previous failures, {int(success_ratio*100)}% reliability)")
            else:
                score -= 10.0
                factors.append(f"Moderate failure history ({failure_count} failures recorded)")
        else:
            factors.append("New customer mandate (no long-term historical baseline)")

        # 2. Failure categorization (+15 for temporary / -25 for permanent)
        temp_codes = {"INSUFFICIENT_FUNDS", "BANK_NETWORK_TIMEOUT", "TEMPORARY_GATEWAY_ERROR", "PROCESSING_TIMEOUT"}
        hard_codes = {"ACCOUNT_CLOSED", "CARD_EXPIRED", "MANDATE_REVOKED", "INVALID_ACCOUNT", "UNAUTHORIZED"}

        if failure_code in temp_codes or is_temporary:
            score += 15.0
            factors.append("Failure categorized as temporary bank/network issue (high likelihood of clearing)")
        elif failure_code in hard_codes:
            score -= 25.0
            factors.append(f"Permanent failure category ({failure_code}) requires customer credential update")
        else:
            score += 0.0
            factors.append("Standard recurring authorization decline")

        # 3. Customer recency and engagement (+10 or -15)
        if last_active_days_ago <= 7:
            score += 10.0
            factors.append(f"Customer active recently ({last_active_days_ago} days ago)")
        elif last_active_days_ago > 45:
            score -= 15.0
            factors.append(f"Customer inactive for {last_active_days_ago} days (high churn risk)")

        # 4. Subscription value context (+5 for high value)
        if amount >= 10000.0:
            score += 5.0
            factors.append(f"High-value subscription (INR {amount:,.2f})")

        # 5. Prior attempt penalty (-10 per failed attempt in current case)
        attempt_count = max(int(context.get("attempt_count", 0)), len(attempts))
        if attempt_count > 0:
            penalty = min(attempt_count * 10.0, 20.0)
            score -= penalty
            factors.append(f"{attempt_count} prior recovery attempt(s) already failed in current cycle")

        # Bound score between 0 and 100
        score = max(0.0, min(100.0, score))
        probability = round(score / 100.0, 2)

        # Determine advisory recommendation
        if score >= 80.0:
            recommended_action = "RETRY"
            recommended_delay_hours = 24
            explanation = (
                f"Customer demonstrates high payment reliability ({score:.0f}/100) with a temporary failure pattern. "
                f"AI recommends scheduling a retry in 24 hours to maximize recovery probability ({int(probability*100)}%)."
            )
        elif score >= 60.0:
            recommended_action = "RETRY"
            recommended_delay_hours = 24
            explanation = (
                f"Moderate recovery score ({score:.0f}/100). "
                f"AI recommends notifying the customer via email/SMS alongside an automated retry after 24 hours."
            )
        elif score >= 40.0:
            recommended_action = "NOTIFY"
            recommended_delay_hours = 48
            explanation = (
                f"Low-to-moderate recovery score ({score:.0f}/100). Direct automated retry is discouraged without "
                f"first notifying the customer to update payment details or deposit funds."
            )
        else:
            recommended_action = "HUMAN_REVIEW"
            recommended_delay_hours = 0
            explanation = (
                f"Low recovery score ({score:.0f}/100) due to repeated failures or prolonged customer inactivity. "
                f"AI recommends routing to Human Review queue to avoid unnecessary mandate attempts."
            )

        return AIDecisionResponse(
            score=round(score, 1),
            probability=probability,
            recommended_action=recommended_action,
            recommended_delay_hours=recommended_delay_hours,
            explanation=explanation,
            factors=factors
        )

    def optimize_strategy(self, context: Dict[str, Any]) -> StrategyOptimizerResponse:
        customer = context.get("customer", {})
        attempts = context.get("attempts", [])
        attempt_count = max(int(context.get("attempt_count", 0)), len(attempts))
        failure_code = context.get("failure_code", "UNKNOWN_FAILURE")
        is_temporary = context.get("is_temporary", True)
        amount = float(context.get("amount", 0.0))
        last_active_days_ago = context.get("last_active_days_ago", 0)
        has_dispute = bool(customer.get("has_dispute", False))
        is_opted_out = bool(customer.get("is_opted_out", False))
        is_high_risk = bool(customer.get("is_high_risk", False)) or failure_code == "FRAUD_OR_RISK_SIGNAL"

        # 1. Failure Intelligence lookup
        classification = FailureIntelligenceService.get_classification(failure_code)

        score = 50.0
        positive_factors: List[str] = []
        negative_factors: List[str] = []
        reasoning: List[str] = []

        # 2. Historical Track Record
        success_count = int(customer.get("historical_success_count", 0))
        failure_count = int(customer.get("historical_failure_count", 0))
        total_hist = success_count + failure_count

        if total_hist > 0:
            success_ratio = success_count / total_hist
            if success_ratio >= 0.9 and success_count >= 5:
                score += 30.0
                positive_factors.append(f"{success_count} successful previous payments ({int(success_ratio*100)}% historical reliability)")
            elif success_ratio >= 0.7:
                score += 15.0
                positive_factors.append(f"Consistent payment track record ({success_count} of {total_hist} successful)")
            elif success_ratio < 0.4 or failure_count >= 4:
                score -= 30.0
                negative_factors.append(f"Poor payment history ({failure_count} historical failures, {int(success_ratio*100)}% reliability)")
            else:
                score -= 10.0
                negative_factors.append(f"Moderate failure history ({failure_count} failures recorded)")
        else:
            reasoning.append("New customer mandate (no long-term historical baseline)")

        # 3. Failure Severity & Classification Impact
        if classification.code in ["BANK_NETWORK_TIMEOUT", "PROCESSING_TIMEOUT"]:
            score += 20.0
            positive_factors.append("Transient infrastructure timeout; underlying account is in good standing")
        elif classification.code == "INSUFFICIENT_FUNDS":
            score += 5.0
            reasoning.append("Temporary balance shortfall. Recoverable with timely customer notification")
        elif classification.code in ["MANDATE_EXPIRED", "PAYMENT_METHOD_INVALID"]:
            score -= 25.0
            negative_factors.append(f"Mandate / Payment method issue ({classification.name}) requires credential re-authentication")
        elif classification.code in ["CUSTOMER_DISPUTE", "FRAUD_OR_RISK_SIGNAL"]:
            score -= 45.0
            negative_factors.append(f"Active risk / dispute signal ({classification.name})")

        # 4. Customer Engagement Recency
        if last_active_days_ago <= 7:
            score += 10.0
            positive_factors.append(f"Customer active recently ({last_active_days_ago} days ago)")
        elif last_active_days_ago > 45:
            score -= 15.0
            negative_factors.append(f"Customer inactive for {last_active_days_ago} days (high churn risk)")

        # 5. Prior Attempt Penalties
        if attempt_count > 0:
            penalty = min(attempt_count * 15.0, 30.0)
            score -= penalty
            negative_factors.append(f"{attempt_count} recovery attempt(s) already failed in current cycle")

        # 6. High Value context
        if amount >= 10000.0:
            positive_factors.append(f"High-value subscription (INR {amount:,.2f}) prioritizes revenue retention")

        # 7. Dispute / Opt-out Hard Triggers
        if has_dispute:
            negative_factors.append("Active customer dispute registered against recurring charge")
        if is_opted_out:
            negative_factors.append("Customer opted out of payment recovery automation")
        if is_high_risk:
            negative_factors.append("Account flagged for high risk or compliance review")

        score = max(0.0, min(100.0, score))
        probability = round(score / 100.0, 2)
        expected_recovery_amount = round(amount * probability, 2)

        # Confidence calculation
        confidence = 0.70
        if total_hist >= 5:
            confidence += 0.15
        if last_active_days_ago <= 14:
            confidence += 0.10
        if attempt_count >= 1:
            confidence += 0.04
        confidence = min(0.98, round(confidence, 2))

        # Determine Structured Strategy
        if has_dispute or is_opted_out or is_high_risk:
            strategy = RecoveryStrategyConstants.STOP_RECOVERY
            strategy_label = "Stop Recovery (Safety Lock)"
            recommended_delay_hours = 0
            human_review_required = True
            risk_level = "CRITICAL"
            reasoning.append("Deterministic policy mandates halting automated recovery due to active dispute or risk flag.")
        elif attempt_count >= 2 or failure_code == "REPEATED_FAILURE":
            strategy = RecoveryStrategyConstants.STOP_RECOVERY
            strategy_label = "Stop Recovery (Max Retries Reached)"
            recommended_delay_hours = 0
            human_review_required = True
            risk_level = "HIGH"
            reasoning.append("Maximum retry attempts limit reached (2 attempts). Escrowing case for human review.")
        elif classification.code == "MANDATE_EXPIRED":
            strategy = RecoveryStrategyConstants.REQUEST_MANDATE_REAUTHORIZATION
            strategy_label = "Request Mandate Re-Authorization"
            recommended_delay_hours = 0
            human_review_required = True
            risk_level = "HIGH"
            reasoning.append("Mandate expired. Automated retries will fail. Sending re-authorization link to customer.")
        elif classification.code == "PAYMENT_METHOD_INVALID":
            strategy = RecoveryStrategyConstants.REQUEST_PAYMENT_METHOD_UPDATE
            strategy_label = "Request Payment Method Update"
            recommended_delay_hours = 0
            human_review_required = True
            risk_level = "HIGH"
            reasoning.append("Card/account invalid. Prompting customer to register a new payment method.")
        elif classification.code == "INSUFFICIENT_FUNDS":
            strategy = RecoveryStrategyConstants.SEND_PAYMENT_REMINDER
            strategy_label = "Send Payment Reminder + Retry in 48h"
            recommended_delay_hours = 48
            human_review_required = False
            risk_level = "MEDIUM"
            reasoning.append("Balance shortfall. Recommended action is gentle payment reminder followed by a 48h retry.")
        elif classification.code in ["PROCESSING_TIMEOUT", "BANK_NETWORK_TIMEOUT"]:
            strategy = RecoveryStrategyConstants.RETRY_AFTER_24H
            strategy_label = "Retry After 24 Hours"
            recommended_delay_hours = 24
            human_review_required = False
            risk_level = "LOW"
            reasoning.append("Gateway/Bank processing timeout. Standard 24h retry provides optimal clearance.")
        elif score >= 80.0:
            strategy = RecoveryStrategyConstants.RETRY_AFTER_24H
            strategy_label = "Retry After 24 Hours"
            recommended_delay_hours = 24
            human_review_required = False
            risk_level = "LOW"
            reasoning.append("High recovery probability customer. Standard 24h retry cooldown provides optimal clearance.")
        elif score >= 60.0:
            strategy = RecoveryStrategyConstants.RETRY_AFTER_24H
            strategy_label = "Notify Customer + Retry in 24h"
            recommended_delay_hours = 24
            human_review_required = False
            risk_level = "MEDIUM"
            reasoning.append("Moderate recovery score. Recommend dual email notification and automated 24h retry.")
        elif score >= 40.0:
            strategy = RecoveryStrategyConstants.SEND_PAYMENT_REMINDER
            strategy_label = "Send Payment Reminder"
            recommended_delay_hours = 48
            human_review_required = False
            risk_level = "MEDIUM"
            reasoning.append("Low recovery probability. Advise sending payment reminder before any further debit attempts.")
        else:
            strategy = RecoveryStrategyConstants.HUMAN_REVIEW
            strategy_label = "Route to Human Review"
            recommended_delay_hours = 0
            human_review_required = True
            risk_level = "HIGH"
            reasoning.append("Low recovery score (<40%) or inactive customer. Manual operator intervention recommended.")

        # Guardrail precheck advisory
        guardrail_precheck_status = "ALLOWED"
        guardrail_precheck_reason = None
        if has_dispute:
            guardrail_precheck_status = "BLOCKED"
            guardrail_precheck_reason = "Active customer dispute will be blocked by Guardrail Rule 5"
        elif is_opted_out:
            guardrail_precheck_status = "BLOCKED"
            guardrail_precheck_reason = "Customer opt-out will be blocked by Guardrail Rule 4"
        elif attempt_count >= 2:
            guardrail_precheck_status = "BLOCKED"
            guardrail_precheck_reason = "Attempt limit will be blocked by Guardrail Rule 1"
        elif human_review_required:
            guardrail_precheck_status = "REVIEW_REQUIRED"
            guardrail_precheck_reason = "Case flagged for operational review before automated action"

        case_id = str(context.get("case_id", "SR-SIM"))

        return StrategyOptimizerResponse(
            case_id=case_id,
            strategy=strategy,
            strategy_label=strategy_label,
            recovery_score=round(score, 1),
            estimated_success_probability=probability,
            expected_recovery_amount=expected_recovery_amount,
            confidence=confidence,
            recommended_delay_hours=recommended_delay_hours,
            reasoning=reasoning,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            risk_level=risk_level,
            human_review_required=human_review_required,
            guardrail_precheck_status=guardrail_precheck_status,
            guardrail_precheck_reason=guardrail_precheck_reason
        )

def get_intelligence_engine() -> RecoveryDecisionEngine:
    return RuleBasedIntelligenceEngine()
