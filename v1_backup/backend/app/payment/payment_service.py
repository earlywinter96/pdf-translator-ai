"""
Razorpay Payment Service
------------------------
Handles payment order creation, verification, and webhook processing
"""

import razorpay
import hmac
import hashlib
import logging
from typing import Dict, Optional, Tuple
import threading
from datetime import datetime

from .payment_config import (
    RAZORPAY_KEY_ID,
    RAZORPAY_KEY_SECRET,
    CURRENCY,
    BUSINESS_INFO,
    is_demo_mode,
    format_amount,
    RAZORPAY_WEBHOOK_SECRET
)

logger = logging.getLogger(__name__)

# ============================================================================
# RAZORPAY CLIENT INITIALIZATION
# ============================================================================

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Payment tracking
PAYMENT_STORE: Dict[str, dict] = {}
_lock = threading.Lock()


# ============================================================================
# ORDER CREATION
# ============================================================================

def create_payment_order(
    amount_paise: int,
    job_id: str,
    session_id: str,
    page_count: int,
    notes: Optional[Dict] = None
) -> Dict:
    """
    Create a Razorpay payment order
    
    Args:
        amount_paise: Amount in paise (INR * 100)
        job_id: Associated job ID
        session_id: User session ID
        page_count: Number of pages being paid for
        notes: Additional notes for the order
        
    Returns:
        Order details including order_id, amount, and checkout data
    """
    try:
        # Prepare order data
        order_data = {
            "amount": amount_paise,  # Amount in paise
            "currency": CURRENCY,
            "receipt": f"job_{job_id}",
            "notes": {
                "job_id": job_id,
                "session_id": session_id,
                "page_count": page_count,
                "service": "PDF Translation",
                **(notes or {})
            }
        }
        
        # Create order with Razorpay
        order = razorpay_client.order.create(data=order_data)
        
        # Store payment information
        payment_id = order["id"]
        with _lock:
            PAYMENT_STORE[payment_id] = {
                "order_id": payment_id,
                "job_id": job_id,
                "session_id": session_id,
                "amount": amount_paise,
                "amount_inr": amount_paise / 100,
                "page_count": page_count,
                "currency": CURRENCY,
                "status": "created",
                "created_at": datetime.now(),
                "payment_id": None,  # Set when payment is captured
                "signature": None,  # Set when payment is verified
            }
        
        logger.info(f"💳 Created payment order: {payment_id}")
        logger.info(f"   Amount: {format_amount(amount_paise)}")
        logger.info(f"   Job: {job_id}")
        logger.info(f"   Pages: {page_count}")
        
        # Return order details for frontend
        return {
            "order_id": order["id"],
            "amount": amount_paise,
            "amount_inr": amount_paise / 100,
            "currency": CURRENCY,
            "key_id": RAZORPAY_KEY_ID,
            "business_name": BUSINESS_INFO["name"],
            "description": f"Translation for {page_count} pages",
            "prefill": {
                "name": "",
                "email": "",
                "contact": ""
            },
            "theme": {
                "color": BUSINESS_INFO["theme_color"]
            },
            "notes": order_data["notes"]
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create payment order: {e}")
        raise Exception(f"Payment order creation failed: {str(e)}")


# ============================================================================
# PAYMENT VERIFICATION
# ============================================================================

def verify_payment_signature(
    order_id: str,
    payment_id: str,
    signature: str
) -> Tuple[bool, str]:
    """
    Verify Razorpay payment signature
    
    Args:
        order_id: Razorpay order ID
        payment_id: Razorpay payment ID
        signature: Payment signature to verify
        
    Returns:
        (is_valid: bool, message: str)
    """
    try:
        # In demo mode, always accept signature
        if is_demo_mode():
            logger.warning("⚠️  DEMO MODE: Skipping signature verification")
            with _lock:
                if order_id in PAYMENT_STORE:
                    PAYMENT_STORE[order_id]["status"] = "verified"
                    PAYMENT_STORE[order_id]["payment_id"] = payment_id
                    PAYMENT_STORE[order_id]["signature"] = signature
            return True, "Payment verified (demo mode)"
        
        # Production mode - verify signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Update payment store
        with _lock:
            if order_id in PAYMENT_STORE:
                PAYMENT_STORE[order_id]["status"] = "verified"
                PAYMENT_STORE[order_id]["payment_id"] = payment_id
                PAYMENT_STORE[order_id]["signature"] = signature
        
        logger.info(f"✅ Payment verified: {payment_id}")
        return True, "Payment verified successfully"
        
    except razorpay.errors.SignatureVerificationError as e:
        logger.error(f"❌ Signature verification failed: {e}")
        
        with _lock:
            if order_id in PAYMENT_STORE:
                PAYMENT_STORE[order_id]["status"] = "verification_failed"
        
        return False, "Payment signature verification failed"
    
    except Exception as e:
        logger.error(f"❌ Payment verification error: {e}")
        return False, f"Payment verification error: {str(e)}"


# ============================================================================
# PAYMENT STATUS
# ============================================================================

def get_payment_status(order_id: str) -> Optional[Dict]:
    """
    Get payment status
    
    Args:
        order_id: Razorpay order ID
        
    Returns:
        Payment status data or None
    """
    with _lock:
        return PAYMENT_STORE.get(order_id)


def is_payment_verified(order_id: str) -> bool:
    """
    Check if payment is verified
    
    Args:
        order_id: Razorpay order ID
        
    Returns:
        True if payment is verified
    """
    with _lock:
        payment = PAYMENT_STORE.get(order_id)
        return payment and payment["status"] == "verified"


def get_payment_by_job(job_id: str) -> Optional[Dict]:
    """
    Get payment information by job ID
    
    Args:
        job_id: Job identifier
        
    Returns:
        Payment data or None
    """
    with _lock:
        for order_id, payment in PAYMENT_STORE.items():
            if payment["job_id"] == job_id:
                return payment
        return None


# ============================================================================
# WEBHOOK HANDLING (Optional - for production)
# ============================================================================

def verify_webhook_signature(payload: str, signature: str) -> bool:
    """
    Verify Razorpay webhook signature
    
    Args:
        payload: Webhook payload string
        signature: X-Razorpay-Signature header value
        
    Returns:
        True if signature is valid
    """
    if not RAZORPAY_WEBHOOK_SECRET:
        logger.warning("⚠️  No webhook secret configured")
        return False
    
    try:
        expected_signature = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    except Exception as e:
        logger.error(f"❌ Webhook signature verification failed: {e}")
        return False


def handle_payment_webhook(event: Dict):
    """
    Handle Razorpay webhook events
    
    Args:
        event: Webhook event data
    """
    event_type = event.get("event")
    payload = event.get("payload", {}).get("payment", {}).get("entity", {})
    
    order_id = payload.get("order_id")
    payment_id = payload.get("id")
    status = payload.get("status")
    
    logger.info(f"📩 Webhook received: {event_type}")
    logger.info(f"   Order: {order_id}")
    logger.info(f"   Payment: {payment_id}")
    logger.info(f"   Status: {status}")
    
    # Update payment status based on event
    if event_type == "payment.captured":
        with _lock:
            if order_id in PAYMENT_STORE:
                PAYMENT_STORE[order_id]["status"] = "captured"
                PAYMENT_STORE[order_id]["payment_id"] = payment_id
                logger.info(f"✅ Payment captured: {payment_id}")
    
    elif event_type == "payment.failed":
        with _lock:
            if order_id in PAYMENT_STORE:
                PAYMENT_STORE[order_id]["status"] = "failed"
                logger.warning(f"⚠️  Payment failed: {payment_id}")


# ============================================================================
# DEMO MODE HELPERS - FIXED
# ============================================================================

def create_demo_payment(
    amount_paise: int,
    job_id: str,
    session_id: str,
    page_count: int
) -> Dict:
    """
    Create a demo/mock payment (for testing without Razorpay)
    
    Args:
        amount_paise: Amount in paise
        job_id: Job ID
        session_id: Session ID
        page_count: Number of pages
        
    Returns:
        Mock order details (COMPLETE with all required fields)
    """
    import uuid
    
    order_id = f"order_demo_{uuid.uuid4().hex[:16]}"
    
    with _lock:
        PAYMENT_STORE[order_id] = {
            "order_id": order_id,
            "job_id": job_id,
            "session_id": session_id,
            "amount": amount_paise,
            "amount_inr": amount_paise / 100,
            "page_count": page_count,
            "currency": CURRENCY,
            "status": "created",
            "created_at": datetime.now(),
            "payment_id": f"pay_demo_{uuid.uuid4().hex[:16]}",
            "signature": "demo_signature",
            "demo": True
        }
    
    logger.info(f"🎭 Created DEMO payment order: {order_id}")
    logger.info(f"   Amount: {format_amount(amount_paise)}")
    
    # ✅ FIXED: Return ALL required fields for PaymentOrderResponse
    return {
        "order_id": order_id,
        "amount": amount_paise,
        "amount_inr": amount_paise / 100,
        "currency": CURRENCY,
        "key_id": RAZORPAY_KEY_ID,  # ✅ ADDED
        "business_name": BUSINESS_INFO["name"],  # ✅ ADDED
        "description": f"Translation for {page_count} pages",  # ✅ ADDED
        "demo": True,
        "message": "⚠️ DEMO MODE: This is a test payment. No real money will be charged."
    }


def auto_verify_demo_payment(order_id: str) -> bool:
    """
    Auto-verify demo payment after a delay
    
    Args:
        order_id: Demo order ID
        
    Returns:
        True if verified
    """
    with _lock:
        if order_id in PAYMENT_STORE and PAYMENT_STORE[order_id].get("demo"):
            PAYMENT_STORE[order_id]["status"] = "verified"
            logger.info(f"✅ Auto-verified DEMO payment: {order_id}")
            return True
    return False


# ============================================================================
# PAYMENT STATISTICS
# ============================================================================

def get_payment_stats() -> Dict:
    """Get payment statistics"""
    with _lock:
        total = len(PAYMENT_STORE)
        verified = sum(1 for p in PAYMENT_STORE.values() if p["status"] == "verified")
        failed = sum(1 for p in PAYMENT_STORE.values() if p["status"] == "failed")
        pending = total - verified - failed
        
        total_amount = sum(p["amount"] for p in PAYMENT_STORE.values() if p["status"] == "verified")
        
        return {
            "total_orders": total,
            "verified": verified,
            "failed": failed,
            "pending": pending,
            "total_revenue_paise": total_amount,
            "total_revenue_inr": total_amount / 100
        }