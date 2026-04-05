# 🎯 Meridian

> Ask any question about the economy. Watch an AI agent research it in real time — 
> then tell you where the market might be wrong.

[![Built for GLM-5.1 Challenge](https://img.shields.io/badge/GLM--5.1-Challenge-blue?style=for-the-badge)](#)
[![Powered by Z.AI](https://img.shields.io/badge/Powered_by-Z.AI-7B68EE?style=for-the-badge)](https://z.ai)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](#)

---

## What is Meridian?

Most people can't afford a research analyst. Meridian gives anyone the ability to ask 
a complex financial question in plain English — and get back a fully sourced, 
AI-generated research brief in under a minute.

**Try asking:**
- *"What's the current recession probability and how does it compare to prediction markets?"*
- *"Are there any macro signals that suggest the Fed will cut rates this quarter?"*
- *"Find the top 5 events where the market's implied probability differs most from the data."*

Meridian uses **GLM-5.1** — Z.AI's latest model — to autonomously search the Federal 
Reserve's data, SEC filings, prediction markets, and financial news, then reason 
across all of it to produce a cited, structured answer.

---

## 🎬 See it in action

**[▶ Watch the full demo (2 min)](https://meridian-brown.vercel.app)**

![Research Terminal — GLM-5.1 reasoning in real time](screenshots/terminal.png)
*The agent's live reasoning trace: every data source it checks, every conclusion it draws*

![Market Dislocation Screener](screenshots/screener.png)
*The screener surfaces markets where the AI's estimate differs most from market-implied odds*

---

## The core idea: finding where markets are wrong

Prediction markets like Kalshi price the probability of real-world events — Fed rate 
decisions, GDP growth, elections. But market prices aren't always right.

Meridian computes its own probability estimate by analyzing Federal Reserve data, SEC 
filings, and economic indicators — then compares that to what the market is pricing in.
AI estimate:     68% chance of rate cut
Market says:     41% chance
─────────────────────────────────────
Dislocation:     27 percentage points  ← flagged by screener

The **Dislocation Screener** ranks every tracked market by the size of this gap, 
automatically surfacing the most interesting opportunities for deeper research.

---

## How it works

When you ask a question, Meridian's GLM-5.1 agent doesn't just retrieve a stored 
answer — it reasons through the problem in real time:

1. **Plans** which data sources to check (Fed data, SEC filings, news, prediction markets)
2. **Queries** up to 10 specialized tools autonomously
3. **Reasons** through the evidence, checking itself every 5 steps
4. **Writes** a citation-backed research brief with a clear conclusion
5. **Scores** each market for dislocation vs. current prediction market prices

You can watch every step of this process live in the terminal panel — every tool call, 
every intermediate finding, every conclusion.

---

## Quick start

No API key needed for demo mode:
```bash
git clone https://github.com/aaravjj2/Meridian.git && cd Meridian
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
npm install
MERIDIAN_MODE=demo npm run dev
```

Open **http://localhost:3000** and ask your first question.

For live GLM-5.1 inference, get a free API key at [platform.z.ai](https://platform.z.ai):
```bash
MERIDIAN_MODE=live ZAI_API_KEY="your-key" npm run dev
```

---

## What's under the hood

| What you see | What's powering it |
|---|---|
| Live reasoning trace | GLM-5.1 ReAct agent loop with SSE streaming |
| Economic data | Federal Reserve (FRED) — 800,000+ time series |
| Company filings | SEC EDGAR database |
| Market probabilities | Kalshi & Polymarket prediction markets |
| Dislocation scores | AI model probability vs. market-implied probability |
| Semantic memory | ChromaDB vector store for context-aware synthesis |

Full tech stack: Next.js 15, FastAPI, Python, ChromaDB, DuckDB, Recharts.

---

## Built for the GLM 5.1 Challenge

This project was built in one week to demonstrate what's possible when you give 
GLM-5.1 real tools, real data, and a hard problem.

The 200,000-token context window means the agent can read an entire SEC 10-K filing 
plus 20 economic data series in a single pass — something that wasn't practical 
with earlier models.

**[→ View on Devpost](https://build-with-glm-5-1-challenge.devpost.com/)**

---

⚖️ *Meridian is a research tool for informational purposes only. Not investment advice.*
