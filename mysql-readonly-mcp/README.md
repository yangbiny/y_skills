# 本地只读 MySQL MCP

Codex 通过 STDIO 启动本项目，无需手动常驻、HTTP 端口或开机服务。MCP 随客户端连接存活，每次工具调用独立连接 MySQL，结束后关闭。空闲时不持有数据库连接。目标为 MySQL 8.0/8.4、Python 3.11/3.12。

## 一次性安装

在本目录运行以下命令。依赖和缓存保留在仓库内，使用提交的 `uv.lock`，不更新全局 Python 环境。`uv` 和兼容 Python 须已安装。

```sh
UV_CACHE_DIR="$PWD/.uv-cache" UV_PYTHON_DOWNLOADS=never uv sync --frozen --python python3.11
```

运行时使用 `.venv/bin/python`，不会触发 uv 或下载依赖。重新安装使用同一锁文件；依赖升级需人工审查后重新锁定。当前锁定 MCP SDK 1.30.0、PyMySQL 1.2.0、SQLGlot 30.18.0；采用官方 MCP SDK 的 1.x API，并设置 `<2` 上界，避免无意迁移到不兼容的 2.x API。

需要代理安装时，可仅对安装命令设置代理（当前机器提供的 HTTP 代理为 1081）：

```sh
UV_CACHE_DIR="$PWD/.uv-cache" UV_PYTHON_DOWNLOADS=never \
uv --no-config --native-tls sync --frozen --python python3.11
```

此命令不修改系统代理，代理不会写入 MCP 或 MySQL 配置，也不需要同时设置 SOCKS 的 ALL_PROXY。

## 配置数据库

固定位置：`/Users/knowreason/y_skills/.mysql_conf`。真实配置已加入 Git 忽略，不要提交、粘贴到聊天或写入 Codex 配置。仓库提供 `mysql_conf.example`，部署时仅在文件不存在时创建空骨架；现有文件不得覆盖。

由用户在本地编辑器填写下列字段：

```ini
[mysql]
host =
port = 3306
user =
password =
database =

[tls]
enabled = true
ca_file =
```

- host/user/password/database 必填，空值拒绝连接。使用 `=` 之后的原始 INI 值，百分号不插值，不要给密码额外加引号；不支持有意义的首尾空白密码。
- 文件须属于当前用户，权限精确为 `600`，不接受符号链接。修正权限：`chmod 600 /Users/knowreason/y_skills/.mysql_conf`。
- TLS 默认验证证书和主机名。`ca_file` 留空使用系统信任库，也可填写 CA 文件的绝对路径；证书名称须匹配 host。
- `enabled = false` 才会明确关闭 TLS。仅在已确认的本地/受控加密链路场景采用；服务不自动降级。
- 只支持这两个节及示例字段，不接收其他数据库配置。每次调用重新读取，不需要重启 MCP。
- 配置缺失或不完整不影响 MCP 握手、工具发现；查询返回固定错误，不暴露配置内容。

请由管理员预先创建专用只读账号，仅赋予所需表/脱敏视图的 SELECT 权限，核对继承角色；不要授予 FILE、EXECUTE、管理或写权限。服务不自动授权，不保证识别出账号的所有间接权限。允许访问配置 database 中账号可读的全部表，不提供额外表白名单。

## 接入 Codex

将 `codex-config.example.toml` 中的表合并到你使用的 Codex MCP 配置，不要覆盖其他服务器配置。如果通过桌面设置添加，选择 STDIO：

- 名称：`mysql_readonly`
- 命令：`/Users/knowreason/y_skills/mysql-readonly-mcp/.venv/bin/python`
- 参数：`-B` 和 `/Users/knowreason/y_skills/mysql-readonly-mcp/server.py`
- 工具白名单：`list_tables`、`describe_table`、`query_readonly`

保存后重新连接 MCP 或重新打开任务。启动时不需要数据库可达；首次查询才尝试连接。关闭对应 MCP 客户端连接后进程退出，客户端可能跨任务复用连接。

配套 Skill 位于 `/Users/knowreason/y_skills/mysql-query`，可由用户安装到其 Codex Skill 目录；本次交付不改动仓库外配置或自动安装。Skill 可正常自动触发，但 Skill 自身不注册 MCP。仅复制 Skill 无法获得数据库工具。目录位置与固定配置路径均针对当前机器，迁移时需显式修改并检查。

