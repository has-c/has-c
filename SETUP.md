# Daily Quote Automation

The profile quote is updated once a day by privately hosted, reviewed
automation. This public repository intentionally contains no model API key,
model-calling script, self-hosted GitHub Actions runner, or remotely executable
workflow for the quote updater.

## What runs privately

- **Prefect** schedules the update, records each run, and retries transient
  failures.
- A reviewed, rotating allowlist supplies candidate public HTTPS source pages;
  the job does not depend on a general web-search service.
- **Qwen3.8**, served locally through **vLLM**, selects a direct quotation from
  bounded source text and returns strict schema-validated JSON. It has no
  repository credential and no tools.
- Deterministic Python checks that the exact quote and author appear on the
  selected page, rejects recent duplicates and unsafe Markdown, and fails
  closed when verification is not possible.

The public checkout is treated as untrusted data: the private service does not
import, source, build, or execute files from it. It may modify only `README.md`,
between the existing daily-quote markers. Each new quote links to its verified
public source.

The flow code, tests, installer, documentation, and trusted de-duplication seed
live together in the private Cheenulabs repository. That seed preserves the
former public quote list; ongoing de-duplication is reconstructed from bounded
historical versions of this README in Git. This repository therefore needs no
writable quote cache or private automation implementation.

## Publishing access

Publishing uses a dedicated SSH deploy key with write access to only this
repository. The key is held by a low-privilege service account and is not stored
in GitHub Actions or committed here. The private key is not shared with an
operator account or another service.

The retired updater used the Gemini API from a scheduled GitHub Action. After
this change is merged, delete the unused `GEMINI_API_KEY` Actions secret. The
contribution-snake workflow is independent and remains unchanged.

## Failure behavior

If search, source fetching, model output, verification, or publishing fails,
Prefect records the failed run and retries it. No quote is published unless it
passes source verification, and there is no hard-coded fallback quote.
