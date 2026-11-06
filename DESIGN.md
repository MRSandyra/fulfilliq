# FulfillIQ interface system

## Operating premise

The dashboard is a focused operational workspace: an analyst should locate the delivery-risk signal before noticing the visual system. It uses a **route ledger** world inspired by transit timetables, not as an interface costume, but through a precise time-column rhythm, a dense ink-and-paper palette, and one route-pulse visual treatment for SLA change.

## Tokens

- Ground: `#F5F1E8`; ink: `#18202C`; deep rail: `#163044`; muted: `#62707A`.
- Signal teal: `#0A7D79`; amber: `#B56818`; risk red: `#B5413E`; line: `#D8D2C5`.
- Type: Source Sans 3 for interface reading, IBM Plex Mono only for quantities and metadata.
- Corners are restrained (6px), borders are one-pixel rules, and shadow is soft/elevated only for floating controls.

## Structure

Desktop uses a permanent left rail, a compact context header, then a responsive analysis canvas. Mobile collapses navigation to a horizontal route list. Overview leads with KPI context, a daily SLA pulse, then regional and category tables. Controls are recognisable native selects, buttons, and text inputs.

## Signature move

The daily SLA series is a **route pulse**: late-rate points travel along a precise baseline, with the latest point and its label visually carried through the page’s signals. It communicates trend without disguising data as decoration.

## Accessibility

State is conveyed with words and values as well as color; contrast, visible focus, semantic headings, labelled controls, responsive reflow, and no-data/error states are required.
