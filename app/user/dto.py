from sqlmodel import SQLModel, Field


class CreateUserDto(SQLModel):
    name: str = Field(description="Name")
    username: str = Field(description="Username")
    email: str = Field(description="Email address")
