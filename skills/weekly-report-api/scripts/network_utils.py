"""HTTP helper - tự thử direct / proxy / env; cache mode OK theo host group."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

DEFAULT_TIMEOUT = 10
JIRA_TIMEOUT = 10
GOOGLE_TIMEOUT = 25
RETRYABLE_HTTP = {502, 503, 504}

CACHE_FILE = Path("/tmp/.pm_webapp_net_mode_cache.json")


def _load_disk_cache() -> Dict[str, str]:
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_disk_cache(cache: Dict[str, str]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception:
        pass


# route ("jira" | "google" | "default") -> mode_key đã thành công
_MODE_CACHE: Dict[str, str] = _load_disk_cache()


def env_proxy_map() -> Optional[Dict[str, str]]:
    http = (os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy") or "").strip()
    https = (os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or http).strip()
    if not http and not https:
        fallback = (
            os.environ.get("npm_config_https_proxy")
            or os.environ.get("npm_config_proxy")
            or os.environ.get("ALL_PROXY")
            or os.environ.get("ftp_proxy")
            or "http://proxy.hcm.fpt.vn:80"
        ).strip()
        if fallback:
            http = fallback
            https = fallback
    if not http and not https:
        return None
    return {"http": http or https, "https": https or http}


def host_route(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "atlassian.net" in host or "jira.nccsoft.vn" in host:
        return "jira"
    if "google" in host:
        return "google"
    if "microsoft.com" in host or "office.com" in host or "office365.com" in host:
        return "microsoft"
    return "default"


def timeout_for_url(url: str) -> float:
    route = host_route(url)
    if route == "jira":
        return JIRA_TIMEOUT
    if route == "google":
        return GOOGLE_TIMEOUT
    return DEFAULT_TIMEOUT


def default_mode_order(route: str) -> List[Tuple[str, str]]:
    proxies = env_proxy_map()
    direct = ("direct", "no_proxy")
    proxied = ("proxy", "use_proxy") if proxies else None
    env_default = ("env", "trust_env")

    # Với Jira, Google, Microsoft trong môi trường có Proxy (như FPT):
    # Ưu tiên proxy trước để phản hồi tức thì (<1s), tránh bị timeout direct 30s
    if route in ("jira", "google", "microsoft"):
        order = []
        if proxied:
            order.append(proxied)
        order.append(env_default)
        order.append(direct)
    else:
        order = [env_default, direct]
        if proxied:
            order.append(proxied)
    return order


def modes_for_url(url: str) -> List[Tuple[str, str]]:
    route = host_route(url)
    order = default_mode_order(route)
    cached = _MODE_CACHE.get(route)
    if not cached:
        return order
    preferred = [m for m in order if m[1] == cached]
    rest = [m for m in order if m[1] != cached]
    return preferred + rest


def remember_mode(url: str, mode_key: str, label: str) -> None:
    route = host_route(url)
    if _MODE_CACHE.get(route) == mode_key:
        return
    _MODE_CACHE[route] = mode_key
    _save_disk_cache(_MODE_CACHE)
    print(f"  [NET] Lưu mode «{label}» cho {route} - request sau dùng mode này trước")


def forget_route(route: str) -> None:
    _MODE_CACHE.pop(route, None)
    _save_disk_cache(_MODE_CACHE)


def session_for_mode(mode_key: str, proxies: Optional[Dict[str, str]]) -> requests.Session:
    s = requests.Session()
    apply_mode_to_session(s, mode_key, proxies)
    return s


def apply_mode_to_session(
    session: requests.Session,
    mode_key: str,
    proxies: Optional[Dict[str, str]],
) -> None:
    if mode_key == "no_proxy":
        session.trust_env = False
        session.proxies = {"http": None, "https": None}
    elif mode_key == "use_proxy":
        session.trust_env = False
        session.proxies = dict(proxies or {})
    else:
        session.trust_env = True


def is_retryable_network_error(exc: BaseException) -> bool:
    return isinstance(
        exc,
        (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ProxyError,
            requests.exceptions.ReadTimeout,
            requests.exceptions.SSLError,
        ),
    )


def _should_retry_mode(
    route: str,
    mode_key: str,
    *,
    http_status: Optional[int] = None,
    exc: Optional[BaseException] = None,
) -> bool:
    if http_status in RETRYABLE_HTTP and mode_key == "use_proxy":
        return True
    if exc is not None and is_retryable_network_error(exc):
        return True
    return False


def request_with_proxy_fallback(
    method: str,
    url: str,
    *,
    timeout: Optional[float | Tuple[float, float]] = None,
    **kwargs: Any,
) -> requests.Response:
    """Gọi HTTP - thử các mode; cache mode thành công theo host group."""
    t = timeout if timeout is not None else timeout_for_url(url)
    route = host_route(url)
    modes = modes_for_url(url)
    proxies = env_proxy_map()
    last_err: Optional[BaseException] = None

    for label, mode_key in modes:
        # Nếu là direct ("no_proxy"), rút ngắn connect timeout xuống 3.5s để tránh treo quá lâu
        if isinstance(t, (int, float)) and mode_key == "no_proxy":
            req_t: Any = (min(3.5, float(t)), float(t))
        else:
            req_t = t
        try:
            session = session_for_mode(mode_key, proxies)
            resp = session.request(method, url, timeout=req_t, **kwargs)
            if _should_retry_mode(route, mode_key, http_status=resp.status_code):
                if _MODE_CACHE.get(route) == mode_key:
                    forget_route(route)
                    print(f"  [NET] mode «{label}» không còn OK - thử mode khác...")
                else:
                    print(f"  [NET] {label} HTTP {resp.status_code} - thử mode khác...")
                continue
            remember_mode(url, mode_key, label)
            return resp
        except requests.exceptions.HTTPError:
            raise
        except BaseException as e:
            last_err = e
            if _should_retry_mode(route, mode_key, exc=e):
                if _MODE_CACHE.get(route) == mode_key:
                    forget_route(route)
                    print(f"  [NET] mode «{label}» lỗi ({type(e).__name__}) - thử mode khác...")
                else:
                    print(f"  [NET] {label} lỗi ({type(e).__name__}) - thử mode khác...")
                continue
            raise

    if last_err:
        raise last_err
    raise requests.exceptions.ConnectionError(f"Không kết nối được {url}")


def configure_session_proxy_fallback(
    session: requests.Session,
    url_hint: str,
    *,
    timeout: Optional[float] = None,
) -> requests.Session:
    """Gắn fallback + cache mode lên session (AuthorizedSession / gspread)."""
    proxies = env_proxy_map()
    original_request = session.request

    def request_with_fallback(*args: Any, **kwargs: Any):
        url = args[1] if len(args) > 1 else url_hint
        t = timeout if timeout is not None else timeout_for_url(url)
        kwargs.setdefault("timeout", t)
        route = host_route(url)
        modes = modes_for_url(url)
        last_err: Optional[BaseException] = None

        for label, mode_key in modes:
            apply_mode_to_session(session, mode_key, proxies)
            try:
                resp = original_request(*args, **kwargs)
                if _should_retry_mode(route, mode_key, http_status=resp.status_code):
                    if _MODE_CACHE.get(route) == mode_key:
                        forget_route(route)
                    continue
                remember_mode(url, mode_key, label)
                return resp
            except BaseException as e:
                last_err = e
                if _should_retry_mode(route, mode_key, exc=e):
                    if _MODE_CACHE.get(route) == mode_key:
                        forget_route(route)
                    print(f"  [NET] {label} lỗi ({type(e).__name__}) - thử mode khác...")
                    continue
                raise

        if last_err:
            raise last_err
        raise requests.exceptions.ConnectionError("All proxy modes failed")

    session.request = request_with_fallback  # type: ignore[method-assign]
    return session
