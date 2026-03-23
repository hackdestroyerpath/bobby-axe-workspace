"""Trading algorithms shared modules and Phase 2 runtime assets."""

from .machine_registry import MACHINE_REGISTRY, MachineSpec, WarmupSpec, get_machine_spec
from .machines import (
    MachineExecutor,
    execute_elliott_machine,
    execute_levels_fibo_hv_machine,
    execute_rsi_macd_machine,
    execute_volume_machine,
)
from .runtime_contract import (
    BEN_KIM_ORCHESTRATION_EXPECTATIONS,
    FAILURE_MODE_MATRIX,
    STATUS_ERROR,
    STATUS_PARTIAL,
    STATUS_READY,
)
from .strategy_cores import (
    StrategyComputation,
    compute_elliott,
    compute_levels_fibo_hv,
    compute_rsi_macd,
    compute_volume,
)

__all__ = [
    "BEN_KIM_ORCHESTRATION_EXPECTATIONS",
    "FAILURE_MODE_MATRIX",
    "MACHINE_REGISTRY",
    "MachineExecutor",
    "MachineSpec",
    "STATUS_ERROR",
    "STATUS_PARTIAL",
    "STATUS_READY",
    "StrategyComputation",
    "WarmupSpec",
    "compute_elliott",
    "compute_levels_fibo_hv",
    "compute_rsi_macd",
    "compute_volume",
    "execute_elliott_machine",
    "execute_levels_fibo_hv_machine",
    "execute_rsi_macd_machine",
    "execute_volume_machine",
    "get_machine_spec",
]
