# Добавление выбора Advertiser в UI приложения UA-IP-parcer

## Проблема

В интерфейсе приложения нет выбора advertiser (4ra и Crore).

## Решение

### Вариант 1: Заменить файл public/index.html (Рекомендуется)

1. **Откройте репозиторий UA-IP-parcer:**
   ```bash
   cd /path/to/UA-IP-parcer
   ```

2. **Скопируйте готовый HTML файл:**
   ```bash
   cp /path/to/superset-railway/07_scripts/public_index_with_advertiser.html public/index.html
   ```

3. **Или вручную добавьте секцию Advertiser** в ваш `public/index.html`:

```html
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
    <p class="help-text">
        Если не выбрано ни одного advertiser, будут включены все advertiser
    </p>
</div>
```

**Разместите эту секцию между "Типы событий" и "Диапазон сумм депозитов".**

### Вариант 2: Обновить JavaScript код

Убедитесь, что в JavaScript коде правильно собирается параметр `advertisers`:

```javascript
const data = {
    startDate: formData.get('startDate'),
    endDate: formData.get('endDate'),
    eventTypes: formData.getAll('eventTypes'),
    advertisers: formData.getAll('advertisers'),  // ВАЖНО: используйте getAll, а не get
    excludeEvents: formData.getAll('excludeEvents'),
    minDeposit: parseFloat(formData.get('minDeposit')) || 0,
    maxDeposit: parseFloat(formData.get('maxDeposit')) || 1000000
};
```

**Ключевой момент:** Используйте `formData.getAll('advertisers')`, а не `formData.get('advertisers')`, чтобы получить массив всех выбранных чекбоксов.

### Вариант 3: Проверить server.js

Убедитесь, что в `server.js` правильно обрабатывается параметр `advertisers`:

```javascript
app.post('/api/export', async (req, res) => {
  const { 
    advertisers = [],  // Должен быть массивом
    // ... другие параметры
  } = req.body;
  
  console.log('Advertisers:', advertisers);  // Для отладки
  
  // ... остальной код
});
```

## Проверка

После добавления:

1. **Откройте приложение** в браузере
2. **Проверьте наличие секции "Advertiser"** с двумя чекбоксами:
   - ☐ 4ra (ID: 1)
   - ☐ Crore (ID: 2)
3. **Выберите один или оба advertiser**
4. **Откройте консоль браузера** (F12) и проверьте, что в запросе отправляется:
   ```json
   {
     "advertisers": ["1", "2"]
   }
   ```
5. **Проверьте логи сервера** - должно быть:
   ```
   Export request: { advertisers: [ '1', '2' ], ... }
   ```

## Структура HTML формы

Правильный порядок секций:

1. Период
2. Типы событий
3. **Advertiser** ← Добавьте здесь
4. Диапазон сумм депозитов
5. Исключить события

## Готовый файл

Полный готовый файл `public/index.html` находится в:
- `07_scripts/public_index_with_advertiser.html`

Скопируйте его в репозиторий UA-IP-parcer как `public/index.html`.

## После обновления

1. **Закоммитьте изменения:**
   ```bash
   git add public/index.html
   git commit -m "Add advertiser filter to UI"
   git push
   ```

2. **Railway автоматически задеплоит** новую версию (если настроен автодеплой)

3. **Проверьте работу** - выберите advertiser и попробуйте экспорт

