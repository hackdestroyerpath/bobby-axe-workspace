# Output specification

## Status
Accepted.

## Purpose
Этот документ фиксирует канонический состав пользовательских выходов OpenClaw для агента `Jusetta` и управляющего executive summary от `Bobby Axe`.

Спецификация нужна для того, чтобы:

- все типы отчётов имели единый словарь и ожидаемую структуру;
- PDF, табличные артефакты и краткие сводки собирались из одних и тех же upstream-данных;
- downstream-поиск, архивирование и аудит работали по детерминированным именам файлов;
- пользователь получал одинаково устроенный результат независимо от канала доставки.

Документ дополняет `contracts/jusetta.md`, `contracts/schemas/report_job.schema.json`, а также роли `Jusetta`, `Bobby Axe`, `Maffi` и `1$_Dollar_Bill`.

---

## 1. Supported report types

Система обязана поддерживать четыре типа пользовательских отчётов.

### 1.1. `live_snapshot`

Назначение: быстрый срез по текущему окну для оперативного чтения.

Когда используется:

- ad-hoc запрос пользователя;
- внутридневной просмотр без ожидания полного периода;
- ручная проверка состояния стратегий, сеток и аллокаций.

Требования:

- строится по одному актуальному окну `report_period`;
- может содержать только последние доступные результаты без исторического сравнения за длинный период;
- обязан включать executive summary и краткую сводку по тикерам;
- графики допускаются в компактном формате, но обязательные таблицы не могут быть пропущены.

### 1.2. `periodic_report`

Назначение: плановый отчёт за фиксированный период.

Когда используется:

- регулярный выпуск по расписанию;
- закрытие смены, дня или иного согласованного окна;
- архивируемый отчёт для последующего сравнения выпусков.

Требования:

- должен охватывать полный интервал `report_period.from -> report_period.to`;
- обязан содержать агрегированный executive summary, полный блок по тикерам и секцию изменений относительно начала периода;
- исторические графики и таблицы обязательны в полном объёме;
- должен быть пригоден для долгосрочного хранения как основной архивный PDF.

### 1.3. `exception_report`

Назначение: отчёт по отклонению, рисковому событию или нарушению пайплайна.

Когда используется:

- отсутствуют обязательные upstream-артефакты;
- стратегия, сетка или аллокация были отклонены;
- сработали лимиты risk framework;
- произошла ошибка рендера, доставки или несогласованность окна.

Требования:

- первым экраном/разделом должен показывать характер исключения и его влияние;
- обязан явно перечислять, что готово, что отсутствует и что было заблокировано;
- вместо нормального пользовательского повествования должен содержать формализованный блок `Issue / Impact / Required Action`;
- если финансовые выводы неполные, отчёт должен явно маркироваться как непригодный для торгового исполнения.

### 1.4. `portfolio_allocation_report`

Назначение: отдельный отчёт, центрированный на распределении капитала по тикерам и риск-бакетам.

Когда используется:

- пользователь хочет увидеть именно результат работы `1$_Dollar_Bill`;
- требуется сравнение целевых долей по инструментам;
- нужно объяснить, почему часть тикеров получила больший или меньший вес.

Требования:

- главным содержанием являются аллокации, лимиты и риск-обоснование;
- для каждого тикера обязательно показываются `Maffi`-направление, доля капитала и ключевые риски;
- должен включать как минимум одну визуализацию структуры портфеля;
- если сумма `ready`-аллокаций не равна `100.0`, отчёт выпускается только как `exception_report`, а не как валидный allocation report.

---

## 2. Canonical report package

Каждый пользовательский выпуск должен рассматриваться как пакет артефактов, а не как одиночный PDF.

### 2.1. Обязательные артефакты пакета

Для любого типа отчёта пакет должен включать:

- `report_job` с метаданными сборки и публикации;
- основной PDF от `Jusetta`;
- табличный артефакт (`csv` или `xlsx`) со сводкой по тикерам;
- отдельный executive summary от `Bobby Axe` по пути `artifacts.summary_path`;
- manifest-файл по пути `artifacts.manifest_path`.

