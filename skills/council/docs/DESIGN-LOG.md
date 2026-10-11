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

## `ambassador`: first round 1 runs

Two runs over `ai/` (`Pathfinding`, `Node`, `SoliditySource`), a package just modified by hand, so the real
problems were known beforehand. ~90k and ~96k tokens per reviewer. No finding passed the cross-examination
filter (none deletes an abstraction or changes a public signature), so `architect` was not launched.

| Run | Confirmed | Refuted | Failures observed |
|-----|-----------|---------|-------------------|
| 1 (original definition) | 2 of 5 | 3 | Reported a behaviour bug as its top finding (negative coordinates truncated in `markBlockingEntities`), outside its axis and already refuted by an earlier guardian run; its origin evidence was defensive `floorDiv` code elsewhere, not code that produces negative positions. Fell in its trap once (renaming `Node.solid`, no concrete misuse). One conditional finding ("worth doing when a second caller appears"). Discarded a real javadoc attached to the wrong member as "over the five-finding cap" while keeping weaker ones. |
| 2 (corrected definition) | 3 of 5 | 2 | Left the behaviour bug and the conditional to Discarded on its own, naming guardian. Found the misplaced javadoc and a second javadoc that contradicts its method (`prepareWindow` claims to resolve solidity, which is lazy). Still fell in its trap once (a javadoc for `Node.row/col` justified by code nobody would write) and gave one invented figure ("16x", the real factor is `TILE_SIZE` = 64). Inflated a private javadoc to medium. |
| 3 (adds a fifth part: the line that writes each persisted field today) | 1 of 6, plus the run's one high | 5 | Ignored the recipe: three findings in defect shape and none citing the writing line, so the tile-record findings fell again on `setTile` having no caller. Line numbers again past the end of the files. Its first finding was nonetheless the best of all runs: the tick thread reads a region file (`RegionFileManager.java:188`) while the writer thread replaces it, and on Windows `Files.move` with `REPLACE_EXISTING` over an open file fails with `AccessDeniedException`, verified on this machine with a 20-line program. The failed write drops the evicted chunk's destroyed decoratives and mobs, and the next save throws out of `Game.loop()`. A guardian finding, found by the role that was told not to look for it. |

Correction applied to `roles.md`, the only change between the two runs: "Looks for" adds javadocs that lie
(including one attached to the wrong member) and requires each finding to name its concrete misuse, the call or
the reading someone would make today; "Trap" adds reporting a behaviour bug because it touches a name or a
helper. The positive form (what the finding must contain) was chosen over a bare prohibition, per
`writing-skills`. The remaining trap fall and the invented figure were caught by step 5 verification, so no
further rule was added.

Coverage is still narrow: one package, two runs. Marked as tested, but a run over a package with public APIs
used from several others would exercise "signatures hard to misuse" far more than a package with one caller.

## `conservative`: nine round 1 runs, passed with the new premise

Five runs over `io/chunk` (~132k, ~106k, ~116k, ~107k and ~129k tokens) one over `world/chunk` (~119k) and one over `io` without `io/chunk` (~103k). The decisive fact for verification was outside the scope:
`ChunkChanges.setTile` has no caller, so no chunk record written by the program carries tiles, and every path
that starts from a tile record has no origin today.

| Run | Confirmed | Refuted | Failures observed |
|-----|-----------|---------|-------------------|
| 1 (original definition) | 1 of 5 | 4 | Hunted current defects (guardian's and optimizer's ground) instead of mapping where touching is dangerous. Four findings started from tile records the program never writes, one rated high. The remap I/O figure used a wrong model (a growing region instead of a full one). Only the maintenance finding survived (the remap count says "rewritten" but returns every saved chunk). |
| 2 (corrected definition) | 1 of 3 | 2 | The two remap findings moved to the maintenance shape, as asked, but still claimed the corruption happens today and never looked for whether tiles are written: the dormant hook the recipe points at went unseen. The one confirmed finding is a guardian defect (a failed write during eviction loses destroyed decoratives, external origin, medium). Cited lines 314-375 of a 158-line file. |

Corrections tried between the runs, to `roles.md`: every finding takes four parts (the likely change, taken
from a TODO, a document or a hook without a caller; the dependent `file:line`; what breaks; what has to exist
first), and the trap adds reporting as a current defect a path whose input the program does not produce. It
changed the shape of the output but not the search behind it. Run 3 added a fifth part, the line that writes
each persisted field the finding relies on; the reviewer did not fill it in. Both corrections were reverted:
`roles.md` keeps the original definition, because a wording that changed nothing is not worth keeping.

Three iterations without compliance point at the design, not the wording. Under "persisted formats and hidden
coupling", the reviewer reads the same code guardian reads and reports what guardian would; the "what is needed
before touching" output never appeared. Options left for whoever picks this up: give the role a different output
than findings (a map of risky spots and the test each one needs before a change), merge it into guardian, or
drop it.

