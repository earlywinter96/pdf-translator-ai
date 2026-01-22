import type { Metadata } from "next";
import ConvertClient from "@/components/ConvertClient";

export const metadata: Metadata = {
  title: "Upload PDF for Translation | AI PDF Translator",
  description:
    "Upload scanned or text-based PDFs and translate them into English or Indian languages using AI-powered OCR and document translation.",
  keywords: [
    "translate pdf",
    "pdf translator",
    "ai pdf translation",
    "translate scanned pdf",
    "ocr pdf translation",
    "gujarati pdf translation",
    "hindi pdf translation",
    "marathi pdf translation",
  ],
};

export default function ConvertPage() {
  return <ConvertClient />;
}
