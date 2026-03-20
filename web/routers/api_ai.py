from fastapi import APIRouter, Depends, HTTPException, Request
from modules.database import AdminUser, AIProvider
from web.deps import get_current_user

router = APIRouter(prefix="/api/ai/providers", tags=["ai_providers"])

def _require_admin(user: AdminUser):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

@router.get("")
async def list_providers(user: AdminUser = Depends(get_current_user)):
    _require_admin(user)
    providers = await AIProvider.all().order_by("priority", "id")
    return [
        {
            "id": p.id,
            "name": p.name,
            "api_type": p.api_type,
            "api_key": p.api_key[:8] + "..." if p.api_key else "",
            "base_url": p.base_url,
            "model_name": p.model_name,
            "is_active": p.is_active,
            "priority": p.priority,
        }
        for p in providers
    ]

@router.post("")
async def create_provider(request: Request, user: AdminUser = Depends(get_current_user)):
    _require_admin(user)
    body = await request.json()
    name = body.get("name")
    api_type = body.get("api_type", "openai")
    api_key = body.get("api_key")
    model_name = body.get("model_name")
    
    if not all([name, api_key, model_name]):
        raise HTTPException(status_code=400, detail="name, api_key, model_name are required")
        
    provider = await AIProvider.create(
        name=name,
        api_type=api_type,
        api_key=api_key,
        base_url=body.get("base_url"),
        model_name=model_name,
        is_active=body.get("is_active", True),
        priority=body.get("priority", 10)
    )
    return {"ok": True, "id": provider.id}

@router.patch("/{provider_id}")
async def update_provider(provider_id: int, request: Request, user: AdminUser = Depends(get_current_user)):
    _require_admin(user)
    provider = await AIProvider.get_or_none(id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    body = await request.json()
    if "name" in body: provider.name = body["name"]
    if "api_type" in body: provider.api_type = body["api_type"]
    if "api_key" in body and body["api_key"]: provider.api_key = body["api_key"]
    if "base_url" in body: provider.base_url = body["base_url"]
    if "model_name" in body: provider.model_name = body["model_name"]
    if "is_active" in body: provider.is_active = bool(body["is_active"])
    if "priority" in body: provider.priority = int(body["priority"])
    
    await provider.save()
    return {"ok": True}

@router.delete("/{provider_id}")
async def delete_provider(provider_id: int, user: AdminUser = Depends(get_current_user)):
    _require_admin(user)
    deleted = await AIProvider.filter(id=provider_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {"ok": True}