Runs 4 and 5 changed the design instead of the wording, with the structural form `writing-skills` prescribes
for an omitted element: `roles.md` gives `conservative` its own **Output** shape (Change with its cited source,
Written today by, Depends on it, Breaks, Needed first), and `reviewer-prompt.md` lets a role's Output replace the
Defect and Maintenance shapes. A current bug goes to Discarded "for guardian".

| Run | Confirmed | Refuted | Observed |
|-----|-----------|---------|----------|
| 4 (Output shape) | 1 of 4 | 3 | First run in the role: all findings in the new shape, current bugs routed to guardian. Confirmed: chest contents are bound to a local index that comes from `EntitySpawner`'s draw, so the TODO at `EntitySpawner.java:153` can silently drop what the player left in a chest; no test covers the draw. Refuted: a change invented with no source ("a debug view"), a consequence already documented in `AGENTS.md` (bumping `FORMAT_VERSION`), and "Written today by" claiming tile records that `setTile` never produces. Line numbers still continuous across files. |
| 5 (a change with no citable source goes to Discarded; read each file on its own) | 0 of 2 | 2 | Line numbers now correct in every citation checked: the per-file reading rule fixed that failure. It discarded its own guesses, as asked. The two findings left were weak: the reserved flags field (breaks only if someone defines a flag and forgets to read it) and a handle used after `release()` (the cited "source" is the javadoc describing today's design, not a change anyone plans). It missed the chest finding of run 4. |

The shape problem is solved: the reviewer now does the role's job and routes the rest. Precision is not: 1 of 6
across runs 4 and 5, against 3 of 5 for `ambassador`. `io/chunk` may simply hold few risks of this kind that are
not already documented, so the next test should use a package with live TODOs and caller-less hooks before
judging the role again.

Run 6, same definition as run 5, over `world/chunk` (live TODOs, `setTile` with no caller): 0 of 3 confirmed.
The shape held and the per-file line numbers held. All three findings fell on verification: pinning the
`Direction` ordinal is already a rule in `AGENTS.md`; the null/`Optional` contract of `restoreFromDisk` is
documented in its javadoc and already pinned by `ChunkChangesTest` (`restoreFromDisk_neverWritten_returnsEmpty`),
and the change it guards against had no citable source; and "the overworld tile overlay would apply inside a
dungeon once `setTile` has a caller" is false, because entering a dungeon evicts every overworld chunk
(`Overworld.unloadAll`) and each eviction drops its overlay (`ChunkChanges.onEvict`). The third one did cite a
real caller-less hook and filled "Written today by" correctly with "none today": the form works, the reasoning
about the future path does not.

Across runs 4 to 6: 1 confirmed out of 9, on two packages. The package was not the cause. A finding about a
change that has not happened asks the reviewer to trace a path that does not exist yet, and that is where it
fails: each one skipped a link that today's code already settles (a document, a test, an eviction). The role is
not recommended until someone tries a different premise.

Run 7, same definition, over `io` without `io/chunk` (`SaveManager`, `PlayerStore`, `WorldData`, `AtomicFiles`): chosen
because it has a documented pending change (equipment is not persisted yet, `AGENTS.md`), persisted JSON formats and
no tests for `SaveManager` or `PlayerStore`. 1 of 4 confirmed. The shape and line numbers held again.

- Confirmed (low): the `SAVE_VERSION` guard runs after `readValue`, and the default `ObjectMapper` fails on unknown
  properties, so a renamed or removed component makes the load fail as "Failed to load world" and the "Incompatible
  save version" message is never reached. The reviewer cited no source for the change; the orchestrator supplied
  `data.md` (a content change bumps `SAVE_VERSION`) and the history (`worldSeed` → `seed`, `dungeonDoorX` →
  `dungeonX`). That same history means saves from before those renames already hit it today, so the finding sits
  on guardian's border. The impact is only the logged message, because `Game.startWorld` catches both exceptions
  alike.
- Refuted: persisting equipment "breaks" old `player.json` files. `data.md` already prescribes the bump and
  `AGENTS.md` already accepts that a bump leaves old saves unreadable, so it is a documented decision.
- Refuted: a null `tileCatalog` turns into an empty one and remaps every tile to unknown. No source for the change,
  and no chunk record carries tiles today (`setTile` has no caller), so nothing on disk would be lost.
- Refuted: publishing the pointer first would orphan the previous save. The cited source is the `writeAll` javadoc
  describing what the API allows, not a change anyone plans: the same pattern as run 5.

Across runs 4 to 7: 2 confirmed out of 13, on three packages. The package with the documented pending change
produced the best finding, and it was the one closest to a current bug. The failure is stable across packages: the
reviewer anchors on a real source, then skips the document or test that already settles the future path.

Run 8, new premise (the role is a map of persisted formats and public APIs that a documented pending change will touch
and no test pins; each entry carries **Already settled**, the document, test or guard that already covers the
change, found by a search the reviewer reports). Same scope as run 7 (`io` without `io/chunk`): 1 of 2 confirmed.

- Confirmed (low): persisting the player's equipment (pending in `AGENTS.md:131`, `data.md:248-250`, javadoc of
  `PlayerStore`) has no test to fix the format (`src/test` mentions none of `SaveManager`, `PlayerStore`,
  `PlayerData`, `WorldData`), and `Equipment` holds the same `Item` instances that sit in the inventory:
  `ContainerModel.equip` only calls `toggle`, it never removes the item from its slot. Saving the equipment as a
  second list of names would load each equipped item twice. The reviewer left that identity question unverified
  ("not verified"); the orchestrator closed it by reading `ContainerModel.java` and the strategies. "Already
  settled" was filled in honestly as "partly": the version rule settles the gate, not the encoding.
