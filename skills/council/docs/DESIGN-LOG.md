# Design history of `/council`

The agent running the skill does not read this file (it is not referenced from `SKILL.md`). It is a record for
whoever edits the skill next: what failed in each test run and which rule corrects it. It exists so a failure
already seen is not reintroduced, and so a new improvement can be weighed against what it costs.

## Methodology

`superpowers:writing-skills` (RED without the skill → GREEN with it → REFACTOR, repeated). 9 subagent runs over
two real Java packages (`world/chunk`, `io/chunk`), plus 2 micro-test agents for the cross-examination. A full
run (3 reviewers + verification + report) averaged ~93k tokens, ranging from 77k to 109k.

## Failures observed and their correction

| #  | Failure observed                                                                                                                                                                           | Correction applied                                                                                        |
|----|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| 1  | Without the skill: the orchestrator sorted and deduplicated findings and called it “verification”; the false ones stayed on top as CRITICAL                                                | The “Verify” step: open the cited code, link by link of the Path                                          |
| 2  | A “race condition” in `writeAll()` that did not exist: the only caller never reuses the map                                                                                                | Every link cites real code, not a hypothetical caller                                                     |
| 3  | Invented figures (“hundreds of MB”, “-10% GC”) with no arithmetic                                                                                                                          | `reviewer-prompt.md`: figures only if computed from the code, showing the arithmetic                      |
| 4  | “Loads 100 times per second”, ignoring the early return at `Overworld.java:134`                                                                                                            | The “Frequency” link: check early returns and caches between the trigger and the code                     |
| 5  | “If `onEvict()`/`writeChunks()` throw...” when those calls only enqueue a task: the real exception happens on the worker thread                                                            | The “Exception” link: the line that throws it runs on the same thread that receives it                    |
| 6  | HIGH severity for a crash that only happens with a corrupt or hand-edited save file (the game never writes it that way)                                                                    | The “Origin” link: if the initial state can only come from outside the program, the maximum is medium     |
| 7  | Guardian dismissed the concurrency because “everything runs on the tick thread”, ignoring the writer thread that lives in another package                                                  | `roles.md`: guardian also looks for objects crossing to a thread that lives outside the scope             |
| 8  | The orchestrator wrote the report citing 3 reviewers when only 1 had come back                                                                                                             | The “Wait for all of them” step; the report opens with “Reviewers: role (n findings), ...”                |
| 9  | Refuted the real `destroyedDecoratives` bug with a reason covering a single branch (`Set.of()` in the empty case), ignoring the other (a live `HashSet` when the chunk does have an entry) | “Refuting demands the same evidence as confirming”: if the link has branches, all of them must be covered |
| 10 | Confirmed as “medium” something the reviewer itself framed as hypothetical (“if a list were modified... even though snapshots are passed today”)                                           | A conditional link with no current code producing it goes to Refuted                                      |
| 11 | The minimum evidence for a confirmed finding was not enforced                                                                                                                              | Template: mandatory “Starts at” and “Ends up as” fields                                                   |
| 12 | A subagent left an empty file (`eldest)`) in the repo during a “read-only” review                                                                                                          | The “Check for side effects” step: compare `git status --porcelain` before and after                      |

## Never detected in 9 runs

