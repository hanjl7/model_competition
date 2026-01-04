from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    system_prompt: str = ""
    user_prompt: str
    models: list[str]


class ModelConfig(BaseModel):
    display_name: str
    provider: str
    model_id: str
    api_key: str
    base_url: str = ""  # openai_compatible 必须提供，openrouter 会忽略此字段
