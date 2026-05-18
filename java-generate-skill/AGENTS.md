# AGENTS.md

## 1. 语言

- 全过程使用中文。
- 分析源码、解释方案、说明生成结果时，必须给出关键类名、方法名、文件路径。

## 2. 执行顺序

1. 先读取目标仓库的 `AGENTS.md`、开发约定、模块结构说明、同类实现。
2. 先分析问题，再给出方案，最后生成代码。
3. 如果目标仓库要求“修改前先说明并获批准”，必须严格遵守。

## 3. 生成硬约束

- 保持目标仓库现有架构和目录风格，不新建平行结构。
- Domain 不得依赖 Dubbo DTO、Proto DTO、数据库 DO、具体 RepoImpl。
- Facade 不得返回数据库 DO，不得承载核心业务逻辑。
- RepoImpl 只负责 `DO <-> Domain` 映射，不做协议层转换。
- 遇到写类型操作，必须显式检查是否需要 `database.withPrimary` 或 `databases.withPrimary`。
- 如果目标仓库规定 Facade 写操作必须包 `withPrimary`，必须遵守。
- 核心逻辑必须补测试，但永远不能执行单元测试，只做编译验证。
- 优先放到目标仓库已有的同类测试目录。
- 接口、RPC、DTO等一律在：/Users/knowreason/object/dt-metadata 中
- 生成的每一个类、方法，都要有对应的注释
- 方法中的状态变更、调用其他方法等都需要提供注释说明：当前的操作是什么
- 所有的逻辑优先考虑放入Domain中：例如：
```kotlin
data class TestClass(
  val state: Ine
) {

  /**
   * 逻辑：结束的逻辑
   */
  fun finish(): Boolean{
    this.state = 2
  }
}
```

## 4. MCP 优先级

- 涉及 JDK 源码时，优先使用 `java MCP`。
- 涉及 Spring 实现时，优先使用 `spring MCP`。
- 涉及 MySQL 内部实现时，优先使用 `mysql MCP`。
- 涉及 TiDB 源码或文档时，优先使用 `tidb MCP`。

## 5. 参考文件

- 生成前检查与生成后说明格式：`references/generation_checklist.md`
- 分层、文件组织、对象引用边界：`references/layering_and_object_rules.md`
- Facade、Converter、Repo、Domain、`withPrimary`、测试规则：`references/generation_patterns.md`
- 反面案例：`references/negative_case_code.md`

当 `AGENTS.md`、`SKILL.md`、`references/` 之间存在冲突时，优先遵守本文件与目标仓库自身约束。
