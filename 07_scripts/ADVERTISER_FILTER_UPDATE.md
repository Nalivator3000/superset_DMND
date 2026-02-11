# Обновление: Добавлен фильтр по Advertiser

## Что добавлено

В приложение UA-IP-parcer добавлен фильтр по advertiser с двумя опциями:
- **4ra** (advertiser ID: '1')
- **Crore** (advertiser ID: '2')

## Изменения в файлах

### 1. SQL запрос (`ua_ip_export_query.sql`)

Добавлен параметр `:advertisers` и фильтр в CTE `filtered_users`:

```sql
-- Фильтр по advertiser (если указан)
AND (
    :advertisers = ARRAY[]::TEXT[]  -- Нет фильтра по advertiser
    OR ue.advertiser = ANY(:advertisers)
)
```

### 2. Node.js сервер (`server.js.fixed.example`)

- Добавлен параметр `advertisers` в `req.body`
- Добавлен фильтр в SQL запрос
- Обновлена функция диагностики для учета advertiser

**Ключевые изменения:**

```javascript
const { 
  advertisers = [],  // Массив advertiser ID: ['1'] для 4ra, ['2'] для Crore
  // ... другие параметры
} = req.body;

// В SQL запросе:
if (advertisers.length > 0) {
  query += `\n          AND ue.advertiser = ANY($${paramIndex}::text[])`;
  params.push(advertisers);
  paramIndex++;
}
```

### 3. HTML форма (`public_index_html_example.html`)

Добавлена секция с чекбоксами:

```html
<div class="section">
    <h3>Advertiser</h3>
    <p>Выберите advertiser для фильтрации:</p>
    <div class="checkbox-group">
        <input type="checkbox" name="advertisers" value="1" id="advertiser_4ra">
        <label for="advertiser_4ra">4ra (ID: 1)</label>
    </div>
    <div class="checkbox-group">
        <input type="checkbox" name="advertisers" value="2" id="advertiser_crore">
        <label for="advertiser_crore">Crore (ID: 2)</label>
    </div>
</div>
```

### 4. Flask пример (`ua_ip_export_app_example.py`)

Добавлена обработка параметра `advertisers`:

```python
advertisers = request.form.getlist('advertisers')  # ['1'] для 4ra, ['2'] для Crore

# В SQL запросе:
if advertisers:
    user_query += """
      AND ue.advertiser = ANY(:advertisers)
    """
```

## Как применить изменения

### Для Node.js приложения (UA-IP-parcer):

1. **Обновите `server.js`:**
   - Добавьте параметр `advertisers` в деструктуризацию `req.body`
   - Добавьте фильтр по advertiser в SQL запрос (см. `server.js.fixed.example`)
   - Обновите формирование параметров запроса

2. **Обновите `public/index.html`:**
   - Скопируйте секцию "Advertiser" из `public_index_html_example.html`
   - Добавьте обработку чекбоксов в JavaScript

3. **Проверьте API endpoint:**
   - Убедитесь, что `POST /api/export` принимает массив `advertisers`
   - Если ни один advertiser не выбран, фильтр не применяется (включаются все)

### Пример запроса к API:

```json
{
  "startDate": "2025-01-01",
  "endDate": "2025-12-31",
  "eventTypes": ["regfinished"],
  "advertisers": ["1", "2"],  // Оба advertiser
  "excludeEvents": ["deposit", "ftd"],
  "minDeposit": 0,
  "maxDeposit": 1000000
}
```

## Логика фильтрации

- **Если выбраны advertiser:** фильтруются только события с указанными advertiser ID
- **Если не выбран ни один:** фильтр не применяется, включаются все advertiser
- **Можно выбрать оба:** `["1", "2"]` - будут включены оба advertiser

## Проверка в БД

Колонка `advertiser` в таблице `user_events`:
- Тип: `TEXT` или `VARCHAR`
- Значения: `'1'` для 4ra, `'2'` для Crore
- Может быть `NULL` для старых записей

Проверить можно запросом:

```sql
SELECT DISTINCT advertiser, COUNT(*) 
FROM public.user_events 
WHERE advertiser IS NOT NULL 
GROUP BY advertiser;
```

## Тестирование

1. Выберите только 4ra (ID: 1) - должны быть только записи с `advertiser = '1'`
2. Выберите только Crore (ID: 2) - должны быть только записи с `advertiser = '2'`
3. Выберите оба - должны быть записи с обоими advertiser
4. Не выбирайте ни одного - должны быть все записи независимо от advertiser

