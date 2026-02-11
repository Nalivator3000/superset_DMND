# 🚀 Быстрое исправление чартов на дашборде 7

## ⚡ Самый частый случай (90% проблем)

### Проблема: Чарты таймаутятся или не загружаются

**Решение (2 минуты):**

1. Откройте: https://superset-railway-production-38aa.up.railway.app
2. **Data** → **Databases** → кликните на **"Ubidex Events DB"**
3. Прокрутите вниз → найдите **"Advanced"** или **"Query Execution Options"**
4. ✅ **Включите "Asynchronous query execution"**
5. Установите **"Query timeout"** = `600`
6. **Save**
7. **Перезапустите Superset на Railway:**
   - Railway Dashboard → проект → сервис Superset
   - ⋮ → **Restart**

**Готово!** Чарты должны заработать.

---

## 🔍 Если не помогло

### Проверьте фильтры по дате

1. Откройте дашборд 7 → **Edit Dashboard**
2. Кликните на чарт → **Edit chart**
3. Проверьте **Filters** → найдите `event_date`
4. **Измените даты** на период с данными (например: `2025-12-01` до `2026-01-31`)
5. **Update chart**

---

## 📋 Полная инструкция

См. подробное руководство: [`DASHBOARD_7_CHARTS_FIX.md`](DASHBOARD_7_CHARTS_FIX.md)

---

## 🛠️ Автоматическая диагностика

Запустите скрипт для проверки:

```bash
python3 07_scripts/diagnose_dashboard_7.py
```