- Discarded by the orchestrator: dropped items and active spells. Pending in the same documents, but there is no
  format yet ("written by: none today"), so nothing exists to break or to pin.
- The Discarded section did the work run 7 lacked: version equality, the unknown-item drop, the catalog remap, the
  atomic-write order and the `AtomicFiles` fallback were each sent away with the document or test that settles them.
  Run 7's three refuted findings were not reproduced. Line numbers held in every citation checked.

One run, one package. The premise moved precision from 1 of 4 to 1 of 2 and removed the failure pattern, but that
is not enough to mark the role as passed: it needs a second package with a documented pending change. Candidates
with live TODOs: `entity/player/equipment` itself (the TODOs in `WeaponEquipmentStrategy`) or `entity/spawn`.

Run 9, new premise, over `entity/player/equipment` (5 files, no tests, TODOs in `WeaponEquipmentStrategy`): 2 of 2
confirmed, none refuted. Line numbers and the shape held.

- Confirmed (low): the pending equipment persistence has no test to fix `player.json` (same finding as run 8,
  now reached from the equipment side), and the version gate offers no migration path: an optional field on read
  or a `SAVE_VERSION` bump that makes old saves unreadable.
- Confirmed (low): restoring a saved weapon, shield or light has three traps today. `isEquipped` compares with `==`
  (`WeaponEquipmentStrategy.java:33`, same in shield and light), so a restored item has to be the inventory's own
  instance, not a new one built from its name. The setters only assign (`Equipment.java:41-59`); `stats.attack` and
  `stats.defense` are recomputed only inside the strategies. And `onEquip` replays the draw sound
  (`WeaponEquipmentStrategy.java:17`). The reviewer's remedy "restore without `onEquip`" is too broad, because
  `onEquip` also loads the weapon sprite, which a restore needs; the traps stand.
- Discarded, rightly: the two TODOs on the attack update (`WeaponEquipmentStrategy.java:8,23`) are stale because
  `unequip` already calls `updateAttack`; version equality, the strategy registration and `LightEquipmentStrategy`
  had no pending change.

Both confirmed findings hang from one documented pending change (the equipment is not persisted yet), so they are not
independent evidence. Over runs 8 and 9 the new premise gives 3 confirmed out of 4, with no false finding, against 2
of 13 before it. The role is marked as tested. Expect an empty report where no pending change is written down: that
is the intended behaviour, not a failure.

Real problems surfaced on the way, verified by the orchestrator: the javadoc of
`ChunkFileManager.remapSavedChunks` claims retrying is safe, which is false for any non-identity remap; and a
failed save throws out of `Game.loop()` uncaught, closing the game without `cleanup()`.

## `modernizer`: two round 1 runs, passed with the Output shape

One run (~158k tokens) over `utils` (5 files, 630 lines), chosen because `pom.xml` declares Java 21, Guava 32.0.1-jre,
JOML 1.10.8 and libGDX, so there is something to replace with. 6 findings: 3 confirmed, 2 refuted, 1 doubtful.

