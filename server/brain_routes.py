"""GET /brain/status — pool ka live haal. Sab kuch masked, koi key nahi.

Sirf naam/tier/model/cooldown dikhta hai. Key, ya prompt ka content, ya file ka
private text kabhi is route se bahar nahi jaata.

Note: is file me `router` naam FastAPI ka router hai, brain wala nahi — isliye
brain ko `brain_router` alias se import kiya gaya hai.
"""

import re

from fastapi import APIRouter, HTTPException, Request

from brain import router as brain_router
from gatekeeper import audit
from log_setup import get_logger
from server import security

log = get_logger("brain_routes")
router = APIRouter()

# Key/token jaisa koi bhi field hata do — chahe kabhi galti se aa jaye.
SECRET_FIELD_RE = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)", re.IGNORECASE)


def _clean(row: dict) -> dict:
    """Secret-named field poora hatao, baaki string values mask karo. Number waise."""
    return {
        k: (audit.mask(v) if isinstance(v, str) else v)
        for k, v in row.items()
        if not SECRET_FIELD_RE.search(k) or k == "has_key"
    }


@router.get("/brain/status")
async def brain_status(request: Request):
    """active_tier, provider, model, cooldowns, last_fail_reasons — sab masked."""
    denied = security.verify_request(request, request.headers.get(security.TOKEN_HEADER, ""))
    if denied:
        raise HTTPException(*denied)

    data = _clean(brain_router.status())
    data["providers"] = [_clean(row) for row in data.get("providers", [])]
    log.info("brain/status: tier=%s provider=%s", data.get("active_tier"),
             data.get("provider"))
    return data