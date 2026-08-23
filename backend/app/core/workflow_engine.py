import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.entities import (
    RecoveryCase, Customer, Subscription, Mandate, PaymentAttempt,
    RecoveryAction, GuardrailEvent, AuditLog
)
from app.schemas.dtos import (
    StateConstants, StopReasonConstants, AIDecisionResponse,
    GuardrailDecisionResponse, DualDecisionView, ExecuteActionResponse
)
from app.core.intelligence_engine import get_intelligence_engine
from app.core.guardrail_engine import GuardrailEngine
from app.core.payment_simulator import PaymentSimulator
from app.core.audit_service import AuditService
from app.core.human_review_service import HumanReviewService

logger = logging.getLogger("smartrecover.workflow")

class RecoveryWorkflowEngine:
    """
    Authoritative state machine orchestrator for failed recurring payment recovery.
    Enforces that AI is advisory only, Guardrails are deterministic, and Safe Stopping is guaranteed.
    """

    # Legal state transitions map
    VALID_TRANSITIONS = {
        StateConstants.FAILED: {
            StateConstants.ANALYZING, StateConstants.GUARDRAIL_CHECK, StateConstants.RETRYING,
            StateConstants.HUMAN_REVIEW, StateConstants.STOPPED
        },
        StateConstants.ANALYZING: {
            StateConstants.AI_RECOMMENDED, StateConstants.HUMAN_REVIEW, StateConstants.STOPPED, StateConstants.ANALYZING
        },
        StateConstants.AI_RECOMMENDED: {
            StateConstants.GUARDRAIL_CHECK, StateConstants.HUMAN_REVIEW, StateConstants.STOPPED, StateConstants.ANALYZING
        },
        StateConstants.GUARDRAIL_CHECK: {
            StateConstants.ACTION_ALLOWED, StateConstants.ACTION_BLOCKED, StateConstants.RETRYING,
            StateConstants.HUMAN_REVIEW, StateConstants.STOPPED, StateConstants.ANALYZING
        },
        StateConstants.ACTION_ALLOWED: {
            StateConstants.RETRY_SCHEDULED, StateConstants.RETRYING, StateConstants.NOTIFICATION_SENT,
            StateConstants.HUMAN_REVIEW, StateConstants.STOPPED, StateConstants.ANALYZING
        },
        StateConstants.ACTION_BLOCKED: {
            StateConstants.HUMAN_REVIEW, StateConstants.STOPPED, StateConstants.ANALYZING, StateConstants.GUARDRAIL_CHECK
        },
        StateConstants.RETRY_SCHEDULED: {
            StateConstants.RETRYING, StateConstants.HUMAN_REVIEW, StateConstants.STOPPED, StateConstants.ANALYZING
        },
        StateConstants.RETRYING: {
            StateConstants.RECOVERED, StateConstants.FAILED, StateConstants.HUMAN_REVIEW, StateConstants.STOPPED,
            StateConstants.RETRY_SCHEDULED
        },
        StateConstants.NOTIFICATION_SENT: {
            StateConstants.RETRY_SCHEDULED, StateConstants.RETRYING, StateConstants.HUMAN_REVIEW, StateConstants.STOPPED
        },
        # Terminal states - can only be reopened by human operator or explicit demo reset
        StateConstants.RECOVERED: {StateConstants.STOPPED},
        StateConstants.HUMAN_REVIEW: {StateConstants.STOPPED, StateConstants.ANALYZING, StateConstants.RETRY_SCHEDULED},
        StateConstants.STOPPED: {StateConstants.ANALYZING, StateConstants.FAILED}  # Allow reset in demo harness
    }

    @classmethod
    def transition_state(
        cls,
        db: Session,
        case: RecoveryCase,
        new_status: str,
        reason: str,
        actor: str = "SYSTEM",
        metadata: Optional[Dict[str, Any]] = None
    ) -> RecoveryCase:
        """
        Validate and execute an explicit state transition with an immutable audit log.
        """
        old_status = case.current_status
        allowed_next = cls.VALID_TRANSITIONS.get(old_status, set())

        if new_status not in allowed_next and old_status != new_status:
            error_msg = f"Invalid state transition attempted: from '{old_status}' to '{new_status}'"
            logger.error(error_msg)
            raise ValueError(error_msg)

        case.current_status = new_status
        case.updated_at = datetime.now(timezone.utc)

        AuditService.record_event(
            db=db,
            recovery_case_id=case.id,
            event_type="STATE_TRANSITION",
            description=f"State transitioned from {old_status} to {new_status}: {reason}",
            actor=actor,
            state_before=old_status,
            state_after=new_status,
            metadata=metadata
        )
        db.flush()
        return case

    @classmethod
    def analyze_case(cls, db: Session, case_id: str) -> Dict[str, Any]:
        """
        Full analysis pipeline:
        1. Context extraction
        2. Advisory AI Scoring & Recommendations
        3. Authoritative Guardrail validation
        4. State updates and stopping trigger evaluations
        """
        case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            raise ValueError(f"Recovery case {case_id} not found")

        customer = case.customer
        attempts = case.payment_attempts

        # Step 1: Transition to ANALYZING
        cls.transition_state(
            db=db,
            case=case,
            new_status=StateConstants.ANALYZING,
            reason="Initiating recovery intelligence evaluation and risk scoring",
            actor="SYSTEM"
        )

        # Step 2: Compute context
        now = datetime.now(timezone.utc)
        last_active = customer.last_active_at or customer.created_at
        if last_active and last_active.tzinfo is None:
            last_active = last_active.replace(tzinfo=timezone.utc)
        days_inactive = max(0, (now - (last_active or now)).days)

        context = {
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "historical_success_count": customer.historical_success_count,
                "historical_failure_count": customer.historical_failure_count,
                "is_active": customer.is_active,
                "has_dispute": customer.has_dispute,
                "is_opted_out": customer.is_opted_out,
            },
            "attempts": attempts,
            "failure_code": case.failure_code,
            "is_temporary": True if "INSUFFICIENT" in case.failure_code or "TIMEOUT" in case.failure_code or "TEMPORARY" in case.failure_code else False,
            "amount": case.amount,
            "last_active_days_ago": days_inactive
        }

        # Step 3: Run Advisory Intelligence Engine
        ai_engine = get_intelligence_engine()
        ai_res = ai_engine.evaluate(context)

        case.recovery_score = ai_res.score
        case.recovery_probability = ai_res.probability
        case.ai_recommendation = ai_res.recommended_action
        case.ai_recommended_delay_hours = ai_res.recommended_delay_hours
        case.ai_explanation = ai_res.explanation
        case.ai_decision_factors = ai_res.factors

        cls.transition_state(
            db=db,
            case=case,
            new_status=StateConstants.AI_RECOMMENDED,
            reason=f"AI recommended {ai_res.recommended_action} with recovery score {ai_res.score:.1f}/100",
            actor="RECOVERY_INTELLIGENCE",
            metadata={
                "score": ai_res.score,
                "probability": ai_res.probability,
                "recommendation": ai_res.recommended_action,
                "factors": ai_res.factors
            }
        )

        # Step 4: Run Guardrail Engine
        cls.transition_state(
            db=db,
            case=case,
            new_status=StateConstants.GUARDRAIL_CHECK,
            reason="Submitting AI recommendation to GuardrailEngine for compliance verification",
            actor="SYSTEM"
        )

        last_attempt_time = attempts[-1].created_at if attempts else None
        case_data_for_guardrails = {
            "customer": {
                "is_opted_out": customer.is_opted_out,
                "has_dispute": customer.has_dispute,
            },
            "payment_attempts": attempts,
            "attempt_count": case.attempt_count,
            "current_status": case.current_status,
            "initial_failure_at": case.initial_failure_at,
            "last_attempt_at": last_attempt_time
        }

        proposed_act = "RETRY_PAYMENT" if ai_res.recommended_action in ["RETRY", "NOTIFY"] else "ROUTE_HUMAN_REVIEW"
        guardrail_res = GuardrailEngine.evaluate(case_data_for_guardrails, proposed_action=proposed_act)

        # Record Guardrail Event
        guardrail_event_id = f"GR-{uuid.uuid4().hex[:8].upper()}"
        gr_event = GuardrailEvent(
            id=guardrail_event_id,
            recovery_case_id=case.id,
            action_type=proposed_act,
            allowed=guardrail_res.allowed,
            status=guardrail_res.status,
            blocked_reason=guardrail_res.blocked_reason,
            stop_reason=guardrail_res.stop_reason,
            rules_checked_json=json.dumps([r.model_dump() for r in guardrail_res.rules_checked]),
            evaluated_at=now
        )
        db.add(gr_event)

        case.guardrail_status = guardrail_res.status
        case.guardrail_block_reason = guardrail_res.blocked_reason
        case.guardrail_rules_checked = [r.rule_name for r in guardrail_res.rules_checked]

        if guardrail_res.allowed:
            cls.transition_state(
                db=db,
                case=case,
                new_status=StateConstants.ACTION_ALLOWED,
                reason=f"Guardrail verification PASSED for {proposed_act}",
                actor="GUARDRAIL_ENGINE",
                metadata={"rules_passed": len(guardrail_res.rules_checked)}
            )
            case.next_action = proposed_act
            case.next_action_scheduled_at = now + timedelta(hours=ai_res.recommended_delay_hours)
        else:
            cls.transition_state(
                db=db,
                case=case,
                new_status=StateConstants.ACTION_BLOCKED,
                reason=f"Guardrail verification BLOCKED: {guardrail_res.blocked_reason}",
                actor="GUARDRAIL_ENGINE",
                metadata={"blocked_reason": guardrail_res.blocked_reason, "stop_reason": guardrail_res.stop_reason}
            )
            case.stop_reason = guardrail_res.stop_reason
            case.next_action = None
            case.next_action_scheduled_at = None

            # Route to Human Review or Safe Stop
            if guardrail_res.stop_reason == StopReasonConstants.CUSTOMER_DISPUTED:
                HumanReviewService.create_or_get_review(
                    db=db,
                    recovery_case_id=case.id,
                    customer_id=customer.id,
                    trigger_reason=f"Guardrail block: Customer disputed payment"
                )
                cls.transition_state(
                    db=db,
                    case=case,
                    new_status=StateConstants.HUMAN_REVIEW,
                    reason="Customer dispute requires mandatory human review. Automation halted.",
                    actor="GUARDRAIL_ENGINE"
                )
            elif guardrail_res.stop_reason in [
                StopReasonConstants.CUSTOMER_OPTED_OUT,
                StopReasonConstants.MAX_ATTEMPTS_REACHED,
                StopReasonConstants.RECOVERY_WINDOW_EXPIRED
            ]:
                cls.transition_state(
                    db=db,
                    case=case,
                    new_status=StateConstants.STOPPED,
                    reason=f"Automation stopped safely: {guardrail_res.blocked_reason}",
                    actor="GUARDRAIL_ENGINE"
                )

        db.commit()
        db.refresh(case)

        return {
            "case_id": case.id,
            "ai_decision": ai_res,
            "guardrail_decision": guardrail_res,
            "current_status": case.current_status,
            "stop_reason": case.stop_reason
        }

    @classmethod
    def validate_action(cls, db: Session, case_id: str, proposed_action: str = "RETRY_PAYMENT") -> DualDecisionView:
        """
        Fetch side-by-side AI decision and current Guardrail decision for the case.
        """
        case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            raise ValueError(f"Recovery case {case_id} not found")

        customer = case.customer
        attempts = case.payment_attempts
        last_attempt_time = attempts[-1].created_at if attempts else None

        case_data = {
            "customer": {
                "is_opted_out": customer.is_opted_out,
                "has_dispute": customer.has_dispute,
            },
            "payment_attempts": attempts,
            "attempt_count": case.attempt_count,
            "current_status": case.current_status,
            "initial_failure_at": case.initial_failure_at,
            "last_attempt_at": last_attempt_time
        }

        gr_res = GuardrailEngine.evaluate(case_data, proposed_action=proposed_action)

        ai_res = AIDecisionResponse(
            score=case.recovery_score or 50.0,
            probability=case.recovery_probability or 0.5,
            recommended_action=case.ai_recommendation or "RETRY",
            recommended_delay_hours=case.ai_recommended_delay_hours,
            explanation=case.ai_explanation or "Analysis pending or completed.",
            factors=case.ai_decision_factors
        )

        if gr_res.allowed:
            final_status = "🟢 RETRY ALLOWED"
            summary = "AI recommends retry and all deterministic safety guardrails passed. Action permitted."
        else:
            final_status = "🔴 ACTION BLOCKED"
            summary = f"Execution prohibited by GuardrailEngine: {gr_res.blocked_reason}"

        return DualDecisionView(
            ai_decision=ai_res,
            guardrail_decision=gr_res,
            final_status=final_status,
            final_allowed=gr_res.allowed,
            summary=summary
        )

    @classmethod
    def execute_action(
        cls,
        db: Session,
        case_id: str,
        action_type: str = "RETRY_PAYMENT",
        idempotency_key: Optional[str] = None,
        force_outcome: Optional[str] = None
    ) -> ExecuteActionResponse:
        """
        CRITICAL EXECUTE ENDPOINT SAFETY:
        1. Load current DB state
        2. Enforce idempotency (reject duplicate executions)
        3. Authoritatively RE-RUN GuardrailEngine (never trust client)
        4. If blocked, abort execution and log event
        5. If allowed, execute simulated payment and update workflow state
        """
        case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            raise ValueError(f"Recovery case {case_id} not found")

        # Step 2: Idempotency Check
        idem_key = idempotency_key or f"ACT-{case.id}-{case.attempt_count + 1}-{uuid.uuid4().hex[:6]}"
        existing_action = db.query(RecoveryAction).filter(
            RecoveryAction.idempotency_key == idem_key,
            RecoveryAction.status == "EXECUTED"
        ).first()

        if existing_action:
            return ExecuteActionResponse(
                success=True,
                action_id=existing_action.id,
                action_type=existing_action.action_type,
                status="ALREADY_EXECUTED",
                execution_result=existing_action.execution_result,
                current_case_status=case.current_status,
                stop_reason=case.stop_reason,
                message="Action already executed (Idempotent response)."
            )

        customer = case.customer
        attempts = case.payment_attempts
        last_attempt_time = attempts[-1].created_at if attempts else None

        # Step 3: Authoritatively RE-RUN GuardrailEngine
        case_data = {
            "customer": {
                "is_opted_out": customer.is_opted_out,
                "has_dispute": customer.has_dispute,
            },
            "payment_attempts": attempts,
            "attempt_count": case.attempt_count,
            "current_status": case.current_status,
            "initial_failure_at": case.initial_failure_at,
            "last_attempt_at": last_attempt_time
        }

        gr_res = GuardrailEngine.evaluate(case_data, proposed_action=action_type)

        now = datetime.now(timezone.utc)
        action_id = f"ACT-{uuid.uuid4().hex[:10].upper()}"

        action_record = RecoveryAction(
            id=action_id,
            recovery_case_id=case.id,
            action_type=action_type,
            status="PENDING",
            idempotency_key=idem_key,
            guardrail_evaluated=True,
            guardrail_allowed=gr_res.allowed,
            created_at=now
        )
        db.add(action_record)
        db.flush()

        # Step 4: Handle Guardrail BLOCKED
        if not gr_res.allowed:
            action_record.status = "BLOCKED"
            action_record.execution_result = {
                "error": "Guardrail violation",
                "blocked_reason": gr_res.blocked_reason,
                "stop_reason": gr_res.stop_reason
            }

            AuditService.record_event(
                db=db,
                recovery_case_id=case.id,
                event_type="ACTION_EXECUTION_BLOCKED",
                description=f"Execution of {action_type} was blocked by GuardrailEngine: {gr_res.blocked_reason}",
                actor="GUARDRAIL_ENGINE",
                metadata={"blocked_reason": gr_res.blocked_reason, "action_id": action_id}
            )

            # Route appropriately if terminal stop
            if gr_res.stop_reason == StopReasonConstants.CUSTOMER_DISPUTED:
                HumanReviewService.create_or_get_review(
                    db=db,
                    recovery_case_id=case.id,
                    customer_id=customer.id,
                    trigger_reason=f"Customer dispute blocked execution: {gr_res.blocked_reason}"
                )
                cls.transition_state(
                    db=db,
                    case=case,
                    new_status=StateConstants.HUMAN_REVIEW,
                    reason=f"Customer dispute detected during execution. Halted.",
                    actor="GUARDRAIL_ENGINE"
                )
            elif gr_res.stop_reason:
                case.stop_reason = gr_res.stop_reason
                cls.transition_state(
                    db=db,
                    case=case,
                    new_status=StateConstants.STOPPED,
                    reason=f"Execution halted: {gr_res.blocked_reason}",
                    actor="GUARDRAIL_ENGINE"
                )

            db.commit()
            db.refresh(case)

            return ExecuteActionResponse(
                success=False,
                action_id=action_id,
                action_type=action_type,
                status="BLOCKED",
                execution_result=action_record.execution_result,
                current_case_status=case.current_status,
                stop_reason=case.stop_reason,
                message=f"Action blocked by GuardrailEngine: {gr_res.blocked_reason}"
            )

        # Step 5: Execute Allowed Action
        cls.transition_state(
            db=db,
            case=case,
            new_status=StateConstants.RETRYING,
            reason=f"Executing permitted action: {action_type}",
            actor="RECOVERY_WORKFLOW_ENGINE",
            metadata={"action_id": action_id}
        )

        # Execute simulated payment
        sim_result = PaymentSimulator.simulate_mandate_debit(
            mandate_id=case.mandate_id,
            amount=case.amount,
            attempt_number=case.attempt_count + 1,
            force_outcome=force_outcome
        )

        attempt_id = f"ATT-{uuid.uuid4().hex[:10].upper()}"
        attempt_record = PaymentAttempt(
            id=attempt_id,
            recovery_case_id=case.id,
            mandate_id=case.mandate_id,
            attempt_number=case.attempt_count + 1,
            amount=case.amount,
            status=sim_result["status"],
            failure_code=sim_result.get("failure_code"),
            failure_reason=sim_result.get("response_message"),
            is_temporary=sim_result.get("is_temporary", True),
            idempotency_key=idem_key,
            created_at=now
        )
        db.add(attempt_record)

        case.attempt_count += 1
        action_record.status = "EXECUTED"
        action_record.executed_at = now
        action_record.execution_result = sim_result

        if sim_result["success"]:
            # Payment Recovered Successfully!
            customer.historical_success_count += 1
            customer.last_active_at = now

            cls.transition_state(
                db=db,
                case=case,
                new_status=StateConstants.RECOVERED,
                reason=f"Payment of INR {case.amount:,.2f} successfully recovered via NPCI/E-NACH debit",
                actor="PAYMENT_SIMULATOR",
                metadata=sim_result
            )

            # AUTOMATIC STOP on success
            case.stop_reason = StopReasonConstants.PAYMENT_RECOVERED
            case.next_action = None
            case.next_action_scheduled_at = None

            cls.transition_state(
                db=db,
                case=case,
                new_status=StateConstants.STOPPED,
                reason="Workflow stopped automatically because payment was successfully recovered.",
                actor="RECOVERY_WORKFLOW_ENGINE",
                metadata={"recovered_amount": case.amount, "currency": case.currency}
            )

            msg = f"Payment of INR {case.amount:,.2f} successfully recovered! Automation safely stopped."
        else:
            # Payment Retry Failed
            customer.historical_failure_count += 1

            AuditService.record_event(
                db=db,
                recovery_case_id=case.id,
                event_type="PAYMENT_RETRY_FAILED",
                description=f"Payment retry #{case.attempt_count} failed: {sim_result.get('response_message')}",
                actor="PAYMENT_SIMULATOR",
                metadata=sim_result
            )

            if case.attempt_count >= GuardrailEngine.MAX_RETRY_ATTEMPTS:
                case.stop_reason = StopReasonConstants.MAX_ATTEMPTS_REACHED
                case.next_action = None
                case.next_action_scheduled_at = None

                HumanReviewService.create_or_get_review(
                    db=db,
                    recovery_case_id=case.id,
                    customer_id=customer.id,
                    trigger_reason=f"Maximum retry attempts ({GuardrailEngine.MAX_RETRY_ATTEMPTS}) reached without recovery"
                )

                cls.transition_state(
                    db=db,
                    case=case,
                    new_status=StateConstants.HUMAN_REVIEW,
                    reason=f"Max retry limit ({GuardrailEngine.MAX_RETRY_ATTEMPTS}) reached. Escalating to Human Review.",
                    actor="GUARDRAIL_ENGINE"
                )
                msg = f"Payment retry failed. Maximum attempts reached ({case.attempt_count}). Case escalated to Human Review."
            else:
                cls.transition_state(
                    db=db,
                    case=case,
                    new_status=StateConstants.RETRY_SCHEDULED,
                    reason=f"Retry attempt {case.attempt_count} failed. Cooling down for next eligible window.",
                    actor="RECOVERY_WORKFLOW_ENGINE"
                )
                case.next_action = "RETRY_PAYMENT"
                case.next_action_scheduled_at = now + timedelta(hours=24)
                msg = f"Payment retry failed. Attempt {case.attempt_count} recorded. Cooldown scheduled."

        db.commit()
        db.refresh(case)

        return ExecuteActionResponse(
            success=sim_result["success"],
            action_id=action_id,
            action_type=action_type,
            status=action_record.status,
            execution_result=sim_result,
            current_case_status=case.current_status,
            stop_reason=case.stop_reason,
            message=msg
        )
