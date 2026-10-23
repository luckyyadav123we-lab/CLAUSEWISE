# Architecture

The React/TypeScript Vite client submits files or pasted text to FastAPI under `/api/v1`. Document parsing extracts digital PDF, DOCX, and UTF-8 TXT content; a clause segmenter preserves source snippets and IDs. The offline analyzer emits structured findings and pairwise notice-period conflicts. The risk engine validates numeric bounds and computes the maximum score plus one point when another agent corroborates at 5 or above, capped at 10. Current analysis records live in process memory.

Four agent modules establish separate quality, liability, jurisdiction, and whole-contract contradiction boundaries. In this MVP their interfaces are deterministic rule modules; only the contradiction module compares clauses. There is no provider-backed LLM implementation, persistence, or authentication yet.
