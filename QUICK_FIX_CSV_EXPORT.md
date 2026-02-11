# 🚀 Быстрое исправление CSV экспорта

## Проблема

Ошибка: `ReferenceError: userIds is not defined` на строке 250

## Быстрое решение

Найдите в `server.js` строку ~250, где используется `userIds`, и замените:

### ❌ БЫЛО (неправильно):
```javascript
const userResult = await client.query(userQuery, userParams);
const userIds = userResult.rows.map(row => row.external_user_id);
// ... дальше используется userIds без проверки
```

### ✅ СТАЛО (правильно):
```javascript
const userResult = await client.query(userQuery, userParams);

// Всегда инициализируем userIds
let userIds = [];
if (userResult.rows && userResult.rows.length > 0) {
  userIds = userResult.rows.map(row => row.external_user_id).filter(id => id != null);
}

console.log(`User query returned ${userResult.rows.length} rows`);
console.log(`Extracted ${userIds.length} unique user IDs`);

// Проверяем ПЕРЕД использованием
if (userIds.length === 0) {
  console.log('===== EXPORT ERROR: No users found =====');
  return res.status(400).json({
    error: 'No users found matching the selected criteria',
    suggestion: 'Try adjusting date range, event types, or filters'
  });
}

console.log(`Sample user IDs: ${userIds.slice(0, 5).join(', ')}`);

// Только теперь используем userIds дальше
```

## Проблема с фильтром паблишеров

Если фильтр по publisher_id не работает, проверьте функцию `buildWhereConditions`:

```javascript
// Убедитесь, что фильтр по publisher_id правильно обрабатывается
if (req.body.publisherIds && Array.isArray(req.body.publisherIds) && req.body.publisherIds.length > 0) {
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
```

## Полное руководство

См. [`CSV_EXPORT_FIX.md`](CSV_EXPORT_FIX.md) для детальных инструкций.

