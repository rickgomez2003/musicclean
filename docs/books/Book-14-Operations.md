# Book 14 — Operations

**Status:** Active foundation

## Safe action lifecycle

Orion separates recommendation from execution.

1. Generate a Decision.
2. Human/system policy records a Review.
3. Only an approved Review may receive an AuthorizationGrant.
4. An authorized Decision may produce an ActionPlan.
5. Future executors will validate preconditions immediately before mutation.
6. Quarantine operations must retain enough information for undo.

## Quarantine-first principle

Where removal from the active library is eventually appropriate, Orion should
prefer reversible quarantine over deletion.

0.6.11 implements planning only. It performs no filesystem mutation.
