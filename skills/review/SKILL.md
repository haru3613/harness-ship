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
2. the originating ticket, spec, acceptance-contract revision, and SC-ID → AC-ID mappings;
3. the repository standards sources (`AGENTS.md` / `CLAUDE.md`, relevant ADRs and local
   conventions);
4. the `git log --oneline <fixed-point>..HEAD` **commit list**.

Verify the fixed point resolves, the working tree is clean, and
`git diff <fixed-point>...HEAD` is non-empty. Review this committed range—not only staged files or
the last commit. The reviewed range is `fixed-point...HEAD`. Stop if the tree is dirty, the range is
empty, or the originating behaviour source cannot be identified; do not silently review a partial
change or guess the Spec axis.

## Two axes (do not rerank across them)

**Standards** — is the code good?
- Follows this repo's documented conventions (read them first; the repo overrides any generic
  baseline). Naming, structure, error handling, no reinvented stdlib, no dead abstraction.
- Correctness, security at trust boundaries, resource handling.

**Spec** — is it the *right* code?
- Does the change satisfy the originating ticket's acceptance criteria — all of them?
- Anything built that wasn't asked for (scope creep)? Anything asked for that's missing?

Report each axis separately. A finding on one axis never cancels a finding on the other.

When `review` is orchestrated by `implement`, root dispatches Standards and Spec as **two fresh
child runs** of the mapped, pre-defined independent-verification profile. They receive the same
fixed-point diff and sources, but do not communicate or rerank each other; the same profile may be
instantiated twice. If that profile is missing, drifted, or cannot be live-verified, the
`implement` review gate is **blocked**—root-run analysis cannot be presented as independent review.

When this self-contained block is invoked directly in a host without configured child profiles,
root may perform both axes sequentially. Keep the findings separate and label the result
`independence: not established`; it is a useful standalone review, but it cannot satisfy
`implement`'s mandatory independent gate.

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

Findings ranked most-severe first, each **CRITICAL / HIGH / LOW** with `file:line`, the concrete
failure it causes, and a one-line fix. If nothing blocks, say so plainly — don't manufacture faults.
Blocking findings must be fixed and re-reviewed; non-blocking may be deferred but must be listed.

Include the fixed point, reviewed HEAD, commit count, originating work item/contract revision, and
the profile/run identity for each independent axis. After any fix, require a clean committed tree
and rerun the affected axis in a fresh child against the new HEAD.
