# Feltabout Safety Boundaries

This document is the public, contributor-friendly summary of Feltabout’s safety posture. For detailed implementation guidance, see `docs/safety-spec.md`.

## Product Boundary

Feltabout is a non-clinical reflection and conversation-prep tool.

It can help with:

- clarifying what happened
- naming feelings and needs
- preparing calmer language for a difficult conversation
- surfacing assumptions and reducing escalation

It cannot serve as:

- therapy
- diagnosis
- psychiatric care
- crisis support
- abuse mediation
- a tool for controlling or pressuring other people

## Safety Rules

The project should:

- run safety checks before normal generation
- avoid content that helps manipulation, coercion, stalking, threats, or emotional blackmail
- avoid clinical framing and false therapeutic authority
- route crisis, abuse, or immediate-danger situations away from normal conversation advice

## Language Rules

The project should avoid:

- false intimacy such as "I’m here for you" or "I understand exactly how you feel"
- therapeutic claims or diagnosis
- revenge framing, blame amplification, or pressure tactics
- exaggerated emotional theater

The project should prefer:

- calm, practical language
- clear boundaries
- concise reframing
- honest uncertainty
- user agency over dependency

## Engineering Implications

- safety-sensitive changes should have tests when practical
- raw intake and generated output should remain separable for review and auditing
- provider integrations should sit behind abstractions rather than hard-coded model calls
- docs and prompts must not overstate capabilities that the code does not support

## When to Refuse

Refuse or redirect when the user asks for help with:

- manipulation
- coercion
- stalking or surveillance
- threats or violence
- self-harm or suicide content that requires crisis routing

## Where to Read More

- `docs/safety-spec.md`
- `docs/language-boundaries.md`
- `docs/facilitation-philosophy.md`
- `AGENTS.md`
