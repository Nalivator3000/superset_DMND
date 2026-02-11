# Руководство по исправлению ошибки "CSV данные пусты" в UA-IP-parcer

## Анализ проблемы

На основе структуры репозитория [UA-IP-parcer](https://github.com/Nalivator3000/UA-IP-parcer), это Node.js приложение с Express сервером.

## Типичные причины ошибки "CSV данные пусты"

### 1. Проблема с SQL запросом

**Симптом:** Запрос выполняется, но возвращает 0 строк.

**Проверьте в `server.js`:**

```javascript
// ❌ НЕПРАВИЛЬНО - может вернуть пустой результат из-за строгих фильтров
const query = `
  SELECT DISTINCT ue.user_agent, ue.ip_address
  FROM user_events ue
  WHERE ue.event_type = ANY($1)
    AND ue.event_date >= $2
    AND ue.event_date <= $3
    AND NOT EXISTS (
      SELECT 1 FROM user_events ue2 
      WHERE ue2.external_user_id = ue.external_user_id 
        AND ue2.event_type = ANY($4)
    )
  AND ue.user_agent IS NOT NULL 
  AND ue.ip_address IS NOT NULL
`;

// ✅ ПРАВИЛЬНО - сначала находим пользователей, потом их UA+IP
const query = `
  WITH filtered_users AS (
    SELECT DISTINCT external_user_id
    FROM user_events
    WHERE event_type = ANY($1)
      AND event_date >= $2::timestamp
      AND event_date <= $3::timestamp
      AND external_user_id IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM user_events ue2 
        WHERE ue2.external_user_id = user_events.external_user_id 
          AND ue2.event_type = ANY($4)
      )
  )
  SELECT DISTINCT
    ue.user_agent,
    COALESCE(ue.ip_address, ue.ip) as ip_address
  FROM user_events ue
  INNER JOIN filtered_users fu ON ue.external_user_id = fu.external_user_id
  WHERE ue.user_agent IS NOT NULL 
    AND ue.user_agent != ''
    AND (ue.ip_address IS NOT NULL AND ue.ip_address != '' 
         OR ue.ip IS NOT NULL AND ue.ip != '')
`;
```

### 2. Проблема с обработкой пустого результата

**Симптом:** Запрос возвращает данные, но CSV пустой.

**Проверьте обработку результатов:**

```javascript
// ❌ НЕПРАВИЛЬНО
app.post('/api/export', async (req, res) => {
  const result = await db.query(query, params);
  if (result.rows.length === 0) {
    return res.json({ error: 'CSV данные пусты' });
  }
  // ... формирование CSV
});

// ✅ ПРАВИЛЬНО - с логированием и детальной диагностикой
app.post('/api/export', async (req, res) => {
  try {
    console.log('Export request:', req.body);
    const result = await db.query(query, params);
    console.log(`Query returned ${result.rows.length} rows`);
    
    if (result.rows.length === 0) {
      // Проверяем, почему нет данных
      const checkQuery = `
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN user_agent IS NOT NULL THEN 1 END) as with_ua,
               COUNT(CASE WHEN ip_address IS NOT NULL THEN 1 END) as with_ip
        FROM user_events
        WHERE event_date >= $1::timestamp AND event_date <= $2::timestamp
      `;
      const checkResult = await db.query(checkQuery, [startDate, endDate]);
      console.log('Data check:', checkResult.rows[0]);
      
      return res.status(400).json({ 
        error: 'CSV данные пусты. Проверьте логи сервера в Railway Dashboard.',
        debug: {
          total: checkResult.rows[0].total,
          with_ua: checkResult.rows[0].with_ua,
          with_ip: checkResult.rows[0].with_ip
        }
      });
    }
    
    // Формируем CSV
    const csv = convertToCSV(result.rows);
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', `attachment; filename="export_${Date.now()}.csv"`);
    res.send(csv);
  } catch (error) {
    console.error('Export error:', error);
    res.status(500).json({ error: error.message });
  }
});
```

### 3. Проблема с именами колонок

**Симптом:** Колонка может называться `ip` вместо `ip_address`.

**Исправление:**

```javascript
// Проверяем наличие колонок
const columnCheck = await db.query(`
  SELECT column_name 
  FROM information_schema.columns 
  WHERE table_name = 'user_events' 
    AND table_schema = 'public'
    AND column_name IN ('user_agent', 'ip_address', 'ip')
