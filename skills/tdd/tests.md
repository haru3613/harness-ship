# Behaviour-first tests

## Prefer the public interface

A durable test describes what a caller can observe and does not inspect how the module produced it.

```typescript
test("an accepted invitation makes the member visible", async () => {
  const invitation = await workspace.invite("dev@example.test");

  await workspace.accept(invitation.token);

  expect(await workspace.members()).toContainEqual(
    expect.objectContaining({ email: "dev@example.test" }),
  );
});
```

The test crosses the same interface as a caller, uses a result with product meaning, and can survive
an internal rewrite.

Avoid assertions about private calls:

```typescript
test("accept calls repository.save once", async () => {
  await invitation.accept();
  expect(repository.save).toHaveBeenCalledTimes(1);
});
```

This test describes implementation choreography. A harmless refactor can break it without changing
the accepted behaviour.

## Keep expected values independent

Do not repeat the production calculation in the test:

```typescript
// Weak: expected and implementation can share the same mistake.
const expected = lines.reduce((total, line) => total + line.price * line.quantity, 0);
expect(invoice.total(lines)).toBe(expected);

// Strong: the worked example is an independent oracle.
expect(invoice.total([
  { price: 12, quantity: 2 },
  { price: 5, quantity: 1 },
])).toBe(29);
```

## Prove a meaningful RED

A useful failure reaches the intended interface and disagrees at the behaviour assertion:

```text
Expected rejected invitations to leave members unchanged
Expected: 2
Received: 3
```

These failures do not prove missing behaviour:

```text
Cannot find module './fixture'
Connection refused
SyntaxError: unexpected token
```

Fix the harness first, then rerun until the test fails for the reason named by its scenario.

## One logical outcome per test

One test may need several assertions to describe a single outcome. Split it when failures would
represent different behaviours or different SC-ID / AC-ID mappings.
