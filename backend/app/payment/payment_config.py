"""
Payment Configuration
---------------------
Razorpay configuration and payment calculation logic
"""

import math
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

# Customer-facing packages. These prices cover Sarvam translation, OCR for
# scanned PDFs, Razorpay fees, and operating margin at their stated text cap.
# A plan is displayed only when the selected page range fits both limits.
FREE_CHARACTER_LIMIT = 2_000
SMALL_DOCUMENT_PACKAGES = (
    # Caps are intentionally set for typical scanned Indian-language pages.
    # They permit low-cost confidence purchases while still covering Sarvam
    # translation, Vision/OCR, Razorpay fees, and a sustainable margin.
    {"id": "starter", "name": "Starter", "max_pages": 2, "max_characters": 5_000, "amount": 1900},
    {"id": "basic", "name": "Basic", "max_pages": 5, "max_characters": 13_000, "amount": 3900},
    {"id": "standard", "name": "Standard", "max_pages": 8, "max_characters": 21_000, "amount": 6900},
    {"id": "plus", "name": "Plus", "max_pages": 10, "max_characters": 26_000, "amount": 8900},
)
CHARACTER_BLOCK_SIZE = 10_000
PRICE_PER_CHARACTER_BLOCK = 4900  # ₹49 per started 10,000 characters
MINIMUM_FULL_PDF_AMOUNT = 4900  # ₹49 minimum for documents outside packages
EXTRA_PAGE_AMOUNT = 1500  # ₹15 for each page after the 10-page Plus plan
EXTRA_CHARACTER_BLOCK_AMOUNT = 2500  # ₹25 per started 10K chars above Plus

