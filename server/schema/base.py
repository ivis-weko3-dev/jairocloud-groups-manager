from pydantic import BaseModel as PydanticBaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseModel(PydanticBaseModel):
    """Base model with common configuration.

    Converts field names from snake_case to camelCase when serializing to JSON,
    and forbids extra fields not defined in the model.
    """

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
    )
    """Base model configuration."""
