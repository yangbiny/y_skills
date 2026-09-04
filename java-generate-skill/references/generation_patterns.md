# 生成模式与专项规则

## Facade 生成规则

1. 先看同类 Facade 属于哪种风格：
   - 直接调用 `CommandDispatcher` / `QueryDispatcher`
   - 直接调用 `App`
   - 先转 Proto，再复用现有 gRPC 逻辑
2. 如果已有 gRPC / Proto 流程，优先复用，不要在 Dubbo Facade 里重写一套业务逻辑。
3. 常见模式：
   - `Dubbo DTO -> Proto DTO -> Dispatcher`
   - `Dubbo DTO -> Internal Command -> Dispatcher`
   - `Req -> App`
4. Converter 只做转换，不做业务判断。

## 写操作与 `withPrimary`

1. 仅在 `dt-vshop`项目中，启用此规则

每次生成写代码时，必须先判断两件事：

1. 这是不是写操作。
2. 这一层是否必须显式包 `withPrimary`。

默认按写操作处理的场景：

- 新增
- 修改
- 删除
- 审核
- 确认
- 发奖
- 提交
- 生成任务
- 状态迁移

判断规则：

- 如果仓库明确要求“任何写类型操作都需要在 Facade 方法中使用 `withPrimary` 包裹”，优先满足该规则。
- 如果同类 Facade 已统一包裹 `withPrimary`，继续沿用。
- 如果该模块统一在 App 内处理主库写入，保持模块一致，不随意改风格。

禁止事项：

- 写操作漏包主库。
- 在读接口里偷偷写状态。
- 为了图省事，把所有查询也包进 `withPrimary`。

## Converter 生成规则

1. 先复用已有 Converter。
2. 如果需要新增，优先遵循既有命名：
   - `xxxConverter`
   - `xxxDubboConverter`
   - `xxxValueConverter`
3. 方法命名保持明确：
   - `toProto`
   - `fromProto`
   - `toDTO`
   - `from`
   - `map`
4. Converter 只表达字段映射，不夹带业务逻辑。
5. 如果某领域已把 Dubbo Converter 放在 `domain/<biz>` 下，继续沿用，不强制搬到 `facade`。

## Repo / Infra 生成规则

1. 仓储接口放 `domain/.../repo` 或业务领域包下。
2. 仓储实现放 `infra/repo/...` 或 `components/<biz>/infra/...`。
3. RepoImpl 负责：
   - 查询条件拼装
   - `DO <-> Domain` 映射
   - JSON 字段序列化与反序列化
   - 数据库异常语义转换
4. RepoImpl 不负责：
   - 协议 DTO 转换
   - Facade 响应包装
   - 领域规则校验
5. 如果项目已使用 `DatabaseTemplate` 风格，继续使用，不强行改成 JPA、MyBatis 或其他新 ORM 风格。

## Domain 生成规则

1. Domain 保持纯业务含义。
2. 新增实体、值对象、枚举时，优先对齐现有命名和构造风格。
3. 能用值对象表达的概念，不要长期散落在 Application 或 Facade 的裸字段里。
4. 状态流转、可生成判断、次数校验、唯一性规则，优先落在 Domain 或 Domain Service。
5. 不把协议层兼容字段的脏语义带入 Domain 命名。
6. 参数验证：需要将参数验证放在一个方法中，反向案例和正向案例如下
```kotlin
// 反向案例
fun func(req){
   require(data.accountId > 0) { "参数非法" }
   require(data.accountId > 0) { "参数非法" }
   require(data.accountId > 0) { "参数非法" }
}

// 正向案例
fun func(req){
  checkParams(req)
}

private fun checkParams(req){
  // 验证XXX 必须为：XXX
   require(data.accountId > 0) { "参数非法" }
   // 验证XXX 必须为：XXXX
   require(data.accountId > 0) { "参数非法" }
   require(data.accountId > 0) { "参数非法" } 
} 
```
7. 主方法中，必须保持干净、清晰的逻辑链路，比如：第一步、第二步、第三步；每一个主链路必须有注释

## Facade调用逻辑

1. Facade调用服务时，优先使用 Facade的原始方法类，不要新增 Cmd 等中转类

## 测试生成规则

1. 核心逻辑必须有测试。
2. 先找同类测试位置，再新增测试：
   - Facade 测试放 `it-tests/src/test/kotlin/.../facade/...`
   - Application / Handler 测试放 `it-tests/src/test/kotlin/.../application/...`
   - RepoImpl 测试放 `it-tests/src/test/kotlin/.../infra/repo/...`
   - Domain 测试放 `it-tests/src/test/kotlin/.../domain...`
3. 纯字段透传的薄 Converter 可以由调用方测试覆盖；如果转换有条件分支，单独补测试。
4. 失败路径不要省略：
   - 参数非法
   - 状态不允许
   - 数据不存在
   - 重复提交
   - 写入失败

## 禁止事项

- 不要在 Facade 层写核心业务逻辑。
- 不要让 Domain 依赖 Infra、Dubbo DTO、Proto DTO、数据库 DO。
- 不要让 RepoImpl 直接返回 DO 给上层。
- 不要无依据地引入新抽象、新目录、新依赖。
- 不要改变既有接口契约，除非用户明确要求。
- 不要无测试交付明显包含核心规则的代码。
