# Security Policy

## Scope

Feltabout is pre-release software focused on non-clinical reflection and conversation preparation. Security work in this repository includes both traditional software vulnerabilities and product-safety failures that could expose users to harm.

Examples:

- authentication or authorization bypass
- data exposure or insecure storage
- prompt paths that help users manipulate, threaten, stalk, or coerce others
- failures to route crisis or abuse content away from normal advice
- unsafe defaults in self-hosted deployment guidance

## Supported Versions

There is no long-term support matrix yet. Security fixes should target the current default branch and the active MVP 1 stack in `services/api/` and `frontend/`.

## Reporting a Vulnerability

Please do not post sensitive exploit details in a public issue.

Preferred path:

1. Use GitHub private vulnerability reporting if it is enabled for this repository.
2. If private reporting is not available, open a minimal public issue requesting a private contact path and omit exploit details, secrets, payloads, and reproduction steps.

For non-sensitive safety or policy concerns, use the Safety Concern issue template.

## What to Include

- affected area and file path if known
- concise impact statement
- reproduction steps
- whether user data, auth, or safety routing is affected
- any suggested mitigation or temporary workaround

## Response Goals

The project aims to:

- acknowledge reports promptly
- reproduce and triage issues conservatively
- prioritize user-safety and data-exposure issues first
- document fixes clearly in public once disclosure is safe

## Disclosure Expectations

Please give the maintainer reasonable time to investigate before publishing full details. If the issue concerns crisis handling, coercion, or abuse-related behavior, prioritize user harm reduction over disclosure speed.
