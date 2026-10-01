---
name: council
description: >
  Use when the user invokes /council to review a file or directory with reviewers of opposing incentives
  (simplifier, guardian, optimizer, architect, conservative, modernizer, ambassador).
argument-hint: <path> [role1, role2, ... | all]
disable-model-invocation: true
---

# Council

## Overview

Reviewers with opposing incentives see trade-offs a generic reviewer misses, but each one inflates its own
ground: without verification, the top of the report ends up occupied by false findings. The central work of
this skill is to verify, not to collect.

## Arguments

`$ARGUMENTS` = `<path> [roles]`.

- No path: ask for it and stop. Do not infer it from the working directory or from what was being discussed.
- Roles: a comma-separated list, or `all`. Defaults to `simplifier, guardian, optimizer`.
- The definitions live in `references/roles.md`. If they ask for a role that isn't there, list the valid ones
  and stop.
- `simplifier`, `guardian` and `optimizer` went through several test rounds against real code; `architect`,
  `conservative`, `modernizer` and `ambassador` did not. Mark them as "untested" in the report header if they
  are in the list, and also if the cross-examination (step 6) launches one as a counterweight — with the default
  roles, the counterweight of `simplifier` is `architect`, so it can happen without the user asking.

## Process

1. **Prepare.**
    - List the source files under the path with their line counts.
    - If there is a `CLAUDE.md`, `AGENTS.md` or other project instruction file at the repo root, read it and
      note its path plus those of the documents it requires reading before reviewing or planning (codemaps,
      ADRs). The reviewer gets those paths, not a summary of yours.
    - If it is a git repo, save the output of `git status --porcelain` as the initial snapshot.
2. **Launch.** One `Agent` (`subagent_type: general-purpose`) per role, all in a single message. The prompt is
   `references/reviewer-prompt.md`, filled in. Pass paths, not pasted code: the reviewer has to be able to
   search for callers outside the scope.
3. **Wait for all of them.** The following steps need every reviewer's answer. If the environment runs the
   agents in the background, keep waiting for their notifications: the report is written only once the last one
   is back.
4. **Check for side effects.** If it is a git repo, compare `git status --porcelain` against the initial
   snapshot. Any new change was produced by a reviewer: show it to the user before undoing it.
