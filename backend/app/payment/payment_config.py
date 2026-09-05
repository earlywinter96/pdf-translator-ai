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

# Customer-facing packages. A package is eligible only when the included page
# range fits both its character cap and its provider/payment cost.
FREE_CHARACTER_LIMIT = 2_000
SMALL_DOCUMENT_PACKAGES = (
    {"id": "starter", "name": "Starter", "max_pages": 2, "max_characters": 4_000, "amount": 500},
    {"id": "basic", "name": "Basic", "max_pages": 5, "max_characters": 9_000, "amount": 1900},
    {"id": "standard", "name": "Standard", "max_pages": 8, "max_characters": 14_000, "amount": 2900},
    {"id": "plus", "name": "Plus", "max_pages": 10, "max_characters": 18_000, "amount": 3900},
)
CHARACTER_BLOCK_SIZE = 10_000
PRICE_PER_CHARACTER_BLOCK = 4900  # ₹49 per started 10,000 characters
MINIMUM_FULL_PDF_AMOUNT = 4900  # ₹49 minimum for documents outside packages

# Provider and checkout cost model. Sarvam's published Translate V1 price is
# ₹20 per 10,000 characters. Razorpay's 2% + 18% GST is 2.36% of checkout.
# Sarvam Vision/document digitization is currently ₹0.50/page; it is charged
# only for scan-estimate pages. These values are kept in one engine so pricing
# can be updated when provider invoices change.
SARVAM_TRANSLATION_COST_PER_10K_PAISE = 2_000
SARVAM_DIGITIZATION_COST_PER_PAGE_PAISE = 50
RAZORPAY_FEE_RATE = 0.0236

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


def get_page_characters(
    total_pages: int, billable_characters: int, page_characters: list[int] | None,
) -> list[int]:
    """Return per-page billable characters, with a safe proportional fallback."""
    if page_characters and len(page_characters) == total_pages:
        return [max(0, int(value)) for value in page_characters]
    if total_pages < 1:
        return []
    base, remainder = divmod(max(0, int(billable_characters)), total_pages)
    return [base + (1 if index < remainder else 0) for index in range(total_pages)]


def estimate_provider_cost_paise(
    characters: int, pages: int, pricing_basis: str = "detected",
) -> int:
    """Estimate Sarvam + OCR costs before Razorpay's checkout fee."""
    translation = (max(0, characters) * SARVAM_TRANSLATION_COST_PER_10K_PAISE) / CHARACTER_BLOCK_SIZE
    digitization = (
        max(0, pages) * SARVAM_DIGITIZATION_COST_PER_PAGE_PAISE
        if pricing_basis == "scan_estimate" else 0
    )
    return math.ceil(translation + digitization)


def estimate_checkout_fee_paise(amount_paise: int) -> int:
    return math.ceil(max(0, amount_paise) * RAZORPAY_FEE_RATE)


def estimate_margin_paise(
    amount_paise: int, characters: int, pages: int, pricing_basis: str,
) -> int:
    return amount_paise - estimate_provider_cost_paise(characters, pages, pricing_basis) - estimate_checkout_fee_paise(amount_paise)


def package_offer(
    package: Dict, total_pages: int, page_characters: list[int], pricing_basis: str,
) -> Dict | None:
    """Build a package offer for its actual included page range."""
    page_limit = min(total_pages, int(package["max_pages"]))
    if page_limit <= FREE_PAGES_LIMIT:
        return None
    included_characters = sum(page_characters[:page_limit])
    if included_characters > int(package["max_characters"]):
        return None
    margin = estimate_margin_paise(package["amount"], included_characters, page_limit, pricing_basis)
    if margin < 0:
        return None
    return {
        "id": package["id"],
        "name": package["name"],
        "page_limit": page_limit,
        "amount": package["amount"],
        "amount_inr": package["amount"] / 100,
        "max_characters": package["max_characters"],
        "estimated_characters": included_characters,
        "estimated_cost_inr": estimate_provider_cost_paise(included_characters, page_limit, pricing_basis) / 100,
        "estimated_margin_inr": margin / 100,
        "is_full_document": page_limit == total_pages,
    }


def available_page_packages(
    total_pages: int, billable_characters: int,
    page_characters: list[int] | None = None,
    pricing_basis: str = "detected",
) -> list[Dict]:
    """Return every relevant partial package and the best fixed full offer."""
    pages = get_page_characters(total_pages, billable_characters, page_characters)
    offers: list[Dict] = []
    for package in SMALL_DOCUMENT_PACKAGES:
        offer = package_offer(package, total_pages, pages, pricing_basis)
        if offer:
            offers.append(offer)
        # Once a tier covers the complete document, larger tiers are not
        # relevant to the customer-facing offer list.
        if offer and offer["is_full_document"]:
            break
    return offers


