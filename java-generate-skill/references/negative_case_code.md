# 反面案例代码

下面的哪里代码均为反面案例，请勿生成此类代码：

1. 过于细化：可直接在业务层处理，不需要单独拆分文件
```kotlin
val start = normalizeStart(cmd.start)
val limit = normalizeLimit(cmd.limit)

fun normalizeStart(start: Int?): Int {
  return if (start <= 0) 0 else start
}
```

2. 方法过于拆分：应直接提供一个验证参数的方法即可，如果只有一处使用，则不应创建方法
```kotlin
 validateCreateActivityCmd(cmd)
    validateSeriesInventory(cmd.seriesInventoryId)
    ensureActivitySeriesUnique(cmd.seriesInventoryId, null)
```
3. 领域的变更在事务中完成： 应现在事务外完成所有的领域变更，事务中一般只做数据库操作
4. 事务中应该有try catch：捕获异常，打日志并且回滚事务
```kotlin
    val saved = database.withTransaction { _ ->
      activity.updateConfig(
        seriesInventoryId = targetSeriesInventoryId,
        title = targetTitle,
        coverPhoto = targetCoverPhoto,
        ruleText = targetRuleText,
        activityBeginAt = targetBeginAt,
        activityEndAt = targetEndAt,
        state = targetState,
      )
      colorCardActivityRepo.saveActivity(activity)
    } ?: throw IllegalStateException("xxx")
```