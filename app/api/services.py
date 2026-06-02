from typing import List

from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile

from app.core.context import get_app_code
from app.core.dependencies import get_current_user_base
from app.core.response import fail, success
from app.schemas.services import CreateServiceRequest, UpdateServiceRequest
from app.services.services_service import ServicesService

router = APIRouter(prefix="/api/services", tags=["services"])


# ── 创建服务（需登录） ──

@router.post("")
def create_service(
    request: CreateServiceRequest,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data = request.model_dump()
    data["user_id"] = current_user["id"]
    data["app_code"] = app_code

    result = ServicesService.create_service(data)
    return success(data=result)


# ── 服务列表（公开） ──

@router.get("")
def list_services(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    category: str = Query(None),
    app_code: str = Depends(get_app_code),
):
    data, total = ServicesService.list_services(
        app_code=app_code,
        page=page,
        page_size=page_size,
        category=category,
    )

    total_page = (total + page_size - 1) // page_size

    return success(data={
        "list": data,
        "total": total,
        "total_page": total_page,
        "page": page,
        "page_size": page_size,
    })


# ── 我的服务列表（需登录）──
# ⚠️ 放在 /{service_id} 之前，避免 "mine" 被当作 service_id 匹配

@router.get("/mine")
def list_my_services(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data, total = ServicesService.list_my_services(
        app_code=app_code,
        user_id=current_user["id"],
        page=page,
        page_size=page_size,
    )

    total_page = (total + page_size - 1) // page_size

    return success(data={
        "list": data,
        "total": total,
        "total_page": total_page,
        "page": page,
        "page_size": page_size,
    })


# ── 服务详情（公开，但联系方式仅登录用户可见） ──

@router.get("/{service_id}")
def get_service_detail(
    service_id: str,
    app_code: str = Depends(get_app_code),
    authorization: str = Header(default=None),
):
    current_user = ServicesService._resolve_user_from_token(authorization, app_code)

    data = ServicesService.get_detail(
        service_id=service_id,
        app_code=app_code,
        current_user=current_user,
    )

    if not data:
        return fail(code=404, message="Service not found", data=None)

    return success(data={"service": data})


# ── 更新服务（需登录 + 所有权） ──

@router.put("/{service_id}")
def update_service(
    service_id: str,
    request: UpdateServiceRequest,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data = {k: v for k, v in request.model_dump().items() if v is not None}

    if not data:
        return fail(code=400, message="No fields to update", data=None)

    result = ServicesService.update_service(
        service_id=service_id,
        app_code=app_code,
        user_id=current_user["id"],
        data=data,
    )

    return success(data=result)


# ── 删除服务（需登录 + 所有权） ──

@router.delete("/{service_id}")
def delete_service(
    service_id: str,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    result = ServicesService.delete_service(
        service_id=service_id,
        app_code=app_code,
        user_id=current_user["id"],
    )

    return success(data=result)


# ── 上传服务者头像（需登录 + 所有权） ──

@router.post("/{service_id}/images/provider")
def upload_provider_image(
    service_id: str,
    file: UploadFile = File(...),
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    content = file.file.read()

    result = ServicesService.upload_provider_image(
        service_id=service_id,
        app_code=app_code,
        user_id=current_user["id"],
        file_bytes=content,
        filename=file.filename or "image",
        content_type=file.content_type or "application/octet-stream",
    )

    if isinstance(result, dict) and result.get("error") == "service_not_found":
        return fail(code=404, message="Service not found", data=None)
    if isinstance(result, dict) and result.get("error") == "forbidden":
        return fail(code=403, message="Forbidden", data=None)

    return success(data=result)


# ── 上传资质佐证图（需登录 + 所有权，最多6张） ──

@router.post("/{service_id}/images")
def upload_service_images(
    service_id: str,
    files: List[UploadFile] = File(...),
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    result = ServicesService.upload_service_images(
        service_id=service_id,
        app_code=app_code,
        user_id=current_user["id"],
        files=files,
    )

    if result.get("error") == "service_not_found":
        return fail(code=404, message="Service not found", data=None)
    if result.get("error") == "forbidden":
        return fail(code=403, message="Forbidden", data=None)
    if result.get("error") == "image_limit_reached":
        return fail(code=400, message="Maximum 6 images per service", data=None)

    return success(data=result)


# ── 删除资质佐证图（需登录 + 所有权） ──

@router.delete("/{service_id}/images/{image_id}")
def delete_service_image(
    service_id: str,
    image_id: str,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    result = ServicesService.delete_service_image(
        service_id=service_id,
        image_id=image_id,
        app_code=app_code,
        user_id=current_user["id"],
    )

    if result.get("error") == "service_not_found":
        return fail(code=404, message="Service not found", data=None)
    if result.get("error") == "forbidden":
        return fail(code=403, message="Forbidden", data=None)
    if result.get("error") == "image_not_found":
        return fail(code=404, message="Image not found", data=None)

    return success(data=result)
