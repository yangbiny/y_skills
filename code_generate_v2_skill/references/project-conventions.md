# 按项目启用的约定

只读取与当前仓库相关的部分；路径只是定位线索，不授予跨仓库访问或修改权限。

## dt 系列项目

- 涉及 Dubbo Facade、RPC、DTO 等共享契约时，在已授权且存在的 `/Users/knowreason/object/dt-metadata` 查找定义与消费者；不能假定所有项目的 HTTP DTO 或内部对象都归这个仓库。
- 同时核对生产者、消费者的分支、接口版本和实际依赖。共享契约变化列出所有受影响仓库和文件，纳入修改审批，不凭本地同名类认定运行环境一致。
- `dt-vshop` 写链路显式核对 `databases.withPrimary` / `database.withPrimary`。目标约定要求在 Facade 包裹时必须遵守；同模块已有统一 App 层路由且无冲突时沿用，不能遗漏主库路由或把它当事务。
- 其他项目不因借鉴代码而强制引入 `withPrimary`。
- `dtw-guide`：用户已授权完成已批准修改和必要检查后自动提交、推送本次改动，不重复询问。仍需确认目标分支、最终 diff、检查结果、hooks 与单测禁令的兼容性；详见 [前端验证与推送](frontend-push-checks.md)。既有用户提交信息约定为 `[it reboot]变更内容[from codex]`，同时核对当前仓库规则，不能将此格式误称为已存在的可执行 hook。
- `hasaki`：提交推送仍需明确授权；遵循当前 commitlint 的 Conventional Commits 规则，不套用 dtw-guide 的消息格式。两仓库的类型检查、测试源码覆盖、环境构建及 Git hooks 必须按 [前端验证与推送](frontend-push-checks.md) 分开验证。

## dt-metadata 版本与 SNAPSHOT 发布

用户已明确要求新分支使用日期 SNAPSHOT 版本，并确认 deploy 指 **发布 Maven SNAPSHOT 制品到远程制品仓库**。这项长期授权不包含 Git 提交推送、正式版本发布或执行单元测试；修改文件和建立分支仍在已批准任务范围内进行。

### 新分支版本

1. 新建开发分支前读取所选基线的实际项目版本及来源，核对父 POM、`revision`、模块引用和命令行/profile 覆盖；“当前版本”是该基线的版本，不擅自升级 major/minor/patch，也不直接取远程最新版本。
2. 默认格式为 `<基础版本>-<YYYYMMDD>-SNAPSHOT`，日期使用创建分支当天的 Asia/Shanghai 日期。规范化时移除末尾已有的 `-SNAPSHOT` 和本规则产生的末尾 `-YYYYMMDD`，保留其他合法版本限定符，再追加新日期和单个 `-SNAPSHOT`。格式无法可靠识别时先确认，不盲目删版本片段。
3. 例如在 2026-11-11 从 `4.26.0`、`4.26.0-SNAPSHOT` 或 `4.26.0-20261110-SNAPSHOT` 新建分支，目标均为 `4.26.0-20261111-SNAPSHOT`。数字与日期仅为示例，执行时读取实际版本和日期。
4. 同一开发分支后续修改保留已确定的 SNAPSHOT 版本，不随每次保存或跨日工作反复加日期。开发分支有效版本必须以大写 `-SNAPSHOT` 结尾；若已有分支仍为正式版本，在修改方案中包含转为日期 SNAPSHOT，不自动执行正式版 deploy。
5. 沿用统一版本源，不把所有模块 POM 改成重复的硬编码。2026-11-11 核验快照中根 `pom.xml` 为 `<revision>4.26.0</revision>`，项目版本、子模块 parent 和内部依赖使用 `${revision}`；通常更新 revision 即可，仍需核对当前所有引用及最终有效版本。不得顺带修改无关第三方依赖。
6. 已核验的 `version.sh snapshot` 会升级 minor 并生成不带日期的 SNAPSHOT，不符合本规则，不能直接调用；不为完成本次版本变更擅自重写该脚本。
7. 同一基础版本、同一天的新分支可能生成相同 Maven 坐标。发现并行分支共用坐标或已有制品来源不明时说明覆盖风险，不擅自增加分支名后缀或升级版本；需要独立坐标时由用户确定例外。

### 修改后自动 deploy

1. `dt-metadata` 完成本次已批准修改后，核对将发布内容、实际有效版本及模块；版本以 `-SNAPSHOT` 结尾时，在必要验证完成后自动 deploy，不仅执行 compile/install 就结束。一次完整修改任务发布一次，不在每次文件保存时发布。
2. 在执行前确认目标为项目既有、已确定的 Maven SNAPSHOT 仓库，核对 effective POM/profile/命令参数的发布目标、repository id 与凭据可用性。根 POM 没有 distributionManagement 时不得猜测 URL，也不得把下载依赖的 mirror 当发布目标；缺少配置时报告具体缺口。不要输出凭据，不擅自修改个人 Maven 配置或改发正式仓库。
3. 核验 JDK、插件、模块依赖、flatten POM 和 deploy 生命周期，确认生成的是本次修改的制品，避免发布旧 target。按实际 reactor 完成所需模块及父 POM 的一致发布，不任意漏掉内部依赖，也不扩大到其他仓库。
4. **禁止执行单元测试仍有效**，包括 deploy 前序阶段、自定义插件和脚本间接执行。可根据实际配置使用 `mvn -Dmaven.test.skip=true -DskipTests -DskipITs deploy` 作为命令模板；这不是免检查保证，必须确认所有实际测试执行器尊重相应跳过设置。需要额外 profile/目标参数时使用已核实值；参数未确定前不把模板说成可直接执行。
5. 需要验证测试源码编译时，先确认生命周期不会执行测试，再单独使用项目支持的 `test-compile` 路径，例如 `mvn -DskipTests -DskipITs test-compile`。核验没有生效的 `maven.test.skip=true` 跳过编译，并检查 Kotlin/Java 测试目录及实际编译结果。`skipTests`、`skipITs` 是否被自定义插件识别须核验；测试编译通过不等于用例执行通过。
6. deploy 自身可完成前序编译/打包，不机械重复已成功且未受后续变更影响的构建。只有必要验证通过且发布目标明确才继续；发布配置不明、编译失败或无法避免单测执行时停止并说明，不改版本掩盖失败，不声称已发布。
7. 检查 deploy 命令结果、实际上传的坐标与目标仓库信息；有可用只读接口时核对远程 SNAPSHOT 元数据/制品。Maven 发布成功与独立远程核验结果分开记录，多模块部分上传失败时明确说明部分发布，不能报告整体成功或无依据反复重试。
8. 消费者如需采用新版本，在对应仓库已批准范围内更新依赖并刷新 SNAPSHOT 缓存、验证实际解析版本。发布成功不代表消费者已经更新或部署；不擅自修改、提交或推送消费者仓库。

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