| Finding | Status | Why |
|---------|--------|-----|
| `Utils.lerp` duplicates `org.joml.Math.lerp` | Confirmed (low) | The reviewer opened the JOML 1.10.8 sources jar and quoted the method (line 527); the JDK has no `lerp`, so it ruled that out. The trap (constructs the version lacks) did not appear. Missed: `StatusBarsView.java:133` has a second private copy. |
| `Pool.freeAll` and the no-arg constructor have no caller | Confirmed (low) | `EffectPool` calls `super(initialCapacity, max)`, and `new Pool` only appears in the javadoc example. Its sub-claim that the `peak` javadoc is false does not hold: the field is public, so it can be reset by assignment. |
| `Global.RENDER_SCALE` javadoc says 30x17 and 15x8 tiles | Confirmed (low) | The numbers are from 32 px tiles; commit `17a651fa` doubled the scale to 64 px, so it is 15x8.4 and 7.5x4.2. |
| Overworld spawn draws from `Math.random`, outside `SeedMixer` | Refuted | `Overworld.findSpawn` documents the draw ("elegida al azar") and `architecture.md` says "sorteado"; `AGENTS.md` demands determinism per cell, not for the spawn. It is also outside the scope and has nothing to do with the standard library. |
| `Utils.random(max)` is 1-based and the name does not say so | Refuted | The javadoc states it (`Utils.java:18`), the reviewer itself says the code is correct today, and the misuse (`random(0)`) is hypothetical. |
| `ConfigPaths` javadoc says `%LOCALAPPDATA%`, the code builds from `user.home` | Doubtful | They differ only in a redirected profile; on this machine both resolve to the same `AppData/Local` directory. |

What worked: it read the build file first, proved the replacement from the library's own sources, and its
Discarded section rightly turned down `Guava Files.getNameWithoutExtension` (different semantics), `Math.clamp`,
`ThreadLocalRandom` and the Timer counters. Line numbers held.

What did not: only 1 of the 6 is modernization. The other five are a javadoc that lies, dead API, a name and a
design choice, which belong to `ambassador`, `simplifier` and `guardian`. This is the drift `conservative` showed in
run 1: with nothing to replace, the reviewer fills the quota with the neighbours' ground. The cure that worked for
`conservative` was structural, not a wording: an **Output** slot that cannot be filled unless the replacement is
named (class, method, dependency, version in `pom.xml`). That has not been written or tested for `modernizer`.

Not passed: one run, one on-role finding. Next, a second run on a package with more candidates (hand-rolled JSON,
file or collection helpers), with or without the slot, before judging.

Run 2, over `json` (`JsonLoader` and 16 records, ~100k tokens), after giving the role an **Output** shape whose
"Provided by" slot needs the class, method, dependency and version in `pom.xml`, plus where it was read, and whose
"Same behaviour" slot compares the replacement input by input. A finding with nothing to put in "Provided by" goes to
Discarded with the role it belongs to. 1 finding, confirmed; nothing refuted.

- Confirmed (low): the dotted-path walk in `JsonLoader.deserialize` (lines 102-108) can use
  `JsonNode.at(String)` from jackson-databind 2.18.6. The reviewer opened the sources jar, and I checked it: `at`
  returns `MissingNode` instead of null on a miss, and `ArrayNode.get(String)` returns null. It listed the real
  differences: a missing inner segment needs an `isMissingNode()` guard to keep the exception, a numeric segment
  indexes an array, and `/` and `~` in a key change meaning. No data key has `/` or `~` and no caller uses numeric
  segments. The cost it gives is honest: after the guard the saving is about five lines, so the change is optional.
- The drift of run 1 did not come back: the neighbours' ground (the singleton whose javadoc claims thread safety,
  the nine `put` calls, the manual validation in `SpriteData`, the array in `ParticleData`) went to Discarded with
  the reason, and no off-role finding was reported. Fewer findings than the limit is the intended behaviour when
  there is little to replace.

Over both runs: 2 confirmed on role, 0 off-role findings once the shape existed, 2 refuted and 1 doubtful only
before it. Marked as tested. Its one remaining risk is the opposite of the old one: in a package with nothing to
replace it may return nothing, which is correct.

## `architect`: first round 1 run

One run (~156k tokens) over `world/chunk` (8 files, 1,134 lines), with the definition in `roles.md` as it was and the
generic Defect and Maintenance shapes. 5 findings: 3 confirmed, 2 refuted.

| Finding | Status | Why |
|---------|--------|-----|
| Loading a save made right after leaving a dungeon puts the player back inside it | Confirmed (medium) | The block that stops the re-entry (`ZoneTransition.canTransition`, `previousTransition`) is not persisted, and `ChunkManager.restore` calls `zoneTransition.reset()`, which re-arms it. The reviewer said it had not run the game and that the claim depended on where the hitbox centre lands after `exit()`. Checked with the numbers: `placePlayer` puts the centre at `(x*64+38, y*64+30)` for the player hitbox in `player.json` (x 14, y 70, 24x40), which is inside the entrance tile. The save menu is reachable at that moment (`GameViewPresenter.saveWorld`), and `PlayerStore` saves the position, so the first tick after loading finds `ENTRANCE` under the player. |
| `world.chunk` and `io.chunk` import each other; `ChunkCoord` lives in the wrong one | Confirmed (low) | `io/chunk` imports `world.chunk.ChunkCoord` (3 files); `world/chunk` imports `io.chunk` records and `TileRemap` (`ChunkChanges.java:3-7`, `Overworld.java:10-11`). Nothing in `dependencies.md` or an ADR documents it. |
| `ZoneTransition`'s javadoc says `ChunkManager` owns the zone | Confirmed (low) | The field lives in `World` (`World.java:41`), and `ZoneTransition` calls `world.setZone` itself (lines 72, 83) next to `ChunkManager.restore` (line 92). |
| Dirty flags are cleared before the write is confirmed, so a failed save loses changes | Refuted | Key claim: "the player keeps playing" after the failed save. `saveWorld` has no catch and `Game` only catches in `startWorld`, so the `IllegalStateException` from `ChunkFileManager.flush()` leaves the loop and the game closes; there is no later save that skips the chunks. The real nearby problem, that a failed save closes the game, was already known. |
| The render path ignores the `ChunkChanges` overlay | Refuted | Conditional: it says it cannot trigger today because `setTile` has no production caller, and `data.md` documents the overlay as the planned copy-on-write. |

