from pydantic import BaseModel


class FlowSchema(BaseModel):
    name: str
    env: dict = {}