The real bug in `ChunkChanges.buildRecord` (`world/chunk/ChunkChanges.java:235`): it enqueues the live `int[][]`
and `HashSet` without copying them, so if the player edits the same chunk while the writer thread serializes,
there is a race. Guardian came close twice (failures #7 and #9) without reaching it. No rule fixes this: it is
the limit of what a reviewer sees in a single read.

## Cross-examination (step 6): why it is selective

Before implementing it, a micro-test of 2 agents was run over already-confirmed findings from earlier runs,
comparing a real counterweight's objection against the one the orchestrator had formulated on its own. The
result was asymmetric:

| Cross                                                                               | Self-formulated objection                                | Real counterweight objection                                                                                                                                                                                                                                                                                    | Verdict                                                               |
|-------------------------------------------------------------------------------------|----------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| Guardian judges “batch the writes in `Overworld.unloadAll()`” (from optimizer)      | “rare event, the saving does not justify the complexity” | `Overworld.java:381-396` mixes in-memory cleanup with persistence: skipping `onEvict()` to batch leaves `mobsResolved` and `pendingMobRecords` uncleaned, and the javadoc at 386-387 says their entries would be “orphaned forever”. The proposal cannot be applied without refactoring first                   | **Positive**: a real, verified obstacle the orchestrator had not seen |
| Optimizer judges “validate offsets at `RegionFileManager.java:141`” (from guardian) | “one comparison per entry (negligible)”                  | “Cost: negligible (O(1))” — the same conclusion. It also chose AMENDS and asked for more validations (the guardian axis), claiming that with `data.length < TABLE_BYTES` line 137 “creates a malformed buffer” and will “read garbage”: false, `ByteBuffer.wrap` throws `IndexOutOfBoundsException` right there | **Negative**: nothing new on its axis, role drift and a false claim   |

The asymmetry is structural. "What does this change break?" is guardian's job, so it criticizes well. "How much
does this validation cost?" almost always comes out "negligible", so the optimizer has nothing real to say on
its axis and fills the gap with someone else's work. Hence the three design decisions:

1. **A filter up front** (the table in `cross-exam-prompt.md`): cross-examine only if the counterweight's axis
   touches the change. Validations in code that runs once, renames and dead-code deletions are excluded.
2. **ENDORSES presented as the expected answer**, explicitly not a failure. A prohibition ("do not step outside
   your role") was not used, because `writing-skills` documents that prohibitions get negotiated under contrary
   incentive; a positive expectation leaves nothing to negotiate.
3. **The cross-examination answers are verified** with the same rules as the round 1 findings. Without that,
   the false claim about `ByteBuffer.wrap` would have made it into the report.

Cost measured in the micro-test: 63k and 86k tokens per agent, because each one reads the project instructions
and the code from scratch. That is why the step is selective and comes after verification: cross-examining
every finding against every role would have taken a run from ~93k to ~270k tokens.

## Consistency review and the first run with step 6

A review of the four files found six problems, all corrected:

1. **The cross-examination could hand a finding back to whoever proposed it.** The table decided the
   destination by kind of change, so a guardian proposal that "changes the order of operations" came back to
   guardian; and it did not cover conservative, modernizer or ambassador. The destination is now a single rule,
   the counterweight in `roles.md`, and the table is only the axis filter, with one row per each of the six
   counterweights.
2. **An untested role was launched without warning.** With the default roles, the counterweight of `simplifier`
   is `architect`, which was never tested. The "untested" warning now also covers the roles of step 6.
3. **The template refuted every dead-code finding.** The Starts at and Ends up as fields were designed for
   defects; a maintenance finding consists precisely of there being no caller, so read literally the rule "if
   the trigger is «none today», it goes to Refuted" discarded it. There are now two shapes: **defect** (Starts
   at / Path / Ends up as) and **maintenance** (Evidence), the latter with a maximum severity of medium and
   with its own verification rules (redo the search, including the name as a string; look at visibility).
4. **Step 6 launched agents without inheriting the round 1 protections**: neither waiting for all of them (failure #8)
   nor comparing `git status` again (the step 4 check runs before those agents exist).
5. **The counterweight's objection was formulated twice**: the reviewer already fills in a "Cost" field that
   step 7 ignored. It now starts from that field and verifies it.
6. **One row of "Common mistakes" did not come from any observed failure** ("not saving the report"): removed.

The validation run over `io/chunk` was the best of the 11 and the first with step 6 active:

- The cross-examination ran, picked the destination correctly, and all three verdicts appeared: `architect`
  **ENDORSED** a signature change, `guardian` **AMENDED** the write batching, citing the documented invariant of
  `RegionWriteQueue` (the same obstacle from the micro-test, reproduced), and `optimizer` **OBJECTED** to the
  defensive copy in `writeAll()` on O (n) cost with no current risk.
- That last objection matters: **it is the false finding the orchestrator had confirmed as real in earlier
  runs** (failure #10). The cross-examination stopped it on its own, with no intervention.
- Three findings were left out by the filter with the reason recorded. All three low-severity ones were
  verified against the code and are real.
- Cost: **117k tokens**, that is ~24k over the average without step 6, not the ~150k estimated. The filter
  leaves out half the findings, and the round 2 agents read far less code than the round 1 ones.

Two minor details left uncorrected as harmless: the agent answered in English (the test prompt spoke of an
abstract user, not the real one), and it classified two cost findings as "maintenance" instead of defect,
filling in the fields that hold the finding up anyway.

## Key claim (step 5): taken from the `consejo-7-sabios` repo

Reading that repo's code, not just its README, showed that it **does have verification**, in `consensus.py:543`
(`verify_plan_claims`), wired in at `orchestrator.py:662`: one adversarial Verifier subagent per task, with an
uncapped tool budget, redoing the counts and the existence claims. Its strongest piece is
`_enforce_core_refutation()`: the model marks `is_core: true` on the claim that *is* the task's justification,
and then **Python code**, not the model, forces a refuted core claim to refute the whole task. The docstring
documents that this fixed a calibration failure of 2026-05-30, where a task with a refuted claim was softened
to "weakened" and survived in the plan: the same failure #10 of this table.

The **key claim** mechanism was taken from there, adapted to what a Markdown file can do:

- The orchestrator names it, not the reviewer (just as over there the verifier marks it, not the sage: whoever
  proposes picks the part easiest to defend).
- It is named **before** verifying, which is the only thing that cuts off the later retrofit ("what really
  mattered was this other thing, which does hold").
- A refuted claim **is not softened**: it does not drop to doubtful, it does not drop a severity level, and it
  is not reworded into a smaller finding. What still stands is a new finding with its own verification.
- No equivalent to the deterministic guard: here the rule still depends on the model applying it. The closest
  thing is making "Key claim" a mandatory template field, so failing to fill it in is noticeable.

Validation run over `world/chunk` (121k tokens), a **split** result:

- **What improved:** 3 refuted out of 5, against 0 in every earlier run. It refuted both guardian findings, one
  of them exactly of the class of failure #5 ("if the write in `onEvict` fails"), with the correct argument: it
  enqueues asynchronously and the exception only surfaces in `flush()`.
- **What did not:** the two confirmed ones are weak. One proposes moving the `Zone.DUNGEON` guard out of
  `ChunkChanges`, against a decision documented in `CLAUDE.md`, in two javadocs and pinned by the
  `destroyDecorative_dungeonZone_throws` test. The other picked as its claim "it maps twice over the same
  Optional", literally true, when the two `.map()` calls extract different fields and there is no repeated
  work: the mechanism failing from the other side, with a claim chosen too weak from the start rather than
  retrofitted afterwards.

Two corrections applied from that run, **both still untested**: choose the claim by its load and not by its
literalness (with the test "if this were false, does the finding die?"), and count a javadoc that explains the
behaviour or a test that pins it down as evidence that it is there on purpose, at the same level as a project
document.

## Untested

- The `conservative`, `modernizer` and `ambassador` roles: never launched. `architect` acted only once, as a
  counterweight in the cross-examination, not as a round 1 reviewer. `SKILL.md` requires marking them as
  "untested" in the report if anyone uses them.
- Saving to `council-report-<date>.md` **in the working directory**: the validation run wrote it to a temporary
  directory so as not to leave files in the user's repo. The repo should have `council-report-*.md` in its
  `.gitignore`.
