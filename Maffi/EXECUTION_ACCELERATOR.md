# Maffi Execution Accelerator

Статус: `active`  
Дата: `2026-03-24`

## Зачем нужен этот файл

Этот документ закрывает операционный разрыв между описанным `TODO` и реальным ежедневным execution-cycle.

Цель: дать Maffi быстрый и однозначный контур «что запускать / что считать сигналом готовности / как эскалировать» без длинной переписки.

## Управленческий цикл (один run)

1. Проверить, что входной payload валиден и не деградировал до `bad`.
2. Прогнать сценарии acceptance-smoke.
3. Зафиксировать результат запуска и причину reject (если есть).
4. Если smoke упал — не пропускать в production handoff.

## Acceptance smoke (быстрый контур)

Новый исполняемый артефакт:

- `Maffi/runtime/acceptance_suite.py`

Покрываемые сценарии:

- `healthy_long` → ожидается `long`
- `healthy_short` → ожидается `short`
- `weak_confidence` → ожидается `reject`
- `chaotic_market` → ожидается `reject`
- `invalid_payload` → ожидается `reject` + invalid

Также в каждом сценарии проверяется детерминизм (`deterministic_replay`) для одинакового timestamp override.

## Команды оператора

```bash
python -m Maffi.runtime.acceptance_suite
python -m Maffi.runtime.acceptance_suite --json
```

## Правило go/no-go

`GO` только если одновременно:

- acceptance suite вернул `ACCEPTANCE_SUITE_OK`
- нет сценариев с `passed=false`
- нет расхождения replay (`replay_equal=false`)

`NO-GO`, если хотя бы один критерий нарушен.

## Формат короткого отчёта Bobby -> MAXIMUS

- What done: smoke suite выполнен, статус `GO|NO-GO`
- What active: следующий шаг по runtime/validator
- What blocked: сценарий/ошибка/причина
- Recommended next move: конкретный фикс и owner

## Минимальный SLA на реакцию

- Падение acceptance-smoke: triage в течение 15 минут
- Исправление критического fail перед production: в текущем рабочем цикле
- Повторный smoke после фикса: обязателен
