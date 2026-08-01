---
name: clarify
description: >-
  Resolve requirement forks: answer the 90% a user didn't state with explicit assumptions, and ask only the few questions that change the plan.
disable-model-invocation: true
---

# clarify

Surface the cognitive gap between what the user said (~10%) and what the work needs (~90%) —
**without interrogating them**. Interrogation is the failure mode this skill exists to prevent.

## The rule

- **Ask only load-bearing decisions.** A question earns a spot only if a *different answer would
  change the plan or block the first unit of work*. Everything else, you decide.
- **Everything with a safe default → do not ask.** State it as an assumption instead:
  *"Assuming X, because Y."* The user corrects by exception, not by answering a quiz.
- **Facts are self-served.** If the answer is in the repo, logs, or an API, look it up — never ask
  the user for something you can find.
- **Rank by impact and cap it.** At most ~3–4 real questions, presented together (not a drip of
  one-at-a-time interrogation, not a wall of twenty).

## Output

1. **Assumptions** — the 90% you filled in, each one line with its *why*. This is the deliverable;
   it makes your reasoning inspectable so the user can correct a wrong assumption at a glance.
2. **Open forks** — the ≤4 load-bearing questions, asked once, ideally as concrete options.

If the decision is a content/creative/taste call rather than a technical one, say so and hand the
judgment back — those are the user's to make, not yours to assume.

## Why not just grill everything

Relentless interviewing feels thorough but taxes the user for decisions that have obvious defaults
and buries the two or three that actually matter. Answer the obvious, surface the pivotal.
