from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, billing, bots, deploy, logs, stats

router = APIRouter()
router.include_router(auth.router)
router.include_router(deploy.router)
router.include_router(bots.router)
router.include_router(logs.router)
router.include_router(stats.router)
router.include_router(billing.router)
router.include_router(admin.router)
