# Исправление проблем с CSV экспортом

## Проблемы

1. **Ошибка `userIds is not defined`** на строке 250
   - Происходит, когда запрос возвращает 0 строк
   - Переменная `userIds` не инициализируется, но используется дальше

2. **Проблема с фильтром паблишеров**
   - Фильтр не работает корректно
   - Запрос возвращает 0 строк даже при наличии данных

## Исправления для server.js

### Исправление 1: Инициализация userIds при пустом результате

Найдите место в коде, где выполняется запрос пользователей (примерно строка 240-250):

```javascript
// БЫЛО (неправильно):
const userResult = await client.query(userQuery, userParams);
const userIds = userResult.rows.map(row => row.external_user_id);

// ИСПРАВЛЕНО:
const userResult = await client.query(userQuery, userParams);
const userIds = userResult.rows.length > 0 
  ? userResult.rows.map(row => row.external_user_id)
  : []; // Инициализируем пустым массивом, если результатов нет

console.log(`Extracted ${userIds.length} unique user IDs`);
console.log(`Sample user IDs: ${userIds.slice(0, 5).join(', ')}`);

// Проверяем, есть ли пользователи
if (userIds.length === 0) {
  console.log('⚠️  No users found matching the criteria');
  return res.status(400).json({
    error: 'No users found matching the selected criteria',
    suggestion: 'Try adjusting date range, event types, or filters'
  });
}
```

### Исправление 2: Исправление фильтра по publisher_id

Проблема может быть в функции `buildWhereConditions`. Убедитесь, что фильтр по publisher_id правильно обрабатывается:

```javascript
function buildWhereConditions(req, paramIndex) {
  const conditions = [];
  const values = [];
  let currentIndex = paramIndex;

  // ... существующие условия ...

  // ИСПРАВЛЕНИЕ: Правильная обработка publisher_id
  if (req.body.publisherIds && Array.isArray(req.body.publisherIds) && req.body.publisherIds.length > 0) {
    // Фильтруем только валидные ID (не null, не undefined, не пустые строки)
    const validPublisherIds = req.body.publisherIds.filter(id => 
      id !== null && id !== undefined && id !== '' && !isNaN(Number(id))
    );
    
    if (validPublisherIds.length > 0) {
      conditions.push(`ue.publisher_id = ANY($${currentIndex}::integer[])`);
      values.push(validPublisherIds.map(id => Number(id)));
      currentIndex++;
      console.log(`[buildWhereConditions] Filtering by publisher_id: [ ${validPublisherIds.join(', ')} ]`);
    }
  }

  // ... остальные условия ...

  return { conditions, values, nextIndex: currentIndex };
}
```

### Исправление 3: Полное исправление обработки пустого результата

В функции обработки экспорта (примерно строка 240-280):

```javascript
try {
  // ... выполнение запроса пользователей ...
  
  const userResult = await client.query(userQuery, userParams);
  
  // ИСПРАВЛЕНИЕ: Всегда инициализируем userIds
  let userIds = [];
  if (userResult.rows && userResult.rows.length > 0) {
    userIds = userResult.rows.map(row => row.external_user_id).filter(id => id != null);
  }
  
  console.log(`User query returned ${userResult.rows.length} rows`);
  console.log(`Extracted ${userIds.length} unique user IDs`);
  
  if (userIds.length > 0) {
    console.log(`Sample user IDs: ${userIds.slice(0, 5).join(', ')}`);
  } else {
    console.log('⚠️  No user IDs extracted - query returned 0 rows or all IDs were null');
  }

  // Проверяем наличие пользователей ПЕРЕД дальнейшей обработкой
  if (userIds.length === 0) {
    console.log('===== EXPORT ERROR: No users found =====');
    return res.status(400).json({
      error: 'No users found matching the selected criteria',
      details: {
        dateRange: { start: startDate, end: endDate },
        eventTypes: eventTypes,
        advertisers: advertisers || [],
        publisherIds: req.body.publisherIds || [],
        excludeEvents: excludeEvents || []
      },
      suggestion: 'Try adjusting filters or date range'
    });
  }

  // Только если userIds не пустой, продолжаем обработку
  // ... остальной код экспорта ...
  
} catch (error) {
  console.log('===== EXPORT ERROR =====');
  console.log(`Error type: ${error.constructor.name}`);
  console.log(`Error message: ${error.message}`);
  console.log(`Error stack: ${error.stack}`);
  
  // Правильная обработка ошибок
  return res.status(500).json({
    error: 'Export failed',
    message: error.message,
    type: error.constructor.name
  });
}
```

## Проверка фильтра паблишеров

### Проблема

Из логов видно:
```
[buildWhereConditions] Filtering by advertiser: [ '1' ]
[buildWhereConditions] Mapped advertiser values: [ '4rabet' ]
```

Но запрос возвращает 0 строк. Возможные причины:

1. **Неправильное маппирование advertiser**
   - Значение `'1'` маппится в `'4rabet'`
   - Но в базе данных может быть другое значение

2. **Фильтр по publisher_id не применяется**
   - Если фильтр по publisher_id не работает, запрос может вернуть 0 строк

### Решение

Проверьте маппинг advertiser и убедитесь, что фильтр по publisher_id правильно применяется:

```javascript
// Проверка маппинга advertiser
const advertiserMap = {
  '1': '4rabet',
  '2': 'crore',
  // ... другие маппинги
};

// В buildWhereConditions:
if (advertisers && advertisers.length > 0) {
  // Маппим значения
  const mappedAdvertisers = advertisers.map(adv => {
    if (advertiserMap[adv]) {
      return advertiserMap[adv];
    }
    return adv; // Если нет маппинга, используем как есть
  });
  
  console.log(`[buildWhereConditions] Filtering by advertiser: [ ${advertisers.join(', ')} ]`);
  console.log(`[buildWhereConditions] Mapped advertiser values: [ ${mappedAdvertisers.join(', ')} ]`);
  
  conditions.push(`ue.advertiser = ANY($${currentIndex}::text[])`);
  values.push(mappedAdvertisers);
  currentIndex++;
}
```

## Быстрое исправление

Если нужно быстро исправить ошибку `userIds is not defined`, найдите строку 250 и замените использование `userIds` на:

```javascript
// Найти место, где используется userIds (примерно строка 250)
// И заменить на:

if (!userIds || userIds.length === 0) {
  console.log('===== EXPORT ERROR: No users found =====');
  return res.status(400).json({
    error: 'No users found matching the selected criteria'
  });
}

// Только после проверки использовать userIds
// ... остальной код ...
```

## Тестирование

После исправлений проверьте:

1. **Экспорт с данными:**
   - Выберите период с данными
   - Выберите типы событий
   - Нажмите Export
   - Должен вернуться CSV файл

2. **Экспорт без данных:**
   - Выберите период без данных
   - Нажмите Export
   - Должно вернуться сообщение об ошибке (не краш)

3. **Фильтр по паблишерам:**
   - Выберите паблишера
   - Проверьте, что фильтр применяется
   - Проверьте логи на наличие `Filtering by publisher_id`

