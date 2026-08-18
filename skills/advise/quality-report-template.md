# Quality Report — `<project>` — `<date>`

- **Shape:** `<pyramid | ice-cream | hourglass | empty | thin-middle>`
- **What already pays rent:** `<the tests or CI jobs that would catch a real failure>`
- **Flashlight:** `<risky modules or journeys the suite never touches>`

## Next cuts

At most three. Cheapest seam that can fail for the reason named.

| # | Cut | Seam | Why existing coverage misses it | Framework if missing |
|---|---|---|---|---|
| 1 | `<the failure a user would feel>` | `<layer + citation or proposed file>` | `<nearest test and the hole>` | `<none \| name, wait for approval>` |

## If you later want a release verdict

`test-plan` still owns approved criteria. `release-gate` still reads existing evidence.
This report is diagnosis, not a GO.

## Approval

- **Installs requested:** `<none | named framework, waiting>`
- **Next skill if the user wants one:** `<exploratory-testing | test-plan | none>`
