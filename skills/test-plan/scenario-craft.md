# Writing scenarios worth gating on

The contract's table has a shape. This is how to fill it so the rows mean something.

A scenario that cannot fail is a scenario that proves nothing, and it costs the same to carry as a
real one. Most weak contracts fail here rather than at coverage: every journey is listed, every row
is `required`, and none of them could have caught the last incident.

## Cut journeys by what the user is trying to finish

A journey is one thing a person set out to accomplish — not one screen, one endpoint, or one
feature name. Screens split and merge; the intent behind them is what stays stable, and scenario IDs
have to outlive the UI that happens to serve them today.

Group by the part of the product a failure would belong to, then number within it. Prefixed IDs
(`AUTH-01`, `MATCH-02`) survive a journey being retired, and reading them tells you which area is
thin.

The right size is testable directly: **a correctly cut journey fits one sentence that names both the
outcome and a specific way it could go wrong.**

- *"A member manages their collection"* — too big. Nothing specific can go wrong with it, so
  nothing specific can be proven about it.
- *"`POST /items` returns 201"* — too small, and not a journey. Nobody set out to receive a status
  code.
- *"Add one physical copy with the acquisition details the owner actually entered; never infer a
  cost that was never given."* — one intent, one concrete failure.

Cut by intent first and the seams follow. Cut by module and every scenario ends up describing the
module's internals, which is the same mistake as a test asserting on private calls.

## Write expected and forbidden in one breath

Both halves are externally observable, and the forbidden half is not the negation of the expected
half. "Adds the copy" negates to "does not add the copy" — a failure the happy path already
catches. The forbidden half names a **different** wrong outcome, one that occurs while the expected
half still appears to succeed.

That is why it earns its column. A contract with only expected behaviour passes every test while the
thing the user actually fears ships intact.

## The four ways a system goes wrong while appearing to work

Most useful forbidden clauses are one of these. Reach for them in order when a row's forbidden half
is blank.

**Conflation** — two things that must stay separate got merged.
*Never attribute one workspace's invitations to another; never price a graded item from raw
evidence.* Look for every place the domain says two things are distinct: separate currencies,
locales, tenants, environments, identities, evidence classes.

**Fabrication** — output appeared that no evidence supports.
*Never render a missing total as zero; never publish an average built from one sample.* Any place
the system must say "not enough information" is a place it might say a number instead. Absence
rendered as a value is the most common release-day surprise.

**Leak** — data crossed a boundary it was never allowed to cross.
*Never expose the private note on a public projection; never reveal whether an account exists.*
Every projection, share link, error message, and notification payload is a boundary. Error text and
enumeration behaviour leak more often than the main response does.

**Duplication and timing** — the right action at the wrong count or the wrong moment.
*Never charge twice on a retry; never notify on a state that was already notified.* Anything
retried, scheduled, resumed, or triggered by a transition belongs here.

## Where the forbidden half is already written down

Do not invent these from imagination when the project has already stated them.

- **Stated invariants.** A repository instruction file that says *never* is handing you forbidden
  clauses directly. Each one is a scenario row or an admitted gap.
- **A domain glossary's rejected terms.** A glossary that says a Price Observation is *not* a market
  value is describing a conflation the product must not commit.
- **Schema constraints and triggers.** An append-only trigger exists because someone once edited
  what should have been appended. The constraint says what; the scenario says what a user would see
  when it is bypassed.
- **Past incidents.** Every mechanism that already escaped once is a forbidden clause with evidence
  behind it. A mechanism that recurred despite a defence has disproved that defence.

An invariant enforced only by prose, with no test and no constraint, is the highest-value scenario
in the contract. It is the one everybody believes is covered.

## Check a row before accepting it

A row is not ready while any of these is true:

- the forbidden half is a restatement of failure — *"never errors"*, *"never fails to load"*,
  *"never behaves incorrectly"*. Name the wrong state, not the absence of the right one.
- neither half is observable from outside the system. *"Never calls the repository twice"* is an
  implementation claim; it belongs in a test, not a contract.
- no evidence would distinguish a pass from a fail. If a passing run and a failing run produce the
  same artifact, the row's evidence requirement is not written yet.
- an `automated` row names its seam in a form nobody can resolve later. *"Covered by the pricing
  tests"* cannot be checked against the repository; a file path plus test name, a command, or a CI
  job can. `release-gate` re-resolves these at the candidate SHA, and an unresolvable citation
  blocks — so a vague seam does not buy leniency, it costs the row its result.
- the seam named cannot actually reach the forbidden half. A widget test cannot prove two tenants
  stay separated. Say the seam cannot prove it rather than recording the weaker proof.

The last one is the honest failure. `not-configured` is a truthful state; a row whose seam cannot
reach its own forbidden clause is a row that will report PASS forever.

## Then ask why this seam and not a better one

A ready row still has one question left, and it is not a readiness condition — the author usually
cannot fix it. Ask it anyway, of every row: **is there a seam that would catch a failure this one
structurally cannot see, which was not used because it could not be run here?**

Better means reach, not realism. The rubric stays *the cheapest stable seam that proves the row*, so
a more faithful seam is not automatically a better one — a real browser that proves exactly what the
component test proves is more expensive, not better. It is better only when the used seam is blind to
something the forbidden half names, and the answer is no whenever the used seam already reaches it.

Answer yes and the row still stands: record it in **Seam runnability** with what the used seam cannot
see, and an owner. This is where the two failures divide. The bullet above applies first — a seam
that reaches nothing the row forbids proves nothing, and that row is `not-configured` no matter how
unrunnable its alternative was. **Seam runnability** records a proof weaker than it should be, never
a proof that is not one.

Ask it at writing time because afterwards nothing looks wrong. A row saying "component test, mocked
API" reads as a considered choice; what happened may have been that no local database was running, so
the faithful seam was never on the table. Both produce the same sentence and are entirely different
facts — one is a decision, the other is an unfixed environment. Six months later nobody can tell them
apart, and the environment is still unfixed.

Which is worth more than it looks. An agent writes tests at the layer where it can get a real signal,
and no instruction moves that — making the layer runnable does. A workflow that quietly accepts an
unrunnable seam is discarding the one intervention that changes what gets written, so this is a
finding about the project's environment, not a footnote about the row.
