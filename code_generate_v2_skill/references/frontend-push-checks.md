# dtw-guide / hasaki 验证与提交推送

适用于这两个项目的代码改动与交付。仓库脚本会变化，每次以当前分支的文件和有效 Git 配置为准，不把本文中的核验快照当作永久事实。文档、注释等不影响可执行内容的改动可说明理由后缩减编译范围；业务代码改动不能只检查 diff 就提交。

## 授权与停止条件

- 用户于 2026-11-11 明确授权：`dtw-guide` 写完已批准范围的代码、完成必要检查后，自动提交并推送本次改动，不需要再次请求提交/推送许可。适用当前已确认分支；主分支写入确认、修改审批和工具权限仍按入口规则执行。
- 自动提交只包含本次授权改动，不能把已有人工修改、无关暂存内容或无关的本地未推提交一起推送。遇到混合内容先分清，不能安全分离时停止并说明。
- `hasaki` 没有自动提交推送授权；当前会话明确授权后才执行。
- 两者仍禁止单元测试执行。已授权提交不代表允许间接跑单测，不默认使用 `HUSKY=0`、`--no-verify`、改 hooksPath 或改脚本跳过门禁。发现钩子将执行单测时停止提交，完成其余检查后说明具体冲突，由用户明确处理；没有冲突时不额外询问。
- 必需检查失败或缺少证据时不自动提交推送；用户明确接受已知检查缺口时按限定范围执行并保留未通过状态。不将“历史错误”自动视为豁免。
- 授权不包含强推、删除远端分支、重写历史、合并 PR 或另行运行部署脚本。推送可能触发已有 CI，报告已知触发行为，不擅自手动追加发布。

## 预检

1. 核对 cwd、分支、HEAD、工作区与暂存 diff，确认 remote、upstream、待推提交及用户授权范围。真实远端/分支明确后才组成推送命令，不猜测 origin 或目标分支。
2. 读取适用 `AGENTS.md`、`package.json`、锁文件、`tsconfig*.json`、Vite/Jest 配置、`.husky`、lint-staged、commitlint、CI 入口和被调用脚本；查 `git config --get core.hooksPath` 确定有效 hooks。Husky 的通用分发壳不代表项目已配置具体检查。
3. 核对 Node、包管理器和现有依赖。通过 PATH、本地入口和版本检查判断可用性；依赖缺失按目标仓库规则恢复，不因某个入口缺失就认定工具未安装，不临时下载未声明工具。
4. 已知快照：两仓库 Node 要求均为 `>=24.11.0`，hasaki 声明 pnpm `10.22.0`；执行时重读配置，不把版本永久写死。hook 会直接调用 pnpm 时确认实际提交环境的 PATH 能找到它，不以关闭 hook 代替修复环境。
5. 检查格式化、构建清理目录、产物覆盖、插件上传及服务启动等副作用；所有写入必须在批准范围内。以只检查模式开始，自动格式化后的最终内容需要重新核验。

## 类型检查与单测编译的证据边界

“单测编译验证”在此指测试源码的静态类型/编译检查，不执行测试用例。两个仓库的已核验配置都没有独立覆盖全部测试文件的 `typecheck:test` 脚本。

- 列出本次新增/修改及受影响的测试文件；核对 `files/include/exclude/extends/references`、实际导入和编译器文件列表，确认它们真正进入检查范围。`include` 不是完整的最终文件集合。
- `pnpm exec tsc --noEmit --project tsconfig.json` 可用于现有 TypeScript 项目的静态类型检查；先确认本地工具与当前配置，再执行。只报告实际包含的文件和检查结果。
- 测试目录未纳入配置时明确列出缺口。需要专用 tsconfig 或转换检查脚本时，先说明具体文件、继承配置和覆盖范围，纳入批准范围；不为让检查通过随意排除测试、降低 strict 或替换类型声明。
- `tsc --noEmit` 不执行测试断言，不保证 Jest 的环境、mock、转换插件或模块加载在运行时正常。普通 tsc 也不能直接证明 Vue SFC 模板全部正确；`allowJs` 不等于已开启完整 JS 类型检查。
- Jest 的 babel-jest 去类型或 ts-jest 转换并非“仅编译”命令。`jest --findRelatedTests`、`jest -o` 都会执行用例，不得在单测禁令下借它们验证编译。
- 测试源码通过静态检查不等于单测通过；没有覆盖测试文件时只能报告源码类型检查结果，不能说“单测编译通过”。
- 全量类型检查失败时保留诊断；只有相同工具、依赖、配置及可比基线证据支持时才区分历史错误与新增错误。仅过滤出改动文件无报错，不足以证明没有跨文件回归。不得重置当前人工修改来建立基线。

