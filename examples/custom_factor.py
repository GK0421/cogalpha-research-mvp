# Example: Custom Factor
"""Define and evaluate a custom factor using the safe DSL."""

from cogalpha_mvp.factors.dsl import FactorDefinition, FactorInterpreter, FactorParser
from cogalpha_mvp.factors.registry import FactorMetadata, FactorRegistry
from cogalpha_mvp.factors.seed_factors import register_seed_factors


def main():
    # Create a custom factor
    expression = "rank(div(sub(close, delay(close, 20)), delay(close, 20)))"

    # Validate expression
    is_valid, msg = FactorParser.validate(expression)
    print(f"Expression valid: {is_valid}")
    if not is_valid:
        print(f"Error: {msg}")
        return

    # Create factor metadata
    custom_factor = FactorMetadata(
        factor_id="custom_001",
        name="custom_momentum_20",
        agent_id="Agent_10",
        level=4,
        expression=expression,
        direction=1,
        description="20-day momentum factor with cross-sectional ranking",
        source="custom",
    )

    # Register
    registry = FactorRegistry()
    register_seed_factors(registry)
    registry.register(custom_factor)

    print(f"Total factors: {registry.count}")
    print(f"Factor IDs: {[f.factor_id for f in registry.all_factors()]}")


if __name__ == "__main__":
    main()
