from __future__ import annotations

import logging
from pipes.accessgroups.manager import AccessGroupManager
from pipes.catalogmodels.manager import GeneralCatalogModelManager
from pipes.catalogmodels.schemas import (
    GeneralCatalogModelCreate,
    GeneralCatalogModelRead,
    GeneralCatalogModelUpdate,
)
from pipes.common.exceptions import (
    DocumentAlreadyExists,
    DocumentDoesNotExist,
    DomainValidationError,
)
from pipes.users.auth import auth_required
from pipes.users.schemas import UserDocument

from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/catalogmodel/detail", response_model=GeneralCatalogModelRead, status_code=200)
async def get_catalog_model(
    model_name: str,
    user: UserDocument = Depends(auth_required),
):
    manager = GeneralCatalogModelManager()
    catalogmodel = await manager.get_model(model_name, user)
    return catalogmodel


@router.post("/catalogmodel/create", response_model=GeneralCatalogModelRead, status_code=201)
async def create_catalog_model(
    data: GeneralCatalogModelCreate,
    user: UserDocument = Depends(auth_required),
):
    manager = GeneralCatalogModelManager()
    try:
        mc_doc = await manager.create_model(data, user)
    except (
        DocumentAlreadyExists,
        DomainValidationError,
        DocumentDoesNotExist,
    ) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    mr_doc = await manager.read_model(mc_doc)
    return mr_doc


@router.get("/catalogmodels", response_model=list[GeneralCatalogModelRead], status_code=200)
async def get_catalog_models(
    user: UserDocument = Depends(auth_required),
):
    manager = GeneralCatalogModelManager()
    catalogmodels = await manager.get_models(user)
    return catalogmodels


@router.patch("/catalogmodel/update", response_model=GeneralCatalogModelRead, status_code=200)
async def update_catalog_model(
    model_name: str,
    data: GeneralCatalogModelUpdate,
    user: UserDocument = Depends(auth_required),
):
    """Update a catalog model. Only provided fields will be updated."""
    logger.info(f"Updating catalog model '{model_name}'")

    # Convert access group names to IDs if provided
    if data.access_group is not None:
        ag_manager = AccessGroupManager()
        ag_read_list = []
        for ag_name in data.access_group:
            try:
                ag_doc = await ag_manager.get_accessgroup(ag_name, created_by=user)
            except DocumentDoesNotExist:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Access group with name '{ag_name}' does not exist.",
                )
            # ag_read_list.append(await ag_manager.read_accessgroup(ag_doc))
            ag_read_list.append(ag_doc.id)
        data.access_group = ag_read_list

    manager = GeneralCatalogModelManager()
    try:
        updated_model = await manager.update_model(model_name, data, user)
    except (
        DocumentAlreadyExists,
        DomainValidationError,
        DocumentDoesNotExist,
    ) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return updated_model


@router.delete("/catalogmodel/delete", status_code=204)
async def delete_catalog_model(
    model_name: str,
    user: UserDocument = Depends(auth_required),
):
    manager = GeneralCatalogModelManager()
    try:
        await manager.delete_model(model_name, user)
    except DocumentDoesNotExist as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
