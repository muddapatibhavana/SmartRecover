import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class PaymentSimulator:
    """
    Realistic simulation engine for recurring mandate execution, disputes, and opt-outs.
    NO real payment credentials or gateways are used.
    """

    @staticmethod
    def simulate_mandate_debit(
        mandate_id: str,
        amount: float,
        attempt_number: int,
        force_outcome: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulate mandate retry execution with mock transaction identifiers and realistic response codes.
        """
        txn_id = f"SIM-TXN-{uuid.uuid4().hex[:12].upper()}"
        bank_rrn = f"NPCI-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)

        if force_outcome == "SUCCESS":
            is_success = True
        elif force_outcome == "FAILED":
            is_success = False
        else:
            # Deterministic default: attempt 1 or 2 can succeed if score was high
            is_success = True

        if is_success:
            return {
                "success": True,
                "status": "SUCCESS",
                "transaction_id": txn_id,
                "bank_reference_number": bank_rrn,
                "amount": amount,
                "currency": "INR",
                "response_code": "00",
                "response_message": "Mandate debit successful via NPCI / E-NACH gateway",
                "timestamp": now.isoformat()
            }
        else:
            return {
                "success": False,
                "status": "FAILED",
                "transaction_id": txn_id,
                "bank_reference_number": bank_rrn,
                "amount": amount,
                "currency": "INR",
                "response_code": "U16",
                "failure_code": "INSUFFICIENT_FUNDS",
                "response_message": "Insufficient balance in customer bank account",
                "is_temporary": True,
                "timestamp": now.isoformat()
            }
