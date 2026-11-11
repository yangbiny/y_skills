# 按项目启用的约定

只读取与当前仓库相关的部分；路径只是定位线索，不授予跨仓库访问或修改权限。

## dt 系列项目

- 涉及 Dubbo Facade、RPC、DTO 等共享契约时，在已授权且存在的 `/Users/knowreason/object/dt-metadata` 查找定义与消费者；不能假定所有项目的 HTTP DTO 或内部对象都归这个仓库。
- 同时核对生产者、消费者的分支、接口版本和实际依赖。共享契约变化列出所有受影响仓库和文件，纳入修改审批，不凭本地同名类认定运行环境一致。
- `dt-vshop` 写链路显式核对 `databases.withPrimary` / `database.withPrimary`。目标约定要求在 Facade 包裹时必须遵守；同模块已有统一 App 层路由且无冲突时沿用，不能遗漏主库路由或把它当事务。
- 其他项目不因借鉴代码而强制引入 `withPrimary`。
- `dtw-guide` 不自动提交或推送。用户明确授权后，若当前仓库仍要求该格式，提交信息使用 `[it reboot]变更内容[from codex]`；分别报告本地提交和远程推送实际结果。

## IntelliJ 平台仓库

以下规则仅适用于目标确实使用 IntelliJ 平台 API 或对应目录时；普通业务项目不引入这些依赖。

- 新文件默认 Kotlin，既有 Java 保持 Java，用户指定语言时按用户要求。实验性平台 API 使用项目已有的 `@ApiStatus.Experimental`。
- `.editorconfig` 优先；没有定义时沿用原 IntelliJ 默认：缩进 2 空格（Go 为 4），行宽 140，`else/catch/finally` 换行。`/rustrover` 下 Kotlin 使用 4 空格的标准格式。
- build-scripts 代码：有 `community/platform/build-scripts/kotlin-style-recommendations.md` 时读取当前版本；保留内部 data class 字段 `@JvmField`、`.put()/.get()`、显式 `HashMap/HashSet/LinkedHashMap` 的适用约定。
- Eel/IJent 的 sealed/enum 判断按仓库的穷尽 `when` 规则处理，避免 `is/as?/==/else` 替代完整分支；存在 `community/platform/eel/docs/api/exhaustive-when.md` 时读取它。普通项目不套用该禁令。
- 新增 `@RequiresEdt/@RequiresBackgroundThread/@RequiresReadLock/@RequiresWriteLock/@RequiresReadLockAbsence` 时默认不传 `generateAssertion`。仅在用户明确要求或已证实断言不适用时设为 false 并解释；不复制 `IJPL-115548` 迁移标记。
- 捕获 Throwable/Exception 时，先调用 `com.intellij.diagnostic.rethrowControlFlowException(e)`，避免取消等控制流异常进入日志。Java 使用 `com.intellij.diagnostic.ControlFlowExceptionsKt.rethrowControlFlowException` 的静态导入；不用废弃包名，不手工列举 CancellationException。
- 保留 EDT、读写锁、协程作用域、生命周期和平台执行器约束。修改作用域前从当前源码确认创建者、父作用域、取消和释放关系；本包不依赖其他协程 skill。

上述仓库文档不存在时，根据当前源码和有效约定判断并说明缺口，不把旧文档路径当成已验证事实。
