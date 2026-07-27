---
name: review
description: >-
  Review a change on two independent axes — Standards (is the code clean per this repo's
  conventions?) and Spec (did it build the thing the ticket asked for?) — without letting one mask
  the other. Optional data-mutation safety gate for batch/cron DB writers. Use before merging.
  Triggers: "/review", "review this", "code review", "is this ready to merge".
---

# review

Review the diff on **two axes at once**, kept separate so a clean-code pass can't hide a
built-the-wrong-thing miss, and vice versa.

## Pin the review source

Before reviewing, establish and report:

1. the exact **fixed point** supplied by `implement`, or derive it with
   `git merge-base HEAD <configured-integration-ref>`;
2. the originating spec. Look in this order: the acceptance-contract revision and SC-ID → AC-ID
   mappings supplied by `implement`; issue references in the commit messages (`#123`, `Closes #45`);
   a path the user passed; a spec file under `docs/`, `specs/`, or `.scratch/` matching the branch.
   If none resolves, ask. If the user says there is no spec, **skip the Spec axis and report "no
   spec available"** — do not invent something to review against;
3. the repository standards sources (`AGENTS.md` / `CLAUDE.md`, relevant ADRs and local
   conventions);
4. the `git log --oneline <fixed-point>..HEAD` **commit list**.

Verify the fixed point resolves, the working tree is clean, and
`git diff <fixed-point>...HEAD` is non-empty. Review this committed range—not only staged files or
the last commit. The reviewed range is `fixed-point...HEAD`. Stop if the tree is dirty or the range is empty. Fail here rather than inside two child agents.

## Two axes (do not rerank across them)

**Standards** — is the code good?

- Follows this repo's documented conventions. Read them first: `AGENTS.md` / `CLAUDE.md`,
  `CONTRIBUTING.md`, ADRs, local convention files.
- Correctness, security at trust boundaries, resource handling.
- The **smell baseline** below, which applies even when a repo documents nothing.

**Spec** — is it the *right* code?

- Does the change satisfy the originating ticket's acceptance criteria — all of them?
- Anything built that wasn't asked for (scope creep)? Anything asked for that's missing?
- Anything that looks implemented but is implemented wrong?

Report each axis separately. A finding on one axis never cancels a finding on the other.

**Skip whatever tooling already enforces.** Formatting, import order, anything the linter autofixes.
A review that repeats the linter spends the reader's attention on findings that do not need a human.

### The smell baseline

Fowler's code smells (*Refactoring*, ch. 3), each as *what it is* → *how to fix*. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins. Where it endorses something the
  baseline would flag, suppress the smell.
- **Always a judgement call.** Report a baseline hit as a labelled heuristic — "possible Feature
  Envy" — never as a hard violation. A breach of a *documented* standard can be hard; a smell cannot.

- **Mysterious Name** — a function, variable, or type whose name doesn't reveal what it does or
  holds. → rename it; if no honest name comes, the design is murky.
- **Duplicated Code** — the same logic shape in more than one hunk or file in the change. → extract
  the shared shape, call it from both.
- **Feature Envy** — a method that reaches into another object's data more than its own. → move the
  method onto the data it envies.
- **Data Clumps** — the same few fields or params keep travelling together. → bundle them into one
  type and pass that.
- **Primitive Obsession** — a primitive or string standing in for a domain concept. → give the
  concept its own small type.
- **Repeated Switches** — the same `switch`/`if`-cascade on the same type recurs. → replace with
  polymorphism, or one map both sites share.
- **Shotgun Surgery** — one logical change forces scattered edits across many files. → gather what
  changes together into one module.
- **Divergent Change** — one file is edited for several unrelated reasons. → split so each module
  changes for one reason.
- **Speculative Generality** — abstraction, parameters, or hooks for needs the spec doesn't have. →
  delete it; inline back until a real need shows.
- **Message Chains** — long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the
  walk behind one method on the first object.
- **Middle Man** — a class or function that mostly just delegates onward. → cut it, call the real
  target direct.
- **Refused Bequest** — a subclass that ignores or overrides most of what it inherits. → drop the
  inheritance, use composition.

## Dispatch reviewers at invocation

Resolve reviewer identity from the subagent types the running host exposes now; never require or
persist a project/global profile. Prefer a purpose-built read-only verifier. If none exists, use a
fresh `generic`, `default`, `worker`, or equivalent host child for each axis.

Dispatch the two axes in one message so they run in parallel and neither pollutes the other's
context. Each brief carries the diff command, commit list, its own sources, a **400-word cap**, and
instructions not to edit source, mutate external state, or spawn children. They receive the same
fixed-point diff and never communicate or rerank each other.

Record each actual agent type and run identity. Use `host-enforced` only when the host exposes an
enforceable read-only boundary; otherwise record `independence: not established` without blocking
the review. If no child capability exists, root performs both axes sequentially with that label.

Before and after every run, compare `git rev-parse HEAD`, `git rev-parse HEAD^{tree}`, and
`git status --porcelain`. Any source edit, commit, external-state mutation, nested child dispatch,
or false `host-enforced` claim invalidates the review receipt and stops the handoff.

## Optional: data-mutation safety gate

Enable this when the project has scheduled jobs or scripts that **batch-write a database**
(popularity/price/stats recomputes, backfills, cron UPDATEs). For any such writer, **BLOCK** unless
it has all three:

1. an **abort guard** before the write loop (refuse to run on empty/sparse input),
2. a **sparse-input test** proving a broken upstream can't zero/NULL real data,
3. **failure alerting** (`if: failure()` / on-call) + first-run validation.

This class of bug — a broken upstream silently overwriting accumulated data with zeros — passes
every unit test and every visible check. Off by default; turn it on in a project that needs it.

## Output

Present the two axes under separate headings. Do **not** merge or rerank findings across them — that
is the reranking the separation exists to prevent. Within each axis, rank most-severe first: each
finding **CRITICAL / HIGH / LOW** with `file:line`, the concrete failure it causes, and a one-line
fix. End with one line: total findings per axis, and the worst issue *within each axis*. No single
winner across axes. If nothing blocks, say so plainly — don't manufacture faults.
Blocking findings must be fixed and re-reviewed; non-blocking may be deferred but must be listed.

Include the fixed point, reviewed HEAD, commit count, originating work item/contract revision, and
the profile/run identity for each independent axis. After any fix, require a clean committed tree
and rerun the affected axis in a fresh child against the new HEAD.
