"""
Payment API Routes
------------------
FastAPI routes for Razorpay payment integration
"""

import asyncio

from fastapi import APIRouter, HTTPException, Header, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging

from .payment_config import (
    calculate_payment,
    get_public_key,
    is_demo_mode,
    FREE_PAGES_LIMIT,
    format_amount
)
from .payment_session import (
    create_session,
    get_session,
    get_free_pages_remaining,
    use_free_pages,
    add_payment_to_session,
    update_session_activity,
    get_session_stats
)
from .payment_service import (
    create_payment_order,
    verify_payment_signature,
    get_payment_status,
    is_payment_verified,
    create_demo_payment,
    auto_verify_demo_payment,
    verify_webhook_signature,
    handle_payment_webhook
)
from app.models.job import get_job
from app.services.discord_notifier import notify_discord

logger = logging.getLogger(__name__)

# Create router
payment_router = APIRouter(prefix="/api/payment", tags=["payment"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SessionResponse(BaseModel):
    session_id: str
    free_pages_remaining: int
    message: str


class PageCheckRequest(BaseModel):
    page_count: int


class PageCheckResponse(BaseModel):
    requires_payment: bool
    free_pages: int
    paid_pages: int
    amount: int
    amount_inr: float
    message: str
    can_proceed: bool


class PaymentOrderRequest(BaseModel):
    job_id: str
    page_count: int


class PaymentOrderResponse(BaseModel):
    order_id: str
    amount: int
    amount_inr: float
    currency: str
    key_id: str
    business_name: str
    description: str
    demo: bool = False
    message: Optional[str] = None


class PaymentVerifyRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str
    job_id: str


class PaymentVerifyResponse(BaseModel):
    verified: bool
    message: str


class PaymentFunnelEvent(BaseModel):
    job_id: str
    event: str


# ============================================================================
# SESSION MANAGEMENT ROUTES
# ============================================================================

@payment_router.post("/session/create", response_model=SessionResponse)
async def create_payment_session():
    """
    Create a new user session for tracking free pages
    
    Returns:
        Session ID and remaining free pages
    """
    try:
        session_id = create_session()
        
        return SessionResponse(
            session_id=session_id,
            free_pages_remaining=FREE_PAGES_LIMIT,
            message=f"Session created with {FREE_PAGES_LIMIT} free pages"
        )
    
    except Exception as e:
        logger.error(f"❌ Session creation failed: {e}")
        raise HTTPException(500, "Failed to create session")


@payment_router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """
    Get session status and statistics
    
    Args:
        session_id: User session ID
        
    Returns:
        Session statistics
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    update_session_activity(session_id)
    
    return {
        "session_id": session_id,
        "free_pages_remaining": get_free_pages_remaining(session_id),
        "stats": get_session_stats(session_id)
    }


# ============================================================================
# PAYMENT CALCULATION ROUTES
# ============================================================================

@payment_router.post("/check-pages", response_model=PageCheckResponse)
async def check_pages_payment(
    request: PageCheckRequest,
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Check if payment is required for given page count
    
    Args:
        request: Page count to check
        session_id: User session ID (from header)
        
    Returns:
        Payment calculation and whether user can proceed
    """
    # Verify session exists
    if not session_id or not get_session(session_id):
        raise HTTPException(401, "Invalid or missing session ID")
    
    update_session_activity(session_id)
    
    # Calculate payment
    payment_calc = calculate_payment(request.page_count)
    
    # Check if user has free pages remaining
    free_remaining = get_free_pages_remaining(session_id)
    
    # User can proceed if:
    # 1. Payment not required (within free limit), OR
    # 2. Payment required and user has some free pages to use
    can_proceed = not payment_calc["requires_payment"] or free_remaining > 0
    
    return PageCheckResponse(
        requires_payment=payment_calc["requires_payment"],
        free_pages=payment_calc["free_pages"],
        paid_pages=payment_calc["paid_pages"],
        amount=payment_calc["amount"],
        amount_inr=payment_calc["amount_inr"],
        message=payment_calc["message"],
        can_proceed=can_proceed
    )


# ============================================================================
# PAYMENT ORDER ROUTES
# ============================================================================

@payment_router.post("/events")
async def record_payment_funnel_event(event: PaymentFunnelEvent):
    """Record client-side preview/payment milestones for operational review."""
    labels = {
        "preview_viewed": "Free preview viewed",
        "payment_modal_opened": "Payment options viewed",
        "payment_modal_dismissed": "Payment options dismissed",
        "razorpay_dismissed": "Razorpay checkout dismissed",
        "payment_failed": "Razorpay payment failed",
    }
    label = labels.get(event.event)
    job = get_job(event.job_id)
    if not label or not job:
        raise HTTPException(400, "Invalid payment event")
    asyncio.create_task(notify_discord("LipiTranslate customer funnel", {
        "Job": event.job_id[:8],
        "Event": label,
        "Price shown": f"₹{(job.get('payment_quote') or {}).get('amount_inr', 0):.0f}",
    }))
    return {"recorded": True}

@payment_router.post("/create-order", response_model=PaymentOrderResponse)
async def create_order(
    request: PaymentOrderRequest,
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Create a Razorpay payment order
    
    Args:
        request: Job ID and page count
        session_id: User session ID (from header)
        
    Returns:
        Payment order details for Razorpay checkout
    """
    # Verify session
    if not session_id or not get_session(session_id):
        raise HTTPException(401, "Invalid or missing session ID")
    
    update_session_activity(session_id)
    
    job = get_job(request.job_id)
    if not job or not job.get("payment_required"):
        raise HTTPException(400, "This job does not require payment")
    if job.get("payment_started"):
        raise HTTPException(409, "Translation has already started")
    if job.get("status") != "completed" or not job.get("output_path"):
        raise HTTPException(409, "Your free preview is still being created. Please review it before payment.")

    # Never accept a browser-controlled page count for billing.
    payment_calc = calculate_payment(
        int(job["page_count"]),
        int(job.get("billable_characters", 0)),
    )
    
    if not payment_calc["requires_payment"]:
        raise HTTPException(400, "Payment not required for this page count")
    
    try:
        # Create payment order
        if is_demo_mode():
            # Demo mode - create mock payment
            order = create_demo_payment(
                amount_paise=payment_calc["amount"],
                job_id=request.job_id,
                session_id=session_id,
                page_count=payment_calc["paid_pages"]
            )
            order["demo"] = True
            order["message"] = "⚠️ DEMO MODE: This is a test payment. No real money will be charged."
        else:
            # Production mode - create real Razorpay order
            order = create_payment_order(
                amount_paise=payment_calc["amount"],
                job_id=request.job_id,
                session_id=session_id,
                page_count=payment_calc["paid_pages"]
            )
        
        # Associate payment with session
        add_payment_to_session(session_id, order["order_id"])
        asyncio.create_task(notify_discord("LipiTranslate payment checkout opened", {
            "Job": request.job_id[:8],
            "Pages to unlock": payment_calc["paid_pages"],
            "Amount": format_amount(payment_calc["amount"]),
            "Status": "Awaiting payment",
        }))
        
        return PaymentOrderResponse(**order)
    
    except Exception as e:
        logger.error(f"❌ Order creation failed: {e}")
        raise HTTPException(500, f"Failed to create payment order: {str(e)}")


# ============================================================================
# PAYMENT VERIFICATION ROUTES
# ============================================================================

@payment_router.post("/verify", response_model=PaymentVerifyResponse)
async def verify_payment(
    request: PaymentVerifyRequest,
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Verify payment signature after successful payment
    
    Args:
        request: Payment verification data
        session_id: User session ID (from header)
        
    Returns:
        Verification result
    """
    # Verify session
    if not session_id or not get_session(session_id):
        raise HTTPException(401, "Invalid or missing session ID")
    
    update_session_activity(session_id)

    payment = get_payment_status(request.order_id)
    if not payment or payment.get("job_id") != request.job_id:
        raise HTTPException(400, "Payment order does not match this translation job")
    
    try:
        # In demo mode, auto-verify
        if is_demo_mode():
            success = auto_verify_demo_payment(request.order_id)
            if success:
                asyncio.create_task(notify_discord("LipiTranslate demo payment verified", {
                    "Job": request.job_id[:8],
                    "Status": "Ready to start full-document translation",
                }))
                return PaymentVerifyResponse(
                    verified=True,
                    message="Demo payment verified (no real transaction)"
                )
        
        # Verify signature
        is_valid, message = verify_payment_signature(
            order_id=request.order_id,
            payment_id=request.payment_id,
            signature=request.signature
        )
        
        if not is_valid:
            raise HTTPException(400, message)
        asyncio.create_task(notify_discord("LipiTranslate payment captured", {
            "Job": request.job_id[:8],
            "Status": "Payment signature verified",
        }))
        return PaymentVerifyResponse(verified=True, message=message)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Payment verification failed: {e}")
        raise HTTPException(500, f"Payment verification failed: {str(e)}")


@payment_router.get("/status/{order_id}")
async def get_order_status(
    order_id: str,
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Get payment order status
    
    Args:
        order_id: Razorpay order ID
        session_id: User session ID (from header)
        
    Returns:
        Payment status
    """
    # Verify session
    if not session_id or not get_session(session_id):
        raise HTTPException(401, "Invalid or missing session ID")
    
    payment = get_payment_status(order_id)
    if not payment:
        raise HTTPException(404, "Payment order not found")
    
    return {
        "order_id": order_id,
        "status": payment["status"],
        "amount_inr": payment["amount_inr"],
        "verified": is_payment_verified(order_id)
    }


# ============================================================================
# WEBHOOK ROUTE (Optional - for production)
# ============================================================================

@payment_router.post("/webhook")
async def razorpay_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle Razorpay webhook events
    
    Args:
        request: Webhook request
        background_tasks: Background task handler
        
    Returns:
        Acknowledgment
    """
    try:
        # Get signature from headers
        signature = request.headers.get("X-Razorpay-Signature")
        if not signature:
            raise HTTPException(400, "Missing signature")
        
        # Get raw body
        body = await request.body()
        
        # Verify signature
        if not verify_webhook_signature(body.decode(), signature):
            raise HTTPException(401, "Invalid signature")
        
        # Parse event
        event = await request.json()
        
        # Process webhook in background
        background_tasks.add_task(handle_payment_webhook, event)
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"❌ Webhook processing failed: {e}")
        raise HTTPException(500, "Webhook processing failed")


# ============================================================================
# CONFIG ROUTE
# ============================================================================

@payment_router.get("/config")
async def get_payment_config():
    """
    Get public payment configuration
    
    Returns:
        Public config data for frontend
    """
    return {
        "key_id": get_public_key(),
        "demo_mode": is_demo_mode(),
        "free_pages_limit": FREE_PAGES_LIMIT,
        "currency": "INR",
        "currency_symbol": "₹"
    }
