# Отчет о диагностике дашборда 7

**Дата:** 2026-02-04  
**Дашборд:** A/B/N tests (ID: 7)  
**URL:** https://superset-railway-production-38aa.up.railway.app/superset/dashboard/7/

## 🔍 Результаты диагностики

### Найденные чарты

На дашборде 7 найдено **2 чарта**:

1. **Kadam Crore A/B/N** (ID: 24)
   - Тип: Table
   - Dataset: `kadam_crore_abn` (ID: 26)
   - Query Mode: raw
   - SQL: 247 строк, 10,426 символов
   - URL: https://superset-railway-production-38aa.up.railway.app/superset/explore/?slice_id=24

2. **Ubidex Crore A/B/N** (ID: 25)
   - Тип: Table
   - Dataset: `ubidex_crore_abn` (ID: 27)
   - Query Mode: raw
   - SQL: 268 строк, 11,712 символов
   - URL: https://superset-railway-production-38aa.up.railway.app/superset/explore/?slice_id=25

---

## ⚠️ КРИТИЧЕСКИЕ ПРОБЛЕМЫ

### 1. Асинхронные запросы ВЫКЛЮЧЕНЫ

**Текущее состояние:**
- `allow_run_async`: `False` ❌
- `query_timeout`: `0` секунд ❌

**Проблема:**
- Чарты таймаутятся через 60 секунд (стандартный таймаут веб-сервера)
- Большие SQL запросы не успевают выполниться
- Dashboard не может загрузить данные

**Решение:**
1. Откройте: https://superset-railway-production-38aa.up.railway.app
2. **Data** → **Databases** → кликните на **"Ubidex Events DB"**
3. Прокрутите вниз до раздела **"Advanced"** или **"Query Execution Options"**
4. ✅ **Включите "Asynchronous query execution"**
5. Установите **"Query timeout"** = `600`
6. **Save**
7. **Перезапустите Superset на Railway**

---

## 📊 Анализ SQL запросов

### Общие характеристики

Оба чарта используют:
- **CTE (WITH)** - сложные запросы с подзапросами (3 блока)
- **Большой размер** - более 10,000 символов каждый
- **Query Mode: raw** - выполняют полный SQL запрос

### Потенциальные проблемы

1. **Долгое выполнение**
   - Запросы могут выполняться несколько минут
   - Без асинхронных запросов таймаут через 60 секунд

2. **Фильтры в чартах**
   - Обнаружены фильтры, но их детали не удалось получить
   - Возможно, фильтры блокируют данные

3. **Отсутствие фильтров по дате в SQL**
   - SQL запросы не содержат явных фильтров по дате
   - Могут обрабатывать все данные из таблицы

---

## 🔧 Рекомендации по исправлению

### Приоритет 1: Включить асинхронные запросы (КРИТИЧНО!)

Это **обязательно** для работы чартов с большими SQL запросами.

**Шаги:**
1. Superset → Data → Databases → "Ubidex Events DB"
2. Advanced → Query Execution Options
3. ✅ Asynchronous query execution
4. Query timeout: 600
5. Save
6. **Перезапустить Superset на Railway**

### Приоритет 2: Проверить фильтры в чартах

1. Откройте каждый чарт отдельно:
   - [Kadam Crore A/B/N](https://superset-railway-production-38aa.up.railway.app/superset/explore/?slice_id=24)
   - [Ubidex Crore A/B/N](https://superset-railway-production-38aa.up.railway.app/superset/explore/?slice_id=25)

2. Проверьте секцию **Filters**
3. Убедитесь, что фильтры не блокируют данные
4. При необходимости измените или уберите фильтры

### Приоритет 3: Оптимизация SQL запросов (опционально)

Если запросы все еще выполняются долго:

1. **Добавить фильтры по дате в SQL:**
   - Ограничить период данных
   - Например: `WHERE event_date >= '2026-01-01'`

2. **Использовать материализованные представления:**
   - Создать предварительно вычисленные результаты
   - Обновлять по расписанию

3. **Разбить на несколько чартов:**
   - Разделить сложный запрос на части
   - Использовать несколько меньших чартов

---

## 📋 Чек-лист исправления

- [ ] Включить асинхронные запросы в настройках базы данных
- [ ] Установить query timeout = 600
- [ ] Перезапустить Superset на Railway
- [ ] Проверить чарт "Kadam Crore A/B/N" отдельно
- [ ] Проверить чарт "Ubidex Crore A/B/N" отдельно
- [ ] Проверить фильтры в каждом чарте
- [ ] Убедиться, что данные есть в базе за нужный период
- [ ] Если проблема сохраняется - оптимизировать SQL запросы

---

## 🔗 Полезные ссылки

- **Дашборд 7:** https://superset-railway-production-38aa.up.railway.app/superset/dashboard/7/
- **Kadam Crore A/B/N:** https://superset-railway-production-38aa.up.railway.app/superset/explore/?slice_id=24
- **Ubidex Crore A/B/N:** https://superset-railway-production-38aa.up.railway.app/superset/explore/?slice_id=25

---

## 📝 Примечания

- API запросы для обновления настроек таймаутятся - возможно, Superset перегружен
- Рекомендуется обновить настройки вручную через UI
- После включения асинхронных запросов чарты должны заработать
- Если проблема сохраняется, проверьте логи Superset на Railway

