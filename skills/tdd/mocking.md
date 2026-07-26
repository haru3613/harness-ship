# Replacing dependencies in tests

Prefer the real implementation behind the interface under test. Replace an adapter only when it
crosses a system seam or makes the test unsafe, nondeterministic, or impractically slow.

## Usually replace

- third-party network services,
- clocks, randomness, and nondeterministic schedulers,
- payment, email, messaging, or other irreversible effects,
- filesystem or object storage when a temporary real implementation is unavailable.

## Usually keep real

- modules owned by the repository,
- internal collaborators,
- parsers, validators, and domain logic,
- a disposable test database when it is fast and isolated.

Mocking an internal collaborator couples the test to implementation choreography. If a dependency
must vary, define a small interface at the real system seam and provide an adapter for production
plus a deterministic fake for tests.

## Assert outcomes, not mock traffic

Use a fake to control the external world, then assert through the module's public interface.
Checking a boundary adapter received a required protocol request is appropriate for a contract test;
checking private call counts or internal ordering is not.

Keep fakes literal and simple. Conditional mock logic that reproduces production behaviour can make
the test tautological and hide the same defect in both paths.