Если executive summary вставляется в PDF, это **не отменяет** обязанность хранить его как отдельный артефакт пакета.

### 2.2. Связность пакета

Все артефакты одного выпуска должны:

- иметь общий `correlation_id`;
- ссылаться на один и тот же `report_period`;
- использовать одинаковый список `symbols` и один `report_type`;
- быть построены только из согласованных upstream-результатов одного запуска или одного осознанного batched-run.

### 2.3. Обязательные поля `report_job`

`report_job` обязан фиксировать как минимум:

- `event_type = report_job`;
- `job_id`;
- `correlation_id`;
- `report_type`;
- `requested_at`;
- `generated_at_utc`;
- `report_period.from` и `report_period.to`;
- `symbols`;
- `artifacts.pdf_path`;
- `artifacts.table_path`;
- `artifacts.summary_path`;
- `artifacts.manifest_path`;
- `delivery.channel`;
- `status`.

Опционально `report_job` может содержать:

- `pipeline_status` — агрегированную оценку готовности upstream-цепочки (`ready` | `partial` | `blocked`);
- `decision` — управленческий итог (`publish` | `informational_only` | `revision_required` | `escalate`).

### 2.4. Канонический enum статусов `Jusetta`

Единый enum `report_job.status`:

- `queued`;
- `running`;
- `ready`;
- `rejected`;
- `error`.

Интерпретация:

- только `ready` считается publishable-статусом package;
- `queued` и `running` описывают незавершённую сборку;
- `rejected` описывает бизнес-блокировку публикации;
- `error` описывает технический сбой публикации.

### 2.5. Что значит publishable

Package считается publishable, если одновременно выполнены условия:

1. `report_job.status = ready`;
2. все обязательные артефакты существуют по `pdf_path`, `table_path`, `summary_path`, `manifest_path`;
3. если поле `decision` присутствует, оно равно `publish` или `informational_only`;
4. manifest и executive summary согласованы по `correlation_id`, `report_type`, окну и итоговому решению.

`decision = informational_only` означает, что выпуск допустим к доставке пользователю, но не должен трактоваться как торгово-исполняемый релиз.

---

## 3. What the PDF from `Jusetta` must contain

PDF является обязательным пользовательским артефактом для каждого publishable `report_job`.

### 3.1. Required cover metadata

На титульной странице или в верхнем блоке первой страницы должны присутствовать:

- название отчёта;
- `report_type`;
- `job_id`;
- `correlation_id`;
- период отчёта: `from` / `to` в UTC;
- список включённых `symbols`;
- `generated_at_utc` в UTC;
- канал доставки или целевой получатель, если это применимо.

### 3.2. Mandatory sections of the PDF

В PDF обязательно должны быть следующие разделы и именно в таком логическом порядке:

1. **Executive summary** от `Bobby Axe`.
2. **Pipeline status** — краткий статус готовности данных, аналитики, сеток, аллокаций и самого отчёта.
3. **Portfolio overview** — сводный раздел по направлениям, итоговым сигналам и капиталу.
4. **Ticker breakdown** — детальная секция по каждому инструменту.
5. **Risks and exceptions** — ключевые риски, ограничения и отклонения.
6. **Artifacts and traceability** — ссылки/пути на связанные артефакты, включая отдельные `table`, `summary` и `manifest`.

### 3.3. Required content inside the PDF

Независимо от типа отчёта PDF должен содержать:

- краткую цель выпуска;
- статус готовности upstream-этапов: `Ben_Kim`, `Maffi`, `1$_Dollar_Bill`, `Jusetta`;
- агрегированную таблицу по всем тикерам;
- отдельный блок по каждому тикеру с канонической сводкой;
- блок риск-комментариев и ограничений;
- явно выраженный итог: публикация допустима / публикация только для информации / требуется эскалация.

### 3.4. Type-specific PDF emphasis

