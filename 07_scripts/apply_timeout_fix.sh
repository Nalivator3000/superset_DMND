#!/bin/bash
# Скрипт для применения исправлений таймаута в UA-IP-parcer

echo "=========================================="
echo "Применение исправлений таймаута"
echo "=========================================="
echo ""

# Проверка наличия файлов
if [ ! -f "server.js.timeout_fix.js" ]; then
    echo "❌ Файл server.js.timeout_fix.js не найден!"
    exit 1
fi

echo "1. Создание резервной копии server.js..."
if [ -f "server.js" ]; then
    cp server.js server.js.backup.$(date +%Y%m%d_%H%M%S)
    echo "   ✓ Резервная копия создана"
else
    echo "   ⚠️  server.js не найден, будет создан новый"
fi

echo ""
echo "2. Применение исправлений..."
echo "   Скопируйте содержимое server.js.timeout_fix.js в server.js"
echo "   Или выполните:"
echo "   cp server.js.timeout_fix.js server.js"
echo ""

echo "3. Создание индексов в БД..."
echo "   Выполните SQL скрипт: create_indexes_ua_ip_export.sql"
echo "   Это ускорит выполнение запросов"
echo ""

echo "4. Перезапуск приложения на Railway..."
echo "   - Откройте Railway Dashboard"
echo "   - Найдите сервис ua-ip-parcer-production"
echo "   - Нажмите ⋮ → Restart"
echo ""

echo "=========================================="
echo "Готово!"
echo "=========================================="

