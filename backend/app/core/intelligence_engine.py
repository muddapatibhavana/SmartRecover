from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timezone
from app.schemas.dtos import AIDecisionResponse

class RecoveryDecisionEngine(ABC):
    """
    Abstract interface for Recovery Intelligence.
    Can be implemented deterministically, via classical ML, or with an LLM.
    The AI layer is strictly advisory and NEVER executes transactions.
    """
    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> AIDecisionResponse:
        pass

class RuleBasedIntelligenceEngine(RecoveryDecisionEngine):
    """
    Deterministic, fully explainable Recovery Intelligence Engine.
    Computes a multi-factor recovery score (0-100) and yields advisory recommendations.
    """

    def evaluate(self, context: Dict[str, Any]) -> AIDecisionResponse:
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
        attempt_count = len(attempts)
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

# Factory helper
def get_intelligence_engine() -> RecoveryDecisionEngine:
    return RuleBasedIntelligenceEngine()
