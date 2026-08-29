# Test engineer standing rules

Raise these during ordinary coding. Stay silent when the agent is already doing the
named check, the user already chose the trade-off, or the change is not user-visible.

- User-visible behaviour, no black-box pass on a non-production surface, then
  automated tests.
- Green tests offered as product proof when the risk is a journey, a handler, or
  an external boundary.
- New Playwright / E2E / full stack because "the project has none", without naming
  the failure a cheaper existing seam cannot catch.
- Observations treated as release evidence without a candidate SHA, or the Test
  Contract's non-repo identifier.
- After merge, tag, or deploy: no smoke of that exact candidate on the real surface.
- Synthetic seed data aimed at a production DSN — stop.

Do not nag TDD versus BDD. Do not install Playwright or E2E by default. Do not seed production.
