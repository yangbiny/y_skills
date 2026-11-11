# JVM 服务端分层与生成模式

适用于已有 DDD/CQRS、Facade 或相近分层的 Java/Kotlin 工程。以当前仓库结构和同类实现为依据，不建立新的架构体系。

## 目录与职责

| 层 | 职责与允许引用 | 边界 |
| --- | --- | --- |
| Facade | HTTP/Dubbo/gRPC 等协议适配；请求响应、Converter、Dispatcher、App | 不承载核心规则、不直接操作数据库模板、不返回 DO |
| Application | 用例编排；内部 Command/Query、领域对象、仓储接口、领域服务 | 不新增对数据库 DO、StreamObserver 或外部协议包装的耦合 |
| Domain | 实体、值对象、状态规则、领域服务、仓储/适配器接口 | 不依赖外部协议 DTO、数据库 DO、具体 RepoImpl |
| Infra / RepoImpl | 查询条件、持久化、缓存、外部接入、DO 与 Domain 映射、JSON 编解码、数据库异常转换 | 不做 Facade 响应包装，不向上泄漏 DO，不承载核心领域规则 |

- 经典目录沿用 `facade/application/domain/infra`，业务目录沿用 `components/<biz>/application|domain|infra`；对外 Facade 沿用现有入口位置。
- 同业务、同类文件就近放置，不把一条链路人为拆到两套目录。
- “service”名称不能决定归属：领域服务承载领域规则，应用服务负责编排，基础设施服务处理技术接入。

## 对象与调用链

优先复用已经存在的路径，选择一条，不同时创造多套中转：

- 写：外部 Req → Converter/组装 → 内部 Command 或 App 入参 → CommandDispatcher/App → Domain → Repo。
- 读：外部 Req → Query/QueryDispatcher/查询 App → Domain 或已有内部查询投影 → Converter → 外部 Resp。
- 存储：Domain ↔ DO，转换留在 Infra；协议转换在 Facade/Converter。
- 如果已有 gRPC/Proto Dispatcher 流程，将 Dubbo DTO 转成既有 Proto 入参复用它，不复制业务逻辑。此时沿用实际内部契约是已有结构的例外，不据此让 Proto 进入 Domain，也不强行重构整个 Application。
- 已有 App/Facade 方法入参足够时直接复用，不为风格新建 Cmd；已有明确 CQRS 契约时沿用 Command/Query。
- 老模块把协议 Converter 放在 `domain/<biz>` 时，不因这次改动搬迁；不得把新的协议依赖扩散到领域实体或规则中。

## Facade 与 Converter

- 定位同类 Facade，确认是 Dispatcher、App 还是 Proto 适配链路。
- Converter 只做字段映射和必要格式适配，不作权限、状态、额度等业务决策。
- 复用既有命名与入口，如 `toProto/fromProto/toDTO/from/map`，不强行统一所有方法名。
- 空值、缺省值、枚举未知值、字段精度和旧协议兼容需显式核对。

## Domain 与 Repo

- 状态流转、资格判断、次数约束和业务唯一性规则放在领域对象或领域服务；并发唯一性仍需数据库约束或合适锁/版本机制保证。
- 仓储接口跟随领域包，RepoImpl 跟随 Infra 包。沿用 DatabaseTemplate/DAO 等已有工具，不擅自引入 ORM。
- 不把协议兼容字段的含混语义扩散到 Domain。
- 参数校验按职责分配：协议形状在边界，业务不变量在领域。多项相关校验可汇总为私有方法；避免重复验证和无意义的透传方法。

## 写操作、事务与异常

- 新增、修改、删除、审核、确认、发奖、提交、生成任务、状态迁移都要检查写路径。读方法含隐式写入时明确标出。
- 主库路由按项目约定决定；`dt-vshop` 的具体要求见 [项目约定](project-conventions.md)。`withPrimary` 不是事务，不保证回滚，也不应包裹所有查询。
- 纯参数检查或不依赖并发状态的准备可在事务外；读取当前状态、并发校验、领域状态变化和持久化是否需在同一事务内，由原子性与锁策略决定，不能一律把领域变更移到事务外。
- 保留框架的回滚语义，不要求每个事务机械增加 `try/catch`。确需捕获时使用项目的异常转换或回滚机制，不吞异常后返回成功，不凭空假定记录日志就能回滚。
- 避免在持锁事务中执行不必要的远程调用；外部副作用、重试和幂等遵循已有设计，不未经批准新增消息/事务框架。

## 有效的反例检查

- 一次使用的 `normalizeStart()`、`normalizeLimit()` 不自动拆成工具类；直接表达默认值时保留原空值和边界语义。
- 不把每条 require 拆成一个方法，也不为“主流程整洁”造多层无业务含义的转发。
- 不复制含未定义变量、修改 `val` 或返回类型不符的旧示例；实际生成代码必须符合项目类型与编译约束。
- 不把 DTO 转换扩展函数误称为扩展属性；选择已有 Converter 或普通方法取决于模块习惯。

## 核心规则验证设计

必要时为状态、额度、幂等、并发或条件转换补充有意义的测试代码，包含非法参数、状态不允许、记录缺失、重复提交、写入失败等相关分支。优先沿用项目测试位置，不强制新建 `it-tests`；已有该模块时按 Facade/Application/Infra/Domain 同类目录放置。纯透传可由调用方覆盖。禁止执行单元测试，交付明确说明仅补代码还是已完成其他验证。
