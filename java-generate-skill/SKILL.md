---
name: java-generate-skill
description: 在 Kotlin + Java、Maven、DDD/CQRS、Dubbo 或 gRPC Facade 项目中生成、补齐或重构服务端代码时使用。适用于新增或修改 facade、application、domain、repo、infra、converter、测试等文件，要求严格遵守分层、对象引用边界、主库写入包装、复用既有 dispatcher 与 converter，并且全过程使用中文说明。
---

# Java 代码生成技能

## 适用场景

- 用户要求生成、补齐、迁移或重构 Java/Kotlin 服务端代码。
- 目标工程存在明显分层，例如 `facade`、`application`、`domain`、`infra`、`repository`、`components`。
- 需求涉及 Dubbo Facade、gRPC Facade、Application Handler、Query/Command、Domain、RepoImpl、Converter、测试。
- 用户要求保持现有架构、接口契约和代码风格，不希望引入新依赖或新框架。

## 使用流程

1. 先读取目标仓库的 `AGENTS.md`、开发约定、模块结构说明。
2. 判断当前业务属于哪种目录风格：
   - 经典分层：`facade / application / domain / infra`
   - 业务目录：`components/<biz>/application|domain|infra`
3. 判断本次变更是读还是写，以及是否涉及 Facade、Converter、Repo、Domain、测试。
4. 查找至少一组同类实现，作为本次生成的样板。
5. 如果仓库要求“修改前先说明并获批准”，必须先给出修改内容、文件落点和方案。
6. 生成代码后，按参考文件中的说明格式给出结果。

## 读取导航

- 生成前检查、生成后说明格式：读取 [references/generation_checklist.md](references/generation_checklist.md)
- 分层、文件组织、对象引用边界：读取 [references/layering_and_object_rules.md](references/layering_and_object_rules.md)
- Facade、Converter、Repo、Domain、`withPrimary`、测试生成规则：读取 [references/generation_patterns.md](references/generation_patterns.md)

## 触发后的默认动作

1. 优先定位同类代码，再决定生成方式，不要凭空设计新模式。
2. 如果是 Dubbo Facade、DTO、契约对象相关代码，优先到 `/Users/knowreason/object/dt-metadata` 查找现有类与接口。
3. 如果仓库要求写类型操作必须包 `database.withPrimary` 或 `databases.withPrimary`，生成时必须显式检查这一点。
