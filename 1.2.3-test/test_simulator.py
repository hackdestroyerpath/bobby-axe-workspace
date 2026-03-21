from pathlib import Path
import json

from simulator import PaperExecutionSimulator
from market_data import Candle
from agent import BobbyAxelrodAgent
from grid_strategy import Decision
from risk import build_risk_engine
from runner import BobbyReadiness, BobbyRunnerSummary


def test_long_grid_roundtrip():
    state = {
        'daily_pnl_usd': 0.0,
        'loss_streak': 0,
        'open_positions': 0,
        'paper': {
            'inventory': {'side': 'FLAT', 'qty': 0.0, 'avg_entry': 0.0},
            'realized_pnl_usd': 0.0,
            'unrealized_pnl_usd': 0.0,
            'fills_count': 0,
            'last_fill_time': ''
        }
    }
    grid = {'regime': 'LONG_GRID', 'center': 100.0, 'spacing': 1.0, 'levels': 3, 'qty_per_level': 2.0, 'invalidation': 96.0}
    sim = PaperExecutionSimulator()

    fills1 = sim.simulate_candle('BTCUSDC', Candle('t1', 100, 100.5, 98.8, 99.5, 1), grid, state)
    assert len(fills1) == 1
    assert state['paper']['inventory']['side'] == 'LONG'
    assert state['open_positions'] == 1

    exit_grid = {'regime': 'SHORT_GRID', 'center': 100.0, 'spacing': 1.0, 'levels': 2, 'qty_per_level': 2.0, 'invalidation': 110.0}
    fills2 = sim.simulate_candle('BTCUSDC', Candle('t2', 99.5, 101.2, 99.4, 101.0, 1), exit_grid, state)
    assert len(fills2) >= 1
    assert any(fill.note == 'long reduce' for fill in fills2)
    assert state['paper']['realized_pnl_usd'] == 4.0
    assert state['loss_streak'] == 0


def test_invalidation_flattens_and_counts_loss():
    state = {
        'daily_pnl_usd': 0.0,
        'loss_streak': 0,
        'open_positions': 1,
        'paper': {
            'inventory': {'side': 'LONG', 'qty': 2.0, 'avg_entry': 100.0},
            'realized_pnl_usd': 0.0,
            'unrealized_pnl_usd': 0.0,
            'fills_count': 0,
            'last_fill_time': ''
        }
    }
    grid = {'regime': 'LONG_GRID', 'center': 100.0, 'spacing': 1.0, 'levels': 3, 'qty_per_level': 2.0, 'invalidation': 97.0}
    sim = PaperExecutionSimulator()

    fills = sim.simulate_candle('BTCUSDC', Candle('t3', 99.0, 99.5, 96.5, 96.8, 1), grid, state)
    assert len(fills) == 1
    assert fills[0].note == 'grid invalidation'
    assert state['paper']['inventory']['side'] == 'FLAT'
    assert state['loss_streak'] == 1
    assert state['paper']['realized_pnl_usd'] == -6.0


def test_multi_symbol_evaluate_many():
    agent = BobbyAxelrodAgent('config.json')
    agent.state = agent.journal.load_state()
    payloads = json.loads(Path('multi_snapshot.json').read_text())
    decisions = agent.evaluate_many(payloads)

    assert len(decisions) == 2
    assert {d.symbol for d in decisions} == {'BTCUSDC', 'ETHUSDC'}
    assert 'symbol_decisions' in agent.state
    assert 'BTCUSDC' in agent.state['symbol_decisions']
    assert 'ETHUSDC' in agent.state['symbol_decisions']
    assert isinstance(agent.state.get('last_scan'), list)


def test_btc_symbol_override_marks_economics_infeasible_when_account_too_small():
    cfg = json.loads(Path('config.json').read_text())
    engine = build_risk_engine(cfg)
    try:
        engine.build_grid_plan('BTCUSDC', 'LONG_GRID', 84210.9, 50.0, 6)
        raise AssertionError('Expected economics infeasible error for BTCUSDC')
    except ValueError as exc:
        assert 'economics infeasible' in str(exc).lower()


