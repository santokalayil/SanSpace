---
name: research-topic
description: |
  Research ANY topic — news, science, business, people, events, products, concepts, or comparisons — by searching the live internet and synthesising authoritative, up-to-date answers grounded in real sources. Every factual claim is cited with a URL; nothing is drawn from LLM training memory alone.

  USE THIS SKILL whenever the user asks:
  - "research X", "look up X", "find out about X", "what is X"
  - "what's happening with X", "latest news on X", "current status of X"
  - "compare X and Y", "which is better X or Y"
  - "who is X", "what does company X do", "is X still a thing"
  - "explain X to me", "summarise X", "give me a briefing on X"
  - "fact-check X", "is it true that X", "verify X"
  - ANY question where the answer might have changed since the LLM's training cutoff

  NEVER rely on training memory to answer — always search live sources first. If search tools are unavailable, say so and stop.
---

# research-topic

Research any topic by searching the live internet and cross-validating across multiple authoritative sources. **Every factual claim must be backed by a fetched URL.** Nothing is stated from LLM training memory alone.

---

## Core principle

> "I don't know what I don't know I'm missing. The only safe default is to fetch before answering."

Training data has a cutoff. APIs change. Companies pivot. People's roles change. Products get discontinued. A confident-sounding answer from memory may be months or years out of date. This skill exists to prevent that failure mode.

---

## Phase 0 — Scope the research

Before searching, confirm (infer from context or ask if ambiguous):

1. **Topic** — what exactly to research
2. **Angle** — what the user needs to know: overview, latest developments, comparison, deep technical detail, quick fact-check
3. **Recency requirement** — is timeliness critical? (news, prices, versions, regulations → yes; historical facts, concepts → less so)
4. **Depth** — quick answer (2-3 sources) vs thorough briefing (5-8 sources vs cross-checked)

---

## Phase 1 — Formulate search queries

Construct **at least 3 varied queries** before searching. Variation is essential — a single query creates a monoculture result set that misses contrary data.

Query design rules:
- **Different angles**: one broad query, one narrow/specific, one comparative or "vs", one recency-focused (add year or "2025" / "2026")
- **Different intents**: factual (what is), news (latest), critical (problems / criticism / risks)
- **Avoid leading phrasing** that only surfaces confirming results

Example for topic "Anthropic Claude 4":
```
"Anthropic Claude 4 release date 2026"
"Claude 4 capabilities benchmark comparison"
"Claude 4 criticism limitations problems"
"Anthropic latest model news April 2026"
```

---

## Phase 2 — Fetch sources

### Tool roles

| Tool | Role |
|---|---|
| `firecrawl_search` | **Discovery only** — find which URLs exist and are relevant |
| `fetch_webpage` | **Content reading** — fetch full page content from discovered URLs |

This two-step split keeps Firecrawl usage lean (search credits only) while using `fetch_webpage` for the actual reading.

### Step 1 — Discover URLs with `firecrawl_search`

Run all queries from Phase 1 in **parallel** using `firecrawl_search`. Keep it simple — no `scrapeOptions`:

```
firecrawl_search(
  query: "<query>",
  limit: 5
)
```

Collect the **URL, title, and snippet** from every result. Do not read page content yet — that happens in Phase 3.

Run all 3+ queries in parallel. You should end up with 10–25 candidate URLs total.

### Step 2 — Rank and filter

From the candidate URLs, select the **top 4–6** that are most likely to be authoritative. Use the source priority table in Phase 3 to rank them. Discard duplicates, SEO farms, and listicles.

### Fallback — Firecrawl unavailable

Only if Firecrawl returns auth errors: derive likely URLs from the topic name and skip to Phase 3 directly.

| Topic type | URLs to try |
|---|---|
| Any concept / person / event | `https://en.wikipedia.org/wiki/<Topic_underscored>` |
| Python package | `https://pypi.org/pypi/<package>/json`, `https://github.com/<org>/<repo>` |
| Technology / protocol | Official spec site, GitHub org, `<project>.dev` or `<project>.io` |
| Company | `https://en.wikipedia.org/wiki/<Company>`, company's own site |
| News / current events | `https://news.ycombinator.com/`, `https://www.bbc.com/news`, Reuters |
| Scientific topic | `https://arxiv.org/search/?query=<topic>`, Wikipedia |
| Standards / RFCs | `https://www.rfc-editor.org/search/rfc_search_detail.php?title=<topic>` |

---

## Phase 3 — Select and scrape top sources

From all search results, select the **top 4–6 sources** most likely to be authoritative and up-to-date, using this priority order:

| Priority | Source type | Examples |
|---|---|---|
| 1 | Primary / official | Official site, press release, official docs, government source |
| 2 | High-credibility journalism | Reuters, AP, BBC, FT, WSJ, NYT, The Verge, Ars Technica |
| 3 | Peer-reviewed / academic | ArXiv, PubMed, Nature, ACM, IEEE |
| 4 | Reputable secondary | Wikipedia (for stable facts), Hacker News summary posts |
| 5 | Community / aggregator | Reddit (for current sentiment), aggregator sites |

**Discard:** SEO-farm content, listicles with no citations, press release aggregators with no original reporting.

Fetch all selected URLs in **parallel** using `fetch_webpage`:

```
fetch_webpage(
  urls: ["<url1>", "<url2>", ...],
  query: "<topic or specific question>"
)
```

