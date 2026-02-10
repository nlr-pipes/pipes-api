from __future__ import annotations

import logging, json
from datetime import datetime

from pymongo.errors import DuplicateKeyError

from pipes.common.exceptions import DocumentAlreadyExists, DocumentDoesNotExist
from pipes.db.manager import AbstractObjectManager
from pipes.catalogmodels.schemas import (
    GeneralCatalogModelCreate,
    GeneralCatalogModelDocument,
    GeneralCatalogModelRead,
    GeneralCatalogModelUpdate,
)
from pipes.catalogmodels.ifac.schemas import (
    IFACCatalogModelCreate
)
from pipes.catalogmodels.default.schemas import (
    DefaultCatalogModelCreate
)
from pipes.users.schemas import UserDocument, UserRead
from pipes.accessgroups.schemas import AccessGroupDocument, AccessGroupRead

logger = logging.getLogger(__name__)

schemas = {
    "IFAC": {"1.0": IFACCatalogModelCreate},
    "Default": {"1.0":DefaultCatalogModelCreate},
}

class GeneralCatalogModelManager(AbstractObjectManager):
    """Manager for catalog model operations"""

    async def create_model(
        self,
        m_create: GeneralCatalogModelCreate,
        user: UserDocument,
    ) -> GeneralCatalogModelDocument:
        if m_create.catalog_schema is not None and m_create.schema_version is not None:
            if m_create.catalog_schema not in schemas or m_create.schema_version not in schemas[m_create.catalog_schema]:
                raise DocumentAlreadyExists(
                    f"Catalog schema '{m_create.catalog_schema}' version '{m_create.schema_version}' does not exist.",
                )
            try: 
                schemas[m_create.catalog_schema][m_create.schema_version].model_validate(m_create.model_dump())
            except Exception as e:
                raise DocumentAlreadyExists(
                    f"Model '{m_create.name}' does not conform to {m_create.catalog_schema} schema version {m_create.schema_version}: {e}",
                )
        else:
            raise DocumentAlreadyExists(
                f"Catalog schema and version must be provided for model '{m_create.name}'.",
            )
        m_doc = await self._create_model_document(m_create, user)
        return m_doc

    async def _create_model_document(
        self,
        m_create: GeneralCatalogModelCreate,
        user: UserDocument,
    ) -> GeneralCatalogModelDocument:
        """Create a new model under given project and project run"""

        # Check if model already exists or not
        m_name = m_create.name
        m_doc_exits = await self.d.exists(
            collection=GeneralCatalogModelDocument,
            query={
                "name": m_name,
            },
        )
        if m_doc_exits:
            raise DocumentAlreadyExists(
                f"Model '{m_name}' already exists in catalog.",
            )
        # object context
        current_time = datetime.now()
        cm_doc = GeneralCatalogModelDocument(
            # model information
            created_at=current_time,
            created_by=user.id,
            last_modified=current_time,
            modified_by=user.id,
            **m_create.model_dump(exclude_none=True)
        )
        # Create document
        try:
            cm_doc = await self.d.insert(cm_doc)
        except DuplicateKeyError:
            raise DocumentAlreadyExists(
                f"Model document '{m_name}'.",
            )

        logger.info(
            "New model '%s' was created successfully in catalog.",
            m_name,
        )
        return cm_doc

    async def get_models(self, user: UserDocument) -> list[GeneralCatalogModelRead]:
        """Read a model from given model document"""
        cm_docs = await self.d.find_all(
            collection=GeneralCatalogModelDocument,
            query={
                "$or": [
                    {"created_by": user.id},
                    {"access_group": {"$elemMatch":{"members":{"$in": [user.id]}}}},
                ],
            },
        )

        print(f"Found {len(cm_docs)} models for user {user.email}")
        cm_reads = []
        for cm_doc in cm_docs:
            cm_read = await self.read_model(cm_doc)
            cm_reads.append(cm_read)
        print(f"{cm_reads}")
        return cm_reads

    async def read_model(
        self,
        cm_doc: GeneralCatalogModelDocument,
    ):
        """Retrieve a specific model from the database by name"""
        # Convert the document to a model document
        if not cm_doc:
            return None
        data = cm_doc.model_dump()
        created_by_doc = await UserDocument.get(data["created_by"])
        data["created_by"] = UserRead.model_validate(created_by_doc.model_dump())
        modified_by_doc = await UserDocument.get(data["modified_by"])
        data["modified_by"] = UserRead.model_validate(modified_by_doc.model_dump())

        access_groups = []
        for access_group_id in data["access_group"]:
            access_group_doc = await AccessGroupDocument.get(access_group_id)
            if access_group_doc:
                access_groups.append(AccessGroupRead.model_validate(access_group_doc.model_dump()))
        data["access_group"] = access_groups
        return GeneralCatalogModelRead.model_validate(data)

    async def get_model(
        self,
        model_name: str,
        user: UserDocument,
    ) -> GeneralCatalogModelRead:
        """Get a specific model by name"""
        query = {
            "name": model_name,
            "$or": [
                {"created_by": user.id},
                {"access_group": {"$in": [user.id]}},
            ],
        }
        cm_doc = await self.d.find_one(
            collection=GeneralCatalogModelDocument,
            query=query,
        )
        if not cm_doc:
            raise DocumentDoesNotExist(
                f"Model '{model_name}' does not exist in catalog.",
            )

        cm_read = await self.read_model(cm_doc)
        return cm_read

    async def update_model(
        self,
        model_name: str,
        m_update: GeneralCatalogModelUpdate,
        user: UserDocument,
    ) -> GeneralCatalogModelDocument:
        """Update an existing catalog model"""
        # Find the model
        query = {"name": model_name, "created_by": user.id}
        cm_doc = await self.d.find_one(
            collection=GeneralCatalogModelDocument,
            query=query,
        )
        if not cm_doc:
            raise DocumentDoesNotExist(
                f"Model '{model_name}' does not exist in catalog.",
            )

        # Update fields
        update_data = m_update.model_dump()
        if update_data:
            update_data["last_modified"] = datetime.now()
            update_data["modified_by"] = user.id

            for key, value in update_data.items():
                setattr(cm_doc, key, value)

            cm_doc = await cm_doc.save()

            logger.info(
                "Model '%s' was updated successfully in catalog.",
                model_name,
            )

        return await self.read_model(cm_doc)

    async def delete_model(
        self,
        model_name: str,
        user: UserDocument,
    ) -> None:
        """Delete a specific model by name"""
        query = {"name": model_name, "created_by": user.id}
        cm_doc = await self.d.find_one(
            collection=GeneralCatalogModelDocument,
            query=query,
        )
        if not cm_doc:
            raise DocumentDoesNotExist(
                f"Model '{model_name}' does not exist in catalog.",
            )
        await self.d.delete_one(
            collection=GeneralCatalogModelDocument,
            query={"_id": cm_doc.id},
        )
        logger.info(
            "Model '%s' was deleted successfully from catalog.",
            model_name,
        )