#### Для `live_snapshot`
- первый экран должен помещаться на 1 страницу без необходимости листать ради ключевого решения;
- детальные приложения допускаются, но не должны раздувать основной narrative;
- в центре — текущее состояние, а не длинная история.

#### Для `periodic_report`
- обязателен раздел изменений за период;
- для каждого тикера желательно указывать состояние на конец периода и изменение относительно начала периода;
- приложения с графиками и таблицами должны быть полными.

#### Для `exception_report`
- на первой странице должна быть заметная маркировка `EXCEPTION REPORT`;
- текст причины исключения должен быть кратким и однозначным;
- недостающие артефакты перечисляются явно, без попытки скрыть пробелы.

#### Для `portfolio_allocation_report`
- PDF должен начинаться с структуры распределения капитала;
- объяснение лимитов и риск-бакетов является обязательным содержанием первой половины отчёта;
- детализация стратегий должна подчиняться задаче объяснения аллокации, а не заменять её.

---

## 4. Executive summary that `Bobby Axe` must produce

`Bobby Axe` обязан выпускать краткий executive summary как самостоятельный артефакт, который затем вставляется в PDF и сохраняется рядом как отдельный файл по `artifacts.summary_path`.

### 4.1. Purpose of the executive summary

Executive summary нужен, чтобы пользователь за 30–60 секунд понял:

- что произошло в рассматриваемом окне;
- какие направления по тикерам доминируют;
- можно ли доверять выпуску;
- как распределён капитал;
- какие риски требуют внимания немедленно.

### 4.2. Required size and style

Сводка должна быть:

- краткой: ориентир `5-8` буллетов или `1-2` коротких абзаца;
- управленческой по тону, без лишней микродетализации формул;
- конкретной: с числом тикеров, числом исключений и суммой аллокаций;
- пригодной для вставки в PDF, email и карточку в UI без переписывания.

### 4.3. Mandatory content of the executive summary

Executive summary обязан содержать:

- тип отчёта и окно времени;
- `correlation_id`;
- общее число тикеров в выпуске;
- краткое распределение направлений `Maffi` (`long` / `short` / `rejected` / `n/a`);
- основной вывод по портфелю: risk-on, neutral, defensive или equivalent narrative;
- информацию о суммарной готовности аллокаций и проверке суммы `100.0`, если применимо;
- перечисление `1-3` главных рисков или исключений;
- явное действие/статус: `publish`, `informational_only`, `revision_required`, `escalate`.

### 4.4. Canonical template

Рекомендуемый канонический шаблон executive summary:

```text
[Bobby Axe Executive Summary]
CorrelationId: <correlation_id>
ReportType: <live_snapshot|periodic_report|exception_report|portfolio_allocation_report>
Period: <from> -> <to>
Universe: <N> symbols
Directional mix: <X long / Y short / Z rejected>
Portfolio stance: <risk-on|neutral|defensive>
Allocation status: <ready 100.0% | partial | blocked>
Top risks:
- <risk 1>
- <risk 2>
Decision: <publish|informational_only|revision_required|escalate>
```

### 4.5. Summary quality rules

`Bobby Axe` не должен:

- пересказывать все стратегии по отдельности;
- скрывать отсутствие данных за нейтральными формулировками;
- утверждать готовность публикации, если upstream-артефакты неполны;
- выпускать summary без явного decision line.

---

## 5. Mandatory tables and charts

### 5.1. Tables required for every normal report

Для `live_snapshot`, `periodic_report` и `portfolio_allocation_report` обязательны следующие таблицы:

1. **Portfolio summary table**
   - один ряд на тикер;
   - включает направление, итоговый сигнал, долю капитала и риск.
2. **Pipeline status table**
   - показывает статусы этапов `Ben_Kim`, `Maffi`, `1$_Dollar_Bill`, `Jusetta`.
3. **Ticker detail table**
   - расширенная форма по каждому тикеру с ключевыми фактами и объяснениями.

Для `exception_report` обязательны:

1. **Issue status table**;
2. **Impacted artifacts table**;
3. **Ticker exception table** для всех затронутых тикеров.

