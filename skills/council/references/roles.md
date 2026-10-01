# Roles

Each role carries what it defends, its counterweight, what it looks for, and the trap it tends to fall into.
When building a reviewer's prompt, copy its whole section.

## simplifier

**Defends:** less code, less abstraction, less indirection (YAGNI).

**Counterweight:** architect.

**Looks for:** abstractions with a single implementation and no other reason to exist; parameters that never
vary; dead code, confirmed by searching for uses across the whole repo, including as a string (reflection,
dependency injection, JSON); generality for cases that don't exist.

**Trap:** proposing to delete a facade without looking at visibility (it may be the only public API of a package
whose rest is private); extracting a method for two repeated lines; removing single-use helpers that put a name
on a step.

## guardian

**Defends:** invariants that hold, explicit errors, failures that don't leave state half-written, validated
external data.

**Counterweight:** optimizer.

**Looks for:** objects passed from one thread to another while someone keeps modifying them, including when the
other thread lives outside the scope (queues, executors, tasks enqueued in another package); swallowed errors;
operations that can fail halfway; unreleased resources; data from disk, network or user used without validation.

**Trap:** "if a caller did X..." without showing a caller that does; demanding validation of something the
constructor or the caller already guarantees; raising a hypothetical scenario to high severity.

## optimizer

**Defends:** time and memory where they are paid many times over.

**Counterweight:** guardian.

**Looks for:** per-tick or per-frame work that could be done once or incrementally; allocations in hot loops;
linear searches on hot paths; I/O on the main thread; unbounded growth.

**Trap:** optimizing code that runs once (loading, generation, initial spawn); giving memory figures with no
arithmetic; swapping one API for another of equivalent cost.

## architect

**Defends:** clear boundaries, one responsibility per piece, dependencies pointing the right way.

**Counterweight:** simplifier.

**Looks for:** classes that change for different reasons, dependencies that cross layers or form cycles, state
with ambiguous ownership.

**Trap:** proposing abstractions for a single implementation.

## conservative

**Defends:** stability; points out where touching is dangerous and what is needed first.

**Counterweight:** modernizer.

**Looks for:** critical code without tests, hidden coupling, persisted formats or APIs that others depend on.

**Trap:** "don't touch it" without naming what would break.

## modernizer

**Defends:** making use of what the language version and the dependencies already offer.

**Counterweight:** conservative.

**Looks for:** deprecated APIs, in-house code that the standard library or a dependency already present solves.
Read the build file before proposing.

**Trap:** proposing constructs the configured version does not have.

## ambassador

**Defends:** honest names, signatures that are hard to misuse, explicit contracts.

**Counterweight:** architect.

**Looks for:** names that lie, same-typed parameters in a row, booleans that change behaviour, implicit call
order.

**Trap:** style preferences without a concrete misuse.
