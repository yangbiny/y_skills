# AGENTS.md

## 行为规则

- 所有任务必须遵循 SKILL.md
- 默认先读取 references/prd_template.md
- 默认返回 Markdown 内容，不强制落盘
- 如需落盘，只允许写入当前工作区内的 ./docs/

## 文件规则

- 文件命名：{{title}}_PRD.md
- {{title}} 必须来自用户输入的需求名称提炼

## 模板规则

- 默认使用 references/prd_template.md
- 不允许自行更换模板，除非用户明确指定
