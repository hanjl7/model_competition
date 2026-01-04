import asyncio
import json
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from models.schemas import ChatRequest, ModelConfig
from providers import OpenAICompatibleProvider, OpenRouterProvider

app = FastAPI(title="AI Model Competition")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def load_config() -> dict[str, ModelConfig]:
    config_path = Path("config.yaml")
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        data = yaml.safe_load(f)
    models = {}
    for name, cfg in data.get("models", {}).items():
        models[name] = ModelConfig(**cfg)
    return models


def get_provider(config: ModelConfig):
    if config.provider == "openai_compatible":
        if not config.base_url:
            raise ValueError(f"openai_compatible provider requires base_url")
        return OpenAICompatibleProvider(config)
    elif config.provider == "openrouter":
        return OpenRouterProvider(config)
    raise ValueError(f"Unknown provider: {config.provider}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/models")
async def get_models():
    configs = load_config()
    return [
        {"id": name, "display_name": cfg.display_name}
        for name, cfg in configs.items()
    ]


@app.post("/api/chat")
async def chat(request: ChatRequest):
    if len(request.models) > 5:
        return {"error": "Maximum 5 models allowed"}

    configs = load_config()
    selected_configs = {
        name: configs[name] for name in request.models if name in configs
    }

    async def event_generator():
        async def stream_model(model_name: str, config: ModelConfig):
            provider = get_provider(config)
            try:
                messages = [{"role": "user", "content": request.user_prompt}]
                async for chunk in provider.stream_chat(messages, request.system_prompt):
                    yield {"model": model_name, "content": chunk}
            except Exception as e:
                yield {"model": model_name, "error": str(e)}
            finally:
                await provider.close()

        async def merge_streams():
            tasks = {}
            for model_name, config in selected_configs.items():
                tasks[model_name] = stream_model(model_name, config)

            queues: dict[str, asyncio.Queue] = {name: asyncio.Queue() for name in tasks}
            done_count = 0
            total = len(tasks)

            async def fill_queue(name: str, gen):
                nonlocal done_count
                try:
                    async for item in gen:
                        await queues[name].put(item)
                finally:
                    await queues[name].put(None)
                    done_count += 1

            for name, gen in tasks.items():
                asyncio.create_task(fill_queue(name, gen))

            while done_count < total or any(not q.empty() for q in queues.values()):
                for name, queue in queues.items():
                    try:
                        item = queue.get_nowait()
                        if item is not None:
                            yield item
                    except asyncio.QueueEmpty:
                        pass
                await asyncio.sleep(0.01)

        async for data in merge_streams():
            yield {"event": "message", "data": json.dumps(data, ensure_ascii=False)}

        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
