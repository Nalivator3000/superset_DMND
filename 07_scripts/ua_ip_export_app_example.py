#!/usr/bin/env python3
"""
Пример приложения для экспорта пар User Agent и IP
Можно использовать как основу для исправления ua-ip-parcer
"""

from flask import Flask, render_template_string, request, send_file, jsonify
import io
import csv
from datetime import datetime
from sqlalchemy import create_engine, text
import os
from pathlib import Path
import sys

# Добавляем путь к db_utils
sys.path.insert(0, str(Path(__file__).parent))
from db_utils import get_db_engine

app = Flask(__name__)

# HTML шаблон (упрощенный)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Ubidex CSV Export</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #4CAF50; background: #f9f9f9; }
        label { display: block; margin: 10px 0 5px 0; font-weight: bold; }
        input, select { width: 100%; padding: 8px; margin: 5px 0; }
        button { background: #4CAF50; color: white; padding: 12px 24px; border: none; cursor: pointer; width: 100%; font-size: 16px; }
        button:hover { background: #45a049; }
        .error { background: #ffebee; border-left-color: #f44336; color: #c62828; padding: 15px; margin: 10px 0; }
        .checkbox-group { margin: 10px 0; }
        .checkbox-group label { display: inline; font-weight: normal; margin-left: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Ubidex CSV Export</h1>
        <p>Экспорт пар User Agent и IP по заданным параметрам</p>
        
        {% if error %}
        <div class="error">
            <strong>Ошибка:</strong> {{ error }}
        </div>
        {% endif %}
        
        <form method="POST" action="/export">
            <div class="section">
                <h3>Период</h3>
                <label>Начало периода:</label>
                <input type="date" name="start_date" value="{{ request.form.get('start_date', '') }}" required>
                
                <label>Конец периода:</label>
                <input type="date" name="end_date" value="{{ request.form.get('end_date', '') }}" required>
            </div>
            
            <div class="section">
                <h3>Типы событий</h3>
                <p>Выберите типы событий для фильтрации:</p>
                <div class="checkbox-group">
                    <input type="checkbox" name="event_types" value="deposit" id="deposit">
                    <label for="deposit">deposit</label>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" name="event_types" value="ftd" id="ftd">
                    <label for="ftd">ftd</label>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" name="event_types" value="regfinished" id="regfinished" checked>
                    <label for="regfinished">regfinished</label>
                </div>
            </div>
            
            <div class="section">
                <h3>Advertiser</h3>
                <p>Выберите advertiser для фильтрации:</p>
                <div class="checkbox-group">
                    <input type="checkbox" name="advertisers" value="1" id="advertiser_4ra">
                    <label for="advertiser_4ra">4ra (ID: 1)</label>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" name="advertisers" value="2" id="advertiser_crore">
                    <label for="advertiser_crore">Crore (ID: 2)</label>
                </div>
                <p style="font-size: 12px; color: #666; margin-top: 10px;">
                    Если не выбрано ни одного advertiser, будут включены все advertiser
                </p>
            </div>
            
            <div class="section">
                <h3>Диапазон сумм депозитов</h3>
                <label>Минимальная сумма (USD):</label>
                <input type="number" name="min_deposit" value="0" min="0" step="0.01">
                
                <label>Максимальная сумма (USD):</label>
                <input type="number" name="max_deposit" value="1000000" min="0" step="0.01">
            </div>
            
            <div class="section">
                <h3>Исключить события</h3>
                <p>Пользователи, у которых НЕТ этих событий:</p>
                <div class="checkbox-group">
                    <input type="checkbox" name="exclude_events" value="deposit" id="exclude_deposit" checked>
                    <label for="exclude_deposit">deposit</label>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" name="exclude_events" value="ftd" id="exclude_ftd" checked>
                    <label for="exclude_ftd">ftd</label>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" name="exclude_events" value="regfinished" id="exclude_regfinished">
                    <label for="exclude_regfinished">regfinished</label>
                </div>
            </div>
            
            <button type="submit">Экспортировать CSV</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/export', methods=['POST'])
def export_csv():
    try:
        # Получаем параметры из формы
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        event_types = request.form.getlist('event_types')
        advertisers = request.form.getlist('advertisers')  # ['1'] для 4ra, ['2'] для Crore
        min_deposit = float(request.form.get('min_deposit', 0))
        max_deposit = float(request.form.get('max_deposit', 1000000))
        exclude_events = request.form.getlist('exclude_events')
        
        # Валидация
        if not start_date or not end_date:
            return render_template_string(HTML_TEMPLATE, error="Укажите период")
        
        if not event_types:
            return render_template_string(HTML_TEMPLATE, error="Выберите хотя бы один тип события")
        
        # Подключаемся к БД
        engine = get_db_engine()
        
        # Проверяем наличие колонок
        with engine.connect() as conn:
            # Проверяем структуру таблицы
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user_events' 
                  AND table_schema = 'public'
                  AND column_name IN ('user_agent', 'ip_address', 'ip')
            """))
            cols = {row[0] for row in result.fetchall()}
            
            if 'user_agent' not in cols:
                return render_template_string(HTML_TEMPLATE, 
                    error="Колонка user_agent не найдена в таблице user_events")
            
            ip_col = 'ip_address' if 'ip_address' in cols else ('ip' if 'ip' in cols else None)
            if not ip_col:
                return render_template_string(HTML_TEMPLATE, 
                    error="Колонка ip_address или ip не найдена в таблице user_events")
            
            # Формируем SQL запрос
            # Сначала находим пользователей
            user_query = f"""
            WITH filtered_users AS (
                SELECT DISTINCT ue.external_user_id
                FROM public.user_events ue
                WHERE ue.event_date >= :start_date::timestamp
                  AND ue.event_date <= :end_date::timestamp
                  AND ue.event_type = ANY(:event_types)
                  AND ue.external_user_id IS NOT NULL
            """
            
            # Добавляем фильтр по advertiser, если выбран
            if advertisers:
                user_query += """
                  AND ue.advertiser = ANY(:advertisers)
                """
            
            # Добавляем фильтр по депозитам, если нужно
            if min_deposit > 0 or max_deposit < 1000000:
                user_query += """
                  AND EXISTS (
                      SELECT 1 
                      FROM public.user_events ue2 
                      WHERE ue2.external_user_id = ue.external_user_id 
                        AND ue2.event_type = 'deposit'
                        AND ue2.converted_amount >= :min_deposit
                        AND ue2.converted_amount <= :max_deposit
                  )
                """
            
            # Добавляем исключения
            if exclude_events:
                user_query += """
                  AND NOT EXISTS (
                      SELECT 1 
                      FROM public.user_events ue3 
                      WHERE ue3.external_user_id = ue.external_user_id 
                        AND ue3.event_type = ANY(:exclude_events)
                  )
                """
            
            user_query += """
            )
            SELECT DISTINCT
                ue.user_agent,
                ue.{ip_col} as ip_address
            FROM public.user_events ue
            INNER JOIN filtered_users fu ON ue.external_user_id = fu.external_user_id
            WHERE ue.user_agent IS NOT NULL 
              AND ue.user_agent != ''
              AND ue.{ip_col} IS NOT NULL 
              AND ue.{ip_col} != ''
            ORDER BY ue.user_agent, ue.{ip_col}
            """.format(ip_col=ip_col)
            
            # Формируем параметры запроса
            query_params = {
                'start_date': start_date,
                'end_date': end_date,
                'event_types': event_types,
                'exclude_events': exclude_events if exclude_events else []
            }
            
            # Добавляем advertiser в параметры, если выбран
            if advertisers:
                query_params['advertisers'] = advertisers
            
            # Добавляем параметры депозитов, если нужно
            if min_deposit > 0 or max_deposit < 1000000:
                query_params['min_deposit'] = min_deposit
                query_params['max_deposit'] = max_deposit
            
            # Выполняем запрос
            result = conn.execute(text(user_query), query_params)
            
            rows = result.fetchall()
            
            if not rows:
                return render_template_string(HTML_TEMPLATE, 
                    error="CSV данные пусты. Проверьте логи сервера в Railway Dashboard.")
            
            # Создаем CSV в памяти
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['User Agent', 'IP Address'])
            
            for row in rows:
                writer.writerow([row[0], row[1]])
            
            # Возвращаем CSV файл
            output.seek(0)
            filename = f"ua_ip_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8-sig')),  # BOM для Excel
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
            
    except Exception as e:
        import traceback
        error_msg = f"Ошибка при экспорте: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)  # Логируем в консоль
        return render_template_string(HTML_TEMPLATE, error=f"Ошибка: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