The `query` parameter guides content extraction — `fetch_webpage` will return the sections of the page most relevant to your query.

Fetch all 4–6 sources in a single parallel call. Extract the relevant content from each response.

**GitHub repos:** prefer the raw README URL — `https://raw.githubusercontent.com/<org>/<repo>/main/README.md` — it's faster and cleaner than scraping the HTML page.

---

## Phase 4 — Cross-validate claims

This is the most important phase. Do not skip it.

For each key factual claim:
1. How many sources confirm it?
2. Does any source contradict, qualify, or add nuance to it?
3. What is the most recent date any source gives for this claim?

Categorise each claim:
- **Confirmed**: ≥ 2 independent sources agree, no contradictions found
- **Unconfirmed**: only 1 source, or source credibility is uncertain
- **Contested**: sources disagree — report both positions and their sources
- **Outdated risk**: claim found but source is > 6 months old for a fast-moving topic

**Never merge contradicting sources into a single confident claim.** Surface the disagreement.

---

## Phase 5 — Handle knowledge gaps honestly

If search returns no useful results for a sub-question:
- State clearly: "No current source found for [X]. The following is from training memory and may be outdated: [claim]."
- Do not invent citations.
- Do not silently blend memory with sourced facts.

If a topic is highly specialised and primary sources are paywalled:
- Report what abstracts / summaries are accessible.
- Note that full-text verification was not possible.

---

## Phase 6 — Produce the report

Output a structured research briefing directly in the conversation (not a separate file, unless the user asks for one).

### Format

---

## Research: [Topic]

**Researched:** [date]  
**Depth:** [quick / standard / thorough]  
**Queries used:** [list the actual queries run]  
**Sources scraped:** [count]

---

### Summary
2–4 sentence answer to the core question. Every sentence cites at least one source inline as `[Source Name](URL)`.

---

### Key findings

Bullet list of the most important confirmed facts. Each bullet ends with `— [Source](URL)`.

---

### Recent developments *(only if time-sensitive)*

What has changed in the last 3–6 months. Dated entries. Each entry cites source.

---

### Contested / unclear points

Explicit table or bullets of anything sources disagree on, or that couldn't be confirmed:

| Claim | Source A says | Source B says | Verdict |
|---|---|---|---|
| [claim] | [position + URL] | [position + URL] | Contested / Unconfirmed |

*(Omit section if nothing is contested.)*

---

### Sources

Numbered list of all sources consulted:

1. [Title](URL) — [publication / domain] — [date if known] — [credibility tier: primary / high-credibility / secondary]
2. ...

---

### Caveats

- Any claims that came from training memory (not fetched sources) — labelled clearly
- Any paywalled sources that could only be partially read
- Recency note if topic is fast-moving

---

---

## Output rules (non-negotiable)

- **No unsourced factual claims.** If a fact is not backed by a URL in the sources list, do not state it as fact — state it as unverified.
- **Inline citations on every key claim**, not just a sources list at the end.
- **Verbatim quotes preferred over paraphrasing** for contentious or technical claims.
- **Contradictions must surface** — never silently pick one side.
- **Memory fallback must be labelled** — any claim from training data (not a live fetch) must say "(from training memory, not live-verified)".
- **Recency at the top** — always state when the search was run and the date of the most recent source.

---

## Anti-patterns — never do these

| Anti-pattern | Why it fails |
|---|---|
| Answer the question from memory, then search to "confirm" | Memory anchors the answer; search is just post-hoc rationalisation |
| Use only one search query | Single query misses contrary or qualifying data |
| Quote a search snippet without scraping the full source | Snippets truncate, decontextualise, and can be misleading |
| Blend one-year-old and current sources in the same paragraph | Reader can't tell what's current |
| Say "according to multiple sources" without citing them | Unfalsifiable; hides cherry-picking |
| Skip the contested-claims table because it "complicates" the answer | This is the most useful part for the user |

---

## Research modes (choose based on depth needed)

| Mode | Search queries | URLs fetched | Use when |
|---|---|---|---|
| **Quick fact** | 1–2 via `firecrawl_search` | 2–3 via `fetch_webpage` | Single verifiable fact, fast answer needed |
| **Standard briefing** | 3–4 via `firecrawl_search` | 4–6 via `fetch_webpage` | General "what is X" or "latest on X" |
| **Thorough analysis** | 5+ via `firecrawl_search` | 7–10 via `fetch_webpage` | Comparisons, contested claims, deep technical topics |

Default to **Standard briefing** unless the user specifies or the topic clearly warrants another mode.

---

## Trigger examples

These are sample phrases that should invoke this skill (non-exhaustive):

- "Research the current state of AI regulation in the EU"
- "What's the latest on OpenAI's o3 model?"
- "Who is Dario Amodei and what has he said recently?"
- "Compare Cursor and Windsurf editors as of 2026"
- "Is Kubernetes still the default for container orchestration?"
- "What happened to the FTX case?"
- "Summarise the recent results from the ACL 2026 conference"
- "Fact-check: did Apple remove the headphone jack from all MacBooks?"
- "What is the current interest rate in the UK?"
- "Brief me on quantum computing progress this year"
- "Give me a pricing comparison of Firecrawl, Apify, and Browserless"
- "What are the known limitations of GPT-4o as of today?"
