# Concurrent claims — opt-in

Load this **only** when the project's config records a `Claim transition` and `Claim recovery`
policy, which `setup` writes only when more than one session works the same tracker. A single
operator does not need any of it: with one root there is no race to lose, a fencing token has
nothing to fence, and a lease can never expire into a takeover.

Most trackers cannot enforce what this file requires. GitHub Issues has no compare-and-set. If the
configured tracker cannot enforce a generation-conditional mutation, **that is the answer** — say so
and hand reconciliation to a human, rather than performing the ceremony without the guarantee.

## Claim and fencing

Apply the configured claim transition atomically with the root/session identity, a monotonically
changing **claim generation**, and the initial recovery receipt in one operation, so there is no
claimed-without-receipt window. Re-read the ticket afterwards to confirm ownership, generation, and
an unchanged contract revision. Release the claim if a terminal validation failure occurs before the
worktree exists.

An active claim owned elsewhere stops this root. Resume only as the same valid owner; **takeover**
only after the recorded lease has expired and the takeover rule succeeds.

Immediately before every external mutation, re-read the claim and abort unless owner, lease,
contract revision, and generation still match. That check alone is not a fence: the mutation must
also be conditional on the expected generation at its target, or use a generation-scoped
ref/resource with CAS/ETag/ref-lease enforcement. Where neither exists, reserve the action
atomically in the claim store and prevent takeover through its completion. **A stale root must be
unable to mutate once a newer generation exists.**

## Write-ahead checkpoints

The implementation receipt becomes a recovery ledger rather than an end-of-run report. Checkpoint:

- after every accepted slice, clean commit, and phase transition;
- before each external mutation, with the intended idempotent action and generation;
- after each external mutation, with its observed tracker/PR/SHA/deployment result;
- after merge, tracker transition, worktree disposal, and entry into `awaiting-deployment`.

Use host idempotency keys where available. If a crash leaves an intent with no result, recovery
reconciles live external state and records what it observed — it does not blindly repeat the
operation. A checkpoint failure stops before the next mutation.

## Dispatch reconciliation

Before dispatching a child, checkpoint the slice ID, a root-generated dispatch ID, the selected role
profile, expected HEAD and working-tree status, allowed files, and `in-flight`. Checkpoint the host
run identity after dispatch, and the terminal result before accepting the work.

On resume, reconcile an `in-flight` dispatch with the host and worktree before starting another
child. If the host cannot prove the prior writer terminal or absent, do not redispatch and do not
allow a takeover to write in that worktree.

## Recovery entry points

A receipt-backed resume revalidates its existing claim instead of applying a second transition. Read
the receipt's workflow phase, merge SHA, PR, and worktree-disposed state, and reconcile it against
live tracker, branch, PR, merge, worktree, CI, and deployment evidence. Live evidence may advance
recovery; it must never be silently overwritten by stale receipt state.

If live evidence proves the PR merged, go to post-merge reconciliation: finish the tracker
transition, dispose the recorded feature worktree until `worktree-disposed=true`, and only then
handle deployment. A deployment-only resume is allowed after that disposal is confirmed — validate
the merged SHA and go straight to Phase 4 deployment handling without creating or resuming a feature
worktree.
