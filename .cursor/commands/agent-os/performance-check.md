# /performance-check — Анализ производительности

Запуск performance-analyzer агента для выявления проблем производительности.

## Агент

- Agent: `.cursor/agents/performance-analyzer.md`

## Синтаксис

```
/performance-check [<target>] [--focus <area>]
```

## Примеры

```
/performance-check
/performance-check UserModule
/performance-check --focus database
/performance-check OrderModule --focus async
```

## Параметры

- `[<target>]` — Модуль для анализа (опционально)
- `[--focus]` — Область фокуса (database, async, caching, api)

## Области анализа

### 1. Database Performance
- N+1 queries
- Missing indexes
- Inefficient queries
- Over-fetching

### 2. Async Performance
- Blocking calls
- Missing concurrency
- Task groups usage

### 3. Caching
- Missing cache
- Cache invalidation
- TTL configuration

### 4. API Response Time
- Pagination
- Response size
- Slow endpoints

## Вывод

```markdown
# Performance Analysis Report

## Critical Issues
1. **N+1 Query in ListOrdersAction**
   - Location: `OrderModule/Actions/ListOrdersAction.py:45`
   - Impact: 1 + N queries per request
   - Fix: Use join or batch fetch

## Optimization Opportunities
1. **Missing cache on GetUserStatsQuery**
   - Benefit: 90% reduction in DB calls
   - Implementation: Add @cache decorator

## Recommendations
1. Add index on `order.user_id`
2. Implement pagination
```