What worked: the finding that matters is a real state-ownership bug, reached from the architect's lens (a piece of
state that lives in one class and is lost when another resets), and the discarded list is sound (the dungeon-exit
callback cycle is documented in `World.java:95-111`, `unloadAll` evicts the overlay, `snapshot()` is called after
every teleport). Line numbers held. The first confirmed finding was a defect, not a layering one, so it sits on
`guardian`'s border; the cause is the role's own "state with ambiguous ownership".

What did not: the two refuted findings were defects whose key claim depends on a path the code does not have (a
game that survives an uncaught exception; a tile edit that nobody calls), the same pattern as `conservative` before
its Output shape. One run is not enough to say whether it repeats.

Not marked as tested: one run. Next, a second run on a package with blurrier boundaries, such as `entity/mob` or
`ui/presenter`, before judging, and a decision on whether `architect` needs an Output shape of its own (the
boundary, who owns it, who depends on it) if the defect pattern repeats.

Run 2 of `architect`, over `entity/mob` (10 files, 548 lines, ~132k tokens), same definition and shapes as run 1.
5 findings, all Maintenance (the reviewer reported no defect with a current caller): 3 confirmed, 2 refuted.

| Finding | Status | Why |
|---------|--------|-----|
| `Mob.isPlayerWithinAttackRange`: its TODO and `SpriteSheet.java:107` say the lizard has the call commented out | Confirmed (low) | `Lizard.doActions` (lines 21-26) has no such line, commented or not. Key claim is the stale comment, not the missing caller, which the TODO already admits. |
| `Oldman`: the follow branch never runs and the hitbox is built twice | Confirmed (low) | `flags.following` is only set by `checkFollow` (called from `followPlayer`, which `Oldman` never calls) and by the `damageReaction` of `Orc`, `Slime` and `RedSlime`; `MeleeSystem.java:101` only calls `damageReaction` inside the non-NPC branch, and `OLDMAN` is NPC. Line 18 replaces the rectangle with a copy of itself. |
| `Orc`, `Slime` and `RedSlime` repeat `doActions` and `damageReaction` | Confirmed (low) | Identical bodies. The proposed fix, a follower default in `Mob`, is wrong: `Trader` has no `doActions` and would inherit it (`Entity.doActions` is the empty default) and start following the player. |
| `dialogue()` has no call site | Refuted | `Mob.java:87` already says "Sin llamador todavia"; it is a documented pending hook, and the reviewer's own proposal keeps it. |
| `Pathfinding.clearPath()` calls in the follow lifecycle have no effect | Refuted | True for steering, but the debug overlay (`World.java:83`) draws `getPath()` every frame, so removing them shows a stale path after an unfollow or a death. The claim needed for the removal does not hold. |

Both runs together: 6 confirmed of 10, but only 3 are architecture (run 1: the unpersisted transition block, the
`io.chunk` cycle, the zone owner). Run 2 produced none: dead code, duplication and stale comments are
`simplifier`'s and `ambassador`'s ground. It is the same drift as `modernizer` run 1, with the same cause: when the
package has no boundary problem the reviewer fills the quota with the neighbours' ground. Its discarded list shows it
looked at the real boundary questions (the `Mob` constructor depending on `JsonLoader`, `Audio` and the pathfinding
window) and sent them away because `AGENTS.md` declares that design, which is right.

Not passed. The cure that worked for `conservative` and `modernizer` is structural: an **Output** shape for
`architect` whose slot cannot be filled without a boundary, for example "Boundary: the two pieces, who owns the
state, which way the dependency points, and the file:line where it is crossed"; a finding with no boundary goes to
Discarded for the role it belongs to. Not written or tested yet. A third run would use it on a package with real
boundaries, such as `ui/presenter` or `core`.

