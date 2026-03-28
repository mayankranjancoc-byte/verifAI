# VerifAI — Misinformation Intelligence

A single-screen, chat-based misinformation detection app that verifies claims across multiple real sources using AI-powered analysis.

![VerifAI Screenshot](docs/screenshot.png)

## Features

- **Multimodal Input** — Text, URLs, images, audio, and video
- **Real-time Fact Checking** — Google Fact Check Tools API + web search
- **AI-Powered Verdicts** — Reality score (0-100) with TRUE / FALSE / MISLEADING / UNVERIFIED ratings
- **Inline Heatmaps** — Suspicious words and phrases highlighted with risk scores
- **Context Drift Detection** — Identifies recycled or out-of-context content
- **Trust Trail** — Supporting and contradicting sources displayed side by side
- **Emotion Analysis** — Detects fear-mongering, urgency, and manipulation tactics
- **Hinglish Humor** — Witty roasts paired with factual explanations
- **Multimodal Consistency** — Image/text, audio/text, and video/text cross-checking

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vite + React, Vanilla CSS |
| Backend | FastAPI (Python) |
| AI Inference | Gemini Flash (primary) + OpenRouter (fallback) |
| Fact-Checking | Google Fact Check Tools API |
| URL Scraping | Trafilatura + BeautifulSoup |

## Quick Start

### 1. Install dependencies

```bash
# Frontend
npm install

# Backend
cd backend
pip install -r requirements.txt
```

### 2. Set API keys

```bash
# Required: at least one of these
set GEMINI_API_KEY=your_gemini_key
set OPENROUTER_API_KEY=your_openrouter_key

# Optional: for enhanced evidence retrieval
set SEARCH_API_KEY=your_google_search_key
set SEARCH_ENGINE_ID=your_custom_search_engine_id
```

### 3. Run

```bash
# Terminal 1 — Backend (port 8001)
cd backend
python main.py

# Terminal 2 — Frontend (port 5173)
npm run dev
```

Open `http://localhost:5173` in your browser.

## Architecture

```
├── src/                    # React frontend
│   ├── App.jsx             # Root — chat state, API integration
│   ├── index.css           # Design system (CSS custom properties)
│   └── components/
│       ├── Welcome.jsx     # Landing screen with suggestion chips
│       ├── InputBar.jsx    # Text, file upload, voice recording
│       ├── ChatMessage.jsx # User bubble + AI Intel Card
│       ├── IntelCard.jsx   # Orchestrates analysis sub-blocks
│       ├── VerdictBlock.jsx    # Reality score + verdict badge
│       ├── HeatmapBlock.jsx    # Inline text highlighting
│       ├── ContextDrift.jsx    # Content reuse warning
│       ├── KeyInsights.jsx     # Evidence findings
│       ├── TrustTrail.jsx      # Source cards
│       ├── EmotionBar.jsx      # Manipulation intensity
│       ├── HumorBlock.jsx      # Hinglish roast
│       └── ActionButtons.jsx   # View Sources, Share, Re-analyze
│
├── backend/                # FastAPI backend
│   ├── main.py             # Server entry point
│   ├── routes/
│   │   └── analyze.py      # /api/analyze endpoint
│   ├── pipeline/
│   │   ├── gemini_client.py       # AI client with fallback
│   │   ├── claim_extractor.py     # LLM claim extraction
│   │   ├── evidence_retriever.py  # Fact-check API + web search
│   │   ├── verdict_engine.py      # Verdict + reality score
│   │   ├── emotion_analyzer.py    # Manipulation detection
│   │   ├── humor_generator.py     # Hinglish humor
│   │   └── multimodal_analyzer.py # Image/audio/video analysis
│   └── utils/
│       └── url_scraper.py  # URL content extraction
```

## Inspired By

- [ARG (AAAI 2024)](https://github.com/HKBUNLP/ARG) — "Bad Actor, Good Advisor" LLM reasoning
- [Unfaker](https://github.com/Fugant1/Unfaker) — API-based fact-checking pipeline
- [Detecting Previously Fact-Checked Claims](https://github.com/firojalam/Detecting-Previously-Fact-Checked-Claims)

## License

MIT
