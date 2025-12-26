from pydantic import ConfigDict
from sqlmodel import SQLModel
from pydantic.alias_generators import to_camel


class BaseModel(SQLModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
