from pydantic import BaseModel, Field, HttpUrl


class DeployGithubRequest(BaseModel):
    name: str = Field(min_length=3, max_length=80)
    repo_url: HttpUrl
    branch: str = "main"
    cpu_limit: int = Field(default=1, ge=1, le=4)
    ram_limit_mb: int = Field(default=256, ge=128, le=4096)


class DeployZipResponse(BaseModel):
    bot_id: str
    status: str


class BotResponse(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    cpu_limit: int
    ram_limit_mb: int
    uptime_seconds: int
