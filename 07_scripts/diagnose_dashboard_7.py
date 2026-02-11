#!/usr/bin/env python3
"""
Диагностика проблем с чартами на дашборде 7
Проверяет все чарты на дашборде и выявляет возможные проблемы
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

DASHBOARD_ID = 7

print("=" * 80)
print(f"ДИАГНОСТИКА ДАШБОРДА {DASHBOARD_ID}")
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

# Step 2: Get Dashboard
print(f"2. Получение информации о дашборде {DASHBOARD_ID}...")
try:
    dashboard_url = f"{SUPERSET_URL}/api/v1/dashboard/{DASHBOARD_ID}"
    dashboard_response = session.get(dashboard_url, headers=headers, timeout=30)
    dashboard_response.raise_for_status()
    dashboard = dashboard_response.json().get("result", {})
    
    print(f"   ✓ Дашборд найден: {dashboard.get('dashboard_title', 'N/A')}")
    print(f"     - Slug: {dashboard.get('slug', 'N/A')}")
    print(f"     - Published: {dashboard.get('published', False)}")
    
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
    
    print(f"     - Чартов на дашборде: {len(chart_ids)}")
    if chart_ids:
        print(f"     - ID чартов: {chart_ids}")
    
except Exception as e:
    print(f"   ✗ Ошибка получения дашборда: {e}")
    print(f"     Ответ сервера: {dashboard_response.text if 'dashboard_response' in locals() else 'N/A'}")
    sys.exit(1)

if not chart_ids:
    print()
    print("⚠️  На дашборде нет чартов!")
    print("   Добавьте чарты через Edit Dashboard → + Chart")
    sys.exit(0)

# Step 3: Check Database settings
print()
print("3. Проверка настроек базы данных...")
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
            
            # Check critical settings
            allow_async = db.get("allow_run_async", False)
            query_timeout = db.get("query_timeout", 0)
            
            print(f"     - Async queries: {'✓ Включено' if allow_async else '✗ ВЫКЛЮЧЕНО (КРИТИЧНО!)'}")
            print(f"     - Query timeout: {query_timeout} секунд {'✓' if query_timeout >= 600 else '⚠️  (рекомендуется >= 600)'}")
            
            # Check extra settings
            extra = db.get("extra", "{}")
            if isinstance(extra, str):
                try:
                    extra = json.loads(extra)
                except:
                    extra = {}
            
            if isinstance(extra, dict):
                if "engine_params" in extra:
                    engine_params = extra["engine_params"]
                    if isinstance(engine_params, dict) and "connect_args" in engine_params:
                        connect_args = engine_params["connect_args"]
                        if isinstance(connect_args, dict) and "connect_timeout" in connect_args:
                            print(f"     - Connection timeout: {connect_args['connect_timeout']}")
            
            break
    
    if not db_id:
        print("   ⚠️  База данных 'Ubidex Events DB' не найдена")
        
except Exception as e:
    print(f"   ✗ Ошибка: {e}")

# Step 4: Check each Chart
print()
print("4. Проверка чартов на дашборде...")
print()

charts_info = []
for chart_id in chart_ids:
    try:
        chart_url = f"{SUPERSET_URL}/api/v1/chart/{chart_id}"
        chart_response = session.get(chart_url, headers=headers, timeout=30)
        chart_response.raise_for_status()
        chart = chart_response.json().get("result", {})
        
        chart_name = chart.get("slice_name", "N/A")
        dataset_id = chart.get("datasource_id")
        viz_type = chart.get("viz_type", "N/A")
        
        print(f"   Чарт: {chart_name} (ID: {chart_id})")
        print(f"     - Тип: {viz_type}")
        print(f"     - Dataset ID: {dataset_id}")
        
        # Get Dataset info
        if dataset_id:
            try:
                dataset_url = f"{SUPERSET_URL}/api/v1/dataset/{dataset_id}"
                dataset_response = session.get(dataset_url, headers=headers, timeout=30)
                dataset_response.raise_for_status()
                dataset = dataset_response.json().get("result", {})
                
                dataset_name = dataset.get("table_name", "N/A")
                is_virtual = dataset.get("is_virtual", False)
                has_sql = bool(dataset.get("sql"))
                
                print(f"     - Dataset: {dataset_name}")
                print(f"     - Виртуальный (SQL): {'Да' if is_virtual or has_sql else 'Нет'}")
                
                # Check if SQL query exists and is valid
                if has_sql:
                    sql = dataset.get("sql", "")
                    if sql:
                        sql_preview = sql[:100].replace("\n", " ")
                        print(f"     - SQL (превью): {sql_preview}...")
                
            except Exception as e:
                print(f"     ⚠️  Не удалось получить Dataset: {e}")
        
        # Check chart params
        params = chart.get("params", {})
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except:
                params = {}
        
        if isinstance(params, dict):
            query_mode = params.get("query_mode", "N/A")
            print(f"     - Query Mode: {query_mode}")
            
            # Check for filters
            adhoc_filters = params.get("adhoc_filters", [])
            if adhoc_filters:
                print(f"     - Фильтров: {len(adhoc_filters)}")
                for filter_item in adhoc_filters[:3]:  # Show first 3
                    if isinstance(filter_item, dict):
                        col = filter_item.get("col", "N/A")
                        op = filter_item.get("op", "N/A")
                        print(f"       • {col} {op}")
        
        charts_info.append({
            "id": chart_id,
            "name": chart_name,
            "dataset_id": dataset_id,
            "viz_type": viz_type
        })
        
        print()
        
    except Exception as e:
        print(f"   ✗ Ошибка получения чарта {chart_id}: {e}")
        print()

# Step 5: Summary and Recommendations
print("=" * 80)
print("РЕЗЮМЕ И РЕКОМЕНДАЦИИ")
print("=" * 80)
print()

issues_found = []

if not allow_async:
    issues_found.append("Асинхронные запросы выключены в настройках базы данных")

if query_timeout < 600:
    issues_found.append(f"Таймаут запросов слишком мал ({query_timeout} сек, рекомендуется >= 600)")

if not charts_info:
    issues_found.append("Не удалось получить информацию о чартах")

if issues_found:
    print("⚠️  НАЙДЕННЫЕ ПРОБЛЕМЫ:")
    for i, issue in enumerate(issues_found, 1):
        print(f"   {i}. {issue}")
    print()
else:
    print("✓ Критических проблем в настройках не обнаружено")
    print()

print("РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
print()
print("1. Включите асинхронные запросы (КРИТИЧНО!):")
print("   - Superset → Data → Databases → 'Ubidex Events DB'")
print("   - Advanced → Query Execution Options")
print("   - Включите 'Asynchronous query execution' ✅")
print("   - Сохраните")
print()

print("2. Установите таймаут запросов:")
print("   - В тех же настройках Database")
print("   - 'Query timeout' установите 600 или больше")
print("   - Сохраните")
print()

print("3. Проверьте каждый чарт отдельно:")
for chart_info in charts_info:
    chart_url = f"{SUPERSET_URL}/superset/explore/?slice_id={chart_info['id']}"
    print(f"   - {chart_info['name']}: {chart_url}")
print()

print("4. Если чарты показывают ошибки:")
print("   - Проверьте фильтры по дате (возможно, данных нет в выбранном периоде)")
print("   - Проверьте SQL запрос в Dataset")
print("   - Попробуйте выполнить запрос в SQL Lab")
print()

print("5. Перезапустите Superset (если изменили настройки):")
print("   - Railway Dashboard → ваш проект → сервис Superset")
print("   - ⋮ → Restart")
print()

