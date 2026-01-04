# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI 模型对比工具 - 支持同时请求多个大模型并对比响应结果。

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) for Python package management.

- Python version: 3.11
- Virtual environment: `.venv/`

## Commands

```bash
# Run the application
uv run python main.py

# Add dependencies
uv add <package>

# Sync dependencies
uv sync
```

## Configuration

复制 `config.example.yaml` 为 `config.yaml`，填入真实的 API Key 和域名配置。

## Architecture

- `main.py` - FastAPI 应用入口，包含路由和 SSE 流式响应处理
- `providers/` - LLM 供应商抽象层
  - `base.py` - Provider 基类定义
  - `openai_compatible.py` - OpenAI Compatible API 实现
  - `openrouter.py` - OpenRouter API 实现
- `models/schemas.py` - Pydantic 模型定义
- `templates/index.html` - 主页面模板
- `static/` - 前端静态资源 (CSS/JS)

## Supported Providers

- **OpenAI Compatible**: 支持 OpenAI、DeepSeek、豆包、通义千问、Kimi 等
- **OpenRouter**: 统一访问多种模型的网关
