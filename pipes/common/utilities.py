from __future__ import annotations

from datetime import datetime, timezone
from pipes.common.constants import DNS_ORG_MAPPING
from typing import Any

from dateutil import parser
from pydantic import BaseModel, EmailStr, Field, create_model
from shortuuid import ShortUUID


def generate_shortuuid() -> str:
    """Generate short identifier for public exposure"""
    _shortuuid = ShortUUID()
    return _shortuuid.random(length=8)


def parse_datetime(value: Any) -> datetime:
    """Parse datetime from given value"""
    if isinstance(value, datetime):
        return value
    value = str(value)

    value = parser.parse(value)

    # remove tzinfo
    native_value = value.astimezone(timezone.utc).replace(tzinfo=None)

    return native_value


def parse_organization(email: EmailStr) -> str | None:
    """Parse organization based on email domain"""
    domain = email.lower().split("@")[1]
    if domain in DNS_ORG_MAPPING:
        return DNS_ORG_MAPPING[domain]
    return None


def make_optional_model(base_model: type[BaseModel], model_name: str, doc: str | None = None) -> type[BaseModel]:
    """Create a model with all fields from base_model but optional.

    Args:
        base_model: The base model to copy fields from.
        model_name: Name for the new model class.
        doc: Optional docstring for the new model.

    Returns:
        A new Pydantic model with all fields optional.
    """
    # Build field definitions with all fields as optional
    field_definitions = {}
    for field_name, field_info in base_model.model_fields.items():
        # Get the annotation and make it optional
        annotation = field_info.annotation
        optional_annotation = annotation | None if annotation else None

        # Create new field with None as default
        field_definitions[field_name] = (
            optional_annotation,
            Field(
                default=None,
                title=field_info.title,
                description=field_info.description,
            ),
        )

    # Create the model
    model = create_model(
        model_name, __doc__=doc or base_model.__doc__, __config__=base_model.model_config, **field_definitions
    )

    return model
