from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.schemas.dtos import GuardrailDecisionResponse, RuleCheckDetail, StateConstants, StopReasonConstants

class GuardrailEngine:
    """
    Authoritative, deterministic safety guardrail engine.
    The AI layer is advisory only; GuardrailEngine is solely authorized to allow/block recovery actions.
    """

    MAX_RETRY_ATTEMPTS = 2
    MIN_RETRY_INTERVAL_HOURS = 24
    MAX_RECOVERY_WINDOW_DAYS = 7

    @classmethod
    def evaluate(cls, case_data: Dict[str, Any], proposed_action: str = "RETRY_PAYMENT") -> GuardrailDecisionResponse:
        """
        Evaluate all 10 deterministic guardrail rules against the current case and customer state.
        """
        rules_checked: List[RuleCheckDetail] = []
        is_blocked = False
        blocked_reason: Optional[str] = None
        stop_reason: Optional[str] = None

        customer = case_data.get("customer", {})
        attempts = case_data.get("payment_attempts", [])
        current_status = case_data.get("current_status", StateConstants.FAILED)
        initial_failure_at = case_data.get("initial_failure_at")
        last_attempt_at = case_data.get("last_attempt_at")
        attempt_count = int(case_data.get("attempt_count", len(attempts)))

        now = datetime.now(timezone.utc)
        if isinstance(initial_failure_at, str):
            try:
                initial_failure_at = datetime.fromisoformat(initial_failure_at.replace("Z", "+00:00"))
            except Exception:
                initial_failure_at = now
        elif initial_failure_at is None:
            initial_failure_at = now
        elif initial_failure_at.tzinfo is None:
            initial_failure_at = initial_failure_at.replace(tzinfo=timezone.utc)

        if isinstance(last_attempt_at, str):
            try:
                last_attempt_at = datetime.fromisoformat(last_attempt_at.replace("Z", "+00:00"))
            except Exception:
                last_attempt_at = None
        elif last_attempt_at is not None and last_attempt_at.tzinfo is None:
            last_attempt_at = last_attempt_at.replace(tzinfo=timezone.utc)

        # RULE 7: Already Recovered / Successful Payment Check
        rule_already_recovered = (current_status == StateConstants.RECOVERED)
        rules_checked.append(RuleCheckDetail(
            rule_name="payment_success_state",
            passed=not rule_already_recovered,
            description="Mandate not already recovered",
            details="Case is already in RECOVERED state" if rule_already_recovered else "Payment recovery still pending"
        ))
        if rule_already_recovered and not is_blocked:
            is_blocked = True
            blocked_reason = "Payment already successfully recovered. Workflow is stopped."
            stop_reason = StopReasonConstants.PAYMENT_RECOVERED

        # RULE 4: Customer Opt-Out Check
        is_opted_out = bool(customer.get("is_opted_out", False))
        rules_checked.append(RuleCheckDetail(
            rule_name="customer_opt_out",
            passed=not is_opted_out,
            description="Customer opted-in for recovery automation",
            details="Customer explicitly opted out of payment recovery" if is_opted_out else "Customer active and opted in"
        ))
        if is_opted_out and not is_blocked:
            is_blocked = True
            blocked_reason = "Customer has opted out of automated payment retries."
            stop_reason = StopReasonConstants.CUSTOMER_OPTED_OUT

        # RULE 5: Customer Dispute Check
        has_dispute = bool(customer.get("has_dispute", False))
        rules_checked.append(RuleCheckDetail(
            rule_name="customer_dispute",
            passed=not has_dispute,
            description="No customer dispute active on mandate/account",
            details="Customer dispute detected on recurring charge" if has_dispute else "Account clean with no disputes"
        ))
        if has_dispute and not is_blocked:
            is_blocked = True
            blocked_reason = "Active customer dispute detected. Automatic retries strictly prohibited."
            stop_reason = StopReasonConstants.CUSTOMER_DISPUTED

        # RULE 1: Maximum Retry Attempts Check (Max 2)
        attempts_exceeded = (attempt_count >= cls.MAX_RETRY_ATTEMPTS)
        rules_checked.append(RuleCheckDetail(
            rule_name="attempt_limit",
            passed=not attempts_exceeded,
            description=f"Attempt count ({attempt_count}) within limit (max {cls.MAX_RETRY_ATTEMPTS})",
            details=f"{attempt_count} attempts executed out of {cls.MAX_RETRY_ATTEMPTS} allowed"
        ))
        if attempts_exceeded and not is_blocked:
            is_blocked = True
            blocked_reason = f"Maximum retry attempts limit ({cls.MAX_RETRY_ATTEMPTS}) reached."
            stop_reason = StopReasonConstants.MAX_ATTEMPTS_REACHED

        # RULE 3 & RULE 10: Maximum Recovery Window Check (7 Days)
        window_elapsed = (now - initial_failure_at).total_seconds() / 86400.0
        window_expired = (window_elapsed > cls.MAX_RECOVERY_WINDOW_DAYS)
        rules_checked.append(RuleCheckDetail(
            rule_name="recovery_window",
            passed=not window_expired,
            description=f"Case within {cls.MAX_RECOVERY_WINDOW_DAYS}-day recovery window ({window_elapsed:.1f} days elapsed)",
            details="Recovery window expired" if window_expired else "Window active"
        ))
        if window_expired and not is_blocked:
            is_blocked = True
            blocked_reason = f"Maximum recovery window of {cls.MAX_RECOVERY_WINDOW_DAYS} days has expired."
            stop_reason = StopReasonConstants.RECOVERY_WINDOW_EXPIRED

        # RULE 2: Minimum Retry Interval Check (24 Hours between payment attempts)
        interval_violated = False
        hours_since_last = None
        if proposed_action == "RETRY_PAYMENT" and last_attempt_at is not None:
            hours_since_last = (now - last_attempt_at).total_seconds() / 3600.0
            if hours_since_last < cls.MIN_RETRY_INTERVAL_HOURS:
                interval_violated = True

        rules_checked.append(RuleCheckDetail(
            rule_name="retry_interval",
            passed=not interval_violated,
            description=f"Minimum {cls.MIN_RETRY_INTERVAL_HOURS}h interval between retries",
            details=f"Last attempt was {hours_since_last:.1f}h ago (minimum {cls.MIN_RETRY_INTERVAL_HOURS}h required)" if hours_since_last is not None else "First retry attempt in cycle"
        ))
        if interval_violated and not is_blocked:
            is_blocked = True
            blocked_reason = f"Minimum retry cooldown of {cls.MIN_RETRY_INTERVAL_HOURS} hours has not elapsed ({hours_since_last:.1f}h elapsed)."
            stop_reason = None  # Not a terminal stop, but blocked until interval expires

        # RULE 9: Human Review Exclusivity
        if current_status == StateConstants.HUMAN_REVIEW and proposed_action == "RETRY_PAYMENT":
            rules_checked.append(RuleCheckDetail(
                rule_name="human_review_lock",
                passed=False,
                description="Cases in Human Review cannot be automatically retried",
                details="Manual operator resolution required"
            ))
            if not is_blocked:
                is_blocked = True
                blocked_reason = "Case is flagged for Human Review. Automatic execution is locked."
                stop_reason = StopReasonConstants.HUMAN_REVIEW_REQUIRED

        # Status outcome
        status = "BLOCKED" if is_blocked else "ALLOWED"
        allowed = not is_blocked

        return GuardrailDecisionResponse(
            allowed=allowed,
            status=status,
            blocked_reason=blocked_reason,
            stop_reason=stop_reason,
            rules_checked=rules_checked
        )
