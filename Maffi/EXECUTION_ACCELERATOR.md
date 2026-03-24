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

Primary-контур Phase 1 (runtime path):

- `llm_happy_path` → `prompt -> route -> llm -> validator -> finalize -> final response(status=ok)`
- `llm_fallback_path` → `prompt -> route -> llm -> validator -> fallback -> finalize -> final response(status=fallback)`
- `llm_reject_path` → `prompt -> route -> llm -> validator -> fallback/retry -> finalize -> final response(status=reject)`

В каждом LLM-сценарии acceptance явно валидирует поля `FinalNormalizedResponse`:
`status`, `ticker`, `timeframe`, `direction`, `model_id`, `prompt_version`, `validator_summary`, `trace`.

Legacy compatibility smoke (`decide` + `deterministic_replay`) остаётся опциональным и запускается отдельным флагом.

## Команды оператора

```bash
python -m Maffi.runtime.acceptance_suite
python -m Maffi.runtime.acceptance_suite --json
python -m Maffi.runtime.acceptance_suite --with-legacy
```

## Правило go/no-go

`GO` только если одновременно:

- acceptance suite вернул `ACCEPTANCE_SUITE_OK`
- в секции `llm_flow` нет сценариев с `passed=false`

`NO-GO`, если хотя бы один критерий нарушен.

Примечание: `legacy_compat` — не primary-критерий Phase 1; используется как дополнительный smoke-check при необходимости.

## Формат короткого отчёта Bobby -> MAXIMUS

- What done: smoke suite выполнен, статус `GO|NO-GO`
- What active: следующий шаг по runtime/validator
- What blocked: сценарий/ошибка/причина
- Recommended next move: конкретный фикс и owner

## Минимальный SLA на реакцию

- Падение acceptance-smoke: triage в течение 15 минут
- Исправление критического fail перед production: в текущем рабочем цикле
- Повторный smoke после фикса: обязателен
