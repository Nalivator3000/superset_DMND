# Исправление таймаута 60 секунд для UA-IP-parcer

## Проблема

При экспорте CSV возникает ошибка:
```
Error: User query timeout after 60 seconds
```

Запрос выполняется дольше 60 секунд и прерывается.

## Решение

### 1. Увеличить таймаут в Pool конфигурации

В `server.js` обновите конфигурацию Pool:

```javascript
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
  // Увеличиваем таймауты для длительных запросов
  statement_timeout: 600000,  // 10 минут (в миллисекундах)
  query_timeout: 600000,      // 10 минут
  connectionTimeoutMillis: 30000,  // 30 секунд на подключение
  idle_in_transaction_session_timeout: 600000,  // 10 минут для транзакций
  max: 20,  // Максимум соединений в пуле
  min: 2,   // Минимум соединений
});
```

### 2. Установить таймаут для HTTP запроса

В функции экспорта добавьте:

```javascript
app.post('/api/export', async (req, res) => {
  // Устанавливаем таймаут для HTTP запроса (10 минут)
  req.setTimeout(600000);
  res.setTimeout(600000);
  
  // ... остальной код
});
```

### 3. Установить таймаут для конкретного запроса

Перед выполнением SQL запроса:

```javascript
const client = await pool.connect();
try {
  // Устанавливаем таймаут для этого конкретного запроса
  await client.query('SET statement_timeout = 600000'); // 10 минут
  await client.query('SET query_timeout = 600000');
  
  const result = await client.query(query, params);
  // ...
} finally {
  client.release();
}
```

### 4. Оптимизировать SQL запрос

Добавьте `LIMIT 1` в подзапросы EXISTS для ускорения:

```sql
AND NOT EXISTS (
  SELECT 1 
  FROM public.user_events ue2 
  WHERE ue2.external_user_id = ue.external_user_id 
    AND ue2.event_type = ANY($4::text[])
  LIMIT 1  -- Останавливаем после первого совпадения
)
```

### 5. Добавить индексы в БД (если еще нет)

Выполните в PostgreSQL:

```sql
-- Индексы для ускорения запросов
CREATE INDEX IF NOT EXISTS idx_user_events_external_user_id 
  ON public.user_events(external_user_id);

CREATE INDEX IF NOT EXISTS idx_user_events_event_date 
  ON public.user_events(event_date);

CREATE INDEX IF NOT EXISTS idx_user_events_event_type 
  ON public.user_events(event_type);

CREATE INDEX IF NOT EXISTS idx_user_events_advertiser 
  ON public.user_events(advertiser);

CREATE INDEX IF NOT EXISTS idx_user_events_user_agent_ip 
  ON public.user_events(user_agent, ip_address) 
  WHERE user_agent IS NOT NULL AND ip_address IS NOT NULL;

-- Композитный индекс для основных фильтров
CREATE INDEX IF NOT EXISTS idx_user_events_filter 
  ON public.user_events(event_date, event_type, advertiser, external_user_id);
```

## Полное исправление

См. файл `server.js.timeout_fix.js` для полного примера с всеми исправлениями.

### Ключевые изменения:

1. ✅ Увеличен таймаут Pool до 10 минут
2. ✅ Установлен таймаут HTTP запроса
3. ✅ Установлен таймаут для конкретного SQL запроса
4. ✅ Добавлены оптимизации в SQL (LIMIT 1 в подзапросах)
5. ✅ Добавлено логирование времени выполнения
6. ✅ Улучшена обработка ошибок таймаута

## Применение исправлений

1. **Скопируйте изменения из `server.js.timeout_fix.js`** в ваш `server.js`

2. **Или примените изменения вручную:**
   - Обновите конфигурацию Pool
   - Добавьте `req.setTimeout(600000)` и `res.setTimeout(600000)`
   - Используйте `client.query()` с установкой таймаута

3. **Создайте индексы в БД** (см. SQL выше)

4. **Перезапустите приложение на Railway**

## Проверка

После применения исправлений:

1. Попробуйте экспорт с теми же параметрами
2. Запрос должен выполняться до 10 минут без ошибки
3. В логах должно быть: `Query timeout: 10 minutes (600 seconds)`
4. После выполнения должно быть: `Query returned X rows in Y seconds`

## Дополнительные оптимизации

Если запрос все еще медленный:

1. **Уменьшите диапазон дат** - используйте меньший период
2. **Добавьте больше фильтров** - advertiser, event types
3. **Используйте пагинацию** - разбивайте экспорт на части
4. **Кешируйте результаты** - для часто используемых фильтров

## Мониторинг

Добавьте логирование времени выполнения:

```javascript
const startTime = Date.now();
// ... выполнение запроса ...
const executionTime = ((Date.now() - startTime) / 1000).toFixed(2);
console.log(`Query returned ${result.rows.length} rows in ${executionTime} seconds`);
```

Это поможет понять, сколько времени занимает запрос и нужно ли дальнейшие оптимизации.