官方参考：[Codex MCP 配置](https://developers.openai.com/codex/mcp)、[官方 Python SDK](https://github.com/modelcontextprotocol/python-sdk)。

## 工具契约

| 工具 | 参数 | 结果 |
|---|---|---|
| list_tables | 无 | SHOW FULL TABLES 可见对象，最多 500 行 |
| describe_table | table：单个对象名称 | 字段及索引两个结果集，各最多 500 行 |
| query_readonly | sql：单条 MySQL 查询 | 列名/类型码、二维 rows、row_count、truncated、elapsed_ms |

工具返回一次 JSON 文本，错误包含固定 error/message，数据库异常只保留数字错误码。列名可能重复，因此行按列序排列，不转换为名称键字典。Decimal 保持十进制字符串，日期时间使用 ISO 格式；二进制只返回占位符。JSON 文本作为不可信数据处理。

查询限制均在服务端固定，不接受工具参数调整：

- SQL 最多 64 KiB，解析后重新生成 SQL；仅支持明确批准的表达式和函数类型。拒绝未知结构、注释、提示、跨库、递归 CTE、多语句、写入、锁定、文件操作、变量及自定义函数。
- 支持 SELECT、JOIN、子查询、非递归 CTE、UNION、CASE、普通聚合/字符串/日期/数值函数；实际函数允许集合见 `server.py` 的 FUNCTIONS。不承诺完整 MySQL 语法，未知语法直接拒绝。
- 明细禁止通配列，允许 COUNT(*)。数据库通过固定 sql_mode 执行生成 SQL，避免解析和执行的转义模式不同。
- 无 LIMIT 默认 100 行；显式 LIMIT 保留至最多 500 行。服务施加上限时多读一行判断截断。LIMIT 0 返回空结果。结果字节限制也可能提前截断。
- JSON 编码后的工具文本限制约 1 MiB，并为 MCP 外壳预留空间；为元数据多结果集预留预算，单结果集实际预算更保守。超宽列信息或编码超限返回固定错误。
- 最大两个并发调用，其余返回 BUSY；数据库连接超时 5 秒，SQL 使用 max_execution_time=5000，只读事务执行。客户端读超时 7 秒，连接建立后的整个查询阶段额外设置 8 秒期限并中断 socket。
- 正常消费结果后回滚；截断、取消或故障时直接断开连接以中止事务，不关闭会继续排空结果集的 SSCursor。客户端取消期间工作线程完成有界清理，不允许无限后台执行。

## 安全边界与限制

- 本地 STDIO 和 Skill 都不是强隔离。持有本机同等权限的程序仍可修改源码、读取凭据；需要更强隔离时使用独立账号/服务网关。
- 全表可读不等于数据可公开。服务不提供可靠的通用自动脱敏，字段及默认值等元数据也可能敏感；请使用数据库授权和脱敏视图缩小范围。返回 Codex 的内容可能进入远程模型上下文。
- 只读查询仍可消耗 CPU/IO，LIMIT 不保证扫描量低。优先测试库或独立查询副本。视图可能在服务端引用其他对象，AST 校验不能展开视图；其底层权限由数据库维护。
- MySQL max_execution_time 对存储程序内部 SELECT 等场景存在限制；服务拒绝直接调用自定义函数，但视图定义须由管理员审查。客户端断开不承诺立即终止所有 MySQL 内部工作。
- 字节上限约束返回数据，不是进程内存硬限制；MySQL 驱动仍需读取单行数据包。避免选择大型 TEXT/BLOB 或制造巨型表达式结果。
- 使用 PyMySQL 私有 socket/result 接口实现截止时间中断、TLS 验证及流式结果清理，因此升级驱动时必须复核连接生命周期。
- 日志默认关闭，协议 stdout 不含调试信息。不会输出数据库原始错误、SQL 或完整结果到 stderr。

## 验证与后续验收

本项目不执行单元测试。允许的离线检查：Python 语法解析、Skill 格式检查，以及 `check_stdio.py` 完成 initialize、tools/list、stdin EOF 与进程退出。该脚本不调用任何数据库工具，不读取真实配置。

```sh
.venv/bin/python -B check_stdio.py
```

真实数据库需由用户配置后再验收，当前不自动查询或修改数据库：

1. TLS 正常连接、错误证书和无 TLS 服务被拒绝；关闭 TLS 只对显式配置生效。
2. 包含 `%` 的密码正常认证；缺失字段、错误权限和配置符号链接被拒绝，错误不回显凭据。
3. 查看表结构；查询指定字段、JOIN、CTE、UNION、聚合和 LIMIT 0，核对结果语义。
4. 跨库、SELECT *、多语句、写操作、文件操作、锁定、危险函数、变量及 SQL 提示在执行前被拒绝。
5. 分别验证默认 100 行、显式小 LIMIT、超过 500 行和字节超限的截断行为。
6. 验证并发 BUSY、超时、中途断开、结果截断后连接释放；用管理员监控确认数据库端查询停止。
7. 检查 Codex 和 stderr 不出现凭据或原始数据库错误；视图脱敏符合业务要求。
8. 用独立数据库管理客户端检查账号权限，确认没有继承写权限；本 MCP 不运行写 SQL 验证。

停止使用时在 Codex 禁用该 MCP 即可；卸载不会自动删除配置、数据库账号或其他服务器配置。