def calculate_full_pdf_amount(total_pages: int, billable_characters: int, pricing_basis: str = "detected") -> int:
    """Character-based price for a document outside the fixed tiers."""
    target = max(MINIMUM_FULL_PDF_AMOUNT, math.ceil(billable_characters / CHARACTER_BLOCK_SIZE) * PRICE_PER_CHARACTER_BLOCK)
    provider_cost = estimate_provider_cost_paise(billable_characters, total_pages, pricing_basis)
    cost_covered = math.ceil(provider_cost / (1 - RAZORPAY_FEE_RATE))
    return max(target, cost_covered)


def full_pdf_pricing_details(total_pages: int, billable_characters: int, pricing_basis: str = "detected") -> str:
    """Customer-facing explanation of the exact full-PDF quote."""
    amount = calculate_full_pdf_amount(total_pages, billable_characters, pricing_basis)
    return f"{billable_characters:,} characters · ₹{amount / 100:.0f} at ₹49 per started 10K characters"


# ============================================================================
# PAYMENT CALCULATION
# ============================================================================

def calculate_payment(
    total_pages: int, billable_characters: int = 0,
    page_characters: list[int] | None = None, pricing_basis: str = "detected",
) -> Dict:
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
        pages = get_page_characters(total_pages, billable_characters, page_characters)
        package = next((item for item in SMALL_DOCUMENT_PACKAGES
                        if (offer := package_offer(item, total_pages, pages, pricing_basis))
                        and offer["is_full_document"]), None)
        if package:
            amount_paise = package["amount"]
            pricing_model = "document_package"
            package_id = package["id"]
            package_name = package["name"]
            package_limit_pages = total_pages
            package_limit_characters = package["max_characters"]
        else:
            amount_paise = calculate_full_pdf_amount(total_pages, billable_characters, pricing_basis)
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
        "full_pdf_amount": calculate_full_pdf_amount(total_pages, billable_characters, pricing_basis) if paid_pages else 0,
        "full_pdf_amount_inr": calculate_full_pdf_amount(total_pages, billable_characters, pricing_basis) / 100 if paid_pages else 0,
        "full_pdf_details": full_pdf_pricing_details(total_pages, billable_characters, pricing_basis) if paid_pages else "",
        "estimated_provider_cost_inr": estimate_provider_cost_paise(billable_characters, total_pages, pricing_basis) / 100,
        "pricing_basis": pricing_basis,
        "requires_payment": paid_pages > 0,
        "message": message,
        "available_packages": available_page_packages(total_pages, billable_characters, page_characters, pricing_basis) if paid_pages else [],
    }


def calculate_selected_package(
    package_id: str, total_pages: int, billable_characters: int,
    page_characters: list[int] | None = None, pricing_basis: str = "detected",
) -> Dict:
    """Return a server-authoritative quote for a displayed package.

    The package id is only a selector; amount and included pages are always
    recomputed from the uploaded document on the server.
    """
    if total_pages < 2:
        raise ValueError("Payment is not required for a one-page document")

    selected_id = (package_id or "full_pdf").strip().lower()
    if selected_id == "full_pdf":
        quote = calculate_payment(total_pages, billable_characters, page_characters, pricing_basis)
        if quote["package_id"] != "full_pdf":
            raise ValueError("Choose the displayed fixed package for this document")
        quote["page_limit"] = total_pages
        quote["message"] = f"Full PDF translation: {format_amount(quote['amount'])}"
        return quote

    package = next((item for item in SMALL_DOCUMENT_PACKAGES if item["id"] == selected_id), None)
    if not package:
        raise ValueError("Please select a valid translation plan")
    if total_pages <= FREE_PAGES_LIMIT:
        raise ValueError("Payment is not required for this document")

    pages = get_page_characters(total_pages, billable_characters, page_characters)
    valid_ids = {
        item["id"] for item in available_page_packages(
            total_pages, billable_characters, pages, pricing_basis
        )
    }
    if selected_id not in valid_ids:
        raise ValueError("This package is not available for this document")
    offer = package_offer(package, total_pages, pages, pricing_basis)
    if not offer:
        raise ValueError("This package is not safe for the selected pages and characters. Please choose another displayed offer.")
    page_limit = offer["page_limit"]
    return {
        "total_pages": total_pages,
        "free_pages": FREE_PAGES_LIMIT,
        "paid_pages": max(0, page_limit - FREE_PAGES_LIMIT),
        "billable_characters": offer["estimated_characters"],
        "pricing_model": "selected_page_package",
        "package_id": package["id"],
        "package_name": package["name"],
        "package_limit_pages": total_pages,
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
    logger.info("Packages: ₹5 / ₹19 / ₹29 / ₹39, then ₹49 per started 10K characters")
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
