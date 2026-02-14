import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

/* ================= LANGUAGE CONFIG ================= */

const TRANSLATOR_PAGES = {
  "gujarati-to-hindi-pdf-translator": {
    from: "Gujarati",
    to: "Hindi",
    fromNative: "ગુજરાતી",
    toNative: "हिन्दी",
  },
  "hindi-to-english-pdf-translator": {
    from: "Hindi",
    to: "English",
    fromNative: "हिन्दी",
    toNative: "English",
  },
  "marathi-to-english-pdf-translator": {
    from: "Marathi",
    to: "English",
    fromNative: "मराठी",
    toNative: "English",
  },
};

/* ================= SEO METADATA ================= */

export function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Metadata {
  const page = TRANSLATOR_PAGES[params.slug as keyof typeof TRANSLATOR_PAGES];

  if (!page) return {};

  return {
    title: `${page.from} to ${page.to} PDF Translator – Free & Online`,
    description: `Translate ${page.from} PDF files to ${page.to} online for free. OCR-supported ${page.from} to ${page.to} PDF translation for scanned and text-based documents.`,
    alternates: {
      canonical: `https://www.lipitranslate.in/${params.slug}`,
    },
  };
}

/* ================= PAGE ================= */

export default function TranslatorPage({
  params,
}: {
  params: { slug: string };
}) {
  const page = TRANSLATOR_PAGES[params.slug as keyof typeof TRANSLATOR_PAGES];

  if (!page) return notFound();

  const { from, to, fromNative, toNative } = page;

  return (
    <main className="max-w-4xl mx-auto px-6 py-24 text-gray-200">

      {/* H1 */}
      <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
        {from} to {to} PDF Translator
      </h1>

      {/* Intro */}
      <p className="text-gray-400 mb-8">
        Translate <strong>{from}</strong> ({fromNative}) PDF documents into{" "}
        <strong>{to}</strong> ({toNative}) using AI-powered OCR. Works with
        scanned PDFs, government documents, textbooks, and certificates.
      </p>

      {/* CTA */}
      <Link
        href="/convert"
        className="inline-block px-6 py-3 mb-12 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium"
      >
        Translate {from} PDF → {to}
      </Link>

      {/* HOW IT WORKS */}
      <section className="space-y-4 mb-12">
        <h2 className="text-2xl font-semibold text-white">
          How to Translate {from} PDF to {to}
        </h2>
        <ol className="list-decimal list-inside text-gray-400 space-y-2">
          <li>Upload your {from} PDF (scanned or digital).</li>
          <li>OCR extracts {from} text accurately.</li>
          <li>AI translates it into {to}.</li>
          <li>Download your translated {to} PDF.</li>
        </ol>
      </section>

      {/* USE CASES */}
      <section className="space-y-4 mb-12">
        <h2 className="text-2xl font-semibold text-white">
          Common Use Cases
        </h2>
        <ul className="list-disc list-inside text-gray-400 space-y-1">
          <li>Government documents & certificates</li>
          <li>NCERT textbooks & study material</li>
          <li>Legal & compliance documents</li>
          <li>Business reports & invoices</li>
        </ul>
      </section>

      {/* FAQ */}
      <section className="space-y-6">
        <h2 className="text-2xl font-semibold text-white">
          Frequently Asked Questions
        </h2>

        <div>
          <h3 className="font-medium text-white">
            Is {from} to {to} PDF translation free?
          </h3>
          <p className="text-gray-400">
            Yes. LipiTranslate offers free {from} to {to} PDF translation
            with OCR support and no signup required.
          </p>
        </div>

        <div>
          <h3 className="font-medium text-white">
            Can you translate scanned {from} PDFs?
          </h3>
          <p className="text-gray-400">
            Yes. Our OCR technology extracts text from scanned PDFs before
            translating them into {to}.
          </p>
        </div>
      </section>

    </main>
  );
}
