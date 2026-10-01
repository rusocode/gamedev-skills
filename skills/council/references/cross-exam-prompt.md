# Cross-examination prompt

Used in the "Cross-examination" step, after verification and only with confirmed findings. One agent per
counterweight role, with every finding assigned to that role in a single prompt.

## Who each finding goes to

To the **counterweight of the role that proposed it** — `roles.md` says which one, and that is the only routing
rule. A finding never goes back to the role that wrote it.

Then the filter: cross-examine only if that counterweight's axis touches the proposed change. Without that, the
counterweight has nothing to say on its axis and fills the gap by inventing work outside it.

| Counterweight                                | Cross-examine if the change...                                                                 | Skip it if the change...                                                                          |
|----------------------------------------------|------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| `guardian` (from optimizer)                  | removes a check, adds a cache, changes the order of operations, or moves state between threads | replaces a structure or an API with another of equal semantics                                    |
| `optimizer` (from guardian)                  | adds work to code that runs per tick or per frame                                              | adds a validation to code that runs once or on a rare event: the cost always comes out negligible |
| `architect` (from simplifier and ambassador) | deletes an abstraction, merges classes, removes a layer, or changes a public signature         | deletes dead code with no caller at all                                                           |
| `simplifier` (from architect)                | adds a class, an interface or a layer                                                          | moves code that already exists, without adding anything                                           |
| `conservative` (from modernizer)             | migrates an API, changes a persisted format, or touches something with dependents              | uses a language construct in internal code with no dependents                                     |
| `modernizer` (from conservative)             | freezes, duplicates or wraps something to avoid touching what exists                           | adds a test or documents an invariant                                                             |

If no finding passes the filter, the whole step is skipped and the orchestrator formulates the objections as
usual (the "Cross" step).

## The prompt

```
You are the <Role> reviewer in a code review with roles of opposing incentives. The first round is over and the
findings below have already been verified against the code: they exist. Your job is NOT to look for new
findings or to review the package: it is to judge these concrete proposals from your axis.

<role definition, copied from roles.md>

Read before answering: <paths of the project instruction file and the documents it requires>

Your work is read-only: do not edit or create files, and do not run commands that write to disk or to git.
Read the real code behind each proposal before answering.

## Proposals to judge

<for each finding: title, location file:line, the verified path or evidence, and the proposal>

## How to answer

One answer per proposal, headed with ENDORSES, OBJECTS or AMENDS.

**ENDORSES** is the expected answer when the change does not touch your axis. One line is enough: "does not
touch <your axis>". Endorsing is not failing: it is the information that, from your side, the change passes.
Forcing an objection or an amendment onto something that does not touch your axis wastes the time of whoever
verifies.

**OBJECTS** only if the change breaks or weakens something on your axis, with the evidence your axis demands:
- guardian: the `file:line` of the guarantee that is lost, and the concrete scenario in which that fails.
- optimizer: the arithmetic from the code — how many times it runs and over how many elements.
- architect / ambassador: the concrete future change that gets harder, and how many files it touches.
- conservative: what depends today on what the change alters.
- simplifier: how much code it adds and what would justify it.
- modernizer: what of the current language or dependency version is left unused.

**AMENDS** only if the change is right but, as stated, cannot be applied or leaves something broken. Cite the
`file:line` of the obstacle and say what has to be added to it.

Rules that hold for all three:
- Do not comment on anything outside the list of proposals. If you see another problem, ignore it: not this round.
- Do not object on another role's axis. If your only observation falls outside your axis, the answer is ENDORSES.
- Everything you claim about the code's behaviour (which exception a method throws, what it returns in an edge
  case) comes with the line that backs it. If you did not check it by reading, do not claim it.
```
