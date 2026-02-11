#!/usr/bin/env python3
"""
Диагностика проблемы с экспортом User Agent и IP пар
Проверяет наличие данных в базе и тестирует запросы
"""

import sys
import io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from db_utils import get_db_engine
from sqlalchemy import text
from datetime import datetime, timedelta

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("ДИАГНОСТИКА ЭКСПОРТА USER AGENT И IP")
print("=" * 80)
print()

engine = get_db_engine()

with engine.connect() as conn:
    # 1. Проверка структуры таблицы
    print("1. Проверка структуры таблицы user_events:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'user_events' 
          AND table_schema = 'public'
          AND column_name IN ('user_agent', 'ip_address', 'ip', 'event_type', 
                              'event_date', 'converted_amount', 'external_user_id')
        ORDER BY column_name
    """))
    cols = result.fetchall()
    found_cols = {}
    for col in cols:
        found_cols[col[0]] = col[1]
        print(f"   ✓ {col[0]} ({col[1]})")
    
    # Проверяем наличие необходимых колонок
    has_user_agent = 'user_agent' in found_cols
    has_ip = 'ip_address' in found_cols or 'ip' in found_cols
    ip_col_name = 'ip_address' if 'ip_address' in found_cols else ('ip' if 'ip' in found_cols else None)
    
    if not has_user_agent:
        print("   ❌ user_agent: НЕ НАЙДЕНА")
    if not has_ip:
        print("   ❌ ip_address/ip: НЕ НАЙДЕНА")
    print()
    
    # 2. Проверка наличия данных
    print("2. Проверка наличия данных:")
    print("-" * 80)
    
    # Общая статистика
    result = conn.execute(text("SELECT COUNT(*) FROM public.user_events"))
    total = result.fetchone()[0]
    print(f"   Всего записей: {total:,}")
    
    if has_user_agent:
        result = conn.execute(text("SELECT COUNT(*) FROM public.user_events WHERE user_agent IS NOT NULL AND user_agent != ''"))
        with_ua = result.fetchone()[0]
        print(f"   С user_agent: {with_ua:,} ({with_ua/total*100:.2f}%)")
    
    if has_ip:
        result = conn.execute(text(f"SELECT COUNT(*) FROM public.user_events WHERE {ip_col_name} IS NOT NULL AND {ip_col_name} != ''"))
        with_ip = result.fetchone()[0]
        print(f"   С {ip_col_name}: {with_ip:,} ({with_ip/total*100:.2f}%)")
    
    # Проверка наличия пар UA+IP
    if has_user_agent and has_ip:
        result = conn.execute(text(f"""
            SELECT COUNT(*) 
            FROM public.user_events 
            WHERE user_agent IS NOT NULL 
              AND user_agent != ''
              AND {ip_col_name} IS NOT NULL 
              AND {ip_col_name} != ''
        """))
        with_both = result.fetchone()[0]
        print(f"   С user_agent И {ip_col_name}: {with_both:,} ({with_both/total*100:.2f}%)")
    print()
    
    # 3. Проверка по типам событий
    print("3. Проверка по типам событий:")
    print("-" * 80)
    event_types = ['deposit', 'ftd', 'regfinished']
    for event_type in event_types:
        result = conn.execute(text(f"""
            SELECT COUNT(*) 
            FROM public.user_events 
            WHERE event_type = :event_type
        """), {"event_type": event_type})
        count = result.fetchone()[0]
        print(f"   {event_type}: {count:,} записей")
        
        if has_user_agent and has_ip:
            result = conn.execute(text(f"""
                SELECT COUNT(*) 
                FROM public.user_events 
                WHERE event_type = :event_type
                  AND user_agent IS NOT NULL 
                  AND user_agent != ''
                  AND {ip_col_name} IS NOT NULL 
                  AND {ip_col_name} != ''
            """), {"event_type": event_type})
            with_both = result.fetchone()[0]
            if count > 0:
                print(f"      С UA+IP: {with_both:,} ({with_both/count*100:.2f}%)")
    print()
    
    # 4. Тестовый запрос по фильтрам из UI
    print("4. Тестовый запрос (имитация фильтров из UI):")
    print("-" * 80)
    print("   Параметры:")
    print("   - Типы событий: regfinished (выбрано)")
    print("   - Диапазон депозитов: 0 - 1000000 USD")
    print("   - Исключить события: deposit, ftd (выбрано)")
    print()
    
    if not has_user_agent or not has_ip:
        print("   ❌ Невозможно выполнить запрос: отсутствуют необходимые колонки")
        print()
        print("=" * 80)
        print("РЕКОМЕНДАЦИИ:")
        print("=" * 80)
        if not has_user_agent:
            print("1. Добавьте колонку user_agent в таблицу user_events:")
            print("   ALTER TABLE public.user_events ADD COLUMN IF NOT EXISTS user_agent TEXT;")
        if not has_ip:
            print("2. Добавьте колонку ip_address в таблицу user_events:")
            print("   ALTER TABLE public.user_events ADD COLUMN IF NOT EXISTS ip_address TEXT;")
        print("3. Загрузите данные user_agent и ip_address из CSV файлов")
        sys.exit(1)
    
    # Тестовый запрос: найти пользователей с regfinished, но без deposit и ftd
    # Затем получить все их UA+IP пары
    test_query = f"""
    WITH 
    -- Находим пользователей по критериям
    filtered_users AS (
        SELECT DISTINCT external_user_id
        FROM public.user_events ue1
        WHERE ue1.event_type = 'regfinished'
          AND ue1.external_user_id IS NOT NULL
          -- Исключаем пользователей с deposit
          AND NOT EXISTS (
              SELECT 1 
              FROM public.user_events ue2 
              WHERE ue2.external_user_id = ue1.external_user_id 
                AND ue2.event_type = 'deposit'
          )
          -- Исключаем пользователей с ftd
          AND NOT EXISTS (
              SELECT 1 
              FROM public.user_events ue2 
              WHERE ue2.external_user_id = ue1.external_user_id 
                AND ue2.event_type = 'ftd'
          )
    )
    -- Получаем все UA+IP пары для этих пользователей
    SELECT 
        ue.user_agent,
        ue.{ip_col_name} as ip_address
    FROM public.user_events ue
    INNER JOIN filtered_users fu ON ue.external_user_id = fu.external_user_id
    WHERE ue.user_agent IS NOT NULL 
      AND ue.user_agent != ''
      AND ue.{ip_col_name} IS NOT NULL 
      AND ue.{ip_col_name} != ''
    LIMIT 10
    """
    
    try:
        result = conn.execute(text(test_query))
        rows = result.fetchall()
        print(f"   Найдено записей (первые 10): {len(rows)}")
        if rows:
            print("   Примеры:")
            for i, row in enumerate(rows[:3], 1):
                print(f"      {i}. UA: {row[0][:50]}... | IP: {row[1]}")
        else:
            print("   ⚠️  Запрос вернул 0 результатов")
            print()
            print("   Проверяю альтернативный запрос (без фильтров исключения)...")
            
            # Упрощенный запрос без исключений
            simple_query = f"""
            SELECT 
                ue.user_agent,
                ue.{ip_col_name} as ip_address
            FROM public.user_events ue
            WHERE ue.event_type = 'regfinished'
              AND ue.user_agent IS NOT NULL 
              AND ue.user_agent != ''
              AND ue.{ip_col_name} IS NOT NULL 
              AND ue.{ip_col_name} != ''
            LIMIT 10
            """
            result = conn.execute(text(simple_query))
            rows = result.fetchall()
            print(f"   Найдено записей: {len(rows)}")
            if rows:
                print("   Примеры:")
                for i, row in enumerate(rows[:3], 1):
                    print(f"      {i}. UA: {row[0][:50]}... | IP: {row[1]}")
    except Exception as e:
        print(f"   ❌ Ошибка при выполнении запроса: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 5. Проверка диапазона дат
    print("5. Проверка диапазона дат:")
    print("-" * 80)
    result = conn.execute(text("""
        SELECT 
            MIN(event_date) as min_date,
            MAX(event_date) as max_date,
            COUNT(*) as total
        FROM public.user_events
        WHERE event_date IS NOT NULL
    """))
    row = result.fetchone()
    if row and row[0]:
        print(f"   Минимальная дата: {row[0]}")
        print(f"   Максимальная дата: {row[1]}")
        print(f"   Всего записей: {row[2]:,}")
    print()
    
    print("=" * 80)
    print("ЗАКЛЮЧЕНИЕ:")
    print("=" * 80)
    if has_user_agent and has_ip:
        print("✓ Колонки user_agent и ip_address найдены")
        if rows:
            print("✓ Данные для экспорта найдены")
            print("  Возможные причины пустого CSV:")
            print("  1. Фильтры слишком строгие (исключение deposit+ftd)")
            print("  2. Проблема с логикой запроса в приложении")
            print("  3. Проблема с форматом экспорта CSV")
        else:
            print("⚠️  Данные не найдены по заданным критериям")
            print("  Попробуйте:")
            print("  1. Убрать фильтры исключения")
            print("  2. Расширить диапазон дат")
            print("  3. Проверить другие типы событий")
    else:
        print("❌ Отсутствуют необходимые колонки в базе данных")
        print("  Нужно добавить колонки и загрузить данные")

