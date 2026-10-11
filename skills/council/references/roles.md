# Roles

Each role carries what it defends, its counterweight, what it looks for, and the trap it tends to fall into. A
role may also carry an **Output** section, which replaces the finding shapes of the reviewer prompt.
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

**Trap:** proposing abstractions for a single implementation; filling the quota with findings that name no
boundary (dead code, duplication, a stale comment), which belong to other roles.

**Output:** every finding is one boundary that is crossed the wrong way, in place of Defect and Maintenance:

    ### <title>
    - Boundary: the two pieces on each side (packages, layers or classes) and the rule that separates them, quoted
      from a project document or from the code's own javadoc with file:line. Without a written rule, say which
      change-reason separates them and cite two members of the same class that change for different reasons
    - Crossed at: file:line of the import, call or field access that goes the wrong way
    - State owner: who owns the state that crosses, and who else reads or writes it (file:line of each). Search for
      the fact itself, not only for the accessor you started from: another field, flag or method may already carry it
    - Already settled: read, do not grep. Read the project document's section for the package on each side and the
      javadoc of both classes at the crossing, and quote what each says about it (file:line), or write "silent" with
      the sections and javadocs you read. A keyword search for a name is not a reading. Then name the existing
      mechanism that already carries the same state (file:line), if any. If a document, a javadoc or a mechanism
      settles it, the item goes to Discarded, or the proposal reuses that mechanism instead of adding a second
    - Proposal: what moves where, in terms of existing classes. A new type needs the second implementation or the
      second reason to change that justifies it
    - Severity: medium | low
    - Cost: what simplifier would object to

A finding that cannot fill "Boundary" with two pieces and a rule is not a finding for this role: list it under
Discarded as "for <simplifier|ambassador|guardian>".

## conservative

**Defends:** stability; points out where touching is dangerous and what is needed first.

**Counterweight:** modernizer.

**Looks for:** persisted formats and public APIs in scope that a documented pending change will touch and that no
test pins down. A pending change is written down: a TODO, a "not persisted yet" line in a project document, a
method with no caller that waits for one. Reading the code and imagining a change is not a source.

**Trap:** "don't touch it" without naming what would break; following a pending change through a path without
first looking for the document, test or guard that already settles it.

**Output:** every finding is one entry of a map, in place of Defect and Maintenance:

    ### <persisted format or API>
    - Pending change: the documented change that will touch it, quoted, with file:line. Without one the item goes
      to Discarded
    - Written by: file:line of the code that writes it today, or "none today"
    - Read by: file:line of the code that reads it
    - Pinned by: the test class and method that fix its current behaviour, or "no test" plus the search you ran
    - Already settled: the project document, test or guard that already covers the pending change (file:line), or
      "none found" plus the search you ran. If you find one, the item goes to Discarded
    - Needed first: the test, migration or guard that has to exist before the change
    - Severity: medium | low
    - Cost: what modernizer would object to

A bug that already happens with today's code is not a finding for this role: list it under Discarded as
"for guardian".

## modernizer

**Defends:** making use of what the language version and the dependencies already offer.

**Counterweight:** conservative.

**Looks for:** deprecated APIs, in-house code that the standard library or a dependency already present solves.
Read the build file before proposing.

**Trap:** proposing constructs the configured version does not have; filling the quota with findings that name no
replacement (a lying javadoc, dead code, a naming choice), which belong to other roles.

**Output:** every finding uses this shape, in place of Defect and Maintenance:

    ### <title>
    - Replaces: the in-house code or the deprecated API (file:line)
    - Provided by: the exact class and method, the dependency or JDK release that provides it, and its version in
      the build file. Say where you read it (sources jar, JDK documentation); a replacement you did not open is a guess
    - Same behaviour: what the replacement does on each input the current code handles (null, empty, error, rounding),
      checked one by one, and every difference
    - Callers affected: file:line of each
    - Severity: medium | low
    - Cost: what conservative would object to

A finding that cannot fill "Provided by" with something already on the classpath or in the JDK release the build
configures is not a finding for this role: list it under Discarded as "for <ambassador|simplifier|guardian>".

## ambassador

**Defends:** honest names, signatures that are hard to misuse, explicit contracts.

**Counterweight:** architect.

**Looks for:** names and javadocs that lie (including a javadoc attached to the wrong member), same-typed
parameters in a row, booleans that change behaviour, implicit call order. Each finding names its concrete
misuse: the call or the reading someone would make today with the code as it is, and what it gets wrong.

**Trap:** style preferences without a concrete misuse; reporting a behaviour bug because it touches a name or a
helper (that is guardian's ground).
