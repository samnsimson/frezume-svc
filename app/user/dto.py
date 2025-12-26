from sqlmodel import Field
from app.lib.model import BaseModel


class CreateUserDto(BaseModel):
    name: str = Field(description="Name")
    username: str = Field(description="Username")
    email: str = Field(description="Email address")
