---
name: spike
description: >-
  Time-box a technical unknown with a throwaway prototype that returns feasible / not / needs-more.
disable-model-invocation: true
---

# spike

Answer one question — *can this be done, and roughly how?* — with the smallest throwaway experiment,
then return a verdict the caller can act on. A spike that ends without a verdict failed its job.

## Rules

- **Throwaway from day one, and say so.** This code will be deleted. Do not make it pretty, general,
  or tested. Optimize for learning speed, not quality.
- **State the time box up front** (e.g. "≤ 2 hours" / "≤ half a day") and stop when you hit it, even
  if the answer is "needs more time" — that is itself a verdict.
- **One command to run it.** Keep the loop tight; surface full state after each step so the user can
  follow.
- **Isolate the unknown.** Spike the *one* risky thing (the integration, the algorithm, the API's
  real behaviour), not the whole feature.

## Required closing verdict

End with an explicit line the upstream feasibility gate can consume:

> **Verdict:** `feasible` — <the path that works, in one sentence> · <the key risk that remains>
>
> or `not-feasible` — <why; the wall you hit> · <alternative if any>
>
> or `needs-more` — <what you learned> · <what's still unknown + how much more time>

Then **capture only the decision** back into the spec/issue — the validated approach, a schema or
state-machine snippet if it encodes the answer more precisely than prose — and **discard the
prototype**. The learning folds forward; the code does not.
