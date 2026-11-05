---
name: interactive-planning-doc
description: >-
  Turn engineering goals into a complete, handoff-ready main plan early through
  upfront investigation and focused clarification. Use for feature, architecture,
  refactor or release planning; skip pure execution of a complete plan and small fixes.
metadata:
  author: "yomihime（如月怜） <evenia@evenia.moe>"
  version: "1.0.0"
  updated_at: "2026-11-05T02:48:56Z"
---

# Interactive Planning Doc

Turn engineering goals into one main plan another executor can use. The default
flow is upfront investigation → focused clarification → complete first draft →
next-executor check → handoff baseline. Aim to produce the whole plan early,
without chapter-by-chapter drafting or approval across chat turns. This does not
limit necessary questions, internal drafts, write calls, or later revisions.

## Trigger Examples and Runtime Requirements

- Use: "Do not change code yet; turn our refactor discussion into an executable plan" or "Update the main plan's milestones and acceptance criteria."
- Do not use: "Implement the approved fix and run tests," "Explain this algorithm," or "Polish an email." TODO or release keywords alone do not make a request a planning-document task.
- This is document guidance with no runtime scripts and no Python, Node.js or operating-system requirement. The host must be able to read relevant materials and, when authorized, edit the plan. Project tools are needed only when checking project-specific assumptions; verify actual host capabilities rather than claiming universal client coverage.

## Ground Rules

- Use the user's latest message for goals and preferences; retain earlier valid
  decisions. Current source, actual candidates, and raw evidence establish
  implemented/verified facts. A target design is not current behavior.
- If the user says "docs only", "no code changes", or equivalent, do not edit
  implementation files.
- Prefer editing one planning document over scattering decisions across files.
- Read existing project guidance before writing claims about the codebase.
- Use current code and stable architecture docs as facts; treat roadmaps and old
  plans as lower-priority references.
- Investigate engineering facts and choose ordinary reversible local approaches
  autonomously. Ask about goals, experience, scope, success criteria, or material
  tradeoffs that need the user. State defaults, recheck triggers, and failure
  impacts for low-impact conditions.
- Stop at the plan for docs-only requests. Preserve existing implementation
  authorization at handoff without inventing whole-document approval. A plan
  does not authorize commits, pushes, installation, publication, or deletion.
- If the user provides a URL, external schema, standard, release rule, or
  current project status that may have changed, verify it from the source before
  writing precise claims.

## Project-Local Plans and Intermediate Files

Use `.agent-workspace/` as the single root for project-local standards and
intermediate files. Keep the working execution plan at
`.agent-workspace/<work-id>/plan.md` and drafts, option comparisons, and temporary
screenshots in that task's `scratch/` directory, for example
`.agent-workspace/feature-search/plan.md`. Read applicable `AGENTS.md` instructions
and existing task entries first, then reuse one main plan. Do not create duplicate
authorities, default duplicate rules, or empty files just to fill a template.
Choose a recognizable work ID that does not collide with existing work. It must not use
`memory`, `design`, `architecture`, `plans`, `work`, or other names reserved by existing tools. The fixed root filenames `runtime.md`, `index.html`, `pipeline-index-data.js`, and `.pipeline-index.lock` are also reserved even before they exist; compare case-insensitively and treat trailing dots or spaces as Windows aliases. Deliver
formal planning documents, product docs, or publication artifacts to the user's
specified destination; do not force those deliverables into a private workspace.

Let `yomihime-init` inventory and safely consolidate legacy directories and entries during
project initialization. Do not maintain long-term compatibility paths or fallback
lookups. Preserve existing plans, guides, and manual edits without overwriting;
report conflicts and obtain confirmation before resolving them, verify the new
content and references, and only then perform authorized cleanup. This skill does
not migrate discovered old files itself or create a duplicate plan while migration
is pending. Continue independent discussion and read-only planning while making
unresolved path issues explicit.

The workspace is local by default: do not stage, commit, publish, or include it in
build outputs by default. Check Git ignore and untracked status and existing
sharing arrangements, explain portability and privacy, and do not silently change
ignore rules or untrack existing files. Deliver or share only with explicit
authorization and a sensitive-information check. Clean up only disposable
intermediate files created for this task; preserve the main plan while needed for
execution or recovery, existing user files, and materials with unclear ownership.

## When Not to Use This Skill

- The user only needs a short answer, command output, or code explanation.
- The user explicitly asks for implementation and does not ask for a plan,
  proposal, or architecture document first.