def test_readiness_output_present():
    agent = BobbyAxelrodAgent('config.json')
    agent.state = agent.journal.load_state()
    payloads = json.loads(Path('multi_snapshot.json').read_text())
    decisions = agent.evaluate_many(payloads)
    readiness = BobbyReadiness.build(decisions, agent.state)
    assert readiness.startswith('readiness=')
    assert 'ready_symbols=' in readiness


def test_runner_summary_marks_economics_blocker():
    decisions = [
        Decision(
            time='2026-03-20T15:00:00Z',
            symbol='BTCUSDC',
            state='NO_TRADE',
            regime='LONG_GRID',
            confidence='LOW',
            reason='Grid economics infeasible for BTCUSDC: exchange filters require about 100.00 USD per level.',
            grid_plan=None,
        ),
        Decision(
            time='2026-03-20T15:00:00Z',
            symbol='ETHUSDC',
            state='GRID_READY',
            regime='NEUTRAL_GRID',
            confidence='LOW',
            reason='Range structure detected.',
            grid_plan=None,
        ),
    ]
    state = {
        'paper_summary': {
            'inventory_side': 'FLAT',
            'realized_pnl_usd': 0.0,
            'unrealized_pnl_usd': 0.0,
            'fills_count': 0,
        }
    }
    summary = BobbyRunnerSummary.build(decisions, state)
    assert 'economics_blocked=BTCUSDC' in summary


def test_daily_lock_clears_active_grids():
    agent = BobbyAxelrodAgent('config.json')
    agent.state = {
        'daily_pnl_usd': 0.0,
        'loss_streak': 0,
        'open_positions': 0,
        'paper': {
            'inventory': {'side': 'FLAT', 'qty': 0.0, 'avg_entry': 0.0},
            'realized_pnl_usd': 0.0,
            'unrealized_pnl_usd': 0.0,
            'fills_count': 0,
            'last_fill_time': ''
        },
        'active_grid': {'symbol': 'BTCUSDC'},
        'active_grids': {
            'BTCUSDC': {'symbol': 'BTCUSDC'},
            'ETHUSDC': {'symbol': 'ETHUSDC'}
        }
    }
    decision = Decision(
        time='2026-03-20T14:55:00Z',
        symbol='BTCUSDC',
        state='DAILY_LOCK',
        regime='NO_TRADE',
        confidence='LOW',
        reason='risk lock',
        grid_plan=None,
    )

    agent._update_state(decision)

    assert agent.state['lock_status'] is True
    assert agent.state['active_grids'] == {}
    assert agent.state['active_grid'] is None


def test_no_trade_clears_stale_grid_without_inventory():
    agent = BobbyAxelrodAgent('config.json')
    agent.state = {
        'daily_pnl_usd': 0.0,
        'loss_streak': 0,
        'open_positions': 0,
        'paper': {
            'inventory': {'side': 'FLAT', 'qty': 0.0, 'avg_entry': 0.0},
            'realized_pnl_usd': 0.0,
            'unrealized_pnl_usd': 0.0,
            'fills_count': 0,
            'last_fill_time': ''
        },
        'active_grid': {'symbol': 'BTCUSDC'},
        'active_grids': {
            'BTCUSDC': {'symbol': 'BTCUSDC'}
        }
    }
    decision = Decision(
        time='2026-03-20T14:56:00Z',
        symbol='BTCUSDC',
        state='NO_TRADE',
        regime='NO_TRADE',
        confidence='LOW',
        reason='filter reject',
        grid_plan=None,
    )

    agent._update_state(decision)

    assert agent.state['lock_status'] is False
    assert agent.state['active_grids'] == {}
    assert agent.state['active_grid'] is None