## dtw-guide

### 证据入口和已核验链路

- `.husky/pre-commit` → `npm run test` → `jest -o --passWithNoTests`：普通 commit 会运行单测。没有有效的项目 pre-push 检查。
- `package.json`：`build` 顺序调用 `build:compile` 与 `build:materialize`。
- `vite.config.ts`：vite-plugin-checker 的 import 和插件调用被注释，Vite 编译不包含完整 TypeScript 检查。
- `lib/dual-public-path/materialize.js` 的 `materializeTarget()`：删除重建 `dist/`、`dist_online/`，替换 public-path sentinel 并检查残留。
- `jenkinsfile`：Testing stage 只输出文字；`Makefile` 和部署脚本另有清理依赖、安装、上传和写构建历史的操作。不得把执行整个 CI/Makefile 当成无副作用的本地编译检查。

### 必要检查

| 检查 | 当前可用入口（在仓库根目录、预检完成后执行） | 能证明什么及限制 |
| --- | --- | --- |
| diff 与格式 | `git diff --check`，并对将提交的内容运行 `git diff --cached --check`；按有效项目配置检查格式 | 不等于类型或构建验证；不虚构不存在的 lint 脚本 |
| 源码/测试 TS | `pnpm exec tsc --noEmit --project tsconfig.json` | 当前配置包含 `src/**/*.ts`，可覆盖其中 TS 测试；不主动覆盖 `lib/dual-public-path/plugin.test.js`，不证明 Vue 模板或完整 Jest 转换链 |
| Vite 编译 | `pnpm run build:compile` | 产生 `dist_build/`；不代表双包完成或类型检查通过 |
| 双包生成 | 前一步成功后运行 `pnpm run build:materialize` | 检查两个目标包、manifest/资源映射及 sentinel 处理；只编译不物化不能称完整发布构建通过 |

- `pnpm run build` 是两阶段的组合入口，确认脚本未变化后也可使用；不重复运行已经成功且未受后续修改影响的阶段。
- 构建会覆盖生成目录，先确认没有用户需保留的文件；不顺手运行 `make clean` 或删除依赖来解决检查问题。
- 当前提交钩子与单测禁令冲突，即使已有自动提交推送授权，也不能直接 commit 或静默跳过钩子。此处是已发现的实际阻塞，不是每次提交都新增审批。
- 提交信息沿用用户约定 `[it reboot]变更内容[from codex]`，核对当前规则；仓库安装了 commitlint 依赖不代表已配置 commit-msg 门禁。

## hasaki

### 证据入口和已核验链路

- `.husky/pre-commit` → `npx --no-install lint-staged`；JS/JSX/TS/TSX/MTS 按顺序运行 `prettier --write`、`pnpm test:staged`、`pnpm lint:staged`。部分文档/样式仅格式化，须根据本次暂存文件匹配实际任务。
- `test:staged` 使用 Jest `--findRelatedTests`，真实运行相关单测；禁止用它代替只读 ESLint/类型检查。提交钩子可能改写并重新暂存文件。
- `.husky/pre-push` 当前为空；`.husky/commit-msg` 调用 commitlint，使用 Conventional Commits，不能套用 dtw-guide 消息格式。
- `jest.config.ts` 的 `createJestConfig()` 使用 babel-jest，Jest 执行或转译不能证明完整 TypeScript 类型正确。
- `jenkinsfile` → `jenkinsScripts/pipeline.js` → SW 构建及 `jenkinsScripts/build.js`；已核验 feature 分支构建 test，master 构建 production/test，Testing stage 被注释。每次依据当前构建模式和 CI 配置确认目标，不假定远端作业与本地脚本完全一致。

### 必要检查

