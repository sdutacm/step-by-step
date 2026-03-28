from pydantic import BaseModel


class SourceBindingRequest(BaseModel):
    source: str
    username: str
    password: str