Run 3 of `architect`, over `ui/presenter` (1 file, 150 lines, ~99k tokens), the first with the Boundary Output shape
written into `roles.md`. 2 findings, both naming a boundary; 5 items sent to Discarded, each with the right role
("for simplifier", "for guardian") or the document that settles it. No drift.

| Finding | Status | Why |
|---------|--------|-----|
| `Player.update` (`Player.java:76`) and `PlayerAnimator` (`:33`) pull container visibility from the presenter, so the tick reads view state | Doubtful | The crossing exists (both calls verified). The two claims around it do not hold: the determinism argument is wrong, because the value changes only in `processEvents()`, called from `render()` (`Game.java:207`), and is constant across the ticks between two renders; and `Game.java:178-180` reads `gameViewImpl.uiBlock()` every tick on purpose. The proposal, a flag pushed into the player, already exists as `InputState.uiBlock`, which the reviewer never found. |
| `Chest` -> `EntityServices` -> `GameViewPresenter` -> `Chest`: a package cycle between `entity` and `ui.presenter` | Confirmed (low) | `Chest.java:52`, `EntityServices.java:7`, `GameViewPresenter.java:5` verified; no document settles it. The ADR sentence it quotes ("El dominio no importa ninguna clase de `com.punkipunk.ui`", `0002:53`) is already false by that ADR's own mechanism, since the domain imports `ui.event.UIQueue` in a dozen places. The cycle is real, the quoted rule is weaker than presented. The proposed `UIEvent.OpenChest(Chest)` would put a domain type into a package of data-only records. |

What I found that the reviewer did not: `UiBlock.CONTAINER` says "el player sigue moviendose e interactuando con el
mouse" and `blocksActions()` returns true only for `MENU`, yet `Player.update` returns early with a container visible,
so the player does not move. Two mechanisms decide "a container blocks the player" and the documented one is the one
that does not apply. This is the ownership ambiguity the shape was meant to expose, and the reviewer filled "State
owner" with the presenter alone.

Shape check: 2 of 2 on role, 0 of 7 items of other roles reported (run 2: 5 of 5 off role). Precision 1 confirmed of 2,
the other doubtful through a missing search, not through drift. The slot that failed is "State owner": it asked who
reads and writes the state but not whether another mechanism already carries it. Edited in `roles.md`: the search is
for the fact and not for the accessor, and "Already settled" also accepts an existing mechanism, in which case the
proposal reuses it.

Not marked as tested: one run with the working shape and one fix since. Next, a run 4 on `core` or `physics`.

Run 4 of `architect`, over `core` (9 files, 984 lines, ~128k tokens), with the shape corrected after run 3.
3 findings, all naming a boundary; 11 items in Discarded, routed to the right role or to the document that settles
them. No drift.

| Finding | Status | Why |
|---------|--------|-----|
| `World` holds a `ui.view.GameView` only to read `isDebugVisible()` in `render` (`World.java:13,33,44-46,78,82`) | Confirmed (low) | It is the only `ui` import under `world/`, the only caller of `new World(...)` is `System.java:55`, and `Game.render` already holds `gameViewImpl`, so passing the boolean works. The reviewer's "medium" does not hold: the read is one boolean per frame and the cited rule (ADR 0002:53) is the same sentence the domain already breaks through `ui.event`. |
| `ImGuiContext.render` defers `lists - 2` draw lists for `CONTAINER`, a number tied to the windows the UI opens | Doubtful | The fragility is real and the reviewer admitted not checking that `2` is right. But "Already settled: none found" is wrong: `HotbarView.java:50-55` and `ImGuiContext.java:40` already say the deferral is by position and not by identity, and what keeps it working. It searched `docs/` by name and did not read the javadocs of the classes at the crossing. Whether an item tooltip (`ContainerView.java:436`, a window of its own) changes the count was not run in the game. |
| `BackdropException` duplicates the three levels of `UiBlock` | Refuted | `architecture.md:270` says why: the enum is stated "en terminos de capas de ImGui y no de vistas concretas", so `core` does not know the views. `UiBlock` is an input lock level. The values coincide today (`darken > 0` equals `isContainerVisible()`, `GameViewImpl.java:204`), which is not a crossing. The reviewer cited those same lines under Discarded as a stale doc and did not read them as the document that settles the item. |

Correct items in its Discarded list, checked: `GameState.PAUSED` and `GAME_OVER` have no use besides their definition
(for simplifier); `architecture.md:269-270` still names `SharpLayer` and `Window.end(Runnable, SharpLayer)`, renamed in
`31f80a6f` (for doc-updater); `core/System` as composition root, `Time`, `Window` and `Fonts` are documented decisions.