| 检查 | 当前可用入口（在仓库根目录、预检完成后执行） | 能证明什么及限制 |
| --- | --- | --- |
| 格式/静态 | 对真实改动文件执行已有 Prettier 的 `--check` 和 ESLint，另检查工作区与暂存 diff | 不直接运行含测试和自动改写的 lint-staged 来冒充只读检查；文件参数使用实际路径并正确引用 |
| 源码/测试 TS | `pnpm exec tsc --noEmit --project tsconfig.json` | 当前配置含 src、shared 中测试；不主动覆盖 `jenkinsScripts/*.test.ts`，须核对具体测试的实际覆盖 |
| Node 配置 TS | `pnpm run typecheck:node` | 适用于 Vite/Jest 配置、bin/dev.ts 等相关变更；不能替代业务或测试文件类型检查 |
| 测试环境编译 | `pnpm run build:test` | test 环境的 Vite 产物，**不是单元测试**，也不执行完整 tsc |
| 生产环境编译 | `pnpm run build:production` | 按目标环境需要执行；先核对 Sentry 外部写入条件，不能假定只是本地编译 |

- SW 或完整交付链路涉及的改动还需覆盖 `build:sw` 及相应构建编排，不能用单个 Vite 构建替代所有产物检查。
- `vite.config.mts` 与 `jenkinsScripts/buildCompileSemantics.js` 的 `getSentryPluginSemantics()` 控制上传：生产环境、master release 且配置齐全时可能上传 sourcemap/release 信息。先确认当前条件与授权；不得输出密钥，不凭空使用未实现的“禁用上传”参数。
- 新增/修改 `@duitang/dt-base` 使用方式，按 `AGENTS.md` 使用 **vite.config.mts 中真实生产 Babel 配置**验证深层 import 和无未绑定原始标识符；不能以 `.babelrc`、tsc、Jest 或 ESLint 替代。
- CI/CD 行为涉及 `jenkinsfile`、`jenkinsScripts/`、`vite.config.mts` 时，同步检查并按批准范围更新 `jenkinsScripts/cicd-guide.html`。
- `test:build` 运行 `bin/verifyBuild.js`，会启动服务/浏览器并生成截图；`test:main` 涉及 Playwright/E2E。两者都不是单纯编译，仅在相应授权下运行。
- 页面验收按项目规则使用实际 `dev.duitang.com` 业务路由和移动设备模式，切换设备后刷新。页面真实渲染、请求与保存行为未验证时明确报告，不用 HTTP 200 或打包通过代替。

## 提交、推送和交付

1. 对最终将提交的改动完成适用检查，记录实际命令、退出状态、覆盖范围和未验证项。只有文档/配置变动时也要检查是否会影响构建或 hook。
2. 按授权只暂存本次文件/变更块；检查暂存 diff，防止无关内容混入。核对消息规则和有效 hooks；预知会触发禁止的单测则停止提交。
3. 获准且门禁满足后提交；检查退出状态、实际提交 SHA 与文件清单。hook 格式化或修复改变了内容时，重新审阅最终提交内容并补做受影响验证；失败就停止，不能继续 push 来“试一下”。不自动 amend/rebase 他人的提交。
4. 确认所有待推提交均在授权内；向已确认 remote/目标分支推送。非快进、远端拒绝、认证或校验失败时保留现场、报告原因，不强推、不擅自改远端目标。
5. 推送成功后核对远端分支包含本次提交；存在并发提交时可通过祖先关系确认，不要求远端 HEAD 永远等于本地 SHA。网络或权限导致无法核实则明确说明证据边界。
6. 分别报告源码类型、测试文件类型覆盖、目标环境构建、单测未执行、浏览器验收、commit、push 和 CI 状态。未读取该提交对应 CI 结果时不得声称 CI 通过；CI stage 名叫 Testing 也不能当测试证据。

## 核验快照

以上脚本事实静态核验于 2026-11-11：dtw-guide `feature/impassive/custom_editor_v6` / `734e7802`；hasaki `master` / `46a6734f0`。本次编写 skill 未运行这些仓库的类型检查、构建、单测或推送，快照不代表对应检查通过。路径均为目标仓库内的证据定位，本参考不依赖其他 skill。
