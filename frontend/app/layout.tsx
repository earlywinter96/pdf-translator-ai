import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";


const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata = {
  title: "AI PDF Translator – Translate Gujarati, Hindi PDFs to English",
  description:
    "Translate scanned and text-based PDFs from Gujarati, Hindi, and Marathi into English using AI with OCR support.",
};


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
