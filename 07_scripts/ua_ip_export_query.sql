-- SQL запрос для экспорта пар User Agent и IP
-- Используется в приложении ua-ip-parcer

-- Параметры (заменить на реальные значения):
-- :start_date - начало периода (например, '2025-01-01')
-- :end_date - конец периода (например, '2025-12-31')
-- :event_types - массив типов событий (например, ARRAY['regfinished'])
-- :advertisers - массив advertiser ID (например, ARRAY['1', '2'] для 4ra и Crore)
-- :min_deposit - минимальная сумма депозита (например, 0)
-- :max_deposit - максимальная сумма депозита (например, 1000000)
-- :exclude_event_types - массив типов событий для исключения (например, ARRAY['deposit', 'ftd'])

WITH 
-- Шаг 1: Находим пользователей по критериям
filtered_users AS (
    SELECT DISTINCT ue.external_user_id
    FROM public.user_events ue
    WHERE ue.event_date >= :start_date::timestamp
      AND ue.event_date <= :end_date::timestamp
      AND ue.event_type = ANY(:event_types)
      AND ue.external_user_id IS NOT NULL
      -- Фильтр по advertiser (если указан)
      AND (
          :advertisers = ARRAY[]::TEXT[]  -- Нет фильтра по advertiser
          OR ue.advertiser = ANY(:advertisers)
      )
      -- Фильтр по сумме депозитов (если есть события deposit)
      AND (
          :min_deposit = 0 AND :max_deposit = 1000000  -- Без фильтра по депозитам
          OR EXISTS (
              SELECT 1 
              FROM public.user_events ue2 
              WHERE ue2.external_user_id = ue.external_user_id 
                AND ue2.event_type = 'deposit'
                AND ue2.converted_amount >= :min_deposit
                AND ue2.converted_amount <= :max_deposit
          )
      )
      -- Исключаем пользователей с определенными событиями
      AND (
          :exclude_event_types = ARRAY[]::TEXT[]  -- Нет исключений
          OR NOT EXISTS (
              SELECT 1 
              FROM public.user_events ue3 
              WHERE ue3.external_user_id = ue.external_user_id 
                AND ue3.event_type = ANY(:exclude_event_types)
          )
      )
)
-- Шаг 2: Получаем все пары UA+IP для найденных пользователей
SELECT DISTINCT
    ue.user_agent,
    COALESCE(ue.ip_address, ue.ip) as ip_address
FROM public.user_events ue
INNER JOIN filtered_users fu ON ue.external_user_id = fu.external_user_id
WHERE ue.user_agent IS NOT NULL 
  AND ue.user_agent != ''
  AND (ue.ip_address IS NOT NULL AND ue.ip_address != '' OR ue.ip IS NOT NULL AND ue.ip != '')
ORDER BY ue.user_agent, ip_address;

-- Пример использования с конкретными значениями:
/*
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
  AND (ue.ip_address IS NOT NULL AND ue.ip_address != '' OR ue.ip IS NOT NULL AND ue.ip != '')
ORDER BY ue.user_agent, ip_address;
*/