def test_foreign_symbol_grid_does_not_replace_inventory_management_context():
    agent = BobbyAxelrodAgent('config.json')
    existing_grid = {'symbol': 'BTCUSDC', 'regime': 'LONG_GRID'}
    agent.state = {
        'daily_pnl_usd': 0.0,
        'loss_streak': 0,
        'open_positions': 1,
        'paper': {
            'inventory': {'symbol': 'BTCUSDC', 'side': 'LONG', 'qty': 0.001, 'avg_entry': 84000.0},
            'realized_pnl_usd': 0.0,
            'unrealized_pnl_usd': 0.0,
            'fills_count': 1,
            'last_fill_time': '2026-03-20T14:50:00Z'
        },
        'active_grid': existing_grid.copy(),
        'active_grids': {
            'BTCUSDC': existing_grid.copy()
        }
    }
    foreign_plan = build_risk_engine(json.loads(Path('config.json').read_text())).build_grid_plan(
        'ETHUSDC', 'SHORT_GRID', 2100.0, 2.0, 6
    )
    decision = Decision(
        time='2026-03-20T14:57:00Z',
        symbol='ETHUSDC',
        state='GRID_READY',
        regime='SHORT_GRID',
        confidence=foreign_plan.confidence,
        reason='candidate grid',
        grid_plan=foreign_plan,
    )

    agent._update_state(decision)

    assert 'ETHUSDC' not in agent.state['active_grids']
    assert agent.state['active_grids']['BTCUSDC']['symbol'] == 'BTCUSDC'
    assert agent.state['active_grid']['symbol'] == 'BTCUSDC'


def test_foreign_symbol_mark_does_not_distort_unrealized_pnl():
    simulator = PaperExecutionSimulator()
    state = {
        'daily_pnl_usd': -0.5,
        'loss_streak': 0,
        'open_positions': 1,
        'paper': {
            'inventory': {'symbol': 'ETHUSDC', 'side': 'SHORT', 'qty': 0.021, 'avg_entry': 2127.5},
            'realized_pnl_usd': 0.0,
            'unrealized_pnl_usd': -0.5,
            'fills_count': 1,
            'last_fill_time': '2026-03-20T20:37:00Z',
            'last_realized_pnl_usd': 0.0,
            'last_event': 'mark_only'
        },
        'active_grid': None,
        'active_grids': {}
    }

    fills = simulator.simulate_candle(
        'BTCUSDC',
        Candle('2026-03-21T08:12:00Z', 84200.0, 84300.0, 84150.0, 84250.0, 1),
        None,
        state,
    )

    assert fills == []
    assert state['paper']['unrealized_pnl_usd'] == -0.5
    assert state['daily_pnl_usd'] == -0.5
    assert state['open_positions'] == 1


def test_no_trade_after_invalidation_repoints_to_other_ready_symbol():
    agent = BobbyAxelrodAgent('config.json')
    btc_grid = {'symbol': 'BTCUSDC', 'regime': 'LONG_GRID'}
    eth_grid = {'symbol': 'ETHUSDC', 'regime': 'SHORT_GRID'}
    agent.state = {
        'daily_pnl_usd': -6.0,
        'loss_streak': 1,
        'open_positions': 0,
        'paper': {
            'inventory': {'side': 'FLAT', 'qty': 0.0, 'avg_entry': 0.0},
            'realized_pnl_usd': -6.0,
            'unrealized_pnl_usd': 0.0,
            'fills_count': 1,
            'last_fill_time': '2026-03-20T14:58:00Z',
            'last_realized_pnl_usd': -6.0,
            'last_event': 'grid invalidation'
        },
        'active_grid': btc_grid.copy(),
        'active_grids': {
            'BTCUSDC': btc_grid.copy(),
            'ETHUSDC': eth_grid.copy(),
        }
    }
    decision = Decision(
        time='2026-03-20T14:59:00Z',
        symbol='BTCUSDC',
        state='NO_TRADE',
        regime='NO_TRADE',
        confidence='LOW',
        reason='post invalidation reset',
        grid_plan=None,
    )

    agent._update_state(decision)

    assert 'BTCUSDC' not in agent.state['active_grids']
    assert agent.state['active_grids']['ETHUSDC']['symbol'] == 'ETHUSDC'
    assert agent.state['active_grid']['symbol'] == 'ETHUSDC'


