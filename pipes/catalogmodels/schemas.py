from __future__ import annotations

from datetime import datetime

import pymongo
from pymongo import IndexModel
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, field_validator, ConfigDict

from pipes.users.schemas import UserRead, UserCreate
from pipes.accessgroups.schemas import AccessGroupRead


class GeneralCatalogModelCreate(BaseModel, extra="allow"):
    """Baseline model schema for model catalog entries. All catalog model entries will validate against this schema first before validating against specific schemas.

    Attributes:
        name: The model name.
        display_name: Display name for this model vertex.
        type: Type of model to use in graphic headers (e.g, 'Capacity Expansion').
        description: Description of the model.
        requirements: Model specific requirements (if different from Project and Project-Run).
        other: Other metadata info about the model in dictionary.
        access_group: A group of users that has access to this model.
    """

    catalog_schema: str = Field(
        title="catalog_schema",
        description="The schema that this model conforms to.",
    )
    name: str = Field(
        title="model_catalog",
        min_length=1,
        description="the model name",
    )
    display_name: str | None = Field(
        title="display_name",
        default=None,
        description="Display name for this model vertex.",
    )
    type: str = Field(
        title="type",
        description="Type of model to use in graphic headers (e.g, 'Capacity Expansion')",
    )
    description: list[str] = Field(
        title="description",
        description="Description of the model",
    )
    requirements: dict = Field(
        title="requirements",
        default={},
        description="Model specific requirements (if different from Project and Project-Run)",
    )
    other: dict = Field(
        title="other",
        default={},
        description="other metadata info about the model in dictionary",
    )

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, value):
        if isinstance(value, str):
            return [value]
        return value


class GeneralCatalogModelUpdate(GeneralCatalogModelCreate):
    """Model update schema.

    Attributes:
        name: The model name.
        display_name: Display name for this model vertex.
        type: Type of model to use in graphic headers (e.g, 'Capacity Expansion').
        description: Description of the model.
        assumptions: List of model assumptions.
        requirements: Model specific requirements (if different from Project and Project-Run).
        expected_scenarios: List of expected model scenarios.
        modeling_team: Information about the modeling team.
        other: Other metadata info about the model in dictionary.
        access_group: A group of users that has access to this model.
    """

    pass


class GeneralCatalogModelRead(GeneralCatalogModelCreate):
    """Model read schema.

    Attributes:
        name: The model name.
        display_name: Display name for this model vertex.
        type: Type of model to use in graphic headers (e.g, 'Capacity Expansion').
        description: Description of the model.
        assumptions: List of model assumptions.
        requirements: Model specific requirements (if different from Project and Project-Run).
        expected_scenarios: List of expected model scenarios.
        modeling_team: Information about the modeling team.
        other: Other metadata info about the model in dictionary.
        access_group: List of access groups that have access to this model.
        created_at: Catalog model creation time.
        created_by: User who created the model in catalog.
    """
    id: PydanticObjectId = Field(exclude=True)
    access_group: list[AccessGroupRead] = Field(
        title="access_group",
        default=[],
        description="List of access groups that have access to this model",
    )
    created_at: datetime = Field(
        title="created_at",
        description="catalog model creation time",
    )
    created_by: UserRead = Field(
        title="created_by",
        description="user who created the model in catalog",
    )

class GeneralCatalogModelDocument(GeneralCatalogModelCreate, Document):
    """Catalog model document.

    Attributes:
        name: The model name.
        display_name: Display name for this model vertex.
        type: Type of model to use in graphic headers (e.g, 'Capacity Expansion').
        description: Description of the model.
        assumptions: List of model assumptions.
        requirements: Model specific requirements (if different from Project and Project-Run).
        expected_scenarios: List of expected model scenarios.
        modeling_team: Information about the modeling team.
        other: Other metadata info about the model in dictionary.
        access_group: List of access group object IDs that have access to this model.
        created_at: Catalog model creation time.
        created_by: User who created the model in catalog.
        last_modified: Last modification datetime.
        modified_by: User who modified the project.
    """

    created_at: datetime = Field(
        title="created_at",
        description="catalog model creation time",
    )
    created_by: PydanticObjectId = Field(
        title="created_by",
        description="user who created the model in catalog",
    )
    last_modified: datetime = Field(
        title="last_modified",
        default=datetime.now(),
        description="last modification datetime",
    )
    modified_by: PydanticObjectId = Field(
        title="modified_by",
        description="user who modified the project",
    )
    access_group: list[PydanticObjectId] = Field(
        title="access_group",
        default=[],
        description="List of access group object IDs that have access to this model",
    )

    class Settings:
        name = "catalogmodels"
        indexes = [
            IndexModel(
                [
                    ("name", pymongo.ASCENDING),
                ],
                unique=True,
            ),
        ]
