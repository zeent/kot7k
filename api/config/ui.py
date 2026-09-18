"""Serve the published Next export without a Next.js runtime."""
import json
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.http import require_safe


LOGOUT_PATHS = {
    "authentication/front-channel-logout",
    "authentication/signed-out",
}


@require_safe
def ui(request, path=""):
    root = Path(settings.UI_DIST_ROOT).resolve()
    # Never expose deployment metadata, dotfiles, or files outside the export.
    if "\\" in path or any(part.startswith(".") for part in path.split("/")):
        raise Http404
    relative = path.rstrip("/")
    candidates = [relative, f"{relative}.html", f"{relative}/index.html"] if relative else ["index.html"]
    for name in candidates:
        file = (root / name).resolve()
        if not file.is_relative_to(root) or not file.is_file():
            continue
        headers = {}
        if relative in LOGOUT_PATHS:
            try:
                manifest = json.loads((root / ".ui-headers.json").read_text())
                headers = manifest[relative]
                if not all(isinstance(headers.get(key), str) and headers[key] for key in (
                    "content-security-policy", "cache-control", "referrer-policy",
                )):
                    raise ValueError("Incomplete logout headers")
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                return HttpResponse("UI build metadata unavailable. Rebuild the frontend.", status=503)
        response = FileResponse(file.open("rb"), content_type="text/html; charset=utf-8" if relative in LOGOUT_PATHS else None)
        response["Cache-Control"] = "no-cache"
        for key in ("content-security-policy", "cache-control", "referrer-policy"):
            if key in headers:
                response[key] = headers[key]
        if relative == "authentication/front-channel-logout":
            # The build's CSP allows only the Microsoft iframe origins.
            response.xframe_options_exempt = True
        return response
    raise Http404
