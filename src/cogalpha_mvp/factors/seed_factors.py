"""21 deterministic seed factors - one per agent across 7 levels.

Each factor is a DSL expression that can be evaluated without any LLM API.
These ensure the MVP pipeline can run end-to-end without external dependencies.
"""

from __future__ import annotations

import logging

from cogalpha_mvp.factors.dsl import FactorParser
from cogalpha_mvp.factors.registry import FactorMetadata, FactorRegistry

logger = logging.getLogger("cogalpha_mvp")

# Agent definitions: (agent_id, level, name, economic_rationale)
AGENTS = [
    # Level 1: Market Structure & Cycle
    ("Agent_01", 1, "趋势与周期相位", "长短周期移动平均的相位差刻画牛熊转换"),
    ("Agent_02", 1, "波动率状态", "波动率历史分位数反映市场状态"),
    ("Agent_03", 1, "市场状态转换", "收益率波动比率识别市场状态转换"),
    # Level 2: Extreme Risk & Fragility
    ("Agent_04", 2, "下行风险", "下行波动率衡量下行风险暴露"),
    ("Agent_05", 2, "尾部风险", "最大日跌幅的滚动统计衡量尾部风险"),
    ("Agent_06", 2, "流动性脆弱性", "成交量萎缩率识别流动性脆弱性"),
    # Level 3: Volume-Price Dynamics
    ("Agent_07", 3, "量价协同", "收益与成交量的相关性衡量量价协同"),
    ("Agent_08", 3, "价格冲击", "单位成交量引起的价格变化衡量价格冲击"),
    ("Agent_09", 3, "成交量异常", "成交量偏离均值衡量成交量异常"),
    # Level 4: Price Volatility Behavior
    ("Agent_10", 4, "中期动量", "20日收益率动量"),
    ("Agent_11", 4, "短期反转", "5日收益率反转"),
    ("Agent_12", 4, "波动率聚集", "波动率自相关衡量波动聚集"),
    # Level 5: Multi-scale Complexity
    ("Agent_13", 5, "多尺度趋势", "长短周期趋势差衡量多尺度趋势"),
    ("Agent_14", 5, "长记忆近似", "收益率的长期自相关近似长记忆特征"),
    ("Agent_15", 5, "回撤恢复结构", "距离近期高点的比率衡量回撤恢复"),
    # Level 6: Stability & Regime Control
    ("Agent_16", 6, "时间稳定性", "因子值的滚动自相关衡量时间稳定性"),
    ("Agent_17", 6, "状态条件过滤", "高波动状态下的动量过滤"),
    ("Agent_18", 6, "信号衰减控制", "信号衰减率控制"),
    # Level 7: Geometry & Fusion
    ("Agent_19", 7, "K线几何", "K线实体与影线的比率"),
    ("Agent_20", 7, "多因子条件融合", "动量与反转的条件融合"),
    ("Agent_21", 7, "非线性融合", "动量和波动率的非线性融合"),
]