Shape check: 3 of 3 on role, drift 0 (runs 3 and 4 together: 5 of 5 on role, 0 of 18 off-role items reported).
Precision 1 confirmed of 3 here, 2 of 5 over the two runs. The slot that fails is the same one: three of five
findings (run 3 `uiBlock`, run 4 the `HotbarView` javadoc and `architecture.md:270`) had the settling text or
mechanism already in files the reviewer had read or cited. The run 3 edit asked for "the document, ADR or javadoc" and
accepted "none found plus the search you ran", and the search was by keyword. Edited in `roles.md`: "Already settled"
now says read, do not grep: read the document section for the package on each side and the javadoc of both classes,
quote what each says, or write "silent" with what was read.

Not passed: drift is cured, precision is not. Run 5, on `physics` or `ui/view`, with the edited slot.

Run 5 of `architect`, over `physics` (5 files, 544 lines, ~104k tokens), with "Already settled" rewritten as "read, do
not grep". 2 findings; 9 items in Discarded.

| Finding | Status | Why |
|---------|--------|-----|
| `EventActions.hurt` writes `EventSystem.canTriggerEvent`, a field nothing reads; the record holds a back-reference to `EventSystem` only for that write | Confirmed (low), thin | `EventActions.java:21` writes it, `EventSystem.java:89` sets it, and the only other mention of the name is the method `canTriggerEvent(Entity)` at `:58`; the real rearm is `previousEvent`. But `EventSystem.register` has no caller (the reviewer discarded that as "for simplifier"), so `events` is always empty and no action ever runs. The "boundary" is two one-line javadocs and the substance is dead code. |
| `CollisionChecker(World)` needs a whole `World` for `checkTile`, which only calls `isSolidTile` | Confirmed (low) | `CollisionChecker.java:10,46,69` verified; the entity half reaches into `world.entitySystem` at 87, 112, 133, 145, 165, 178, 192. No test mentions `CollisionChecker`. `ai` does not import `physics`, so using `SoliditySource` adds an edge but no cycle. The rule it cites is test guidance (`AGENTS.md`, Tests; `architecture.md:252-253` about A*), not a boundary rule for physics, and the reviewer said so. |

Discarded, checked: `EventSystem.register` without callers and `architecture.md:250` listing `TELEPORT` (the enum has
`HURT` and `HEAL`; `procedural-map-report.md:107` records its removal) are correct and go to simplifier and the doc.
`checkPlayer` and `collidesWith` use `entity.direction` while the other checks use `getEffectiveDirection` (true, for
guardian; not checked as a defect). The physics-entity package cycle (`Rectangle` imported by five entity classes,
`CollisionChecker` importing six entity types) was discarded as "settled by `architecture.md:246-249` and the
`EntityServices` javadoc". Those lines describe the wiring and say nothing on the cycle (no codemap or ADR mentions
one as deliberate). The result is defensible, since the service dependency from `entity` to `physics` is intrinsic, but
the reason given is the opposite error to runs 3 and 4: this time "settled" was applied to text that does not settle.

Shape check: 2 of 2 on role, drift 0 (runs 3-5: 7 on role, 0 of 27 off-role items reported). Precision 2 confirmed of
2, but one is thin. The edited slot worked in this run: both findings quote what the documents say and one admits the
rule is not written for physics. One run with the edited slot is not the two the other roles needed.

Not passed yet by the same criterion as `ambassador`, `conservative` and `modernizer` (two runs with the working
design). Run 6, on a package with documented decisions to tempt a wrong "settled", such as `audio` or `ioc`.

Run 6 of `architect`, over `audio` (13 files, 829 lines, ~94k tokens), chosen because its documents (ADR 0005, the
codemap, `AGENTS.md`) tempt a wrong "settled". The prompt added one line: when discarding because a document settles
it, quote the line. 1 finding; 13 items in Discarded.

| Finding | Status | Why |
|---------|--------|-----|
| The partida's music is chosen in two places: `Game.startWorld` (`Game.java:249-250`) and `System.reset` (`System.java:76-78`) | Confirmed (low), with two false supporting claims | The duplicated pair of calls is real and `System.reset(true)` is unreachable (the only caller is `reset(false)`, `Game.java:247`), though its javadoc already says "hoy nadie lo pide" (`System.java:68-70`). False: "`createDefault` receives `audio` but `System` never uses it" (it is passed to `GameViewPresenter`, `System.java:59`); the rule quoted from `AGENTS.md` is about `GameModule`, not about `Game`; and `Source.java:272-275`, cited as state owner, does not exist (the file has 74 lines). |

Discarded, checked: the stale ADR 0005 ("las entidades no importan ninguna clase de `com.punkipunk.audio`", 39 entity
files import `audio`) is right and goes to doc drift; `Volume` persisting its own file is settled by `data.md:255`; the
rest are settled or belong to other roles. No finding was dismissed with a document that does not say it (the failure
of run 5).

