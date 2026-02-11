# Руководство по диагностике и исправлению экспорта UA+IP

## Проблема

При попытке экспорта с `https://ua-ip-parcer-production.up.railway.app/` выдается ошибка:
```
CSV данные пусты. Проверьте логи сервера в Railway Dashboard.
```

## Шаг 1: Диагностика

Запустите диагностический скрипт для проверки данных в базе:

```bash
cd /Users/aleksandrkovmir/superset-railway
python 07_scripts/diagnose_ua_ip_export.py
```

Скрипт проверит:
1. ✅ Наличие колонок `user_agent` и `ip_address`/`ip` в таблице `user_events`
2. ✅ Количество записей с заполненными UA и IP
3. ✅ Распределение по типам событий
4. ✅ Тестовый запрос с фильтрами из UI

### Возможные результаты диагностики:

#### Сценарий 1: Колонки отсутствуют
```
❌ user_agent: НЕ НАЙДЕНА
❌ ip_address/ip: НЕ НАЙДЕНА
```

**Решение:**
```sql
-- Добавить колонки в таблицу user_events
ALTER TABLE public.user_events ADD COLUMN IF NOT EXISTS user_agent TEXT;
ALTER TABLE public.user_events ADD COLUMN IF NOT EXISTS ip_address TEXT;

-- Затем загрузить данные из CSV файлов
-- Используйте скрипт: 07_scripts/load_attribution_from_csv.py
```

#### Сценарий 2: Колонки есть, но данных нет
```
✓ Колонки найдены
⚠️  С user_agent И ip_address: 0 записей
```

**Решение:**
- Загрузите данные `user_agent` и `ip_address` из CSV файлов с raw данными
- Проверьте, что CSV файлы содержат колонки `USER_AGENT` и `IP`

#### Сценарий 3: Данные есть, но запрос возвращает 0 результатов
```
✓ Колонки найдены
✓ С user_agent И ip_address: 1,000,000+ записей
⚠️  Тестовый запрос вернул 0 результатов
```

**Причины:**
1. Фильтры слишком строгие (например, исключение deposit+ftd оставляет очень мало пользователей)
2. Проблема с логикой запроса в приложении
3. Несоответствие формата дат

**Решение:**
- Попробуйте убрать фильтры исключения
- Расширьте диапазон дат
- Проверьте логи приложения в Railway Dashboard

## Шаг 2: Проверка SQL запроса

Используйте файл `07_scripts/ua_ip_export_query.sql` как эталон для правильного запроса.

Проверьте запрос в вашем приложении на соответствие логике из SQL файла.

### Ключевые моменты запроса:

1. **Сначала находим пользователей** по критериям (типы событий, период, депозиты, исключения)
2. **Затем получаем все UA+IP пары** для этих пользователей
3. **Фильтруем только строки** с заполненными `user_agent` и `ip_address`

## Шаг 3: Проверка приложения

Если у вас есть доступ к коду приложения `ua-ip-parcer`, сравните его с примером в `07_scripts/ua_ip_export_app_example.py`.

### Типичные ошибки в коде:

1. **Неправильное имя колонки IP:**
   ```python
   # ❌ Неправильно (если колонка называется ip_address)
   ip_col = 'ip'
   
   # ✅ Правильно (проверять наличие колонки)
   ip_col = 'ip_address' if 'ip_address' in cols else 'ip'
   ```

2. **Неправильная обработка пустых результатов:**
   ```python
   # ❌ Неправильно
   if not rows:
       return "CSV данные пусты"
   
   # ✅ Правильно (создать пустой CSV или показать понятную ошибку)
   if not rows:
       return render_template_string(HTML_TEMPLATE, 
           error="По заданным критериям не найдено данных. Попробуйте изменить фильтры.")
   ```

3. **Проблемы с параметрами запроса:**
   ```python
   # ❌ Неправильно (массивы в SQLAlchemy)
   result = conn.execute(text(query), {'event_types': ['deposit', 'ftd']})
   
   # ✅ Правильно
   result = conn.execute(text(query), {
       'event_types': ['deposit', 'ftd'],
       'exclude_events': exclude_events if exclude_events else []
   })
   ```

## Шаг 4: Проверка логов Railway

1. Откройте Railway Dashboard
2. Перейдите в ваш сервис `ua-ip-parcer-production`
3. Откройте вкладку "Logs"
4. Попробуйте выполнить экспорт снова
5. Ищите ошибки в логах:
   - Ошибки подключения к БД
   - SQL синтаксические ошибки
   - Ошибки выполнения запросов

## Шаг 5: Тестирование запроса напрямую

Выполните тестовый запрос напрямую в базе данных:

```sql
-- Пример запроса для проверки
WITH 
filtered_users AS (
    SELECT DISTINCT ue.external_user_id
    FROM public.user_events ue
    WHERE ue.event_date >= '2025-01-01'::timestamp
      AND ue.event_date <= '2025-12-31'::timestamp
      AND ue.event_type = 'regfinished'
      AND ue.external_user_id IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 
          FROM public.user_events ue2 
          WHERE ue2.external_user_id = ue.external_user_id 
            AND ue2.event_type IN ('deposit', 'ftd')
      )
)
SELECT DISTINCT
    ue.user_agent,
    COALESCE(ue.ip_address, ue.ip) as ip_address
FROM public.user_events ue
INNER JOIN filtered_users fu ON ue.external_user_id = fu.external_user_id
WHERE ue.user_agent IS NOT NULL 
  AND ue.user_agent != ''
  AND (ue.ip_address IS NOT NULL AND ue.ip_address != '' 
       OR ue.ip IS NOT NULL AND ue.ip != '')
LIMIT 100;
```

Если этот запрос возвращает результаты, значит проблема в приложении, а не в данных.

## Быстрое решение

Если нужно быстро исправить проблему:

1. **Упростите фильтры** - уберите исключения deposit и ftd
2. **Расширьте диапазон дат** - используйте больший период
3. **Проверьте наличие данных** - запустите диагностический скрипт

## Контакты для помощи

Если проблема не решается:
1. Запустите `diagnose_ua_ip_export.py` и сохраните вывод
2. Проверьте логи Railway Dashboard
3. Сравните ваш код с `ua_ip_export_app_example.py`

