---
name: dev-workflow
description: Master orchestrator for development workflow. Use when user says "下一阶段", "继续开发", "next task", "proceed", or asks to continue development. Coordinates spec-sync, progress-tracker, implement, testing-stage, and checkpoint skills in a pipeline to complete one sub-task per iteration.
metadata:
  category: orchestration
  triggers: "next task, proceed, continue development, 下一阶段, 继续开发"
allowed-tools: Read
---

# Development Workflow Orchestrator

You are the **Project Manager AI** for the Modular RAG MCP Server. When the user asks to proceed with development, you MUST execute the following pipeline **in order**.

> **This is a Meta-Skill**: It orchestrates other skills. Each stage's **specific implementation details** are defined in the respective skill's SKILL.md file. This file only defines **pipeline flow** and **inter-stage coordination**.

---

## Stage 0: Activate Virtual Environment (Pre-requisite)

**Before executing any pipeline stage**, activate the project's virtual environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

> his step is mandatory and must be completed before invoking any sub-skill.

---

## Pipeline Stages

| Stage | Skill | Description | Skill File |
|-------|-------|-------------|------------|
| 1 | `spec-sync` | Sync spec documents | `.github/skills/spec-sync/SKILL.md` |
| 2 | `progress-tracker` | Find next task | `.github/skills/progress-tracker/SKILL.md` |
| 3 | `implement` | Execute implementation | `.github/skills/implement/SKILL.md` |
| 4 | `testing-stage` | Run tests | `.github/skills/testing-stage/SKILL.md` |
| 5 | `checkpoint` | Save progress | `.github/skills/checkpoint/SKILL.md` |

> **For detailed execution steps, completion criteria, and output formats for each stage, refer to the corresponding SKILL.md file.**

---

## Pipeline Flow

```
                    ┌──────────────────┐
                    │   User: "下一阶段"  │
                    └────────┬─────────┘
                             ▼
                  ┌──────────────────────┐
                  │  Stage 1: spec-sync  │
                  └────────┬─────────────┘
                           ▼
                  ┌──────────────────────┐
                  │ Stage 2: progress-   │
                  │         tracker      │
                  └────────┬─────────────┘
                           │
                     ️ Exception? ──→ User Confirm → Update DEV_SPEC → Back to Stage1
                           │
                           ▼
                  ┌──────────────────────┐
          ┌──────▶│ Stage 3: implement   │
          │       └────────┬─────────────┘
          │                ▼
          │       ┌──────────────────────┐
          │       │ Stage 4: testing-    │
          │       │         stage        │
          │       └────────┬─────────────┘
          │                ▼
          │           ┌─────────┐
          │           │ Tests   │
          │           │ Pass?   │
          │           └────┬────┘
          │     No         │         Yes
          │     ┌──────────┴──────────┐
          │     ▼                     ▼
          │ Iteration < 3?     ┌──────────────────────┐
          │     │              │  Stage 5: checkpoint │
          │ Yes │              └──────────────────────┘
          └─────┘
                │ No (iteration >= 3)
                ▼
          ┌──────────────────┐
          │ Escalate to User │
          └──────────────────┘
```

---

## Inter-Stage Data Flow

The orchestrator is responsible for passing context between stages:

| From | To | Data Passed |
|------|----|-------------|
| Stage 2 | Stage 3 | Task ID, Task Name, Relevant Spec Chapters |
| Stage 3 | Stage 4 | Files Changed, Module Paths |
| Stage 4 | Stage 3 | Test Failures (on failure, for iteration) |
| Stage 4 | Stage 5 | Test Results, Iteration Count |
| Stage 2,3,4 | Stage 5 | Task ID, Files Changed, Test Summary |

---

## Quick Commands

> **Important Note**: Each execution of "next task" completes **one sub-task** (e.g., A1 → A2 → A3), not an entire phase (e.g., Phase A → Phase B).

| User Says | Pipeline Behavior |
|-----------|-------------------|
| "next task" / "下一阶段" | Full pipeline (Stage 1-5), completes **next sub-task** |
| "continue" / "继续实现" | Skip to Stage 3 (assumes task known) |
| "status" / "检查进度" | Stage 2 only |
| "sync spec" / "同步规范" | Stage 1 only |
| "run tests" / "运行测试" | Stage 4 only |
| "fix progress" / "修正进度" | Stage 2 validation + DEV_SPEC update |

---

## Orchestrator Rules

1. **Delegation**: Each stage's specific logic is defined by its skill; the orchestrator only handles invocation and flow
2. **Spec is Source of Truth**: Progress tracking is based on `DEV_SPEC.md`
3. **Stage Order**: Execute in 1→2→3→4→5 order unless explicitly specified otherwise
4. **Single Sub-Task**: Each pipeline run completes **one sub-task**
5. **User Confirmation**: Wait for user confirmation after Stage 2 before continuing
6. **Test Before Checkpoint**: Stage 4 must pass before entering Stage 5
7. **Iteration Discipline**: Enforce 3-iteration limit
8. **Two-Step Checkpoint**: Stage 5 requires two user confirmations:
   - First: Verify work summary (then auto-update DEV_SPEC.md)
   - Second: Decide whether to execute git commit