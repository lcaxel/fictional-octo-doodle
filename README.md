# CS2 Big Data Intelligence Platform

Платформа для глубокого анализа демо-файлов CS2. Извлекает все релевантные данные для построения аналитической системы уровня "Bloomberg для киберспорта".

## Quick Start

### 1. Установка зависимостей

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Или установить заново
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Скачать демку

Поместите `.dem` файл в папку `demos/`:

**Источники демо-файлов:**
- [HLTV.org](https://www.hltv.org/matches) - профессиональные матчи
- CS2 -> Watch -> Your Matches - ваши матчи
- [FACEIT](https://faceit.com) - фасит матчи

### 3. Запустить парсинг

```bash
# Шаг 1: Исследовать содержимое демки
python scripts/02_explore_demo.py

# Шаг 2: Извлечь все данные
python scripts/03_extract_data.py

# Шаг 3: Посмотреть аналитику
python scripts/04_analyze_data.py
```

## Структура проекта

```
.
├── demos/              # Здесь хранятся .dem файлы
├── data/               # Извлечённые данные (JSON, CSV)
├── scripts/
│   ├── 01_download_demo.py     # Инструкции по скачиванию
│   ├── 02_explore_demo.py      # Исследование структуры демки
│   ├── 03_extract_data.py      # Основной парсер
│   └── 04_analyze_data.py      # Анализ данных
├── notebooks/          # Jupyter notebooks для исследований
├── requirements.txt    # Python зависимости
└── README.md
```

## Извлекаемые данные

### Layer 1: События (Events)
| Категория | Данные |
|-----------|--------|
| Kills | attacker, victim, weapon, headshot, distance, positions |
| Damage | attacker, victim, damage, hitgroup, weapon |
| Grenades | type, thrower, position, affected players |
| Bomb | plant/defuse/explode, player, position, site |
| Rounds | winner, reason, duration |
| Economy | money, equipment, weapons per player per round |

### Layer 2: Deep Metrics (рассчитываются)
- ADR (Average Damage per Round)
- K/D Ratio
- Headshot %
- First Kill stats
- Opening duels
- Trade kills
- Utility usage

## Следующие шаги

1. **Batch Processing** - парсинг 15,000+ демо-файлов
2. **Database Schema** - Supabase/PostgreSQL схема
3. **HLTV Integration** - автоматическое скачивание демок
4. **Advanced Metrics** - Time to Damage, Crosshair Placement
5. **Predictive Engine** - ML модели для прогнозов

## Технологии

- **demoparser2** - парсинг CS2 демо-файлов
- **pandas** - обработка данных
- **Supabase** - база данных (планируется)
- **ClickHouse** - Data Lake для больших объёмов (планируется)
