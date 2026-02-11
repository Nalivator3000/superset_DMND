#!/usr/bin/env python3
"""
Детальная проверка чартов на дашборде 7
Проверяет SQL запросы, фильтры и возможные проблемы
"""
import requests
import json
import sys
import io
import os
import re

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SUPERSET_URL = os.environ.get("SUPERSET_URL", "https://superset-railway-production-38aa.up.railway.app")
SUPERSET_USERNAME = os.environ.get("SUPERSET_USERNAME", "admin")
SUPERSET_PASSWORD = os.environ.get("SUPERSET_PASSWORD", "admin12345")

print("=" * 80)
print("ДЕТАЛЬНАЯ ПРОВЕРКА ЧАРТОВ НА ДАШБОРДЕ 7")
print("=" * 80)
print()

# Login
session = requests.Session()
login_url = f"{SUPERSET_URL}/api/v1/security/login"
login_payload = {
    "username": SUPERSET_USERNAME,
    "password": SUPERSET_PASSWORD,
    "provider": "db",
    "refresh": True
}

try:
    login_response = session.post(login_url, json=login_payload, timeout=30)
    login_response.raise_for_status()
    access_token = login_response.json()["access_token"]
    
    csrf_url = f"{SUPERSET_URL}/api/v1/security/csrf_token/"
    csrf_headers = {
        "Authorization": f"Bearer {access_token}",
        "Referer": SUPERSET_URL
    }
    csrf_response = session.get(csrf_url, headers=csrf_headers, timeout=30)
    if csrf_response.status_code == 200:
        csrf_data = csrf_response.json()
        if isinstance(csrf_data, dict):
            result = csrf_data.get("result")
            if isinstance(result, dict):
                csrf_token = result.get("csrf_token")
            elif isinstance(result, str):
                csrf_token = result
            else:
                csrf_token = csrf_data.get("csrf_token")
        else:
            csrf_token = csrf_data
except Exception as e:
    print(f"✗ Ошибка авторизации: {e}")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Referer": SUPERSET_URL
}
if csrf_token:
    headers["X-CSRFToken"] = csrf_token

# Get dashboard
DASHBOARD_ID = 7
dashboard_url = f"{SUPERSET_URL}/api/v1/dashboard/{DASHBOARD_ID}"
dashboard_response = session.get(dashboard_url, headers=headers, timeout=30)
dashboard = dashboard_response.json().get("result", {})

position_json = dashboard.get("position_json", "{}")
if isinstance(position_json, str):
    try:
        position_json = json.loads(position_json)
    except:
        position_json = {}

chart_ids = []
if isinstance(position_json, dict):
    for key, value in position_json.items():
        if isinstance(value, dict) and "meta" in value:
            meta = value["meta"]
            if "chartId" in meta:
                chart_ids.append(meta["chartId"])

print(f"Найдено чартов: {len(chart_ids)}")
print()

for chart_id in chart_ids:
    print("=" * 80)
    chart_url = f"{SUPERSET_URL}/api/v1/chart/{chart_id}"
    chart_response = session.get(chart_url, headers=headers, timeout=30)
    chart = chart_response.json().get("result", {})
    
    chart_name = chart.get("slice_name", "N/A")
    dataset_id = chart.get("datasource_id")
    viz_type = chart.get("viz_type", "N/A")
    
    print(f"ЧАРТ: {chart_name} (ID: {chart_id})")
    print(f"Тип: {viz_type}")
    print(f"URL: {SUPERSET_URL}/superset/explore/?slice_id={chart_id}")
    print()
    
    # Get Dataset
    if dataset_id:
        dataset_url = f"{SUPERSET_URL}/api/v1/dataset/{dataset_id}"
        dataset_response = session.get(dataset_url, headers=headers, timeout=30)
        dataset = dataset_response.json().get("result", {})
        
        dataset_name = dataset.get("table_name", "N/A")
        sql = dataset.get("sql", "")
        
        print(f"Dataset: {dataset_name} (ID: {dataset_id})")
        print()
        
        # Analyze SQL
        if sql:
            print("Анализ SQL запроса:")
            
            # Check for date filters
            date_patterns = [
                r"event_date\s*>=\s*['\"]([^'\"]+)['\"]",
                r"event_date\s*<=\s*['\"]([^'\"]+)['\"]",
                r"event_date\s*>\s*['\"]([^'\"]+)['\"]",
                r"event_date\s*<\s*['\"]([^'\"]+)['\"]",
                r"event_date\s*BETWEEN\s*['\"]([^'\"]+)['\"]\s*AND\s*['\"]([^'\"]+)['\"]",
                r"event_date\s*>=\s*'(\d{4}-\d{2}-\d{2})'",
                r"event_date\s*<=\s*'(\d{4}-\d{2}-\d{2})'",
            ]
            
            dates_found = []
            for pattern in date_patterns:
                matches = re.findall(pattern, sql, re.IGNORECASE)
                if matches:
                    if isinstance(matches[0], tuple):
                        dates_found.extend(matches[0])
                    else:
                        dates_found.extend(matches)
            
            if dates_found:
                print(f"  ⚠️  Найдены фильтры по дате: {', '.join(set(dates_found))}")
                print(f"     Убедитесь, что данные есть в этом периоде!")
            else:
                print("  ✓ Явных фильтров по дате в SQL не найдено")
            
            # Check for complex queries
            if "WITH" in sql.upper() or "CTE" in sql.upper():
                cte_count = sql.upper().count("WITH")
                print(f"  ℹ️  SQL использует CTE (WITH) - {cte_count} блок(ов)")
            
            # Check query length
            sql_lines = len(sql.split('\n'))
            sql_chars = len(sql)
            print(f"  ℹ️  Размер SQL: {sql_lines} строк, {sql_chars} символов")
            
            if sql_chars > 10000:
                print(f"  ⚠️  SQL запрос очень большой - может выполняться долго")
        
        print()
        
        # Check chart params
        params = chart.get("params", {})
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except:
                params = {}
        
        if isinstance(params, dict):
            print("Настройки чарта:")
            query_mode = params.get("query_mode", "N/A")
            print(f"  Query Mode: {query_mode}")
            
            # Check filters
            adhoc_filters = params.get("adhoc_filters", [])
            if adhoc_filters:
                print(f"  Фильтры в чарте: {len(adhoc_filters)}")
                for i, filter_item in enumerate(adhoc_filters, 1):
                    if isinstance(filter_item, dict):
                        col = filter_item.get("col", "N/A")
                        op = filter_item.get("op", "N/A")
                        val = filter_item.get("val", "N/A")
                        print(f"    {i}. {col} {op} {val}")
            else:
                print("  Фильтров в чарте нет")
            
            # Check for all_columns
            all_columns = params.get("all_columns", [])
            if all_columns:
                print(f"  Колонок в таблице: {len(all_columns)}")
        
        print()
    
    print()

print("=" * 80)
print("РЕКОМЕНДАЦИИ")
print("=" * 80)
print()
print("1. КРИТИЧНО: Включите асинхронные запросы в настройках базы данных")
print("   Data → Databases → 'Ubidex Events DB' → Advanced")
print("   ✅ Asynchronous query execution")
print()
print("2. Проверьте фильтры по дате в SQL запросах")
print("   Убедитесь, что данные есть в указанном периоде")
print()
print("3. Если SQL запросы очень большие, рассмотрите:")
print("   - Добавление фильтров по дате в сам SQL")
print("   - Использование материализованных представлений")
print("   - Оптимизацию запросов")
print()