- The task is a local bug fix that does not need future milestones, commit
  cadence, acceptance criteria, or cleanup planning.
- The user already supplied a complete plan and only asks for code execution,
  unless the plan itself needs to be updated.

## Workflow

### 0. First Move After Triggering

Start with one or two sentences explaining how you will use this skill:

- Say whether you are creating, revising, or reviewing a plan.
- Say whether you will avoid code changes.
- Say what context you will read, or which plan document you will create first.

Do not begin with a long methodology explanation. When the user asks you to edit
the document directly, edit first and summarize briefly afterward.

### 1. Establish the Planning Contract

Confirm or infer:

- Planning scope and non-goals.
- Whether code changes are forbidden.
- The target document path and whether it is a local working plan or a formal
  user-requested deliverable.
- The implementation horizon: one feature, one refactor, one release, or a
  multi-phase roadmap.
- Whether the plan should use step-by-step tasks, milestones, or both.

When the user asks for an empty framework, create the framework first and leave
content placeholders concise.

### 2. Gather Only Useful Context

Read the smallest set of files needed to avoid writing fiction:

- Project instructions such as `AGENTS.md` and the relevant standards and plan
  entries in `.agent-workspace/`.
- Existing architecture and roadmap docs relevant to the requested change.
- Current source files only when needed to ground module names, data paths,
  existing behavior, or migration risks.
- External docs only when the plan depends on external formats, APIs, versions,
  release rules, or current upstream status.

With project-memory, the coordinator restores the full current snapshot before
extracting relevant facts, code entry points, and drawings. Maps do not replace
fact checks; without maps, investigate the bounded problem rather than requiring
a repository-wide scan. Separate verified facts, user decisions, AI choices,
conditions/assumptions, and unknowns, with sources and relevant source/dirty
baselines. Investigate researchable questions instead of asking the user to
research the code. Record conflicts and the basis for resolving them.

### 3. Clarify Decisions and Keep a Decision Ledger

Ask obvious missing core goals early while continuing independent investigation.
Group independent questions by topic; resolve upstream decisions first when later
choices depend on them. As useful, give the current understanding, a few distinct
options, impacts, and a recommendation with reasons. Allow free-form answers;
do not reconfirm settled decisions or permissions. There is no fixed question
count or number of clarification rounds.

If a core question is unanswered, retain it and its impact. A complete draft may
include it, but the affected scope is not executable. Silence, timeout, and a
preselected option are not consent. Do not assume away conflicting core goals,
key business semantics, success criteria, irreversible data handling, compatibility
commitments, required permissions, or critical feasibility facts. Investigate
factual gaps; ask the user about intent and permission.

As the user answers questions, move decisions into a stable section such as
`已确认决策` or `Confirmed Decisions`.

Each decision should state:

- What was decided.
- The boundary or invariant it creates.
- Any follow-up condition, such as "re-check upstream before implementation".

Remove agent-side uncertainty, discarded options, and chat history from the
execution-facing plan unless they explain a remaining risk.

### 4. Produce a Complete Main Plan Early

Read and adapt the [plan template](assets/plan-template.md). AI fills and trims it
in the user's language, removing irrelevant sections and placeholders; do not
turn it into a chapter-by-chapter questionnaire. Retain necessary placeholders
only for an explicitly requested empty framework. A complete draft covers the
agreed scope, but does not mean every part is ready or authorized for execution.

A strong planning document usually includes:

- Purpose and scope.
- Non-goals.
- Confirmed decisions.
- Current behavior and target behavior.
- Data model, paths, persistence, and migration notes.
- UI and workflow changes.
- Module boundaries and code structure.
- External format or integration mapping.
- Error handling, privacy, safety, and user-data rules.
- Fine-grained milestones.
- Validation and code self-review requirements.
- Commit grouping.
- Acceptance process.
- Post-acceptance cleanup and merge/release preparation.
- Open questions.

Omit sections that do not help a future implementation agent.

### 5. Write Milestones, Not Vague Intent

Use verifiable capability outcomes when risk is high. State direct dependencies.
Cover all goals and acceptance upfront for large work; make near-term scope
dispatchable and name triggers for elaborating distant details, rather than
inventing file-level implementation.

For each milestone, prefer:

- `交付` / deliverable: the observable outcome.
- `验收` / acceptance: how to verify it.
- Clear boundaries: what it must not modify.

