---
name: smoke-case-skill
description: 根据接口文档、Swagger/OpenAPI、curl、接口列表或自然语言业务流程，生成自动化冒烟测试工具可直接使用的环境 JSON、用例 JSON 和执行请求 JSON。适用于需要创建接口冒烟用例、自动化测试案例、主流程回归用例、步骤链路断言和变量提取配置的场景。
---

# Smoke Case Skill

## 目标

生成当前自动化冒烟测试工具可直接导入的测试配置：

- `envJson`：提交到 `POST /api/envs`。
- `caseJson`：提交到 `POST /api/cases`。
- `runJson`：提交到 `POST /api/runs`，使用占位 `envId`、`caseId`。

本 skill 只生成 JSON 和说明，不直接调用接口、不写数据库、不执行真实测试。

## 工作流

1. 判断输入类型：接口文档、Swagger/OpenAPI、curl、接口列表、自然语言流程或混合输入。
2. 提取公共信息：`baseUrl`、公共 headers、鉴权方式、环境变量、敏感字段。
3. 按业务过程生成步骤：优先使用“登录/鉴权 -> 创建/发起操作 -> 查询状态 -> 校验结果”的 happy path。
4. 为每个步骤生成请求：`name`、`method`、`path`、`headers`、`body`、`timeoutMs`。
5. 为响应生成断言：优先断言 `$.code == 0`、关键状态字段、关键 ID 存在、额度/数量变化。
6. 为后续步骤生成 `extract`：提取 `token`、`orderId`、`taskId`、`userId`、`id` 等稳定字段。
7. 使用 `{{变量名}}` 引用环境变量或上一步提取值。
8. 输出前自检：`caseJson` 必须使用 `assertions` 字段，不能使用 `assert` 字段。

## 必读参考

生成前读取 `references/smoke_case_schema.md`，确认字段结构、断言操作符和完整示例。

如需要校验生成结果，可把 `caseJson` 保存为临时文件后运行：

```bash
python3 scripts/validate_smoke_case.py /path/to/case.json
```

## 输出格式

默认用中文输出，结构如下：

````markdown
## 环境配置 JSON

```json
{ ... }
```

## 用例配置 JSON

```json
{ ... }
```

## 执行请求 JSON

```json
{ ... }
```

## 待补充信息

- ...
```
````

如果输入信息完整，`待补充信息` 可以写“无”。如果信息不完整，仍输出可编辑草案，并明确缺失项。

## 生成规则

- 顶层用例字段固定为：`name`、`priority`、`continueOnFail`、`steps`。
- 步骤字段固定为：`name`、`method`、`path`、`headers`、`body`、`extract`、`assertions`、`timeoutMs`。
- `assertions` 数组元素字段固定为：`path`、`op`、`value`；`exists` 可省略 `value`。
- 支持断言操作符：`eq`、`ne`、`gt`、`lt`、`exists`、`contains`。
- 默认 `priority` 为 `P0`，默认 `continueOnFail` 为 `false`，默认 `timeoutMs` 为 `5000`。
- 不编造真实账号、密码、Token、Cookie、密钥；使用环境变量占位。
- 敏感字段使用变量：`{{adminPassword}}`、`{{token}}`、`{{apiKey}}`、`{{cookie}}`。
- 鉴权 Header 优先生成：`Authorization: Bearer {{token}}`。
- 登录步骤如能从响应中获得 token，必须配置 `extract: { "token": "$.data.token" }`。
- 创建资源步骤如响应中有 ID，必须提取为语义化变量，例如 `orderId`、`taskId`。
- 后续查询、取消、校验步骤必须引用已提取变量，例如 `/api/order/{{orderId}}`。
- 不确定 JSONPath 时使用最可能路径，并在“待补充信息”中标明需要确认。

## 数据筛选规则

当用户表达“筛选、找出、选择、可领取、可兑换、可用、库存大于 0、余额大于 0、次数大于 0、状态为 enabled/active/valid”等含义时，必须优先生成 JSONPath filter，而不是固定取数组第一条 `[0]`。

生成规则：

- 从数组中筛选满足条件的第一条数据时，使用 `数组路径[?(条件)][0]`。
- `extract` 和 `assertions.path` 都可以使用 filter 表达式。
- filter 后默认加 `[0]`，避免提取到整个数组。
- 后续步骤引用 filter 提取出来的变量，不重复硬编码数组下标。
- 如果条件字段不确定，先生成最可能的 filter，并在“待补充信息”中说明需要确认响应字段。

常见示例：

```json
{
  "extract": {
    "colorCardActivityId": "$.data.object_list[?(@.equity.balanceTimes > 0)][0].activity.id",
    "seriesInventoryId": "$.data.object_list[?(@.equity.balanceTimes > 0)][0].activity.seriesInventoryId"
  },
  "assertions": [
    {
      "path": "$.data.object_list[?(@.equity.balanceTimes > 0)][0].equity.balanceTimes",
      "op": "gt",
      "value": 0
    }
  ]
}
```

多条件示例：

```json
{
  "extract": {
    "inventoryId": "$.data.object_list[?(@.status == 'enabled' && @.inventory > 0)][0].id"
  },
  "assertions": [
    {
      "path": "$.data.object_list[?(@.status == 'enabled' && @.inventory > 0)][0].id",
      "op": "exists"
    }
  ]
}
```

## 输入类型处理

### 自然语言流程

- 将每个业务动作转为一个步骤。
- 缺少接口路径时生成占位路径，并列入待补充信息。
- 缺少请求体时保留最小可编辑 body。

### curl

- 解析 method、URL path、headers、body。
- 将完整域名拆分为 `envJson.baseUrl`。
- 将敏感 header/body 值替换为环境变量。

### Swagger / OpenAPI

- 优先使用 `operationId`、`summary`、`description` 命名步骤。
- 优先使用 requestBody 示例生成 body。
- 优先使用 response 示例或 schema 中的稳定字段生成断言。
- 对 `token`、`id`、`orderId`、`taskId`、`data.id` 等字段生成 extract。

### 接口列表

- 按流程含义排序：鉴权接口、创建接口、查询接口、结果校验接口。
- 如果用户未指定流程，生成主流程 happy path，不生成异常流程。

## 质量要求

- 输出 JSON 必须合法，可被 `JSON.parse` 解析。
- 不输出注释到 JSON 代码块内。
- 不使用平台未支持字段，例如 `assert`、`tests`、`preRequest`。
- 不把环境变量写死到用例 body 之外；公共变量放入 `envJson.variables`。
- 用例名称要表达业务目标，例如“购买生图服务-主流程”。
- 步骤名称要表达业务动作，例如“登录”“创建订单”“查询订单状态”。
