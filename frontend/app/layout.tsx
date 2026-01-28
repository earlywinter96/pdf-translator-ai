import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

/* ================= SEO METADATA ================= */

export const metadata: Metadata = {
  title: {
    default: "LipiTranslate – PDF & OCR Translator for Indian Languages",
    template: "%s | LipiTranslate",
  },
  description:
    "Translate PDFs and scanned documents using OCR. LipiTranslate supports Hindi, Marathi, Gujarati and English with fast AI-powered translation.",
  keywords: [
    "pdf translator",
    "ocr pdf translation",
    "hindi pdf to english",
    "marathi pdf translator",
    "gujarati pdf to english",
    "scan pdf translate",
    "ai pdf translator india",
  ],
  alternates: {
    canonical: "https://www.lipitranslate.in/",
  },
  openGraph: {
    title: "LipiTranslate – PDF & OCR Translator",
    description:
      "Translate PDFs & scanned documents in Hindi, Marathi, Gujarati & English using AI-powered OCR.",
    url: "https://www.lipitranslate.in/",
    siteName: "LipiTranslate",
    type: "website",
    locale: "en_IN",
  },
  twitter: {
    card: "summary_large_image",
    title: "LipiTranslate – PDF & OCR Translator",
    description:
      "AI-powered PDF & OCR translation for Hindi, Marathi, Gujarati & English.",
  },
  metadataBase: new URL("https://www.lipitranslate.in"),
};

/* ================= ROOT LAYOUT ================= */

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} bg-[#020617] text-gray-200 antialiased`}
      >
        <Navbar />

        <main className="pt-20 min-h-screen">
          {children}
        </main>

        <Footer />
      </body>
    </html>
  );
}