Avoid milestones like "improve architecture" or "finish UI". Split them into
data model, storage, UI shell, actions, workers, previews, import/export,
validation, docs, and compatibility pieces.

If the user requests milestones instead of step-by-step tasks, do not convert the
plan into a procedural checklist. Milestones can still be numerous and detailed.

### 6. Design Commit Cadence Separately

Design commit cadence only when it is actually needed, such as when the user
requests commit groups or staged review is useful. Otherwise omit this step;
a complete main plan does not require arranging commits. When needed, group by
coherent review boundaries rather than defaulting to one giant commit or one
commit per milestone:

- Responsibility or page boundary changes.
- Data model and storage boundary.
- UI shell and navigation.
- Editing and asset workflow.
- Compile/render/preview core.
- Import/export integrations.
- Documentation and TODO synchronization.
- Version/release preparation when appropriate.

For each commit group, include covered milestones, suggested commit message, and
pre-commit checks. Keep commit messages compatible with the repository's
convention.

### 7. Separate Development From Post-Acceptance Cleanup

Keep development milestones inside the development plan. Documentation updates
are development work when they document implemented behavior.

Tailor completion to the agreed endpoint and risks; design commit groups only
when useful. Require user trials, UI changes, installation, or publication only
when applicable. If the agreed scope includes user trials and post-acceptance
cleanup, begin after the applicable conditions hold:

- All planned milestones are implemented.
- The user has tested the feature.
- Known bugs are fixed.
- Required UI layout adjustments are complete.

Cleanup may include removing temporary bridge code, debug helpers, feature flags,
manual test artifacts, logs, caches, duplicate compatibility paths, intermediate
files, and release/version preparation. If cleanup reveals a behavior bug, return
to the relevant development milestone instead of hiding it in cleanup.

### 8. Plan Architecture Before Implementation

When the plan affects code structure, name boundaries that fit the actual system
and requirements. The following are examples for desktop/UI applications, not
mandatory layers for every project:

- Core models and domain services.
- Storage and path helpers.
- Import/export renderers.
- UI pages, widgets, dialogs, and workers.
- Signals/events between pages.
- Migration and backward compatibility surfaces.
- Places where dependencies must not leak.

For such applications, UI may trigger work, workers may run long tasks, core
modules may own business logic, storage helpers may own paths, and renderers may
own derived formats. Choose based on platform constraints, existing architecture,
and task evidence; do not require these layers or add modules just to fit them.

When a new system, major boundary change, or architecture review needs dedicated
design, load `architecture-design` if available in the runtime. Provide goals and
non-goals, constraints, key quality attributes, current-state evidence, and open
decisions. Keep accepted decisions, necessary contracts, risks, and validation
conditions in the same main plan. When detailed architecture artifacts are useful,
reference the existing canonical source with its baseline, status, and scope; do
not create a parallel plan or duplicate diagram source. Select views by the
question they answer. A design is not proof of implementation or successful
validation. If the skill is unavailable, state the gap and plan within the
affected code and existing documentation; do not install it automatically or
force local changes through a full architecture process.

For detailed diagrams that must survive the task, reuse the existing valid source
in place. Only when no source exists and one is needed, create the long-lived
canonical source on demand under `.agent-workspace/architecture/`, not in task
scratch. Register its path, revision, current/planned status, and owner through
an existing stable entry in `AGENTS.md` or `memory/current.md`. The main plan
references that same source; do not create a duplicate project-memory diagram
source. Keep the recovery-critical overview directly in current.md. At handoff,
verify that the entry is readable and references match the source revision, then
identify the next writer. Preserve the source and still-referenced evidence/views
when cleaning task materials. Finishing the plan does not authorize deleting them
or migrating or overwriting existing materials.

### 9. Add Self-Review Constraints

Include a code self-review section for large plans. It should force the executor
to check:

- Architecture boundaries.
- Dead code and duplicate logic.
- Naming and data ownership.
- User-data safety.
- Error messages and i18n.
- External format compatibility.
- Tests or validation commands.
- Whether temporary development bridges were removed or justified.

Make self-review happen before each commit group and once before user acceptance.

### 10. Iterate Cleanly

When decisions, requirements, evidence, or actual omissions change, the
coordinator identifies affected scope and reconciles in-flight results and write
rights. A single writer revises the main plan:

- Update the canonical section of the document.
- Remove stale text that contradicts the new decision.
- Check related milestones, commit groups, cleanup, and validation sections.
- Update the plan revision, affected task input-version, slices/maps, and evidence
  applicability; notify owners. Unaffected work follows existing scheduling rules;
  a failed pipeline still prohibits new work.
