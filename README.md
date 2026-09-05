# LipiTranslate.in 🇮🇳

**Production PDF translation and OCR for Indian languages**

[Live product](https://www.lipitranslate.in/) · [Founder portfolio](https://my-portfolio2-peach-six.vercel.app/)

LipiTranslate is a commercial document-translation platform founded by **Hemant Solanki**. It helps people translate structured and scanned PDFs while retaining headings, images, tables, and the original visual hierarchy wherever possible.

> **Note:** This repository contains proprietary source code for LipiTranslate. It is public for transparency, portfolio, and technical showcase purposes. Commercial reuse is not permitted without written authorization.

## What the product provides

- Sarvam AI translation for English and major Indian languages, including Gujarati, Hindi, Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi, Odia, Assamese, and Urdu.
- Sarvam Vision/document digitization for scanned PDFs, with a Tesseract fallback when Vision is unavailable.
- Layout-aware PDF extraction and design-preserved translated output, including images and tables where the source structure can be recovered.
- A free first-page translation preview so customers can review quality before payment.
- Razorpay checkout with server-side signature verification and incremental page unlocks.
- Progress reporting while OCR, translation, and PDF generation are running.
- Mobile-friendly original/translated previews, downloadable output, and language-direction validation.
- A Lipi Assistant support chatbot restricted to LipiTranslate questions, with a five-question session limit and email handoff.
- Privacy-safe Discord notifications for visits, uploads, payment funnel events, and translation status.

## Customer pricing

The backend calculates and validates the quote before checkout. Small plans are confidence purchases and include the free first page:

| Unlock | Price |
| --- | ---: |
| First 2 pages (Starter) | ₹19 |
| First 5 pages (Basic) | ₹39 |
| First 8 pages (Standard) | ₹69 |
| First 10 pages (Plus) | ₹89 |
| Full document | ₹89 up to 10 pages, then ₹15 per additional page |

Unusually dense documents can receive a transparent character adjustment. Only plans that fit the document's page and text limits are offered. Payment unlocks only the selected page range; customers can upgrade later and pay the difference.

## Architecture

```text
Next.js frontend (Vercel)
        │
        ▼
FastAPI backend (Render)
   ┌────┼───────────────┐
   ▼    ▼               ▼
PDF/OCR  Sarvam AI    Razorpay
pipeline translation  payments
   │                    │
   └──── design-preserved PDF
```

## Technology

- **Backend:** Python, FastAPI, PyMuPDF, pdfplumber, ReportLab, Tesseract fallback, `httpx`
- **AI:** Sarvam Translate and Sarvam Vision/document digitization; Gemini is used only by the visualization feature
- **Payments:** Razorpay Standard Checkout with server-side order and signature verification
- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Hosting:** Vercel frontend and Render backend

## Run locally

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` (never commit it):

```env
SARVAM_API_KEY=your_sarvam_api_key
SARVAM_MODEL=sarvam-translate:v1
SARVAM_CHAT_MODEL=sarvam-105b-conversations
GEMINI_API_KEY=your_gemini_key
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
```

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

Start Next.js:

```bash
npm run dev
```

Open <http://localhost:3000>.

## Main API routes

- `POST /api/translate` — upload a PDF and start the free first-page preview.
- `GET /api/status/{job_id}` — poll extraction, translation, and PDF-generation progress.
- `GET /api/preview/{job_id}` — retrieve the preview output.
- `POST /api/payment/create-order` — create a validated Razorpay order for a selected package.
- `POST /api/payment/verify` — verify the Razorpay signature and start paid processing.
- `POST /api/support/chat` — ask the site-only Sarvam support assistant.

The Sarvam and Razorpay secrets are read only by the backend. Public frontend variables must never contain a secret key.

## Contributions

LipiTranslate is currently proprietary software.

We welcome suggestions, feedback, bug reports, and collaboration opportunities through GitHub Issues. Code contributions are accepted only with prior approval.

## License

**Proprietary Software — All Rights Reserved**

Copyright © 2026 Hemant Solanki / LipiTranslate.

The source code is publicly available for viewing and evaluation purposes. Commercial use, redistribution, modification, or creation of derivative works requires prior written permission.

For commercial licensing or collaboration inquiries, please contact [lipitranslate.general@gmail.com](mailto:lipitranslate.general@gmail.com).
