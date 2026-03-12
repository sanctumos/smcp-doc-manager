"""
Letta API client for sources, folders, and file operations.
Uses LETTA_BASE_URL and LETTA_API_KEY (or LETTA_SERVER_PASSWORD) from environment.
"""

import os
from typing import Any

import httpx

ENV_BASE_URL = "LETTA_BASE_URL"
ENV_API_KEY = "LETTA_API_KEY"
ENV_SERVER_PASSWORD = "LETTA_SERVER_PASSWORD"
DEFAULT_BASE_URL = "http://127.0.0.1:8284"

# Embedding config: Letta requires embedding_config when creating sources/folders.
# Override via env: DOC_MANAGER_EMBEDDING_ENDPOINT_TYPE, DOC_MANAGER_EMBEDDING_MODEL,
# DOC_MANAGER_EMBEDDING_DIM, DOC_MANAGER_EMBEDDING_ENDPOINT, DOC_MANAGER_EMBEDDING_CHUNK_SIZE.
OPENAI_EMBEDDING_DEFAULT = {
    "embedding_endpoint_type": "openai",
    "embedding_model": "text-embedding-ada-002",
    "embedding_dim": 1536,
    "embedding_endpoint": "https://api.openai.com/v1",
    "embedding_chunk_size": 300,
}


def _default_embedding_config() -> dict[str, Any]:
    """Build embedding_config for Letta source/folder create. Uses env overrides or OpenAI default."""
    cfg = dict(OPENAI_EMBEDDING_DEFAULT)
    if os.environ.get("DOC_MANAGER_EMBEDDING_ENDPOINT_TYPE"):
        cfg["embedding_endpoint_type"] = os.environ["DOC_MANAGER_EMBEDDING_ENDPOINT_TYPE"]
    if os.environ.get("DOC_MANAGER_EMBEDDING_MODEL"):
        cfg["embedding_model"] = os.environ["DOC_MANAGER_EMBEDDING_MODEL"]
    if os.environ.get("DOC_MANAGER_EMBEDDING_DIM"):
        try:
            cfg["embedding_dim"] = int(os.environ["DOC_MANAGER_EMBEDDING_DIM"])
        except ValueError:
            pass
    if os.environ.get("DOC_MANAGER_EMBEDDING_ENDPOINT"):
        cfg["embedding_endpoint"] = os.environ["DOC_MANAGER_EMBEDDING_ENDPOINT"]
    if os.environ.get("DOC_MANAGER_EMBEDDING_CHUNK_SIZE"):
        try:
            cfg["embedding_chunk_size"] = int(os.environ["DOC_MANAGER_EMBEDDING_CHUNK_SIZE"])
        except ValueError:
            pass
    return cfg


def _get_config() -> tuple[str, str]:
    base = (os.environ.get(ENV_BASE_URL) or os.environ.get("LETTA_SERVER_URL") or "").strip() or DEFAULT_BASE_URL
    key = (os.environ.get(ENV_API_KEY) or os.environ.get(ENV_SERVER_PASSWORD) or "").strip()
    return base.rstrip("/"), key


def _headers() -> dict[str, str]:
    _, key = _get_config()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