New failure, not seen in runs 3-5: 8 line citations point past the end of the file (`Volume.java:318-331` in a
104-line file, `Source.java:272-299` in 74, `AudioDevice.java:171-238` in 101, `Mixer.java:201-204` in 133,
`AudioId.java:70-76` in 39), all inside Discarded justifications and the finding's "State owner". It breaks the
per-file reading rule of the reviewer prompt. Possible cause: the added line asking to quote the settling line pushed
it to cite what it had not read. Not fixed, because the verification step caught it and the prompt works for the other
six roles; if it repeats with `architect`, revert the added line first.

Verdict. Runs 5 and 6 are the two with the final design (Boundary shape, "read, do not grep"): 3 findings on role, 3
confirmed in their core fact (one thin, one with false supporting claims), 0 off-role items reported, no document
misapplied in run 6. Runs 3-6 together: 8 findings, 5 confirmed, 2 doubtful, 1 refuted; 0 of 40 off-role items
reported as findings. Same bar as `ambassador`, `conservative` and `modernizer` (two runs with the working design):
**passed**. Severity stays low in nearly every finding, so an `architect` finding is a lead that needs the same
verification as any other, not a measurement. `SKILL.md` and `README.md` now list all seven roles as tested.

## First run with all seven roles

`/council entity/action all` (5 files, 527 lines), followed by hand from `SKILL.md`. Seven reviewers in parallel
(~95-130k tokens each, ~700k in all, about 90 seconds of wall time), then step 6 with three agents (~270k).
`git status --porcelain` identical before and after: no side effects.

| Role | Findings | Result |
|------|----------|--------|
| simplifier | 5 | 5 confirmed, all low |
| guardian | 2 | 2 confirmed: one real crash (NPE when a swing resumes with the weapon unequipped), one external-origin |
| optimizer | 0 | none in scope; its out-of-role note about the first mob in the arc was a real bug, verified and reported as a new finding |
| architect | 3 | 3 confirmed (one weak: the cited rule speaks of `Spell`, not of the strategy) |
| conservative | 1 | confirmed, but outside the scope and already known (`AGENTS.md:131`) |
| modernizer | 2 | 2 confirmed, both thin (`Math.hypot`, `EnumMap`) |
| ambassador | 5 | 3 confirmed (one duplicate of the simplifier, one of the guardian), 1 split in two (structure confirmed, symptom doubtful), 1 refuted (two adjacent `int`, no wrong caller) |

18 reviewer findings collapse into 14 distinct confirmed (3 overlaps between roles), 1 refuted, 1 doubtful symptom,
plus 1 new finding of mine: precision is high for the whole set and no role drifted into another's ground. The case
the skill was built for did show up: the top of the report is a real crash, not the 14 low items below it.

Step 6 filter: of 15 confirmed items only 3 passed (the guardian fix against the optimizer, a public-signature change
against the architect, a new class against the simplifier); the other 12 were skipped by the table, as designed.
Answers: optimizer ENDORSES (verified), simplifier ENDORSES with a condition (verified), architect OBJECTS (verified:
`json.model` would import `entity.Direction` while `entity` already imports `json.model`). The OBJECTS changed the
recommendation, so the step paid for itself once.

What the run found about the skill:

- **The `architect` cross-examination answered in the round 1 Output shape.** The cross-exam prompt says to copy the
  whole role section, and the architect's now carries an **Output** section; its OBJECTS came back as
  `### title / Boundary / Crossed at / ...`. Harmless here, but it breaks the ENDORSES/OBJECTS/AMENDS format. Fixed:
  `cross-exam-prompt.md` now says to copy the role without its **Output** section. Same risk for `conservative` and
  `modernizer`, which also have one.
- **Line citations were valid in all seven reviewers.** The out-of-range citations of `architect` run 6 did not
  repeat; that run had the extra line "quote the line that settles it" and this one did not. One more point for
  the hypothesis, not a proof.
- Two reviewers reported skipping part of the required reading (the guardian did not open `docs/CODEMAPS` or the ADRs,
  the optimizer skipped the ADRs); the prompt says "read before reviewing" but nothing checks it. Their findings held
  up anyway.
- **Report location.** Step 8 says "working directory". Here the shell directory had drifted to `src/main/java/...`
  and the file would have landed in the source tree; it was written at the repo root by hand. The game repo has no
  `council-report-*.md` in `.gitignore`. Worth stating "at the repository root" in `SKILL.md`.
- Step 5 mattered: of the guardian's crash, the reviewer cited one dereference (`:140`) and the same path also
  breaks at `:149` through `Tree.isCorrectWeapon`, which is the more common trigger.

## Untested

- Saving to `council-report-<date>.md`: the first validation run wrote it to a temporary directory; the full run on
  `entity/action` wrote it at the repo root (step 8 now says so). It works, but the game repo still has no
  `council-report-*.md` in its `.gitignore`.
