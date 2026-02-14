"use client";

/* ================= FAQ JSON-LD SCHEMA ================= */

export default function FAQSchema() {
  const schema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "What file types are supported?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text":
            "We currently support PDF files only, including both scanned and text-based PDFs. The maximum file size is 25MB."
        }
      },
      {
        "@type": "Question",
        "name": "How accurate is the translation?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text":
            "Our AI achieves over 95% accuracy for printed text in Gujarati, Hindi, and Marathi. Accuracy may vary for handwritten or low-quality scans."
        }
      },
      {
        "@type": "Question",
        "name": "Is my data safe?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text":
            "Yes. Files are processed temporarily and automatically deleted after download. We never store your documents."
        }
      },
      {
        "@type": "Question",
        "name": "How long does translation take?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text":
            "Most PDFs are translated within 2–3 minutes. Very large PDFs with 300+ pages may take longer."
        }
      }
    ]
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
