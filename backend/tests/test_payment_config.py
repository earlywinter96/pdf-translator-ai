"""Regression tests for the server-authoritative document offers."""

from pathlib import Path
import unittest

from app.payment.payment_config import calculate_payment, calculate_selected_package


class PricingTests(unittest.TestCase):
    def test_best_fixed_offer_covers_complete_document(self):
        cases = [
            (1, 2_000, "free", 0),
            (2, 1_500, "starter", 5),
            (5, 7_000, "basic", 19),
            (8, 14_000, "standard", 29),
            (10, 16_000, "plus", 39),
        ]
        for pages, characters, package_id, amount_inr in cases:
            with self.subTest(pages=pages):
                quote = calculate_payment(pages, characters)
                self.assertEqual(quote["package_id"], package_id)
                self.assertEqual(quote["amount_inr"], amount_inr)
                self.assertEqual(quote["package_limit_pages"], pages)
                if pages > 1:
                    self.assertEqual([item["id"] for item in quote["available_packages"]], [package_id])

    def test_character_boundary_falls_back_to_full_pdf(self):
        quote = calculate_payment(10, 18_001)
        self.assertEqual(quote["package_id"], "full_pdf")
        self.assertEqual(quote["amount_inr"], 98)
        self.assertEqual(quote["available_packages"], [])

    def test_full_pdf_price_scales_by_started_character_blocks(self):
        quote = calculate_payment(100, 80_000)
        self.assertEqual(quote["package_id"], "full_pdf")
        self.assertEqual(quote["amount_inr"], 392)
        self.assertIn("80,000 characters", quote["full_pdf_details"])

    def test_selected_order_amount_is_backend_quote(self):
        quote = calculate_payment(5, 7_000)
        selected = calculate_selected_package("basic", 5, 7_000)
        self.assertEqual(selected["amount"], quote["amount"])
        self.assertEqual(selected["page_limit"], 5)

    def test_browser_cannot_select_different_tier(self):
        with self.assertRaisesRegex(ValueError, "one eligible offer"):
            calculate_selected_package("plus", 3, 7_000)

    def test_frontend_does_not_supply_order_amount(self):
        source = (Path(__file__).parents[2] / "frontend/app/usepayment.ts").read_text()
        create_order_body = source.split("/api/payment/create-order", 1)[1].split("const orderData", 1)[0]
        self.assertNotIn("amount:", create_order_body)


if __name__ == "__main__":
    unittest.main()
