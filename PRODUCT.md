# Product


## Platform

web

## Stack

Python 3.12 backend/data tooling (DuckDB locally) and a Vite TypeScript static dashboard. The implemented architecture and rationale are documented in `README.md` and `docs/architecture.md`.

## Users

Operations managers, logistics analysts, intervention planners, data engineers/reviewers, and recruiters evaluating a delivery-SLA analytics portfolio.

## Product Purpose

FulfillIQ Cloud is a historical research and demonstration system for identifying e-commerce orders at risk of missing their promised delivery date and explaining SLA performance. It is not a live Olist service or logistics API.

## Positioning

The product separates checkout-time order facts from later delivery outcomes, then demonstrates reproducible, idempotent event processing through both local DuckDB and an owner-approved S3/Lambda/Athena implementation.

## Operating Context

The source is the Brazilian E-Commerce Public Dataset by Olist (2016–2018). The dashboard consumes exported aggregates only; raw data and AWS credentials never enter the browser.

## Capabilities and Constraints

- One order is the analytical grain. The late label compares calendar dates, not timestamps to midnight.
- Delivery outcomes, status, reviews, carrier handoff, and other post-checkout facts are excluded from placement events and model features.
- Cloud evidence is scoped and redacted: the approved `ap-southeast-2` deployment, synthetic smoke, staged replay, and full Olist reconciliation passed. Future infrastructure changes still require explicit owner approval.
- Source files in `data/source/` are locally supplied and are not public repository artifacts.

## Evidence on Hand

The owner supplied the official Olist CSV tables under `data/source/`. Their license is CC BY-NC-SA 4.0. Measured local model evidence and redacted Athena reconciliation evidence exist.

## Product Principles

1. Preserve the one-order metric contract end to end.
2. Prefer reproducible local evidence over unverified cloud claims.
3. Fail invalid event batches as a whole, with recoverable quarantine evidence.
4. Make historical, synthetic, and cloud-verification status plainly visible.
5. Keep delivery-risk estimates honest about feature availability and causality.

## Accessibility & Inclusion

The dashboard targets semantic HTML, keyboard-visible focus, responsive layouts, readable contrast, and non-colour-only metric communication. This is an inferred baseline because no additional requirement was provided.