def _get(url_suffix: str, params: dict | None = None) -> dict[str, Any]:
    base, key = _get_config()
    if not key:
        return {"status": "error", "error": "Letta API key not set (LETTA_API_KEY or LETTA_SERVER_PASSWORD)."}
    url = f"{base}{url_suffix}"
    try:
        r = httpx.get(url, headers=_headers(), params=params or {}, timeout=30.0)
        r.raise_for_status()
        return {"status": "success", "data": r.json()}
    except httpx.HTTPStatusError as e:
        body = e.response.text
        return {"status": "error", "error": f"HTTP {e.response.status_code}: {body}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _post_json(url_suffix: str, body: dict) -> dict[str, Any]:
    base, key = _get_config()
    if not key:
        return {"status": "error", "error": "Letta API key not set (LETTA_API_KEY or LETTA_SERVER_PASSWORD)."}
    url = f"{base}{url_suffix}"
    try:
        r = httpx.post(url, headers={**_headers(), "Content-Type": "application/json"}, json=body, timeout=60.0)
        r.raise_for_status()
        return {"status": "success", "data": r.json() if r.content else None}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _patch(url_suffix: str, body: dict | None = None) -> dict[str, Any]:
    base, key = _get_config()
    if not key:
        return {"status": "error", "error": "Letta API key not set."}
    url = f"{base}{url_suffix}"
    try:
        r = httpx.patch(url, headers={**_headers(), "Content-Type": "application/json"}, json=body or {}, timeout=30.0)
        r.raise_for_status()
        return {"status": "success", "data": r.json() if r.content else None}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _delete(url_suffix: str) -> dict[str, Any]:
    base, key = _get_config()
    if not key:
        return {"status": "error", "error": "Letta API key not set."}
    url = f"{base}{url_suffix}"
    try:
        r = httpx.delete(url, headers=_headers(), timeout=30.0)
        r.raise_for_status()
        return {"status": "success", "data": r.json() if r.content else None}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _upload(url_suffix: str, file_bytes: bytes, filename: str, content_type: str) -> dict[str, Any]:
    base, key = _get_config()
    if not key:
        return {"status": "error", "error": "Letta API key not set."}
    url = f"{base}{url_suffix}"
    try:
        files = {"file": (filename, file_bytes, content_type)}
        r = httpx.post(url, headers=_headers(), files=files, timeout=60.0)
        r.raise_for_status()
        return {"status": "success", "data": r.json() if r.content else None}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# --- Sources ---


def list_sources() -> dict[str, Any]:
    out = _get("/v1/sources/")
    if out.get("status") != "success":
        return out
    return {"status": "success", "sources": out.get("data") or []}


def create_source(name: str) -> dict[str, Any]:
    body = {"name": name, "embedding_config": _default_embedding_config()}
    out = _post_json("/v1/sources/", body)
    if out.get("status") != "success":
        return out
    return {"status": "success", "source": out.get("data")}


def list_source_files(source_id: str) -> dict[str, Any]:
    out = _get(f"/v1/sources/{source_id}/files")
    if out.get("status") != "success":
        return out
    return {"status": "success", "files": out.get("data") or []}


def upload_to_source(source_id: str, file_bytes: bytes, filename: str, content_type: str) -> dict[str, Any]:
    return _upload(f"/v1/sources/{source_id}/upload", file_bytes, filename, content_type)


def delete_from_source(source_id: str, file_id: str) -> dict[str, Any]:
    return _delete(f"/v1/sources/{source_id}/{file_id}")


def get_source_file_metadata(source_id: str, file_id: str) -> dict[str, Any]:
    return _get(f"/v1/sources/{source_id}/files/{file_id}")


# --- Folders ---


def list_folders() -> dict[str, Any]:
    out = _get("/v1/folders/")
    if out.get("status") != "success":
        return out
    return {"status": "success", "folders": out.get("data") or []}


def create_folder(name: str) -> dict[str, Any]:
    body = {"name": name, "embedding_config": _default_embedding_config()}
    out = _post_json("/v1/folders/", body)
    if out.get("status") != "success":
        return out
    return {"status": "success", "folder": out.get("data")}


def list_folder_files(folder_id: str) -> dict[str, Any]:
    out = _get(f"/v1/folders/{folder_id}/files")
    if out.get("status") != "success":
        return out
    return {"status": "success", "files": out.get("data") or []}


def upload_to_folder(folder_id: str, file_bytes: bytes, filename: str, content_type: str) -> dict[str, Any]:
    return _upload(f"/v1/folders/{folder_id}/upload", file_bytes, filename, content_type)


def delete_from_folder(folder_id: str, file_id: str) -> dict[str, Any]:
    return _delete(f"/v1/folders/{folder_id}/{file_id}")


def get_folder_file(folder_id: str, file_id: str) -> dict[str, Any]:
    return _get(f"/v1/folders/{folder_id}/files/{file_id}")


# --- Agent attach/detach ---


def attach_source_to_agent(agent_id: str, source_id: str) -> dict[str, Any]:
    return _patch(f"/v1/agents/{agent_id}/sources/attach/{source_id}")


def detach_source_from_agent(agent_id: str, source_id: str) -> dict[str, Any]:
    return _patch(f"/v1/agents/{agent_id}/sources/detach/{source_id}")


def attach_folder_to_agent(agent_id: str, folder_id: str) -> dict[str, Any]:
    return _patch(f"/v1/agents/{agent_id}/folders/attach/{folder_id}")


def detach_folder_from_agent(agent_id: str, folder_id: str) -> dict[str, Any]:
    return _patch(f"/v1/agents/{agent_id}/folders/detach/{folder_id}")