- Summarize the change briefly. Ordinary defects return to their development
  scope instead of reopening the user requirements questionnaire.

When the user asks to commit, amend, or push, verify the specific files authorized
for publication and check for sensitive information. Include only the intended
changes, preserve unrelated user or concurrent edits, and do not stage or publish
other `.agent-workspace/` materials with them.

### 11. Simulate the Next Executor Before Finalizing

Near the end, review the plan as if the next executing agent did not participate
in the discussion:

- Do they know which files to read first?
- Do they know which behavior must not change?
- Do they know how to verify each milestone?
- Do they know what requires user confirmation and what can be done
  autonomously?
- Do they know how commits should be grouped?
- Do they know when post-acceptance cleanup starts and that bug fixes do not
  belong there?

If anything is vague, edit the plan directly or ask the smallest necessary
question.

## Handoff Baseline and Optional Skill Connections

Identify the plan by a lightweight revision and relevant source/dirty baseline.
State executable scope, concrete blockers, endpoint, and permitted actions.
Distinguish revisions affecting requirements, contracts, acceptance, or permission,
and separate document completion, handoff readiness, authorization, implementation,
and verified behavior. Core open items block their dependent scope without
bypassing existing round or failure barriers.

When delegating, the coordinator owns the valid main plan, task assignment, and
result acceptance, identifying the task owner and result recipient/acceptance
responsibility. Writing the plan does not grant implementation, shared-file, or
external-action permission. Supply relevant REQ/sections, all applicable
constraints, candidate/dirty baseline, ready dependencies, allowed actions,
current run/attempt and failure/blocking state when a pipeline is used, and
evidence entry points; do not send the whole plan or chat by default. The receiver
checks valid inputs, actual directory, and permission, resolving gaps by impact.
Before transferring write rights, reconcile the old owner's stopped writes/return
of rights and define the new scope. Old-input results retain their identity;
check applicability before reuse or retesting. Updating the plan revision does
not lift an existing failure barrier.

These skills are optional; the current thread can perform their responsibilities
without installing skills or starting a team:

- **development-pipeline** consumes the same plan to derive REQ → M → SL → JOB,
  dependencies, rounds, and checkpoints. A complete main plan and gradual observer
  rendering are independent: submit definitions progressively or import together,
  while retaining start validation. Investigation, clarification, and milestones
  do not automatically correspond to execution rounds.
- **multi-agent-engineering** retains task-handoff-v1. Existing goal/baseline/
  dependencies reference the plan path, revision, relevant REQ/sections, ready
  scope, and open items. Include cross-domain invariants, role materials,
  candidate, directory, and write rights. Subtasks need only relevant sections,
  not the entire plan. No permanent planning role or mandatory protocol field
  is added.
- **project-memory** supplies sourced facts, entry points, and drawings through
  knowledge-extract-v1. Integrate accepted decisions and facts using its existing
  maintenance protocol. current.md retains recovery-critical goals, constraints,
  actual state, and the plan path/revision, without duplicating the plan/task table
  or presenting targets and planned checks as implemented/verified facts.

Observer return resets attempts, not topology. To add/remove nodes or change
rounds, coordinate in-flight tasks, collect real results, and preserve stop points.
Create an independent run for the revised remaining scope, referencing the old run
with applicable evidence. Preserve the old run's true state, do not force completed
or automatically inherit passed, and do not expand permission or reset user limits.

## Plan Template

Read [assets/plan-template.md](assets/plan-template.md) as needed when producing or
revising the first draft. Reuse the project's main plan without a parallel authority.

## Output Quality Checklist

Before finalizing the plan, verify:

- Project-local plans and intermediate files use the unified workspace; formal
  deliverables follow the requested destination. There are no duplicate main plans
  or long-term legacy-path fallbacks.
- The plan can be executed by an agent that did not participate in the
  discussion.
- Confirmed decisions are easy to find.
- Remaining questions are explicit and few.
- Milestones are fine-grained enough to prevent broad interpretation.
- Commit groups map to coherent review stages, with no required numerical relationship to milestones; one milestone may correspond to one commit.
- Cleanup is not used as a bucket for unfinished development work.
- Version, release, migration, and user-data rules are included when relevant.
- The plan does not duplicate long-term facts that can be read from `AGENTS.md`,
  architecture docs, or source files.
- The document contains no unnecessary praise, meta-chat, or historical debate.
