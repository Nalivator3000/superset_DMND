-- Создание индексов для оптимизации экспорта UA+IP
-- Выполните этот скрипт в PostgreSQL для ускорения запросов

-- 1. Индекс по external_user_id (основной для JOIN)
CREATE INDEX IF NOT EXISTS idx_user_events_external_user_id 
  ON public.user_events(external_user_id)
  WHERE external_user_id IS NOT NULL;

-- 2. Индекс по event_date (для фильтрации по периоду)
CREATE INDEX IF NOT EXISTS idx_user_events_event_date 
  ON public.user_events(event_date);

-- 3. Индекс по event_type (для фильтрации по типам событий)
CREATE INDEX IF NOT EXISTS idx_user_events_event_type 
  ON public.user_events(event_type);

-- 4. Индекс по advertiser (для фильтрации по advertiser)
CREATE INDEX IF NOT EXISTS idx_user_events_advertiser 
  ON public.user_events(advertiser)
  WHERE advertiser IS NOT NULL;

-- 5. Композитный индекс для основных фильтров (самый важный!)
-- Ускоряет поиск пользователей по критериям
CREATE INDEX IF NOT EXISTS idx_user_events_filter 
  ON public.user_events(event_date, event_type, advertiser, external_user_id)
  WHERE external_user_id IS NOT NULL;

-- 6. Индекс для user_agent и ip_address (для финального SELECT)
CREATE INDEX IF NOT EXISTS idx_user_events_user_agent_ip 
  ON public.user_events(user_agent, ip_address) 
  WHERE user_agent IS NOT NULL 
    AND (ip_address IS NOT NULL OR ip IS NOT NULL);

-- 7. Индекс для фильтра по депозитам
CREATE INDEX IF NOT EXISTS idx_user_events_deposit_amount 
  ON public.user_events(external_user_id, event_type, converted_amount)
  WHERE event_type = 'deposit' 
    AND converted_amount IS NOT NULL;

-- 8. Частичный индекс для событий с UA и IP (оптимизация финального запроса)
CREATE INDEX IF NOT EXISTS idx_user_events_ua_ip_not_null 
  ON public.user_events(external_user_id, user_agent, ip_address)
  WHERE user_agent IS NOT NULL 
    AND user_agent != ''
    AND (ip_address IS NOT NULL AND ip_address != '' OR ip IS NOT NULL AND ip != '');

-- Проверка созданных индексов
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'user_events'
  AND schemaname = 'public'
ORDER BY indexname;

-- Анализ таблицы для обновления статистики (важно для оптимизатора!)
ANALYZE public.user_events;