5. **Verify every finding** by reading the code yourself. Before checking anything, write its **key claim** in
   one line: the statement without which the finding does not exist, not a supporting detail. Choose it by its
   load, not by its literalness — test each candidate with "if this were false, does the finding die?". "It is
   called twice" is literal and easy to confirm; "that second call repeats work" is the one holding the finding
   up, and the one you have to verify. You name it, not the reviewer: whoever proposes tends to pick the part
   easiest to defend. And you name it **before** verifying, because that is the only thing that cuts off the
   later manoeuvre: when the claim falls, retreating to "well, what really mattered was this other thing, which
   does hold". Verify the key claim first; if it falls, the finding ends there and there is no need to go on.

   Then, link by link of the "Path" (not just the first and the last). Each kind of link is checked like this:
    - **Call:** the call exists on that line.
    - **Exception:** the line that throws it runs on the same thread as whoever would catch it (an enqueued task
      fails on the worker thread, not on whoever enqueued it).
    - **Concurrency:** write out the order of operations of each thread, including the tasks that same path
      enqueues. If a later operation in that order leaves the state correct, the interleaving is not a bug.
    - **Origin:** if the path starts from anomalous data or state (corrupt file, out-of-range value, shut-down
      executor), there is code that produces it today. If it can only come from outside the program (damaged
      disk, hand editing), it is an external origin and the maximum severity is medium.
    - **Frequency:** between the trigger (tick, frame, event) and the code there is no early return, cache or
      condition that cuts the executions short.
    - **Consequence:** the data or state affected is the one the finding says it is.

   In a maintenance finding there is no path to follow: what gets verified is the Evidence. Redo the search
   yourself — for dead code, search for the name across the whole repo and also as a string, because
   reflection, dependency injection, JSON or configuration use it without it appearing as a call; and look at
   visibility before declaring a public class or method surplus.

   Assign a status. **Confirmed**: the key claim was checked and no other link contradicts it. **Refuted**: the
   key claim does not hold, it is conditional ("if someone were to modify...", "even though it doesn't happen
   today") with no current code producing it, or the behaviour the finding wants to change is there on purpose
   — a project document says so, a javadoc explains it, or a test pins it down. **Doubtful**: the claim holds
   but a secondary link depends on data only visible at runtime.

   **A refuted key claim is not softened.** It does not drop to "doubtful", it does not drop a severity level,
   and it is not reworded into a smaller finding that survives: it goes to Refuted. If, while verifying it, you
   noticed something real nearby, that is a new finding, with its own claim and its own verification from
   scratch — not a rescue of this one.

   Refuting demands the same evidence as confirming: if a link has several branches (a default value and a
   present one, an empty case and a full one), the refutation has to cover them all.
    - If the reasoning is false but points at real mutable or shared state, follow that state to whoever writes
      and reads it: that is often where the bug the reviewer circled without seeing actually is.
    - You assign the final severity, using the criteria in `references/reviewer-prompt.md`; the reviewer's does
      not count.
6. **Cross-examination**, only with the confirmed findings and only with those that pass the filter in
   `references/cross-exam-prompt.md` (that file says which role each finding goes to and when it is worth
   cross-examining). One agent per counterweight role, with all the findings assigned to it together in one
   prompt. Steps 2, 3 and 4 apply just as in round 1: same kind of agent, wait for all of them to come back,
   and compare `git status --porcelain` again. Verify their answers with the rules of step 5: an objection or
   an amendment can also rest on a false claim. If no finding passes the filter, skip the step.
7. **Cross-reference.** The same spot flagged by two roles goes up in priority. Opposing proposals about the
   same code are a conflict for the user to settle. For the confirmed findings that did not go to
   cross-examination, start from the "Cost" field the reviewer already wrote and verify it like any other
   statement; if it does not hold up or was left empty, formulate the objection yourself. Mark in the report
   which ones came from a real reviewer.
8. **Save the report.** Write it to `council-report-<YYYY-MM-DD>.md`, in the working directory, using the
   template below. If one with that date already exists, append `-2`, `-3`, and so on. That way the report
   survives the conversation being compacted or the session being closed.
9. **Report** in the chat: the same content as the file, plus a first line with the path where it was saved.
   Write it in the language the user is writing to you in, which is not necessarily the language of these
   instructions. The field names of the template stay as they are.

Template:

```
## Council on <path> — <roles>

Reviewers: <role> (<n> findings), <role> (<n>), ...
<if any role in the list is "untested": one line saying so, with the names>

<1-3 lines: the most important thing the verification produced>

### Confirmed
1. **<title>** — `<file>:<line>` — <roles> — <severity>
   Key claim: <the statement without which the finding does not exist, and the file:line holding it up>
   [defect] Starts at: <file:line of the code that produces the starting state today>
   [defect] Path: <file:line → file:line → ... → consequence>
   [defect] Ends up as: <how the data is left after every operation on the path has run, including the
   enqueued ones>
   [maintenance] Evidence: <what you checked — the searches you ran, the misuse it enables, or the future
   change it complicates>
   Checked: <which file:line you read and what you checked at each point>
   Fix: <change>
   Cost: <the counterweight's answer — mark whether it came from the cross-examination (role +
   ENDORSES/OBJECTS/AMENDS, and whether you verified it) or whether you formulated it yourself>

### Doubtful
- **<title>** — `<file>:<line>` — <which runtime data would settle it>

### Conflicts
- `<file>:<line>`: <role A> wants <X>, <role B> wants <Y>. Recommendation: <...>

### Refuted (<n>)
- <title> (<role>): <its key claim, and what the code shows against it, with file:line>
```

Each finding uses the fields of its shape: a **defect** (something breaks or costs more than it should) carries
Starts at, Path and Ends up as; a **maintenance** one (surplus code, a name that lies, a limit set wrong)
carries Evidence instead — there, the absence of a caller refutes nothing, it is the finding itself.

It enters Confirmed only if you fill in the fields of its shape with real code. A defect whose trigger is "none
today", or whose final state comes out correct, goes to Refuted; if it depends on runtime data, to Doubtful.

Omit empty sections. Close by offering to apply, one at a time, the confirmed findings the user picks.

## Common mistakes

| Mistake                                                        | Correction                                              |
|----------------------------------------------------------------|---------------------------------------------------------|
| Sorting and deduplicating findings and calling it verification | Verifying means opening the cited code and the caller   |
| Inheriting the severity the reviewer assigned                  | Reclassify with the criteria: no real path, no high     |
| Confirming by looking only at the start and end of the path    | Check every link; the false ones break in the middle    |
| Pasting the code into the reviewer's prompt                    | Pass paths, so it can search for uses                   |
| Skipping the project instruction file                          | Its documented decisions refute many false positives    |
| Cross-examining every confirmed finding against every role     | Only those that pass the filter; the rest is paid noise |
| Taking a cross-examination objection on trust                  | An objection can rest on false premises too             |
| Naming the key claim after verifying                           | Name it first, check it after, or it gets retrofitted   |
| Rescuing a finding with a refuted claim by rewording it        | It goes to Refuted; what still stands is a new finding  |
