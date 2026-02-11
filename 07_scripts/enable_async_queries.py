#!/usr/bin/env python3
"""
Включение асинхронных запросов для базы данных через API
"""
import requests
import json
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SUPERSET_URL = os.environ.get("SUPERSET_URL", "https://superset-railway-production-38aa.up.railway.app")
SUPERSET_USERNAME = os.environ.get("SUPERSET_USERNAME", "admin")
SUPERSET_PASSWORD = os.environ.get("SUPERSET_PASSWORD", "admin12345")

print("Включение асинхронных запросов...")
print()

# Login
session = requests.Session()
login_response = session.post(
    f"{SUPERSET_URL}/api/v1/security/login",
    json={"username": SUPERSET_USERNAME, "password": SUPERSET_PASSWORD, "provider": "db", "refresh": True},
    timeout=30
)
access_token = login_response.json()["access_token"]

csrf_response = session.get(
    f"{SUPERSET_URL}/api/v1/security/csrf_token/",
    headers={"Authorization": f"Bearer {access_token}", "Referer": SUPERSET_URL},
    timeout=30
)
csrf_data = csrf_response.json()
csrf_token = csrf_data.get("result", {}).get("csrf_token") if isinstance(csrf_data.get("result"), dict) else csrf_data.get("result") or csrf_data.get("csrf_token")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Referer": SUPERSET_URL,
    "X-CSRFToken": csrf_token
}

# Get database
db_response = session.get(f"{SUPERSET_URL}/api/v1/database/", headers=headers, timeout=60)
databases = db_response.json().get("result", [])

db_id = None
for db in databases:
    if db.get("database_name") == "Ubidex Events DB":
        db_id = db["id"]
        break

if not db_id:
    print("✗ База данных не найдена")
    sys.exit(1)

# Get full database details
get_response = session.get(f"{SUPERSET_URL}/api/v1/database/{db_id}", headers=headers, timeout=60)
current_db = get_response.json().get("result", {})

print(f"Текущие настройки:")
print(f"  - Async queries: {current_db.get('allow_run_async', False)}")
print(f"  - Query timeout: {current_db.get('query_timeout', 0)}")
print()

# Prepare update - copy all fields except read-only
update_payload = {}
for key, value in current_db.items():
    if key not in ["id", "changed_on", "created_on", "changed_by", "created_by", 
                   "changed_by_fk", "created_by_fk", "owners", "tables", "dashboards"]:
        update_payload[key] = value

# Update settings
update_payload["allow_run_async"] = True
update_payload["query_timeout"] = 600

print("Обновление настроек...")
print(f"  - Async queries: {update_payload['allow_run_async']}")
print(f"  - Query timeout: {update_payload['query_timeout']}")
print()

# Update with longer timeout
try:
    update_response = session.put(
        f"{SUPERSET_URL}/api/v1/database/{db_id}",
        headers=headers,
        json=update_payload,
        timeout=120  # Longer timeout for the update itself
    )
    
    if update_response.status_code == 200:
        print("✓ Настройки успешно обновлены!")
        print()
        print("ВАЖНО: Перезапустите Superset на Railway для применения изменений")
    else:
        print(f"✗ Ошибка: {update_response.status_code}")
        print(f"  {update_response.text[:500]}")
except Exception as e:
    print(f"✗ Ошибка при обновлении: {e}")
    print()
    print("Попробуйте обновить настройки вручную через UI:")
    print(f"  {SUPERSET_URL}")
    print("  Data → Databases → 'Ubidex Events DB' → Advanced")
    print("  ✅ Asynchronous query execution")
    print("  Query timeout: 600")

