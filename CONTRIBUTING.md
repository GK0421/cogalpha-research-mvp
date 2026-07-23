# Contributing

Thank you for your interest in contributing to CogAlpha Research MVP!

## Development Setup

```bash
# Clone and install
git clone https://github.com/GK0421/cogalpha-research-mvp.git
cd cogalpha-research-mvp
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -e ".[dev]"

# Run tests
scripts/run_tests.ps1  # Windows
# Or: ruff check src tests && ruff format --check src tests && mypy src && pytest --cov
```

## Code Style

- Python 3.11+ target
- Use `ruff` for linting and formatting
- Use `mypy` for type checking
- Line length: 100 characters
- Follow PEP 8 with ruff overrides

## Commit Messages

Follow conventional commits:
- `feat:` new feature
- `fix:` bug fix
- `test:` test changes
- `docs:` documentation
- `ci:` CI/CD changes
- `chore:` maintenance

## Pull Requests

1. Create a feature branch from `main`
2. Write tests for new features
3. Ensure all tests pass: `scripts/run_tests.ps1`
4. Ensure no secrets are committed
5. Create a PR with a clear description

## Security

- NEVER commit API keys, tokens, or passwords
- NEVER use `exec()`, `eval()`, or `compile()` for LLM outputs
- ALWAYS use the safe DSL for factor expressions
- ALWAYS run the security scan before submitting

## Testing

- Unit tests for all core modules
- Integration tests for pipeline stages
- End-to-end test for the full pipeline
- Coverage target: >= 85% for core modules

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
