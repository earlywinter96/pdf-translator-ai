"""Regression tests for server-authoritative, cost-safe document offers."""

from pathlib import Path
import unittest

from app.payment.payment_config import calculate_payment, calculate_selected_package, calculate_full_pdf_amount, available_page_packages


class PricingTests(unittest.TestCase):
    def test_one_page_is_free(self):
        quote = calculate_payment(1, 1_500, [1_500])
        self.assertEqual((quote["package_id"], quote["amount_inr"]), ("free", 0))

    def test_two_page_document_shows_only_starter_full_offer(self):
        quote = calculate_payment(2, 1_500, [700, 800])
        self.assertEqual(quote["package_id"], "starter")
        self.assertEqual(quote["amount_inr"], 5)
        self.assertEqual([item["id"] for item in quote["available_packages"]], ["starter"])

    def test_three_pages_show_partial_starter_and_full_basic(self):
        quote = calculate_payment(3, 2_800, [900, 900, 1_000])
        self.assertEqual(quote["package_id"], "basic")
        self.assertEqual([item["id"] for item in quote["available_packages"]], ["starter", "basic"])
        self.assertEqual(quote["available_packages"][0]["page_limit"], 2)
        self.assertEqual(quote["available_packages"][1]["page_limit"], 3)

    def test_fixed_tier_boundaries(self):
        cases = [(5, 7_000, "basic", 19), (8, 14_000, "standard", 29), (10, 16_000, "plus", 39)]
        for pages, chars, package_id, amount in cases:
            with self.subTest(pages=pages):
                quote = calculate_payment(pages, chars, [chars // pages] * pages)
                self.assertEqual((quote["package_id"], quote["amount_inr"]), (package_id, amount))

    def test_character_boundary_falls_back_to_dynamic_full_pdf(self):
        chars = 18_001
        quote = calculate_payment(10, chars, [1_800] * 9 + [1_801])
        self.assertEqual(quote["package_id"], "full_pdf")
        self.assertEqual(quote["amount_inr"], 98)
        self.assertIn("18,001 characters", quote["full_pdf_details"])

    def test_large_document_never_uses_ten_page_price_as_full_price(self):
        quote = calculate_payment(100, 80_000, [800] * 100)
        self.assertEqual(quote["package_id"], "full_pdf")
        self.assertEqual(quote["amount_inr"], 392)
        self.assertGreater(quote["amount"], 3900)

    def test_partial_offer_uses_only_included_page_characters(self):
        pages = [900, 900] + [2_000] * 38
        offers = available_page_packages(40, sum(pages), pages)
        starter = next(item for item in offers if item["id"] == "starter")
        self.assertEqual(starter["estimated_characters"], 1_800)
        self.assertFalse(starter["is_full_document"])

    def test_selected_amount_matches_backend_quote(self):
        page_chars = [900, 900, 1_733, 1_733, 1_734]
        selected = calculate_selected_package("basic", 5, 7_000, page_chars)
        self.assertEqual((selected["amount"], selected["page_limit"]), (1900, 5))
        partial = calculate_selected_package("starter", 5, 7_000, page_chars)
        self.assertEqual((partial["amount"], partial["page_limit"]), (500, 2))

    def test_browser_cannot_select_undisplayed_package(self):
        with self.assertRaisesRegex(ValueError, "not available"):
            calculate_selected_package("plus", 3, 2_800, [900, 900, 1_000])

    def test_full_price_covers_provider_and_checkout_costs(self):
        amount = calculate_full_pdf_amount(100, 80_000, "scan_estimate")
        self.assertGreaterEqual(amount, 26_000)

    def test_frontend_does_not_supply_order_amount(self):
        source = (Path(__file__).parents[2] / "frontend/app/usepayment.ts").read_text()
        create_order_body = source.split("/api/payment/create-order", 1)[1].split("const orderData", 1)[0]
        self.assertNotIn("amount:", create_order_body)

    def test_razorpay_order_uses_server_calculated_amount(self):
        source = (Path(__file__).parents[1] / "app/payment/payment_routes.py").read_text()
        self.assertIn("amount_paise=payment_calc[\"amount\"]", source)
        self.assertNotIn("request.amount", source)


if __name__ == "__main__":
    unittest.main()
