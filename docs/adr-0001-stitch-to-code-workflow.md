# ADR-0001: Stitch-to-Code Workflow

## Status
Accepted

## Context
The product needs a dense institutional UI quickly, but still requires durable, reviewable code. Google Stitch is already validated for the project and is the fastest way to explore surface layout, density, and dark-mode visual rhythm before implementation.

## Decision
We will use Google Stitch as the design acceleration layer for all major UI surfaces.

1. Generate or refine each major screen in Stitch first.
2. Capture the screen identifiers in `PROJECT_DETAILS.md`.
3. Translate the approved screen into implementation components in `apps/web`.
4. Keep the coded frontend as the implementation source of truth.
5. Revisit Stitch only when introducing a materially new surface or interaction pattern.

## Consequences
- Designers and engineers share the same visual source references.
- Frontend implementation stays auditable in Git.
- We can move quickly during the MVP phase without turning screenshots into the real product.
