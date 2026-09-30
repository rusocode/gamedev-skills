# Council

Audits a file or directory with [roles](references/roles.md) that have opposing incentives, then verifies every
finding against the code before it reaches you. What you get back is short and true, not long and padded.

An AI review is easy to inflate, ask for problems and you get problems, whether or not they exist. **Council's main
job is not collecting findings, it's refuting them.**

Each role defends one thing, is priced by one counterweight, and has one trap it tends to fall into. The table
below covers the first two; [roles.md](references/roles.md) has all three, plus what each role goes looking for.

| Role           | Defends                                        | Counterweight  | Tested |
|----------------|------------------------------------------------|----------------|--------|
| `simplifier`   | Less code, less abstraction, less indirection  | `architect`    | yes    |
| `guardian`     | Invariants, explicit errors, validated input   | `optimizer`    | yes    |
| `optimizer`    | Time and memory where they're paid many times  | `guardian`     | yes    |
| `architect`    | Clear boundaries, dependencies pointing right  | `simplifier`   | no     |
| `conservative` | Stability; where it's dangerous to touch       | `modernizer`   | no     |
| `modernizer`   | Using what the language version already offers | `conservative` | no     |
| `ambassador`   | Honest names, signatures hard to misuse        | `architect`    | no     |

**The four untested roles were written but never run against real code. The skill flags them as untested in the
report header, so a finding from one of them is a suggestion, not a measurement.**

## Installation

```bash
npx skills add rusocode/gamedev-skills --skill council
```

## Recommended model

**Use the best model you have.** Most of the run is the skill checking complaints and throwing out the ones that
don't hold up, and that step is pure judgment. A weaker model does the cheap version of it, which is sorting the
complaints and calling that verification. Preventing exactly that is the reason the skill exists.

If your agent can hand subagents a different model, the reviewers are the safe place to spend less, since their
mistakes are what the checking step is there to catch. Don't take them to the cheapest tier, though. A noisier
reviewer saves you nothing, it just moves work onto the step that costs the most.

## Usage

Unlike the other skills in this repo, Council never triggers on its own. You invoke it by command:

```bash
# Audit the package with the default roles
/council src/world/chunk
# Audit the package with the guardian and optimizer roles
/council src/world/chunk guardian, optimizer
# Audit the package with all roles
/council src/world/chunk all
```

_Roles default to `simplifier, guardian, optimizer`. Pass a comma-separated list, or `all`, to change that._

### Choosing the roles

Naming the roles that match the code is the cheapest way to make a run worth its cost, a reviewer with nothing to
look for still reads the whole package, and then invents something to justify the trip.

| What you're auditing             | Roles worth naming         |
|----------------------------------|----------------------------|
| Threads, queues, file or net I/O | `guardian, optimizer`      |
| Per-tick or per-frame hot paths  | `optimizer, guardian`      |
| A package that grew messy        | `simplifier, architect`    |
| Something you're about to change | `guardian, conservative`   |
| A public API others depend on    | `ambassador, conservative` |

### When to use it!

> [!IMPORTANT]
> **Council is an audit, not a review. Run it occasionally, against one package you have reason to distrust, and keep
the file it leaves behind.**

| Situation                                       | Use                 |
|-------------------------------------------------|---------------------|
| Code you just wrote or touched                  | your review command |
| A package you suspect, or are about to refactor | **`/council`**      |
| Markdown, config, or a handful of small scripts | You read it!        |

Most of what it costs goes into verifying findings. On code with no threads, no hot paths and no persisted
formats, most roles have nothing to bite on, and you pay for reviewers that read the whole package to report
nothing.

## How it works

1. **It calls in a panel.** One reviewer per role, all reading your code at the same time, each one told to care
   about a single thing and ignore the rest. They work apart and never see each other's notes, so nobody agrees
   with anybody out of politeness.
2. **It makes sure nobody touched your files.** The reviewers are only supposed to read. "Supposed to" is not a
   promise, so the skill takes a snapshot before and after and shows you anything that moved.
3. **It tries to prove every complaint wrong.** This is where most of the work goes. For each complaint it first
   writes down, in one sentence, the thing the complaint depends on. If that sentence turns out to be false, the
   complaint is dead. Only then does it open the code and check. Writing the sentence down *first* is the whole
   trick, because once you already know the answer, it's too easy to quietly switch to an easier claim and
   declare victory.
4. **It asks the opponent what the fix would cost.** Every role has someone who wants the opposite, so whoever
   wants less code is answered by whoever wants clear structure. Complaints that survive step 3 get handed to
   that opponent, but only when they actually have something to say. Nobody is asked to price a change they
   don't care about; that just invites them to make something up.
5. **It writes everything down.** The result goes to a `council-report-<date>.md` file next to your code, so it
   outlives the chat.

One rule holds the whole thing together. **A complaint that fails step 3 doesn't get to shrink into a smaller
complaint that survives.** It goes in the Refuted list, with the line of code that kills it. If checking it
happened to turn up something real nearby, that counts as a brand-new complaint and goes through the same
wringer from the start.

