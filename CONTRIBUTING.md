# Contributing to TraceX

Thanks for your interest in TraceX.

## Before opening an issue

- Search existing issues for duplicates.
- Never include real banking/customer data, credentials, or personal information.
- Use synthetic examples when reporting bugs.

## Pull requests

1. Keep changes focused and explain the problem being solved.
2. Add or update tests for changed behaviour.
3. Run `python -m pytest` locally.
4. Document assumptions, especially for financial attribution and risk scoring.
5. Do not describe prototype outputs as proof of fraud or legal conclusions.

## Development principles

- Prefer `Decimal` for monetary calculations.
- Preserve source attribution and transaction identifiers where applicable.
- Make assumptions and limitations explicit.
- Keep risk scoring explainable and separate from fund attribution.