def test_invalidation_cleanup_then_same_symbol_rearms_grid():
    agent = BobbyAxelrodAgent('config.json')
    initial_grid = {
        'symbol': 'BTCUSDC',
        'regime': 'LONG_GRID',
        'center': 100.0,
        'spacing': 1.0,
        'levels': 3,
        'qty_per_level': 2.0,
        'invalidation': 97.0,
    }
    agent.state = {
        'daily_pnl_usd': 0.0,
        'loss_streak': 0,
        'open_positions': 1,
        'paper': {
            'inventory': {'side': 'LONG', 'qty': 2.0, 'avg_entry': 100.0},
            'realized_pnl_usd': 0.0,
            'unrealized_pnl_usd': 0.0,
            'fills_count': 0,
            'last_fill_time': '',
            'last_realized_pnl_usd': 0.0,
            'last_event': ''
        },
        'active_grid': initial_grid.copy(),
        'active_grids': {
            'BTCUSDC': initial_grid.copy(),
        }
    }

    fills = agent.simulator.simulate_candle(
        'BTCUSDC',
        Candle('2026-03-20T15:00:00Z', 99.0, 99.5, 96.5, 96.8, 1),
        initial_grid,
        agent.state,
    )

    assert len(fills) == 1
    assert fills[0].note == 'grid invalidation'
    assert agent.state['paper']['inventory']['side'] == 'FLAT'
    assert agent.state['open_positions'] == 0
    assert agent.state['paper']['last_event'] == 'grid invalidation'

    reset_decision = Decision(
        time='2026-03-20T15:01:00Z',
        symbol='BTCUSDC',
        state='NO_TRADE',
        regime='NO_TRADE',
        confidence='LOW',
        reason='post invalidation reset',
        grid_plan=None,
    )
    agent._update_state(reset_decision)

    assert agent.state['active_grids'] == {}
    assert agent.state['active_grid'] is None

    rearm_plan = build_risk_engine(json.loads(Path('config.json').read_text())).build_grid_plan(
        'BTCUSDC', 'LONG_GRID', 101.0, 1.0, 2
    )
    rearm_decision = Decision(
        time='2026-03-20T15:02:00Z',
        symbol='BTCUSDC',
        state='GRID_READY',
        regime='LONG_GRID',
        confidence=rearm_plan.confidence,
        reason='re-arm after invalidation cleanup',
        grid_plan=rearm_plan,
    )
    agent._update_state(rearm_decision)

    assert agent.state['active_grids']['BTCUSDC']['symbol'] == 'BTCUSDC'
    assert agent.state['active_grids']['BTCUSDC']['regime'] == 'LONG_GRID'
    assert agent.state['active_grid']['symbol'] == 'BTCUSDC'
    assert agent.state['lock_status'] is False


if __name__ == '__main__':
    test_long_grid_roundtrip()
    test_invalidation_flattens_and_counts_loss()
    test_multi_symbol_evaluate_many()
    test_btc_symbol_override_marks_economics_infeasible_when_account_too_small()
    test_runner_summary_marks_economics_blocker()
    test_readiness_output_present()
    test_daily_lock_clears_active_grids()
    test_no_trade_clears_stale_grid_without_inventory()
    test_foreign_symbol_grid_does_not_replace_inventory_management_context()
    test_foreign_symbol_mark_does_not_distort_unrealized_pnl()
    test_no_trade_after_invalidation_repoints_to_other_ready_symbol()
    test_invalidation_cleanup_then_same_symbol_rearms_grid()
    print('ok')
