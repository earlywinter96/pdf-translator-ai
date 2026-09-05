# PDF-Translator-AI 🇮🇳  
LIVE : https://pdf-translator-ai-xgu2.vercel.app/


**AI-powered PDF translation platform for Indian regional languages**

A production-ready system currently serving **Gujarati, Hindi, Marathi and English** PDF translation. Additional Indian languages are being quality-tested before release. Designed for real-world document complexity common in Indian workflows.

---

## 🎯 Why This Exists

India produces massive volumes of PDFs in:
- Government notifications
- Legal and compliance documents
- Educational content
- Financial & banking reports
- Healthcare and public sector communication

Most translation tools:
- Fail on mixed-language PDFs (English + Indic)
- Break document structure
- Do not support Indian scripts reliably
- Are not API-first or scalable

**PDF-Translator-AI** addresses these gaps with an AI-driven, Indian-language–focused translation pipeline.

---

## 🧠 Solution Overview

PDF-Translator-AI combines:
- Layout-aware PDF text extraction
- AI-powered Indic language translation
- Chunk-based processing for large documents
- Clean REST APIs for integration with existing systems

Built to support **government, enterprise, ed-tech, and legal use cases** across India.

---

## 🌐 Supported Indian Languages

- Hindi (हिन्दी)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Kannada (ಕನ್ನಡ)
- Malayalam (മലയാളം)
- Marathi (मराठी)
- Gujarati (ગુજરાતી)
- Bengali (বাংলা)
- Punjabi (ਪੰਜਾਬੀ)
- Odia, Assamese, Urdu *(extensible)*

> Language support depends on the configured AI model or translation engine.

---

## ✨ Core Capabilities

### 🇮🇳 Indic-Focused Translation
- Optimized prompts for Indian syntax and grammar
- Handles code-mixed documents (English + Indic)
- Preserves cultural and contextual meaning
- Unicode-safe rendering for all Indic scripts

### 📄 PDF Processing
- Extracts text from structured PDFs
- Handles headers, paragraphs, lists, and tables
- Chunk-based translation avoids token overflow
- OCR-ready design for scanned Indian documents

### 🔌 Backend API
- RESTful, stateless architecture
- Scalable and cloud-ready
- Secure environment-based configuration
- Easy integration with government or enterprise systems

### 🖥️ Frontend UI
- Simple upload & translate workflow
- Language selection for Indian scripts
- Progress tracking for large PDFs
- Replaceable with custom portals

---

## 🧱 High-Level Architecture

```

User / Client System
|
v
Frontend (Web / Portal)
|
v
Backend API
|
+–– PDF Extraction Engine
|
+–– Indic Translation Service
|
+–– AI Model / Translation API

````

---

## 🛠️ Technology Stack

### Backend
- Python
- FastAPI / Flask
- Async processing for large PDFs
- Environment-driven config

### Frontend
- Modern JavaScript framework
- API-first design
- Lightweight UI layer

### AI / NLP
- Large Language Models (LLMs)
- Indic-language optimized prompts
- Context-aware chunk translation

---

## ⚙️ Installation & Setup

### Clone Repository

```bash
git clone https://github.com/earlywinter96/pdf-translator-ai.git
cd pdf-translator-ai
````

---

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create environment file:

```bash
cp .env.example .env
```

Example `.env` configuration:

```env
SARVAM_API_KEY=your_sarvam_api_key
SARVAM_MODEL=sarvam-translate:v1
GEMINI_API_KEY=your_gemini_api_key  # visualization only
DEFAULT_TARGET_LANGUAGE=hi
MAX_CHUNK_SIZE=2000
```

Start backend server:

```bash
uvicorn main:app --reload --port 8000
```

---

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Access UI at:

```
http://localhost:3000
```

---

## 🔌 API Usage

### Translate PDF to Indian Language

```http
POST /translate/pdf
```

**Parameters**

* `file`: PDF document
* `target_language`: `hi`, `ta`, `te`, `kn`, `ml`, `mr`, etc.

**Response Example**

```json
{
  "status": "completed",
  "target_language": "hi",
  "pages_processed": 18,
  "output_file": "translated_hi.pdf"
}
```

---

## 🧪 cURL Example

```bash
curl -X POST http://localhost:8000/translate/pdf \
  -F "file=@gov_notification.pdf" \
  -F "target_language=bn"
```

---

## 📂 Repository Structure

```
pdf-translator-ai/
│
├── backend/
│   ├── main.py              # API entrypoint
│   ├── services/            # Translation & Indic logic
│   ├── models/              # Request/response schemas
│   ├── utils/               # PDF helpers
│
├── frontend/
│   └── src/
│       ├── components/
│       ├── services/
│       └── pages/
│
└── docker-compose.yml
```

---

## 🚢 Deployment

* Docker-ready
* Suitable for:

  * Indian government infrastructure
  * Enterprise private clouds
  * On-premise deployments

```bash
docker compose up --build
```

---

## 🔐 Security & Compliance

* API keys stored via environment variables
* No hard-coded credentials
* Compatible with auth layers (JWT / OAuth)
* Suitable for sensitive Indian documents

---

## 🧩 Roadmap (India-Focused)

* OCR support for scanned regional PDFs
* Batch translation for large document sets
* Translation memory for consistency
* Cost-optimized routing per language
* Support for 22 Scheduled Indian Languages
* SaaS dashboard with usage analytics

---

## 🤝 Contributions

We welcome:

* Indic NLP improvements
* Language accuracy tuning
* Performance optimization
* Enterprise readiness features

Fork → Feature Branch → Pull Request

---

## 📜 License

MIT License
Free for commercial and non-commercial use.

---

## 📬 Contact & Collaboration

Open an issue for feature requests, partnerships, or enterprise integrations.