# Seed factor DSL expressions - one per agent
SEED_EXPRESSIONS: list[tuple[str, str, int, str, str, str, int]] = [
    # (agent_id, factor_name, level, expression, description, economic_rationale, direction)
    # Level 1: Market Structure & Cycle
    (
        "Agent_01",
        "trend_phase_ma",
        1,
        "div(sub(ts_mean(close, 10), ts_mean(close, 60)), ts_mean(close, 60))",
        "10日均线与60日均线差比，刻画趋势相位",
        "长短周期移动平均的比率反映趋势方向和强度",
        1,
    ),
    (
        "Agent_02",
        "volatility_regime",
        1,
        "div(sub(ts_std(ret(close, 1), 20), ts_mean(ts_std(ret(close, 1), 20), 60)), "
        "add(ts_std(ts_std(ret(close, 1), 20), 60), 1e-8))",
        "20日波动率相对60日均值的z-score",
        "波动率的历史分位数反映市场状态",
        1,
    ),
    (
        "Agent_03",
        "market_state_transition",
        1,
        "div(ts_std(ret(close, 1), 5), add(ts_std(ret(close, 1), 60), 1e-8))",
        "短期波动率与长期波动率之比",
        "波动率比率识别市场状态转换",
        -1,
    ),
    # Level 2: Extreme Risk & Fragility
    (
        "Agent_04",
        "downside_risk",
        2,
        "ts_mean(where(ret(close, 1) < 0, ret(close, 1), 0), 20)",
        "20日下行收益率均值",
        "仅关注负收益的波动率衡量下行风险",
        -1,
    ),
    (
        "Agent_05",
        "tail_risk",
        2,
        "ts_min(ret(close, 1), 60)",
        "60日最大日跌幅",
        "极端日跌幅反映尾部风险暴露",
        -1,
    ),
    (
        "Agent_06",
        "liquidity_fragility",
        2,
        "div(sub(ts_mean(volume, 20), volume), add(ts_mean(volume, 20), 1e-8))",
        "当日成交量相对20日均量的偏离",
        "成交量萎缩反映流动性脆弱性",
        1,
    ),
    # Level 3: Volume-Price Dynamics
    (
        "Agent_07",
        "volume_price_correlation",
        3,
        "corr(ret(close, 1), ret(volume, 1), 20)",
        "20日收益与成交量变化的相关性",
        "量价正相关表示量价协同",
        1,
    ),
    (
        "Agent_08",
        "price_impact",
        3,
        "div(abs(ret(close, 1)), add(log1p(volume), 1e-8))",
        "单位对数成交量引起的价格变化",
        "高价格冲击意味着流动性差",
        -1,
    ),
    (
        "Agent_09",
        "volume_anomaly",
        3,
        "div(sub(volume, ts_mean(volume, 20)), add(ts_std(volume, 20), 1e-8))",
        "成交量相对20日均值的z-score",
        "成交量异常偏离可能预示信息到达",
        1,
    ),
    # Level 4: Price Volatility Behavior
    (
        "Agent_10",
        "midterm_momentum",
        4,
        "div(sub(close, delay(close, 20)), delay(close, 20))",
        "20日价格动量",
        "中期价格趋势具有持续性",
        1,
    ),
    (
        "Agent_11",
        "short_term_reversal",
        4,
        "mul(ret(close, 5), -1)",
        "5日收益率反转",
        "短期过度反应后存在均值回复",
        -1,
    ),
    (
        "Agent_12",
        "volatility_clustering",
        4,
        "corr(abs(ret(close, 1)), delay(abs(ret(close, 1)), 1), 20)",
        "绝对收益率的一阶自相关",
        "高自相关表示波动率聚集",
        -1,
    ),
    # Level 5: Multi-scale Complexity
    (
        "Agent_13",
        "multiscale_trend",
        5,
        "sub(div(sub(close, delay(close, 5)), delay(close, 5)), "
        "div(sub(close, delay(close, 60)), delay(close, 60)))",
        "短期动量减长期动量",
        "多尺度趋势差捕捉趋势加速",
        1,
    ),
    (
        "Agent_14",
        "long_memory_approx",
        5,
        "corr(ret(close, 1), delay(ret(close, 1), 10), 60)",
        "收益率与10期前收益率的长期自相关",
        "高自相关近似长记忆特征",
        -1,
    ),
    (
        "Agent_15",
        "drawdown_recovery",
        5,
        "div(sub(close, ts_max(close, 60)), sub(ts_max(close, 60), 1e-8))",
        "当前价格相对60日高点的回撤比率",
        "深度回撤后的恢复潜力更大",
        1,
    ),
    # Level 6: Stability & Regime Control
    (
        "Agent_16",
        "time_stability",
        6,
        "corr(close, delay(close, 5), 20)",
        "价格5阶自相关衡量时间稳定性",
        "高自相关表示因子信号稳定",
        1,
    ),
    (
        "Agent_17",
        "regime_conditional_filter",
        6,
        "where(ts_std(ret(close, 1), 20) > ts_mean(ts_std(ret(close, 1), 20), 60), "
        "mul(ret(close, 10), -1), ret(close, 10))",
        "高波动时反转，低波动时动量",
        "不同市场状态下使用不同策略",
        1,
    ),
    (
        "Agent_18",
        "signal_decay_control",
        6,
        "sub(ret(close, 10), delay(ret(close, 10), 5))",
        "10日动量与其5期前的差值",
        "信号衰减率反映动量的持续性",
        1,
    ),
    # Level 7: Geometry & Fusion
    (
        "Agent_19",
        "candle_geometry",
        7,
        "div(sub(close, open), sub(high, low))",
        "K线实体与全振幅的比率",
        "实体占比反映多空力量对比",
        1,
    ),
    (
        "Agent_20",
        "conditional_fusion",
        7,
        "where(ret(close, 5) > 0, mul(ret(close, 20), 1), mul(ret(close, 20), -1))",
        "短期正收益时持中期动量，否则反转",
        "条件融合动量与反转信号",
        1,
    ),
    (
        "Agent_21",
        "nonlinear_fusion",
        7,
        "mul(rank(ret(close, 20)), rank(mul(ts_std(ret(close, 1), 20), -1)))",
        "动量排名与负波动率排名的乘积",
        "低波动高动量的股票表现更好",
        1,
    ),
]


def get_all_seed_factors() -> list[FactorMetadata]:
    """Get all 21 seed factor metadata objects.

    Returns:
        List of FactorMetadata for each seed factor.
    """
    factors: list[FactorMetadata] = []

    for i, (
        agent_id,
        factor_name,
        level,
        expression,
        description,
        rationale,
        direction,
    ) in enumerate(SEED_EXPRESSIONS, start=1):
        factor_id = f"seed_{i:03d}"

        # Validate expression
        is_valid, msg = FactorParser.validate(expression)
        if not is_valid:
            logger.error("Seed factor %s has invalid expression: %s", factor_id, msg)
            continue

        metadata = FactorMetadata(
            factor_id=factor_id,
            name=factor_name,
            agent_id=agent_id,
            level=level,
            expression=expression,
            direction=direction,
            description=f"{description}。{rationale}",
            parameters={},
            source="seed",
            review_status="pending",
        )
        factors.append(metadata)

    logger.info("Generated %d seed factors", len(factors))
    return factors


def register_seed_factors(registry: FactorRegistry) -> int:
    """Register all seed factors into a registry.

    Args:
        registry: Factor registry to populate.

    Returns:
        Number of factors successfully registered.
    """
    count = 0
    for metadata in get_all_seed_factors():
        if registry.register(metadata):
            count += 1
    logger.info("Registered %d seed factors into registry", count)
    return count