### 5.2. Charts required for every normal report

Минимальный набор графиков:

1. **Portfolio allocation chart**
   - pie, donut или bar;
   - показывает `allocation_pct` по тикерам.
2. **Direction distribution chart**
   - bar или stacked bar;
   - показывает число тикеров по направлениям `long`, `short`, `rejected`, `n/a`.
3. **Per-ticker price/grid chart**
   - минимум один график на тикер;
   - должен показывать цену и, если доступно, границы сетки `Maffi`.

### 5.3. Additional chart requirements for periodic reports

Для `periodic_report` дополнительно обязателен хотя бы один исторический график:

- динамика аллокации по тикерам внутри периода; или
- изменение направлений/сигналов по времени; или
- изменение агрегированного риска по периоду.

### 5.4. Chart requirements for exception reports

В `exception_report` графики не являются главным содержанием, но если они включены, они не должны создавать ложное ощущение полноты.

Поэтому:

- графики допускаются только при наличии валидных данных;
- отсутствующие данные должны быть отмечены как `missing`, а не заменены синтетикой;
- если данных недостаточно, таблица исключений важнее графика и не может быть опущена ради красоты.

---

## 6. Required fields in the ticker-level summary

Сводка по тикеру — это канонический блок, который должен присутствовать и в табличном артефакте, и в PDF.

### 6.1. Mandatory fields

Для каждого тикера обязательны следующие поля:

- `ticker` — канонический символ, например `BTCUSDC`;
- `strategy_directions` — направления по стратегиям `Ben_Kim` с агрегацией по таймфреймам;
- `maffi_outcome` — итог `Maffi`: `long`, `short`, `rejected` или `n/a`;
- `dollar_bill_allocation_pct` — аллокация `1$_Dollar_Bill` в процентах;
- `key_risks` — краткий список ключевых рисков по инструменту.

### 6.2. Expanded canonical field set

Чтобы сводка была полезной для пользователя и для поиска, рекомендуется фиксировать расширенный набор полей:

| Field | Required | Description |
| --- | --- | --- |
| `ticker` | Yes | Канонический тикер. |
| `strategy_directions` | Yes | Краткая агрегация направлений по стратегиям и таймфреймам. |
| `maffi_outcome` | Yes | Итоговое решение `Maffi` по тикеру. |
| `dollar_bill_allocation_pct` | Yes | Доля капитала по тикеру в процентах. |
| `key_risks` | Yes | Список главных рисков или ограничений. |
| `ben_kim_signal_count` | Recommended | Число usable-сигналов, попавших в агрегирование. |
| `maffi_confidence` | Recommended | Confidence или качественный маркер уверенности. |
| `risk_bucket` | Recommended | Бакет риска из `1$_Dollar_Bill`. |
| `top_rationale` | Recommended | Одно короткое объяснение, почему тикер получил именно такой итог. |
| `artifact_refs` | Recommended | Ссылки на связанные `analysis_ids`, `proposal_id`, `allocation_id`. |

### 6.3. Canonical formatting rules for the ticker summary

Правила форматирования:

- один тикер = один логический блок сводки;
- `strategy_directions` должен оставаться кратким и читабельным, например `1m: long; 5m: long; 60m: neutral`;
- `maffi_outcome` не подменяется выводами стратегий и остаётся отдельным полем;
- `dollar_bill_allocation_pct` показывается с точностью, совместимой с шагом `0.1%`;
- `key_risks` ограничиваются `1-3` наиболее важными пунктами.

### 6.4. Example ticker summary row

```json
{
  "ticker": "BTCUSDC",
  "strategy_directions": "1m: long; 5m: long; 60m: neutral",
  "maffi_outcome": "long",
  "dollar_bill_allocation_pct": 25.0,
  "key_risks": [
    "5m signal strength weakened versus prior window",
    "High correlation with ETH group concentration"
  ],
  "risk_bucket": "medium"
}
```

---

## 7. File and artifact naming for search and archival

