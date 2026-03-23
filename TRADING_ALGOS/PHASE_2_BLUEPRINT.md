# PHASE 2 BLUEPRINT

Этот документ фиксирует cross-cutting артефакты Phase 2, чтобы 12 машин поднимались поверх Phase 1 без operational drift.

Closing artifact по итогам всей фазы вынесен в `TRADING_ALGOS/PHASE_2_REPORT.md`.

## 1. Machine registry

Единый frozen registry живёт в `TRADING_ALGOS/machine_registry.py`.

Для каждой из 12 машин зафиксированы:
- `machine_id`
- `agent_id`
- `strategy`
- `timeframe`
- `human_name`
- `input_timeframe_target`
- `primary_output_packet`
- `runtime_entrypoint`
- `api_key_id`
- `build_version_policy`
- `owner`
- `warmup`
- `confidence_downgrade_rules`
- `retryable_failure_codes`

Это означает, что `RSI_MACD_1M` и `RSI_MACD_60M` — разные operational machines, но не разные business-formula forks.

## 2. Common runtime pipeline

Канонический lifecycle закреплён в `TRADING_ALGOS/runtime_contract.py` и реализован в `TRADING_ALGOS/machines.py`.

Порядок обязателен для всех 12 машин:
1. принять request по общему schema;
2. проверить обязательные поля и связку request ↔ machine registry;
3. проверить partial window на уровне shared normalization contract;
4. читать тики только через frozen input window;
5. прогонять сырые тики через `common/tick_normalizer.py`;
6. строить candles и shared microstructure через `common/tick_to_features_engine.py`;
7. считать только strategy-specific indicators;
8. собрать `summary` через общую policy;
9. выставить `status`, `meta` и `errors` без локального переименования причин;
10. вернуть единый response packet.

Запрещено:
- прямое чтение таблиц из strategy-layer;
- локальный пересчёт quality flags, уже зафиксированных shared runtime;
- переопределение `status` в отрыве от `meta.is_partial`, `partial_reason` и `errors`.

## 3. Partial-data policy

Для всех 12 машин policy одна и та же:
- `ready` — окно полное, shared pipeline не зафиксировал деградацию;
- `partial` — стратегия может быть посчитана, но shared pipeline зафиксировал `retention_truncation`, `pagination_truncation` или `gap_heavy_window`;
- `error` — окно пустое (`empty_window`) либо strict-mode запретил деградированный расчёт.

Причины partial транслируются дальше без переименования:
- `retention_truncation`
- `pagination_truncation`
- `empty_window`
- `gap_heavy_window`

Operational discipline:
- `retention_truncation` никогда не маскируется под `ready`;
- `pagination_truncation` всегда остаётся видимой для orchestration;
- `empty_window` не превращается в нейтральный market opinion;
- `gap_heavy_window` снижает confidence и добавляет явную runtime anomaly.

## 4. Warmup policy

Warmup зафиксирован в registry и обязателен для каждой family/timeframe пары.

Принцип:
- `minimum_window` — нижний operational порог;
- `recommended_window` — безопасный рабочий диапазон для runtime;
- `minimum_valid_candles` — минимальное число свечей для usable output;
- `insufficient_warmup_status` — default reaction на недобор истории.

Family comments:
- `RSI_MACD` требует историю не только для RSI(14), но и для устойчивого MACD/EMA состояния.
- `LEVELS_FIBO_HV` требует диапазон для swing detection и volume profile.
- `VOLUME` не может делать уверенные выводы без baseline relative volume.
- `ELLIOTT` остаётся самым консервативным и history-hungry семейством.

## 5. Summary generation rules

`summary` строится в `build_summary()` на базе family-specific feature payload и shared quality flags.

Общие правила:
- `summary.state` — family-specific state, сведённый к общему language layer;
- `summary.strength` — family-specific strength, сведённый к `weak / medium / strong`;
- `summary.confidence` — default по family, но capped quality flags;
- `summary.note` — обязан содержать strategy-specific explanation и quality suffix при деградации.

## 6. Shared family cores

Shared reusable modules живут в `TRADING_ALGOS/strategy_cores.py`:
- `compute_rsi_macd()`
- `compute_levels_fibo_hv()`
- `compute_volume()`
- `compute_elliott()`

Это единые compute layers для 1m / 5m / 60m. Timeframe меняет только входной candle stream, а не business logic.

## 7. 12 runtime wrappers

Runtime wrappers живут в `TRADING_ALGOS/machines.py`.

Подняты 4 entrypoint-группы:
- `execute_rsi_macd_machine()`
- `execute_levels_fibo_hv_machine()`
- `execute_volume_machine()`
- `execute_elliott_machine()`

Каждый wrapper:
- читает spec из machine registry;
- использует общий runtime contract;
- считает признаки только через shared family-core;
- возвращает единый response format.

## 8. Failure modes and traceability

Общий failure-mode matrix и traceability rules зафиксированы в `TRADING_ALGOS/runtime_contract.py`.

Каждый ответ стабильно несёт:
- `response_contract_version`
- `machine_id`
- `api_key_id`
- `build_version`
- `source_contract_version`
- `data_points`
- `coverage_ratio`
- `is_partial`
- `partial_reason`

## 9. Ben_Kim orchestration readiness

Следующая фаза описана в `TRADING_ALGOS/BEN_KIM_ORCHESTRATION_CONTRACT.md`.

Ben_Kim должен:
- адресовать машины только по frozen registry;
- различать `ready / partial / error` без локальных догадок;
- ретраить только retryable failures;
- читать `60m` как context anchor, `5m` как confirmation, `1m` как tactical layer;
- low-confidence Elliott использовать только как candidate context, а не как final signal.
