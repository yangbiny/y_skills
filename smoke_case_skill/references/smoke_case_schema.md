# 自动化冒烟测试用例结构

## 1. 环境配置 JSON

用于 `POST /api/envs`。

```json
{
  "name": "小环境A",
  "baseUrl": "https://test-a.yourcompany.com",
  "headers": {
    "X-Tenant": "tenant-a"
  },
  "variables": {
    "adminUser": "test@a.com",
    "adminPassword": "xxx"
  }
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 环境名称 |
| baseUrl | string | 是 | 目标接口根地址，必须以 http 或 https 开头 |
| headers | object | 否 | 每个请求都会带上的公共 Header |
| variables | object | 否 | 可通过 `{{变量名}}` 引用的环境变量 |

## 2. 用例配置 JSON

用于 `POST /api/cases`。

```json
{
  "name": "购买生图服务-主流程",
  "priority": "P0",
  "continueOnFail": false,
  "steps": []
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 用例名称 |
| priority | string | 是 | 优先级，常用 P0/P1/P2 |
| continueOnFail | boolean | 是 | 步骤失败后是否继续执行 |
| steps | array | 是 | 有序步骤，不能为空 |

## 3. 步骤结构

```json
{
  "name": "创建订单",
  "method": "POST",
  "path": "/api/order/create",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer {{token}}"
  },
  "body": {
    "serviceId": "img-basic"
  },
  "extract": {
    "orderId": "$.data.orderId"
  },
  "assertions": [
    {
      "path": "$.code",
      "op": "eq",
      "value": 0
    },
    {
      "path": "$.data.orderId",
      "op": "exists"
    }
  ],
  "timeoutMs": 5000
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| name | string | 是 | 步骤名称 |
| method | string | 是 | `GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS` |
| path | string | 是 | 接口路径，可包含 `{{变量}}` |
| headers | object | 否 | 步骤级 Header，覆盖或追加公共 Header |
| body | object/array/string | 否 | 请求体，GET 通常省略 |
| extract | object | 否 | 从响应提取变量，key 为变量名，value 为 JSONPath |
| assertions | array | 否 | 断言列表 |
| timeoutMs | number | 否 | 步骤超时时间，默认 5000 |

## 4. 断言结构

```json
{
  "path": "$.data.status",
  "op": "eq",
  "value": "paid"
}
```

支持操作符：

| op | 说明 | 示例 |
| --- | --- | --- |
| eq | 等于 | `$.code == 0` |
| ne | 不等于 | `$.data.status != "failed"` |
| gt | 大于 | `$.data.count > 0` |
| lt | 小于 | `$.data.remain < 10` |
| exists | 字段存在 | `$.data.token` 存在 |
| contains | 包含字符串或数组元素 | `$.message` 包含 `"success"` |

生成断言优先级：

1. 响应状态业务码：`$.code eq 0`。
2. 关键 ID 存在：`$.data.orderId exists`。
3. 关键业务状态：`$.data.status eq "paid"`。
4. 数量、额度、余额：使用 `gt/lt`。
5. 文案字段：使用 `contains`，不要只依赖文案作为唯一断言。

## 5. 变量机制

变量来源：

- 环境变量：`envJson.variables`。
- 上一步 `extract` 出来的值。

引用方式：

```json
{
  "Authorization": "Bearer {{token}}",
  "path": "/api/order/{{orderId}}"
}
```

常用变量名：

| 变量 | 来源 |
| --- | --- |
| adminUser | 环境变量 |
| adminPassword | 环境变量 |
| token | 登录响应 extract |
| orderId | 创建订单响应 extract |
| taskId | 创建任务响应 extract |
| userId | 用户信息响应 extract |

## 6. 完整示例：购买生图服务-主流程

### envJson

```json
{
  "name": "小环境A",
  "baseUrl": "https://test-a.yourcompany.com",
  "headers": {
    "X-Tenant": "tenant-a"
  },
  "variables": {
    "adminUser": "test@a.com",
    "adminPassword": "xxx"
  }
}
```

### caseJson

```json
{
  "name": "购买生图服务-主流程",
  "priority": "P0",
  "continueOnFail": false,
  "steps": [
    {
      "name": "登录",
      "method": "POST",
      "path": "/api/login",
      "headers": {
        "Content-Type": "application/json"
      },
      "body": {
        "email": "{{adminUser}}",
        "password": "{{adminPassword}}"
      },
      "extract": {
        "token": "$.data.token"
      },
      "assertions": [
        {
          "path": "$.code",
          "op": "eq",
          "value": 0
        },
        {
          "path": "$.data.token",
          "op": "exists"
        }
      ],
      "timeoutMs": 5000
    },
    {
      "name": "创建订单",
      "method": "POST",
      "path": "/api/order/create",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer {{token}}"
      },
      "body": {
        "serviceId": "img-basic"
      },
      "extract": {
        "orderId": "$.data.orderId"
      },
      "assertions": [
        {
          "path": "$.code",
          "op": "eq",
          "value": 0
        },
        {
          "path": "$.data.orderId",
          "op": "exists"
        }
      ],
      "timeoutMs": 5000
    },
    {
      "name": "查询订单状态",
      "method": "GET",
      "path": "/api/order/{{orderId}}",
      "headers": {
        "Authorization": "Bearer {{token}}"
      },
      "assertions": [
        {
          "path": "$.code",
          "op": "eq",
          "value": 0
        },
        {
          "path": "$.data.status",
          "op": "eq",
          "value": "paid"
        }
      ],
      "timeoutMs": 5000
    },
    {
      "name": "验证生图权益下发",
      "method": "GET",
      "path": "/api/user/quota",
      "headers": {
        "Authorization": "Bearer {{token}}"
      },
      "assertions": [
        {
          "path": "$.code",
          "op": "eq",
          "value": 0
        },
        {
          "path": "$.data.imgQuota",
          "op": "gt",
          "value": 0
        }
      ],
      "timeoutMs": 5000
    }
  ]
}
```

### runJson

```json
{
  "envId": "env-替换为创建环境返回的ID",
  "caseId": "case-替换为创建用例返回的ID"
}
```
