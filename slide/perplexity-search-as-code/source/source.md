# Source Analysis

## Primary sources

- X thread: https://x.com/perplexity_ai/status/2061506359326384319
- Research article: https://research.perplexity.ai/articles/rethinking-search-as-code-generation
- Agent API sandbox docs: https://docs.perplexity.ai/docs/agent-api/tools/sandbox
- Author: Perplexity
- Published: June 1, 2026

## Verified source facts

- Perplexity introduced `Search as Code` as a new reference architecture for agentic search.
- Instead of invoking search serially through repeated function calls or MCP calls, a model generates Python code inside a secure sandbox.
- The generated code can compose atomized search primitives for retrieval, fan-out, ranking, filtering, deduplication, joining, aggregation, and rendering.
- Perplexity says its Computer product can invoke hundreds or thousands of retrieval operations within minutes.
- The Agentic Search SDK can orchestrate up to thousands of operations inside a single inference turn.
- Search as Code is available through the Perplexity Agent API and is now the default architecture in Perplexity Computer.
- Perplexity evaluated Search as Code against four external systems on DSQA, BrowseComp, HLE, WideSearch, and its unreleased internal WANDR benchmark.
- Perplexity reports Search as Code leading four of five benchmark rows and essentially tying OpenAI on HLE.
- On DSQA, Perplexity reports `0.871`, compared with Anthropic at `0.815`.
- On WANDR, Perplexity reports `0.386`, compared with the next-best system at `0.152`.
- Perplexity says WANDR will be released in the coming weeks. Until then, treat it as an internal benchmark.
- In the CVE case study, Perplexity says Search as Code identified and characterized more than 200 high-severity CVEs with `100%` accuracy while reducing token use `85.1%`, from `288.7K` to `42.9K`.

## Important benchmark caveat

- These are Perplexity-published results, not an independent evaluation.
- The system comparison is not a pure model comparison. Perplexity Search as Code uses GPT-5.5 high reasoning under its production Agent API; other rows use different systems and configurations.
- The strongest claim for the deck is architectural: programmable search primitives can reduce serial tool loops and context pollution.

## Community reactions from replies

- Positive: several replies highlight the shift from rigid serial tool calls toward model-generated code as the execution layer.
- Practical question: when generated search code is wrong, can users inspect and debug the plan?
- Skeptical: code generation does not automatically eliminate HTTP calls, rate limits, or error recovery. It can still generate bad syntax or noisy programs.
- Nuanced: fan-out search is a natural fit; iterative workflows that must re-plan after intermediate results remain the harder case.

## Local assets

- `thread.txt`: raw X thread extraction.
- `replies.json`: replies captured with `bird`.
- `article.html` and `article.txt`: official research article.
- `sandbox-docs.html`: official sandbox docs.
- `tweet-hero.png`: official architecture comparison image.
- `tweet-architecture.png`: official traditional-search timeline image.
- `tweet-benchmarks.png`: official benchmark chart.
- `tweet-dsqa-cost.png`, `tweet-widesearch-cost.png`, `tweet-wandr.png`: official metric images.
- `research-og.webp`: official research article OpenGraph visual.
- `perplexity-logo.svg`: official Perplexity API Platform logo.
