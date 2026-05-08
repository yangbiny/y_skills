# 生成检查清单

## 生成前必须完成的检查

1. 识别本次任务类型：
   - 协议适配
   - 查询逻辑
   - 写入逻辑
   - 领域建模
   - 仓储实现
   - DTO/Proto/Domain 转换
   - 测试补齐
2. 找到至少一个同类样板：
   - 同类 Facade
   - 同类 Application/Handler/App
   - 同类 RepoImpl 或 Converter
   - 同类测试
3. 判断当前业务目录风格：
   - `facade / application / domain / infra`
   - `components/<biz>/application|domain|infra`
4. 判断当前是读还是写：
   - 读：优先 `query`、`QueryDispatcher`、查询应用服务
   - 写：优先 `command`、`CommandDispatcher`、写应用服务，并检查 `withPrimary`
5. 判断主要协议对象来源：
   - Dubbo DTO
   - Proto DTO
   - Internal Command / Query
   - Domain 对象
6. 检查是否已有可复用对象：
   - `Converter`
   - `Dispatcher`
   - `Handler`
   - `App`
   - `Repo`
7. 检查是否涉及对外契约：
   - 如果是 Dubbo Facade、DTO、契约对象，优先到 `/Users/knowreason/object/dt-metadata` 查找现成定义

## 修改前说明模板

如果仓库要求“修改前先说明并获批准”，至少说明下面几点：

1. 要改什么。
2. 为什么改。
3. 计划修改哪些文件。
4. 为什么这些文件应放在这一层、这个目录。
5. 是否涉及写操作，是否需要 `withPrimary`。
6. 是否会补测试，补到哪里。

## 生成后说明模板

生成结束后，默认按下面结构说明：

1. 改了什么。
2. 为什么放在这一层、这个目录。
3. 关键对象如何流转。
4. 是否使用 `withPrimary`，原因是什么。
5. 复用了哪些现有类、方法、转换器。
6. 补了哪些测试；如果没补，缺口在哪里。

## 分析源码时的硬要求

如果用户要求解释代码、分析方案或审查生成结果，必须给出：

- 关键类名
- 关键方法名
- 文件路径

不要只讲概念，不给定位信息。