### What you get

A file named `council-report-<date>.md`, saved in your working directory, and the same content in the chat.
Complaints arrive already sorted into four lists, and that sorting is most of what you are paying for.

| List          | What is in it                                                                | What you do with it   |
|---------------|------------------------------------------------------------------------------|-----------------------|
| **Confirmed** | Checked against your code, and it held up                                    | Act on it             |
| **Doubtful**  | The reasoning holds, but its last step needs data you only see while running | Judge it yourself     |
| **Conflicts** | Two roles want opposite things in the same spot                              | Your call             |
| **Refuted**   | Complaints that died, each with the line of code that killed it              | Read it, then drop it |

The Refuted list is there on purpose. A review that found little and a review that quietly buried its weak
findings look exactly the same from the outside, unless you can see what got thrown out and why.

A Confirmed entry looks like this.

```
1. Inventory list is handed to the save thread while the UI still edits it
   Inventory.java:88 | guardian | high

   Key claim   The list handed over is the live one the UI keeps editing, not a copy
   Starts at   Inventory.java:62, any time the player moves an item
   Path        Inventory.java:88 -> SaveQueue.java:40 -> writer thread reads the list
   Ends up as  A save file with an item counted twice, or missing
   Checked     Read both files, nothing copies the list, and the writer runs on its own thread
   Fix         Hand over a copy instead of the list itself
   Cost        optimizer OBJECTS, one copy per item move, which is an event and not a frame
```

**Key claim** is the sentence from step 3, the one the whole complaint rests on. **Checked** is what the skill
read in order to believe it, so you can redo the check yourself instead of taking its word. **Cost** is the
opposing role's verdict, marked ENDORSES, OBJECTS or AMENDS.

## What it catches, and what it doesn't

Council trades recall for precision, on purpose. Know which side of that trade you're on:

- **It's good at not wasting your time.** Across the test runs, the verification step moved findings to Refuted
  that earlier, unverified runs had reported as real and ranked first — including a race condition that didn't
  exist, a crash reachable only from a hand-edited save file, and a cost argument with invented numbers.
- **It is not a bug finder.** In nine runs over a package that contained a real, known concurrency bug, it never
  found it. Two reviewers passed next to it and went around. A single careful read only sees so much, and no rule
  in the skill fixes that.
- **It is an audit, not a review**, which is why it's worth running only occasionally — see
  [When to use it](#when-to-use-it).

## Similar projects

- [Llicklair/consejo-7-sabios](https://github.com/Llicklair/consejo-7-sabios) is where Council's roles and its key
  claim rule come from. A Python CLI that debates a whole project question with the same seven sages and the same
  counterweights, reaches consensus, has a judge synthesize a plan, and can execute it on an isolated branch. Its
  verifier enforces in Python what Council can only ask for in Markdown, that a refuted key claim kills the finding
  outright. Council keeps the roles, drops the debate and the execution, and points them at one path of code.
- [addyosmani/adverse](https://github.com/addyosmani/adverse) combines three reviewer perspectives with a cross-review
  round. It also ships as a CLI and can review diffs or run in CI. Council is a lighter, explicitly invoked audit
  focused on tracing and verifying each claim against the code, then saving a dated report.
- [alecnielsen/adversarial-review](https://github.com/alecnielsen/adversarial-review), which despite the shared name
  has nothing to do with the entry below it, is a bash script that pits Claude against GPT Codex over a whole
  directory, four phases a round and up to three rounds, then applies the fixes both models agreed on. Its
  independence is the real thing, two vendors rather than one model wearing different hats. Council gets its friction
  from opposing incentives instead, and treats agreement as a claim still to be checked, not as confidence.
- [ng/adversarial-review](https://github.com/ng/adversarial-review) reviews branches and pull requests with multiple
  agents, mechanical checks, optional cross-model review, and a bounded fix-and-verify loop. Council does not modify
  code or manage PR feedback; it focuses on role-based review of a chosen path and a transparent report of confirmed,
  doubtful, and refuted findings.
- [wan-huiyan/agent-review-panel](https://github.com/wan-huiyan/agent-review-panel) is the largest of these: 4-6
  personas auto-selected from the content, several recorded rounds of debate, a judge to settle them, and its own
  verification and anti-groupthink gates, over code, plans and docs alike. Council is narrower by design, seven fixed
  roles you choose yourself, no debate, one counterweight reply per surviving finding, and one Markdown report.

## Structure

```
council/
├── SKILL.md                       # Instructions for the agent: process, verification rules, report template
├── README.md                       # Installation and human-facing usage
├── references/
│   ├── roles.md                    # Roles, counterweights, and traps
│   ├── reviewer-prompt.md          # Round 1 prompt and severity criteria
│   └── cross-exam-prompt.md        # Round 2 prompt and cross-examination filter
└── docs/
    └── DESIGN-LOG.md               # Failure history and the rule derived from each case
```

`docs/DESIGN-LOG.md` is not read by the agent. It's there for whoever edits the skill next: each rule in `SKILL.md`
exists because something failed in a test run, and the log says what.