`);

const columns = columnCheck.rows.map(r => r.column_name);
const hasUserAgent = columns.includes('user_agent');
const ipColumn = columns.includes('ip_address') ? 'ip_address' : 
                 columns.includes('ip') ? 'ip' : null;

if (!hasUserAgent || !ipColumn) {
  return res.status(400).json({ 
    error: `Отсутствуют необходимые колонки. user_agent: ${hasUserAgent}, ip: ${ipColumn}` 
  });
}

// Используем правильное имя колонки в запросе
const query = `
  SELECT DISTINCT
    user_agent,
    ${ipColumn} as ip_address
  FROM user_events
  ...
`;
```

### 4. Проблема с параметрами запроса

**Симптом:** Массивы не передаются правильно в PostgreSQL.

**Исправление:**

```javascript
// ❌ НЕПРАВИЛЬНО
const eventTypes = ['deposit', 'ftd'];
await db.query('SELECT * FROM user_events WHERE event_type = ANY($1)', [eventTypes]);

// ✅ ПРАВИЛЬНО - для pg библиотеки
const eventTypes = ['deposit', 'ftd'];
await db.query('SELECT * FROM user_events WHERE event_type = ANY($1::text[])', [eventTypes]);

// Или используйте IN для простоты
const placeholders = eventTypes.map((_, i) => `$${i + 1}`).join(',');
await db.query(`SELECT * FROM user_events WHERE event_type IN (${placeholders})`, eventTypes);
```

### 5. Проблема с фильтрами исключения

**Симптом:** Фильтры слишком строгие, исключают всех пользователей.

**Исправление - добавьте логирование:**

```javascript
// Логируем количество пользователей на каждом этапе
const step1 = await db.query(`
  SELECT COUNT(DISTINCT external_user_id) as count
  FROM user_events
  WHERE event_type = ANY($1)
    AND event_date >= $2::timestamp
    AND event_date <= $3::timestamp
`, [eventTypes, startDate, endDate]);
console.log(`Step 1 - Users with events: ${step1.rows[0].count}`);

const step2 = await db.query(`
  SELECT COUNT(DISTINCT external_user_id) as count
  FROM user_events
  WHERE event_type = ANY($1)
    AND event_date >= $2::timestamp
    AND event_date <= $3::timestamp
    AND NOT EXISTS (
      SELECT 1 FROM user_events ue2 
      WHERE ue2.external_user_id = user_events.external_user_id 
        AND ue2.event_type = ANY($4)
    )
`, [eventTypes, startDate, endDate, excludeEvents]);
console.log(`Step 2 - After exclusions: ${step2.rows[0].count}`);
```

## Рекомендуемые исправления в server.js

### 1. Добавьте проверку колонок при старте

```javascript
async function checkDatabaseSchema() {
  const result = await db.query(`
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'user_events' 
      AND table_schema = 'public'
      AND column_name IN ('user_agent', 'ip_address', 'ip')
  `);
  
  const columns = result.rows.map(r => r.column_name);
  const ipCol = columns.includes('ip_address') ? 'ip_address' : 
                columns.includes('ip') ? 'ip' : null;
  
  if (!columns.includes('user_agent') || !ipCol) {
    console.error('Missing required columns:', {
      hasUserAgent: columns.includes('user_agent'),
      ipColumn: ipCol
    });
    throw new Error('Missing required columns in user_events table');
  }
  
  return { hasUserAgent: true, ipColumn: ipCol };
}
```

### 2. Улучшите обработку экспорта

```javascript
app.post('/api/export', async (req, res) => {
  const { startDate, endDate, eventTypes, excludeEvents, minDeposit, maxDeposit } = req.body;
  
  try {
    // Проверяем схему БД
    const schema = await checkDatabaseSchema();
    
    // Валидация
    if (!startDate || !endDate) {
      return res.status(400).json({ error: 'Укажите период' });
    }
    if (!eventTypes || eventTypes.length === 0) {
      return res.status(400).json({ error: 'Выберите типы событий' });
    }
    
    // Формируем запрос
    const query = buildExportQuery(schema.ipColumn, {
      startDate,
      endDate,
      eventTypes,
      excludeEvents: excludeEvents || [],
      minDeposit: minDeposit || 0,
      maxDeposit: maxDeposit || 1000000
    });
    
    console.log('Executing export query with params:', {
      eventTypes,
      excludeEvents,
      dateRange: `${startDate} - ${endDate}`
    });
    
    const result = await db.query(query.text, query.values);
    
    console.log(`Query returned ${result.rows.length} rows`);
    
    if (result.rows.length === 0) {
      // Диагностика
      const diagnostic = await runDiagnostics({
        startDate,
        endDate,
        eventTypes,
        excludeEvents,
        ipColumn: schema.ipColumn
      });
      
      return res.status(400).json({
        error: 'CSV данные пусты. Проверьте логи сервера в Railway Dashboard.',
        diagnostic
      });
    }
    
    // Формируем CSV
    const csv = convertToCSV(result.rows);
    
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', `attachment; filename="ua_ip_export_${Date.now()}.csv"`);
    res.send('\ufeff' + csv); // BOM для Excel
    
  } catch (error) {
    console.error('Export error:', error);
    res.status(500).json({ 
      error: 'Ошибка при экспорте',
      message: error.message 
    });
  }
});
```