# Business information
BUSINESS_INFO = {
    "name": "LipiTranslate",
    "description": "AI-Powered PDF Translation",
    "theme_color": "#3399ff",
    "logo": "",
    "contact": {
        "email": "lipitranslate.general@gmail.com",
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


def estimate_selected_characters(total_pages: int, billable_characters: int, page_limit: int) -> int:
    """Conservative per-range estimate before locked pages are OCR-read.

    Direct-text PDFs use their exact document count as a proportional estimate;
    scanned PDFs use the same safe page estimate used for the full quote.
    The server validates it again at checkout, so a browser cannot select an
    under-priced page package.
    """
    if total_pages < 1 or billable_characters < 1:
        return 0
    return math.ceil(billable_characters * min(page_limit, total_pages) / total_pages)


def available_page_packages(total_pages: int, billable_characters: int) -> list[Dict]:
    """Return only fixed packages that are safe for this document's range."""
    available: list[Dict] = []
    for package in SMALL_DOCUMENT_PACKAGES:
        page_limit = min(total_pages, int(package["max_pages"]))
        if page_limit <= FREE_PAGES_LIMIT:
            continue
        estimated_characters = estimate_selected_characters(
            total_pages, billable_characters, page_limit,
        )
        if estimated_characters <= int(package["max_characters"]):
            available.append({
                "id": package["id"],
                "name": package["name"],
                "page_limit": page_limit,
                "amount": package["amount"],
                "amount_inr": package["amount"] / 100,
                "max_characters": package["max_characters"],
                "estimated_characters": estimated_characters,
            })
    return available


def calculate_full_pdf_amount(total_pages: int, billable_characters: int) -> int:
    """A clear incremental quote for the whole document.

    For documents above 10 pages, continue from Plus instead of abruptly
    restarting the price at ₹49 per character block. The page increment covers
    normal scanned pages; the text increment protects against unusually dense
    documents whose Sarvam usage is genuinely higher.
    """
    plus = SMALL_DOCUMENT_PACKAGES[-1]
    if total_pages <= int(plus["max_pages"]):
        return max(
            MINIMUM_FULL_PDF_AMOUNT,
            math.ceil(billable_characters / CHARACTER_BLOCK_SIZE) * PRICE_PER_CHARACTER_BLOCK,
        )

    extra_pages = total_pages - int(plus["max_pages"])
    page_increment = extra_pages * EXTRA_PAGE_AMOUNT
    overflow_characters = max(0, billable_characters - int(plus["max_characters"]))
    character_increment = math.ceil(overflow_characters / CHARACTER_BLOCK_SIZE) * EXTRA_CHARACTER_BLOCK_AMOUNT
    return int(plus["amount"]) + max(page_increment, character_increment)


def full_pdf_pricing_details(total_pages: int, billable_characters: int) -> str:
    """Customer-facing explanation of the exact full-PDF quote."""
    plus = SMALL_DOCUMENT_PACKAGES[-1]
    if total_pages <= int(plus["max_pages"]):
        return "All document pages"
    extra_pages = total_pages - int(plus["max_pages"])
    page_increment = extra_pages * EXTRA_PAGE_AMOUNT
    overflow_characters = max(0, billable_characters - int(plus["max_characters"]))
    character_increment = math.ceil(overflow_characters / CHARACTER_BLOCK_SIZE) * EXTRA_CHARACTER_BLOCK_AMOUNT
    additional = max(page_increment, character_increment)
    if character_increment > page_increment:
        return f"₹89 up to 10 pages + ₹{additional / 100:.0f} for dense additional text"
    return f"₹89 up to 10 pages + ₹{additional / 100:.0f} for {extra_pages} additional page{'s' if extra_pages != 1 else ''}"


# ============================================================================
# PAYMENT CALCULATION
# ============================================================================

def calculate_payment(total_pages: int, billable_characters: int = 0) -> Dict:
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
    if total_pages < 1:
        raise ValueError("A document must contain at least one page")

    # Pages within free limit
    free_pages = min(total_pages, FREE_PAGES_LIMIT)
    
    # Pages that need payment
    paid_pages = max(0, total_pages - FREE_PAGES_LIMIT)
    
    if paid_pages == 0:
        amount_paise = 0
        pricing_model = "free_preview"
        package_id = "free"
        package_name = "Free preview"
        package_limit_pages = FREE_PAGES_LIMIT
        package_limit_characters = FREE_CHARACTER_LIMIT
    else:
        if billable_characters <= 0:
            raise ValueError("Billable character count is required to quote this PDF")
        # A page package covers the whole document when its page cap reaches
        # the uploaded PDF. Character count prices only documents above the
        # available 10-page package range, avoiding a duplicate Full PDF
        # price for a five-page document already covered by Basic.
        package = next(
            (item for item in SMALL_DOCUMENT_PACKAGES
             if total_pages <= item["max_pages"] and billable_characters <= item["max_characters"]),
            None,
        )
        if package:
            amount_paise = package["amount"]
            pricing_model = "document_package"
            package_id = package["id"]
            package_name = package["name"]
            package_limit_pages = package["max_pages"]
            package_limit_characters = package["max_characters"]
        else:
            amount_paise = calculate_full_pdf_amount(total_pages, billable_characters)
            pricing_model = "full_pdf_character_based"
            package_id = "full_pdf"
            package_name = "Full PDF"
            package_limit_pages = total_pages
            package_limit_characters = billable_characters
    
    # Convert to INR
    amount_inr = amount_paise / 100
    
    # Build message
    if paid_pages == 0:
        message = f"Your {total_pages}-page document is covered by the free preview."
    else:
        message = f"{package_name} full-document translation: {format_amount(amount_paise)}"
    
    return {
        "total_pages": total_pages,
        "free_pages": free_pages,
        "paid_pages": paid_pages,
        "billable_characters": billable_characters,
        "pricing_model": pricing_model,
        "package_id": package_id,
        "package_name": package_name,
        "package_limit_pages": package_limit_pages,
        "package_limit_characters": package_limit_characters,
        "amount": amount_paise,
        "amount_inr": amount_inr,
        "full_pdf_amount": calculate_full_pdf_amount(total_pages, billable_characters) if paid_pages else 0,
        "full_pdf_amount_inr": calculate_full_pdf_amount(total_pages, billable_characters) / 100 if paid_pages else 0,
        "full_pdf_details": full_pdf_pricing_details(total_pages, billable_characters) if paid_pages else "",
        "requires_payment": paid_pages > 0,
        "message": message,
        "available_packages": available_page_packages(total_pages, billable_characters) if paid_pages else [],
    }


def calculate_selected_package(
    package_id: str, total_pages: int, billable_characters: int,
) -> Dict:
    """Return the exact checkout amount and page limit a customer selected.

    The first page is always free. Small plans intentionally unlock a limited
    PDF so a customer can verify quality before paying for more pages.
    """
    if total_pages < 2:
        raise ValueError("Payment is not required for a one-page document")

    selected_id = (package_id or "full_pdf").strip().lower()
    if selected_id == "full_pdf":
        quote = calculate_payment(total_pages, billable_characters)
        # A customer explicitly choosing Full PDF receives all pages even
        # where their document would otherwise qualify for a smaller tier.
        if quote["package_id"] != "full_pdf":
            quote.update({
                "package_id": "full_pdf",
                "package_name": "Full PDF",
                "package_limit_pages": total_pages,
                "package_limit_characters": billable_characters,
                "amount": quote["full_pdf_amount"],
                "amount_inr": quote["full_pdf_amount_inr"],
                "pricing_model": "full_pdf_character_based",
            })
        quote["page_limit"] = total_pages
        quote["message"] = f"Full PDF translation: {format_amount(quote['amount'])}"
        return quote

    package = next((item for item in SMALL_DOCUMENT_PACKAGES if item["id"] == selected_id), None)
    if not package:
        raise ValueError("Please select a valid translation plan")
    if total_pages <= FREE_PAGES_LIMIT:
        raise ValueError("Payment is not required for this document")

    page_limit = min(total_pages, int(package["max_pages"]))
    selected_characters = estimate_selected_characters(
        total_pages, billable_characters, page_limit,
    )
    if selected_characters > int(package["max_characters"]):
        raise ValueError(
            f"{package['name']} is not available for this document because its selected pages exceed the plan's text limit. Please choose the character-based Full PDF quote."
        )
    return {
        "total_pages": total_pages,
        "free_pages": FREE_PAGES_LIMIT,
        "paid_pages": max(0, page_limit - FREE_PAGES_LIMIT),
        "billable_characters": selected_characters,
        "pricing_model": "selected_page_package",
        "package_id": package["id"],
        "package_name": package["name"],
        "package_limit_pages": package["max_pages"],
        "package_limit_characters": package["max_characters"],
        "page_limit": page_limit,
        "amount": package["amount"],
        "amount_inr": package["amount"] / 100,
        "requires_payment": True,
        "message": f"{package['name']} unlocks the first {page_limit} pages: {format_amount(package['amount'])}",
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
    logger.info("Packages: ₹19 / ₹39 / ₹69 / ₹89, then ₹49 per started 10K characters")
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
    test_cases = [(2, 3_000), (5, 8_000), (8, 12_000), (11, 25_000)]
    
    print("\n" + "=" * 70)
    print("PAYMENT CALCULATION TESTS")
    print("=" * 70)
    
    for pages, characters in test_cases:
        calc = calculate_payment(pages, characters)
        print(f"\n{pages} pages / {characters} chars:")
        print(f"  Free: {calc['free_pages']}, Paid: {calc['paid_pages']}")
        print(f"  Amount: {format_amount(calc['amount'])}")
        print(f"  Message: {calc['message']}")
