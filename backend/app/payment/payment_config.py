"""
Payment Configuration
---------------------
Razorpay configuration and payment calculation logic
"""

import os
import logging
from typing import Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# RAZORPAY CREDENTIALS
# ============================================================================

# Get from environment variables
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

# Demo mode (if credentials not set)
DEMO_MODE = not (RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)

if DEMO_MODE:
    logger.warning("⚠️  RAZORPAY CREDENTIALS NOT SET - RUNNING IN DEMO MODE")
    logger.warning("⚠️  Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET for production")
    # Use test credentials for demo
    RAZORPAY_KEY_ID = "rzp_test_demo"
    RAZORPAY_KEY_SECRET = "demo_secret"


# ============================================================================
# PAYMENT CONFIGURATION
# ============================================================================

# Currency
CURRENCY = "INR"

# One page is a product preview. Full-document jobs must be paid before they
# are released to the translation worker.
FREE_PAGES_LIMIT = 1

# Price in paise. ₹10/page covers Sarvam's character-billed translation cost,
# PDF processing, Razorpay fees, and a sustainable operating margin.
PRICE_PER_PAGE = 1000  # ₹10 per paid page

# Business information
BUSINESS_INFO = {
    "name": "LipiTranslate",
    "description": "AI-Powered PDF Translation",
    "theme_color": "#3399ff",
    "logo": "",
    "contact": {
        "email": "support@lipitranslate.in",
        "phone": "+91-XXXXXXXXXX"
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_demo_mode() -> bool:
    """Check if running in demo mode"""
    return DEMO_MODE


def get_public_key() -> str:
    """Get Razorpay public key"""
    return RAZORPAY_KEY_ID


def format_amount(paise: int) -> str:
    """
    Format amount in paise to INR string
    
    Args:
        paise: Amount in paise
        
    Returns:
        Formatted string like "₹10.00"
    """
    inr = paise / 100
    return f"₹{inr:.2f}"


# ============================================================================
# PAYMENT CALCULATION
# ============================================================================

def calculate_payment(total_pages: int) -> Dict:
    """
    Calculate payment required for given page count
    
    Args:
        total_pages: Total number of pages in PDF
        
    Returns:
        Dictionary with payment calculation details:
        {
            "total_pages": int,
            "free_pages": int,
            "paid_pages": int,
            "amount": int (in paise),
            "amount_inr": float,
            "requires_payment": bool,
            "message": str
        }
    """
    # Pages within free limit
    free_pages = min(total_pages, FREE_PAGES_LIMIT)
    
    # Pages that need payment
    paid_pages = max(0, total_pages - FREE_PAGES_LIMIT)
    
    # Calculate amount in paise
    amount_paise = paid_pages * PRICE_PER_PAGE
    
    # Convert to INR
    amount_inr = amount_paise / 100
    
    # Build message
    if paid_pages == 0:
        message = f"All {total_pages} pages are free!"
    else:
        message = f"{free_pages} pages free, {paid_pages} pages require payment ({format_amount(amount_paise)})"
    
    return {
        "total_pages": total_pages,
        "free_pages": free_pages,
        "paid_pages": paid_pages,
        "amount": amount_paise,
        "amount_inr": amount_inr,
        "requires_payment": paid_pages > 0,
        "message": message
    }


# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate payment configuration on startup"""
    logger.info("=" * 70)
    logger.info("💳 PAYMENT CONFIGURATION")
    logger.info("=" * 70)
    logger.info(f"Mode: {'DEMO' if DEMO_MODE else 'PRODUCTION'}")
    logger.info(f"Currency: {CURRENCY}")
    logger.info(f"Free Pages: {FREE_PAGES_LIMIT}")
    logger.info(f"Price per Page: {format_amount(PRICE_PER_PAGE)}")
    logger.info(f"Business: {BUSINESS_INFO['name']}")
    
    if DEMO_MODE:
        logger.warning("⚠️  DEMO MODE ACTIVE - No real payments will be processed")
        logger.warning("⚠️  Set environment variables for production:")
        logger.warning("    - RAZORPAY_KEY_ID")
        logger.warning("    - RAZORPAY_KEY_SECRET")
    else:
        logger.info(f"✅ Razorpay Key ID: {RAZORPAY_KEY_ID[:10]}...")
        logger.info("✅ Production mode enabled")
    
    logger.info("=" * 70)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Test payment calculations
    test_cases = [5, 10, 15, 20, 50, 100]
    
    print("\n" + "=" * 70)
    print("PAYMENT CALCULATION TESTS")
    print("=" * 70)
    
    for pages in test_cases:
        calc = calculate_payment(pages)
        print(f"\n{pages} pages:")
        print(f"  Free: {calc['free_pages']}, Paid: {calc['paid_pages']}")
        print(f"  Amount: {format_amount(calc['amount'])}")
        print(f"  Message: {calc['message']}")
