from pydantic import BaseModel as PydanticBaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseModel(PydanticBaseModel):
    """Base schema with common configuration.

    Serializes field names as camelCase and forbids extra fields.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
    )
    """Base model configuration."""
