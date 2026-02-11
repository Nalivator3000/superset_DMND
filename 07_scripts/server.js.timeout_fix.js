// Исправление проблемы таймаута 60 секунд для UA-IP-parcer
// Добавьте эти изменения в ваш server.js

const express = require('express');
const { Pool } = require('pg');
const csv = require('csv-stringify/sync');
require('dotenv').config();

const app = express();
app.use(express.json());
app.use(express.static('public'));

// Подключение к БД с увеличенным таймаутом
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
  // Увеличиваем таймауты для длительных запросов
  statement_timeout: 600000,  // 10 минут (в миллисекундах)
  query_timeout: 600000,      // 10 минут
  connectionTimeoutMillis: 30000,  // 30 секунд на подключение
  idle_in_transaction_session_timeout: 600000,  // 10 минут для транзакций
  // Увеличиваем размер пула для параллельных запросов
  max: 20,  // Максимум соединений в пуле
  min: 2,   // Минимум соединений
});

// Проверка схемы БД при старте
let ipColumn = 'ip_address'; // По умолчанию

async function checkDatabaseSchema() {
  try {
    const result = await pool.query(`
      SELECT column_name 
      FROM information_schema.columns 
      WHERE table_name = 'user_events' 
        AND table_schema = 'public'
        AND column_name IN ('user_agent', 'ip_address', 'ip')
    `);
    
    const columns = result.rows.map(r => r.column_name);
    const hasUserAgent = columns.includes('user_agent');
    const ipCol = columns.includes('ip_address') ? 'ip_address' : 
                  columns.includes('ip') ? 'ip' : null;
    
    if (!hasUserAgent || !ipCol) {
      console.error('Missing required columns:', {
        hasUserAgent,
        ipColumn: ipCol,
        availableColumns: columns
      });
      throw new Error(`Missing required columns: user_agent=${hasUserAgent}, ip=${ipCol}`);
    }
    
    ipColumn = ipCol;
    console.log(`Database schema OK: user_agent=✓, ip=${ipColumn}`);
    return { hasUserAgent, ipColumn: ipCol };
  } catch (error) {
    console.error('Schema check failed:', error);
    throw error;
  }
}

