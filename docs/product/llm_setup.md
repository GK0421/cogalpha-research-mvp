# LLM Setup Guide

## Overview

CogAlpha Studio works **without any LLM API key**. All 21 seed factors are
fully deterministic. LLM integration is optional and enables AI-assisted
factor generation.

## Supported Providers (6)

| Provider | Env Variable | Base URL |
|----------|-------------|----------|
| iFlytek Spark | `IFLYTEK_SPARK_API_KEY` | `https://maas-coding-api.cn-huabei-1.xf-yun.com/v2` |
| MiniMax | `MINIMAX_API_KEY` | `https://api.minimaxi.com/v1` |
| OpenAI | `OPENAI_API_KEY` | `https://api.openai.com/v1` |
| Anthropic | `ANTHROPIC_API_KEY` | (native API) |
| DeepSeek | `DEEPSEEK_API_KEY` | `https://api.deepseek.com/v1` |
| DashScope | `DASHSCOPE_API_KEY` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |

## Setup

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Add one or more API keys:
```
MINIMAX_API_KEY=your-key-here
```

3. Verify with doctor:
```powershell
python -m cogalpha_mvp.cli doctor
```

4. In Studio, go to **Settings** to configure which provider to use.

## Security

- API keys are stored in local `.env` file only
- `.env` is gitignored (never committed)
- Keys are never logged
- No telemetry sends keys anywhere

## Disabling LLM

To explicitly disable LLM:
```
# In .env
COGALPHA_LLM_ENABLED=false
```

Or in Settings page, toggle LLM off.

## Graceful Degradation

When no API key is configured:
- All 21 seed factors work normally
- Factor Lab validator works normally
- Full research pipeline works normally
- Only "Generate with LLM" button is disabled
