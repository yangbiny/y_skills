# 分层与对象引用规则

## 分层落点

### 经典分层工程

- `facade`
  - 对外入口，负责 Dubbo、gRPC、HTTP、Console 等协议适配。
- `application`
  - 负责编排。
  - `command` 放写操作。
  - `query` 放读操作。
- `domain`
  - 放领域对象、值对象、领域服务、仓储接口、领域适配器接口。
- `infra` 或 `repository`
  - 放外部依赖接入、RepoImpl、数据库映射、配置、运行时支持。

### `components/<biz>` 风格工程

- `components/<biz>/application`
  - 放该业务的应用服务、查询服务、编排逻辑。
- `components/<biz>/domain`
  - 放该业务的领域对象、值对象、领域服务、仓储接口。
- `components/<biz>/infra`
  - 放该业务的 RepoImpl、缓存实现、外部依赖适配器。
- 对外 Facade 仍然放 `facade/...`。

## 文件组织规则

1. 优先就近落位。
   - 已经在 `components/assets/...` 的业务，继续放在该业务目录下。
   - 仍使用 `application/command/...`、`domain/...` 的旧业务，不要强迁到 `components`。
2. 同类文件与同类文件放一起。
   - 新 Facade 跟同类 Facade 同包。
   - 新 QueryHandler 跟同类 QueryHandler 同包。
   - 新 RepoImpl 跟同业务 RepoImpl 同包。
3. 不为了“统一架构”而改动既有目录结构。
4. 不要让同一条业务链路一半落旧分层、一半落新分层，除非现有代码本身就是混合结构。

## 引用边界

### Facade 层允许引用

- `Req`、`Resp`
- Dubbo DTO
- Proto DTO
- `CommandDispatcher`
- `QueryDispatcher`
- App / Handler / Query
- 各类 `Converter`

### Facade 层禁止事项

- 编写核心业务规则
- 直接操作数据库模板
- 返回数据库 DO
- 在 Facade 内闭环完成复杂业务

### Application 层允许引用

- Domain 实体、值对象、仓储接口、领域服务
- Internal Command / Query
- 必要的领域适配器接口
- `database.withPrimary` 或 `databases.withPrimary`

### Application 层禁止引用

- Dubbo DTO
- gRPC `StreamObserver`
- 数据库 DO
- 仅属于协议层的字段语义

### Domain 层规则

- 只放业务概念和业务规则。
- 可以定义仓储接口、领域服务接口、适配器接口。
- 不依赖 Dubbo DTO、Proto DTO、HTTP 对象、数据库 DO。
- 不依赖具体 RepoImpl。
- 不把协议层分页对象或响应包装对象带进领域方法签名。

### Infra / RepoImpl 层规则

- 负责把数据库、缓存、第三方接口数据映射成 Domain。
- 负责 `DO <-> Domain`、`POJO <-> Domain` 转换。
- 不向上泄漏 DO。
- 不承担 Facade 协议转换职责。

## 对象流转规则

### Dubbo 写接口

`Dubbo Req -> Converter 或组装 -> Internal Command / Proto Req -> CommandDispatcher 或 App -> Domain -> Repo -> DB`

返回时：

`Domain / Internal Result / Proto Resp -> Converter -> Dubbo Resp`

### Dubbo 读接口

`Dubbo Req -> Converter 或组装 -> Query / Proto Req -> QueryDispatcher 或 Query App -> Domain / DTO -> Converter -> Dubbo Resp`

### Repo 持久化

`Domain -> DO -> DatabaseTemplate / DAO`

读取时：

`DO / DAO Result -> Domain`

## 边界红线

- Dubbo DTO、Proto DTO 只停留在 Facade 或 Converter。
- DO 只停留在 Infra。
- Application 做编排，不替代 Domain 建模。