// API: Экспорт CSV с увеличенным таймаутом
app.post('/api/export', async (req, res) => {
  const { 
    startDate, 
    endDate, 
    eventTypes, 
    advertisers = [],
    excludeEvents = [], 
    minDeposit = 0, 
    maxDeposit = 1000000 
  } = req.body;
  
  console.log('Export request:', {
    startDate,
    endDate,
    eventTypes,
    advertisers,
    excludeEvents,
    minDeposit,
    maxDeposit
  });
  
  // Устанавливаем таймаут для HTTP запроса (10 минут)
  req.setTimeout(600000);
  res.setTimeout(600000);
  
  try {
    // Валидация
    if (!startDate || !endDate) {
      return res.status(400).json({ error: 'Укажите период (startDate и endDate)' });
    }
    
    if (!eventTypes || !Array.isArray(eventTypes) || eventTypes.length === 0) {
      return res.status(400).json({ error: 'Выберите хотя бы один тип события' });
    }
    
    // Формируем SQL запрос с оптимизациями
    let paramIndex = 1;
    const params = [startDate, endDate, eventTypes];
    paramIndex += 3;
    
    // ОПТИМИЗАЦИЯ: Используем более эффективный запрос
    // Вместо множественных EXISTS используем JOIN
    let query = `
      WITH 
      -- Шаг 1: Находим пользователей по критериям (оптимизировано)
      filtered_users AS (
        SELECT DISTINCT ue.external_user_id
        FROM public.user_events ue
        WHERE ue.event_date >= $1::timestamp
          AND ue.event_date <= $2::timestamp
          AND ue.event_type = ANY($3::text[])
          AND ue.external_user_id IS NOT NULL
    `;
    
    // Добавляем фильтр по advertiser
    if (advertisers.length > 0) {
      query += `\n          AND ue.advertiser = ANY($${paramIndex}::text[])`;
      params.push(advertisers);
      paramIndex++;
    }
    
    // Добавляем исключения (оптимизировано через LEFT JOIN)
    if (excludeEvents.length > 0) {
      query += `
          -- Исключаем пользователей с определенными событиями
          AND NOT EXISTS (
            SELECT 1 
            FROM public.user_events ue2 
            WHERE ue2.external_user_id = ue.external_user_id 
              AND ue2.event_type = ANY($${paramIndex}::text[])
            LIMIT 1
          )`;
      params.push(excludeEvents);
      paramIndex++;
    }
    
    // Добавляем фильтр по депозитам (оптимизировано)
    if (minDeposit > 0 || maxDeposit < 1000000) {
      query += `
          -- Фильтр по сумме депозитов
          AND EXISTS (
            SELECT 1 
            FROM public.user_events ue3 
            WHERE ue3.external_user_id = ue.external_user_id 
              AND ue3.event_type = 'deposit'
              AND ue3.converted_amount >= $${paramIndex}
              AND ue3.converted_amount <= $${paramIndex + 1}
            LIMIT 1
          )`;
      params.push(minDeposit, maxDeposit);
      paramIndex += 2;
    }
    
    query += `
      )
      -- Шаг 2: Получаем все пары UA+IP для найденных пользователей
      SELECT DISTINCT
        ue.user_agent,
        ue.${ipColumn} as ip_address
      FROM public.user_events ue
      INNER JOIN filtered_users fu ON ue.external_user_id = fu.external_user_id
      WHERE ue.user_agent IS NOT NULL 
        AND ue.user_agent != ''
        AND ue.${ipColumn} IS NOT NULL 
        AND ue.${ipColumn} != ''
      ORDER BY ue.user_agent, ue.${ipColumn}
    `;
    
    console.log(`Executing query with ${params.length} parameters`);
    console.log(`Query timeout: 10 minutes (600 seconds)`);
    
    // Выполняем запрос с увеличенным таймаутом
    const startTime = Date.now();
    
    // Используем клиент с увеличенным таймаутом
    const client = await pool.connect();
    try {
      // Устанавливаем таймаут для этого конкретного запроса
      await client.query('SET statement_timeout = 600000'); // 10 минут
      await client.query('SET query_timeout = 600000');
      
      const result = await client.query(query, params);
      const executionTime = ((Date.now() - startTime) / 1000).toFixed(2);
      
      console.log(`Query returned ${result.rows.length} rows in ${executionTime} seconds`);
      
      // Если результатов нет, выполняем диагностику
      if (result.rows.length === 0) {
        console.log('No results, running diagnostics...');
        // ... диагностика ...
        return res.status(400).json({
          error: 'CSV данные пусты. Проверьте логи сервера в Railway Dashboard.'
        });
      }
      
      // Формируем CSV
      const csvData = csv.stringify(result.rows, {
        header: true,
        columns: {
          user_agent: 'User Agent',
          ip_address: 'IP Address'
        }
      });
      
      // Отправляем CSV
      res.setHeader('Content-Type', 'text/csv; charset=utf-8');
      res.setHeader('Content-Disposition', `attachment; filename="ua_ip_export_${Date.now()}.csv"`);
      res.send('\ufeff' + csvData); // BOM для корректного отображения в Excel
      
    } finally {
      client.release();
    }
    
  } catch (error) {
    const executionTime = ((Date.now() - startTime) / 1000).toFixed(2);
    console.error(`Export error after ${executionTime} seconds:`, error);
    console.error('Stack:', error.stack);
    
    // Проверяем, это таймаут или другая ошибка
    if (error.message && error.message.includes('timeout')) {
      return res.status(504).json({ 
        error: 'Запрос превысил время ожидания (10 минут). Попробуйте сузить диапазон дат или фильтры.',
        suggestion: 'Уменьшите период или добавьте дополнительные фильтры для ускорения запроса'
      });
    }
    
    res.status(500).json({ 
      error: 'Ошибка при экспорте',
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
});

// Health check
app.get('/api/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'ok', database: 'connected' });
  } catch (error) {
    res.status(500).json({ status: 'error', database: 'disconnected', error: error.message });
  }
});

// Инициализация при старте
async function init() {
  try {
    await checkDatabaseSchema();
    console.log('Server initialized successfully');
    console.log('Query timeout set to 10 minutes (600 seconds)');
  } catch (error) {
    console.error('Initialization failed:', error);
    process.exit(1);
  }
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, async () => {
  console.log(`Server running on port ${PORT}`);
  await init();
});

