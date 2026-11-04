---
name: interactive-planning-doc
description: >-
  Create or revise engineering plans through discussion, with milestones,
  validation and acceptance criteria. Use before implementation, not for coding.
metadata:
  author: "yomihime（如月怜） <evenia@evenia.moe>"
  version: "1.0.0"
  updated_at: "2026-11-04T17:20:31Z"
---

# Interactive Planning Doc

Use this skill to turn an evolving product or engineering discussion into a
clean plan document that another agent can execute later. Keep the document
practical, specific, and free of conversational noise.

## Trigger Examples and Runtime Requirements

- Use: "Do not change code yet; turn our refactor discussion into an executable plan" or "Update the main plan's milestones and acceptance criteria."
- Do not use: "Implement the approved fix and run tests," "Explain this algorithm," or "Polish an email." TODO or release keywords alone do not make a request a planning-document task.
- This is document guidance with no runtime scripts and no Python, Node.js or operating-system requirement. The host must be able to read relevant materials and, when authorized, edit the plan. Project tools are needed only when checking project-specific assumptions; verify actual host capabilities rather than claiming universal client coverage.

## Ground Rules

- Treat the user's latest message as the current source of truth.
- If the user says "docs only", "no code changes", or equivalent, do not edit
  implementation files.
- Prefer editing one planning document over scattering decisions across files.
- Read existing project guidance before writing claims about the codebase.
- Use current code and stable architecture docs as facts; treat roadmaps and old
  plans as lower-priority references.
- Ask only focused questions that block a safe plan. Make reasonable assumptions
  when the risk is low and mark them as assumptions.
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

Record conflicts explicitly instead of silently choosing a side.

### 3. Keep a Decision Ledger

As the user answers questions, move decisions into a stable section such as
`已确认决策` or `Confirmed Decisions`.

Each decision should state:

- What was decided.
- The boundary or invariant it creates.
- Any follow-up condition, such as "re-check upstream before implementation".

Remove agent-side uncertainty, discarded options, and chat history from the
execution-facing plan unless they explain a remaining risk.

### 4. Shape the Document for Future Execution

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

Use many small milestones when risk is high. A milestone should be narrow enough
that an executor can tell whether it is complete.

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

Do not default to one giant commit or one commit per milestone.

Group commits by coherent review stages:

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

Post-acceptance cleanup starts only after:

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

When the user changes a decision:

- Update the canonical section of the document.
- Remove stale text that contradicts the new decision.
- Check related milestones, commit groups, cleanup, and validation sections.
- Summarize the document change briefly.

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

## Minimal Template

```markdown
# <Plan Title>

> This document is an execution plan. It does not prove implementation status.

## 1. Scope

## 2. Non-Goals

## 3. Confirmed Decisions

## 4. Current State and Target State

## 5. Data and Persistence

## 6. UI and Workflow

## 7. Code Structure

## 8. Milestones

### M01: <specific milestone>

Deliverable:

- ...

Acceptance:

- ...

## 9. Validation and Self-Review

## 10. Commit Groups

## 11. Post-Acceptance Cleanup

## 12. Open Questions
```

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
