---
name: product-doc-skill
description: Generate technical product requirement documents in Markdown from a feature request, business requirement, or rough product brief. Use when Codex needs to turn raw product input into a structured PRD with background, business rules, functional requirements, Mermaid flows, implementation approach, data model, tracking plan, acceptance criteria, and open questions.
---

# Product Doc Skill

## Workflow

1. Read `references/prd_template.md` before drafting.
2. Extract a concise title from the user's requirement and use it as the filename hint: `<title>_PRD.md`.
3. Follow the section order and intent from `references/prd_template.md`.
4. Write implementation-oriented content. Cover business rules, functional behavior, system interactions, data model impacts, tracking requirements, acceptance criteria, and open questions.
5. Use Mermaid diagrams when a workflow or decision path is involved. Keep diagrams minimal and directly tied to the feature.
6. If the input is incomplete, make reasonable assumptions and record them in `其他说明`. Ask follow-up questions only when a key gap blocks drafting.
7. Output pure Markdown only. Do not add prefaces or explanations outside the document.
8. Always start the document with:

```text
文件名：<title>_PRD.md
```

## Content Rules

- Keep headings and body content in Chinese unless the user explicitly requests another language.
- Prefer concrete system behavior over generic product rhetoric.
- For each functional section, describe triggering conditions, normal flow, exceptions, and downstream effects when relevant.
- When describing data models or interfaces, list fields, meanings, allowed values, and key constraints.
- For tracking and analytics, provide event name, properties, trigger timing, and purpose.
- Make acceptance criteria testable and specific.

## File Output

- Default behavior is to return Markdown in the response.
- If the user explicitly asks to write a file, write it inside the current workspace only, preferably `./docs/<title>_PRD.md`.
- Never write outside the workspace.