Имена файлов должны позволять искать отчёты по типу, окну, тикерам и `correlation_id` без открытия содержимого.

### 7.1. General naming rules

Для всех артефактов действуют правила:

- использовать только lowercase для префиксов и служебных сегментов имени файла;
- разделитель сегментов — двойное подчёркивание `__`;
- время указывать в UTC в compact-формате `YYYYMMDDThhmmssZ`;
- диапазон окна записывать как `<from>__<to>`;
- множественный список тикеров сворачивать в `universe-<count>` для имени файла, а полный список хранить в manifest;
- `correlation_id` должен входить в имя каждого архивируемого артефакта;
- расширение должно отражать реальный формат: `.pdf`, `.csv`, `.xlsx`, `.json`, `.md`.

### 7.2. Canonical filename pattern

Базовый шаблон имени:

```text
<artifact_kind>__<report_type>__<from_utc>__<to_utc>__<scope>__<correlation_id>__<version>.<ext>
```

Где:

- `artifact_kind` = `pdf`, `table`, `summary`, `manifest`, `issue`;
- `report_type` = один из 4 поддерживаемых типов;
- `scope` = `ticker-<SYMBOL>` или `universe-<N>`;
- `version` = `v1`, `v2`, ... при перевыпуске одного и того же окна.

### 7.3. Required concrete examples

#### PDF

```text
pdf__periodic_report__20260321T110000Z__20260321T121500Z__universe-5__corr-8f3a__v1.pdf
```

#### Table export

```text
table__portfolio_allocation_report__20260321T110000Z__20260321T121500Z__universe-5__corr-8f3a__v1.csv
```

#### Executive summary

```text
summary__live_snapshot__20260321T120000Z__20260321T121500Z__universe-3__corr-8f3a__v1.md
```

#### Manifest

```text
manifest__exception_report__20260321T110000Z__20260321T121500Z__universe-5__corr-8f3a__v1.json
```

### 7.4. Directory layout recommendation

Рекомендуемая раскладка каталогов:

```text
reports/
  <report_type>/
    <YYYY>/
      <MM>/
        <DD>/
          <correlation_id>/
            pdf__...pdf
            table__...csv
            summary__...md
            manifest__...json
```

### 7.5. Manifest contents

Manifest-файл должен содержать минимум:

- `report_type`;
- `job_id`;
- `correlation_id`;
- `generated_at_utc`;
- `report_period.from` и `report_period.to`;
- `symbols`;
- `status`;
- опционально `pipeline_status` и `decision`;
- список артефактов с `kind`, `path`, `producer`, `checksum`, `version` и `embedded_in_pdf` при необходимости;
- признак архивной пригодности: `archivable = true|false`.

Manifest обязан явно перечислять четыре канонических artifact entries:

1. `kind = pdf`, `producer = Jusetta`;
2. `kind = table`, `producer = Jusetta`;
3. `kind = summary`, `producer = Bobby Axe`, при этом `embedded_in_pdf = true` допускается как дополнительный флаг;
4. `kind = manifest`, `producer = Jusetta`.

---

## 8. Acceptance rules for this specification

Выход OpenClaw считается соответствующим данной спецификации, если одновременно выполняются все условия:

1. тип отчёта явно указан и входит в список из четырёх поддерживаемых типов;
2. `report_job` фиксирует `report_type`, `correlation_id`, `generated_at_utc` и пути ко всем четырём артефактам package;
3. `Jusetta` выпускает PDF с обязательными секциями и метаданными;
4. `Bobby Axe` формирует краткий executive summary с decision line и сохраняет его как отдельный артефакт;
5. обязательные таблицы и графики включены либо явно заменены exception-логикой, где это разрешено;
6. по каждому тикеру есть каноническая сводка с обязательными полями;
7. manifest отражает `pdf`, `table`, `summary`, `manifest` и хранит согласованные `status` / `decision`;
8. publishable-выпуск имеет `report_job.status = ready`, а при наличии `decision` — только `publish` или `informational_only`.