### 3. Добавьте функцию диагностики

```javascript
async function runDiagnostics(params) {
  const { startDate, endDate, eventTypes, excludeEvents, ipColumn } = params;
  
  const checks = {};
  
  // Проверка 1: Всего записей в периоде
  const total = await db.query(`
    SELECT COUNT(*) as count
    FROM user_events
    WHERE event_date >= $1::timestamp AND event_date <= $2::timestamp
  `, [startDate, endDate]);
  checks.totalInPeriod = total.rows[0].count;
  
  // Проверка 2: Записи с выбранными типами событий
  const withEventTypes = await db.query(`
    SELECT COUNT(*) as count
    FROM user_events
    WHERE event_date >= $1::timestamp 
      AND event_date <= $2::timestamp
      AND event_type = ANY($3::text[])
  `, [startDate, endDate, eventTypes]);
  checks.withEventTypes = withEventTypes.rows[0].count;
  
  // Проверка 3: Записи с UA и IP
  const withUAIP = await db.query(`
    SELECT COUNT(*) as count
    FROM user_events
    WHERE event_date >= $1::timestamp 
      AND event_date <= $2::timestamp
      AND user_agent IS NOT NULL 
      AND user_agent != ''
      AND ${ipColumn} IS NOT NULL 
      AND ${ipColumn} != ''
  `, [startDate, endDate]);
  checks.withUAIP = withUAIP.rows[0].count;
  
  // Проверка 4: После исключений
  if (excludeEvents && excludeEvents.length > 0) {
    const afterExclusions = await db.query(`
      SELECT COUNT(DISTINCT external_user_id) as count
      FROM user_events
      WHERE event_date >= $1::timestamp 
        AND event_date <= $2::timestamp
        AND event_type = ANY($3::text[])
        AND external_user_id IS NOT NULL
        AND NOT EXISTS (
          SELECT 1 FROM user_events ue2 
          WHERE ue2.external_user_id = user_events.external_user_id 
            AND ue2.event_type = ANY($4::text[])
        )
    `, [startDate, endDate, eventTypes, excludeEvents]);
    checks.afterExclusions = afterExclusions.rows[0].count;
  }
  
  return checks;
}
```

## Быстрое исправление

Если нужно быстро исправить, добавьте в начало функции экспорта:

```javascript
// Добавьте перед основным запросом
console.log('Export params:', JSON.stringify(req.body, null, 2));

// После выполнения запроса
console.log(`Query result: ${result.rows.length} rows`);
if (result.rows.length === 0) {
  // Выполните простой запрос для диагностики
  const simpleCheck = await db.query(`
    SELECT COUNT(*) as total,
           COUNT(CASE WHEN user_agent IS NOT NULL THEN 1 END) as with_ua,
           COUNT(CASE WHEN ip_address IS NOT NULL THEN 1 END) as with_ip
    FROM user_events
    WHERE event_date >= $1::timestamp AND event_date <= $2::timestamp
  `, [startDate, endDate]);
  console.log('Simple check:', simpleCheck.rows[0]);
}
```

## Проверка в Railway

1. Откройте Railway Dashboard
2. Перейдите в ваш сервис `ua-ip-parcer-production`
3. Откройте вкладку "Logs"
4. Попробуйте выполнить экспорт
5. Ищите в логах:
   - `Export params:` - параметры запроса
   - `Query result:` - количество строк
   - Ошибки SQL

## Следующие шаги

1. Скопируйте содержимое `server.js` из репозитория
2. Примените исправления из этого руководства
3. Проверьте логи в Railway после деплоя
4. Если проблема сохраняется, запустите диагностический скрипт:
   ```bash
   python 07_scripts/diagnose_ua_ip_export.py
   ```

