#!/usr/bin/env python3
"""
Исправление проблем с чартами на дашборде 7
Включает асинхронные запросы и настраивает таймауты
"""
import requests
import json
import sys
import io
import os

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SUPERSET_URL = os.environ.get("SUPERSET_URL", "https://superset-railway-production-38aa.up.railway.app")
SUPERSET_USERNAME = os.environ.get("SUPERSET_USERNAME", "admin")
SUPERSET_PASSWORD = os.environ.get("SUPERSET_PASSWORD", "admin12345")

print("=" * 80)
print("ИСПРАВЛЕНИЕ ПРОБЛЕМ С ЧАРТАМИ НА ДАШБОРДЕ 7")
print("=" * 80)
print()

# Step 1: Login
print("1. Авторизация в Superset...")
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
    print("   ✓ Авторизация успешна")
    
    # Get CSRF token
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
    print(f"   ✗ Ошибка авторизации: {e}")
    sys.exit(1)

# Headers
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Referer": SUPERSET_URL
}
if csrf_token:
    headers["X-CSRFToken"] = csrf_token

# Step 2: Fix Database settings
print()
print("2. Исправление настроек базы данных...")
db_url = f"{SUPERSET_URL}/api/v1/database/"
try:
    db_response = session.get(db_url, headers=headers, timeout=30)
    db_response.raise_for_status()
    databases = db_response.json().get("result", [])
    
    db_id = None
    for db in databases:
        if db.get("database_name") == "Ubidex Events DB":
            db_id = db["id"]
            print(f"   ✓ База данных найдена (ID: {db_id})")
            
            # Get full database details
            get_db_url = f"{SUPERSET_URL}/api/v1/database/{db_id}"
            get_response = session.get(get_db_url, headers=headers, timeout=30)
            get_response.raise_for_status()
            current_db = get_response.json().get("result", {})
            
            # Check current settings
            current_async = current_db.get("allow_run_async", False)
            current_timeout = current_db.get("query_timeout", 0)
            
            print(f"   Текущие настройки:")
            print(f"     - Async queries: {current_async}")
            print(f"     - Query timeout: {current_timeout} секунд")
            
            # Prepare update
            if not current_async or current_timeout < 600:
                update_payload = {}
                # Copy all existing fields
                for key, value in current_db.items():
                    if key not in ["id", "changed_on", "created_on", "changed_by", "created_by", 
                                   "changed_by_fk", "created_by_fk", "owners", "tables"]:
                        update_payload[key] = value
                
                # Update settings
                update_payload["allow_run_async"] = True
                update_payload["query_timeout"] = 600
                
                print()
                print(f"   Обновление настроек:")
                print(f"     - Async queries: {update_payload['allow_run_async']}")
                print(f"     - Query timeout: {update_payload['query_timeout']} секунд")
                
                # Update database
                try:
                    update_response = session.put(
                        f"{SUPERSET_URL}/api/v1/database/{db_id}",
                        headers=headers,
                        json=update_payload,
                        timeout=30
                    )
                    if update_response.status_code == 200:
                        print("   ✓ Настройки базы данных обновлены")
                    else:
                        print(f"   ✗ Ошибка обновления: {update_response.status_code}")
                        print(f"     {update_response.text[:200]}")
                except Exception as e:
                    print(f"   ✗ Ошибка: {e}")
            else:
                print("   ✓ Настройки уже правильные")
            
            break
    
    if not db_id:
        print("   ⚠️  База данных 'Ubidex Events DB' не найдена")
        
except Exception as e:
    print(f"   ✗ Ошибка: {e}")

# Step 3: Check charts
print()
print("3. Проверка чартов на дашборде 7...")

DASHBOARD_ID = 7
try:
    dashboard_url = f"{SUPERSET_URL}/api/v1/dashboard/{DASHBOARD_ID}"
    dashboard_response = session.get(dashboard_url, headers=headers, timeout=30)
    dashboard_response.raise_for_status()
    dashboard = dashboard_response.json().get("result", {})
    
    # Parse position_json to get chart IDs
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
    
    print(f"   Найдено чартов: {len(chart_ids)}")
    print()
    
    for chart_id in chart_ids:
        try:
            chart_url = f"{SUPERSET_URL}/api/v1/chart/{chart_id}"
            chart_response = session.get(chart_url, headers=headers, timeout=30)
            chart_response.raise_for_status()
            chart = chart_response.json().get("result", {})
            
            chart_name = chart.get("slice_name", "N/A")
            dataset_id = chart.get("datasource_id")
            
            print(f"   Чарт: {chart_name} (ID: {chart_id})")
            print(f"     URL: {SUPERSET_URL}/superset/explore/?slice_id={chart_id}")
            
            # Get Dataset info
            if dataset_id:
                try:
                    dataset_url = f"{SUPERSET_URL}/api/v1/dataset/{dataset_id}"
                    dataset_response = session.get(dataset_url, headers=headers, timeout=30)
                    dataset_response.raise_for_status()
                    dataset = dataset_response.json().get("result", {})
                    
                    dataset_name = dataset.get("table_name", "N/A")
                    print(f"     Dataset: {dataset_name} (ID: {dataset_id})")
                    
                    # Check if SQL query exists
                    sql = dataset.get("sql", "")
                    if sql:
                        # Check for date filters in SQL
                        if "event_date" in sql.lower() or "2026-01" in sql:
                            print(f"     ⚠️  SQL содержит фильтры по дате - проверьте, что данные есть в этом периоде")
                    
                except Exception as e:
                    print(f"     ⚠️  Не удалось получить Dataset: {e}")
            
            print()
            
        except Exception as e:
            print(f"   ✗ Ошибка получения чарта {chart_id}: {e}")
            print()
    
except Exception as e:
    print(f"   ✗ Ошибка получения дашборда: {e}")

print("=" * 80)
print("ИСПРАВЛЕНИЕ ЗАВЕРШЕНО")
print("=" * 80)
print()
print("ВАЖНО:")
print("1. Если настройки базы данных были изменены, ПЕРЕЗАПУСТИТЕ Superset на Railway")
print("2. Проверьте каждый чарт отдельно по ссылкам выше")
print("3. Если чарты все еще не работают, проверьте:")
print("   - Фильтры по дате в чартах")
print("   - SQL запросы в Dataset")
print("   - Наличие данных в базе за выбранный период")
print()

