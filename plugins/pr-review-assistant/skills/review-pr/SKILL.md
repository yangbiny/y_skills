---
name: review-pr
description: Review local git diffs with /review-pr. Use when the user asks to review staged, unstaged, or local ref-range changes and wants a structured PR-style report without remote APIs or external MCP servers.
---

# Review PR

## Scope

Use this skill for `/review-pr` local code review. Do not use hosted PR URLs, PR IDs, remote APIs, tokens, or external code hosting services.

Inputs:

- `/review-pr`: review current repository local changes by reading both staged and unstaged diff.
- `/review-pr --base <ref> --head <ref>`: review `git diff <base>...<head>`.
- `/review-pr --focus performance|security|readability`: keep the same report structure, but prioritize the selected concern.

If the user passes a hosted PR URL, explain that this plugin is local-only and ask for local refs or local diff content.

## Diff Collection

Run only read-only commands.

For `/review-pr`:

1. Inspect `git status --short`.
2. Read `git diff --cached`.
3. Read `git diff`.
4. Merge findings mentally; do not write files.

For `--base` and `--head`:

1. Validate both refs are present in the local repository.
2. Read `git diff <base>...<head>`.

If no diff exists, output:

```markdown
# PR Review Report

未发现可审查变更。请先产生 staged/unstaged 变更，或使用 `/review-pr --base <ref> --head <ref>` 指定本地 ref 范围。
```

## Review Workflow

Apply these phases in order:

1. `analyze_diff`: summarize changed files, entry points, public interfaces, data flow, and risky areas.
2. `detect_bug`: look for nullability, boundary, lifecycle, concurrency, transaction, permission, resource leak, exception swallowing, and compatibility bugs.
3. `check_style`: check naming, complexity, duplication, readability, layering, and local project conventions.
4. `evaluate_risk`: classify blast radius, data safety, rollback difficulty, and missing verification.
5. `generate_review`: produce the final Markdown report only.

For Java/Kotlin/Maven/DDD repositories, reuse the standards from the local `java-generate-skill` when available:

- Domain layer contains business logic only.
- Repository/infra code handles data access only.
- Facade is the RPC boundary.
- Write operations exposed through Facade must be wrapped with `databases.withPrimary` or the local equivalent.
- Preserve public contracts and existing converter/dispatcher patterns.

For general code quality, reuse the inspection dimensions from the local `code-generate-preview-skill` when available:

- Type and syntax risks.
- Interface and contract compatibility.
- Error handling and edge cases.
- Security, dependency, and maintainability risks.

Do not run unit tests. If validation is needed, mention the exact verification that was not run.

## Prioritization

For large diffs, first group by file and prioritize:

- Core business logic.
- Facade or RPC entry points.
- Repository, infra, SQL, migrations, serialization, permissions, concurrency, configuration, and security-sensitive paths.
- Public API, DTO, command/query, or schema changes.

Avoid cosmetic comments unless the review has no higher-value findings.

## Output Format

Always output Markdown in this exact structure:

```markdown
# PR Review Report

## 🔴 Critical Issues
- ...

## 🟠 Potential Risks
- ...

## 🟡 Improvements
- ...

## ✅ Good Practices
- ...
```

Each actionable item should include:

- File path.
- Line number from the diff hunk when available.
- Problem.
- Impact.
- Concrete fix suggestion.

If a line number cannot be determined, cite the file path and nearby diff context. Do not invent line numbers.

If a section has no findings, write `- 未发现。`
