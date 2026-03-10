#!/usr/bin/env python3
"""
SMCP plugin: doc_manager – administer Letta sources/folders and save markdown as PDF or DOCX.

Lets an agent list/create sources and folders, list/upload/delete files,
convert markdown to PDF or DOCX and upload to Letta, and attach/detach sources and folders to agents.
"""

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Local modules
from letta_client import (
    attach_folder_to_agent,
    attach_source_to_agent,
    create_folder,
    create_source,
    delete_from_folder,
    delete_from_source,
    detach_folder_from_agent,
    detach_source_from_agent,
    get_folder_file,
    get_source_file_metadata,
    list_folder_files,
    list_folders,
    list_source_files,
    list_sources,
    upload_to_folder,
    upload_to_source,
)
from md_export import markdown_to_docx, markdown_to_pdf

PLUGIN_VERSION = "0.1.0"
PDF_CONTENT_TYPE = "application/pdf"
DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def get_plugin_description() -> Dict[str, Any]:
    """Return structured plugin description for SMCP --describe."""
    return {
        "plugin": {
            "name": "doc_manager",
            "version": PLUGIN_VERSION,
            "description": "Administer Letta sources and folders (list, create, list files, upload, delete), save markdown as PDF or DOCX into Letta, and attach/detach sources and folders to agents.",
        },
        "commands": [
            {"name": "list-sources", "description": "List all Letta sources.", "parameters": []},
            {"name": "list-folders", "description": "List all Letta folders.", "parameters": []},
            {
                "name": "create-source",
                "description": "Create a new source.",
                "parameters": [{"name": "name", "type": "string", "description": "Source name.", "required": True, "default": None}],
            },
            {
                "name": "create-folder",
                "description": "Create a new folder.",
                "parameters": [{"name": "name", "type": "string", "description": "Folder name.", "required": True, "default": None}],
            },
            {
                "name": "list-files",
                "description": "List files in a source or folder.",
                "parameters": [
                    {"name": "source_id", "type": "string", "description": "Source ID (use if listing source files).", "required": False, "default": None},
                    {"name": "folder_id", "type": "string", "description": "Folder ID (use if listing folder files).", "required": False, "default": None},
                ],
            },
            {
                "name": "upload-file",
                "description": "Upload a file to a source or folder. Provide either --path to a local file or --content (base64) with --filename.",
                "parameters": [
                    {"name": "source_id", "type": "string", "description": "Source ID to upload to.", "required": False, "default": None},
                    {"name": "folder_id", "type": "string", "description": "Folder ID to upload to.", "required": False, "default": None},
                    {"name": "path", "type": "string", "description": "Local file path to upload.", "required": False, "default": None},
                    {"name": "content", "type": "string", "description": "Base64-encoded file content (use with --filename).", "required": False, "default": None},
                    {"name": "filename", "type": "string", "description": "Filename for upload (required when using --content).", "required": False, "default": None},
                    {"name": "content_type", "type": "string", "description": "MIME type (e.g. application/pdf). Inferred from filename if omitted.", "required": False, "default": None},
                ],
            },
            {
                "name": "delete-file",
                "description": "Delete a file from a source or folder.",
                "parameters": [
                    {"name": "source_id", "type": "string", "description": "Source ID.", "required": False, "default": None},
                    {"name": "folder_id", "type": "string", "description": "Folder ID.", "required": False, "default": None},
                    {"name": "file_id", "type": "string", "description": "File ID to delete.", "required": True, "default": None},
                ],
            },
            {
                "name": "get-file",
                "description": "Get file metadata (and download info if available) from a source or folder.",
                "parameters": [
                    {"name": "source_id", "type": "string", "description": "Source ID.", "required": False, "default": None},
                    {"name": "folder_id", "type": "string", "description": "Folder ID.", "required": False, "default": None},
                    {"name": "file_id", "type": "string", "description": "File ID.", "required": True, "default": None},
                ],
            },
            {
                "name": "markdown-to-pdf",
                "description": "Convert markdown to PDF; optionally upload to a source or folder.",
                "parameters": [
                    {"name": "content", "type": "string", "description": "Markdown content to convert.", "required": False, "default": None},
                    {"name": "path", "type": "string", "description": "Path to markdown file (alternative to --content).", "required": False, "default": None},
                    {"name": "filename", "type": "string", "description": "Output filename (e.g. report.pdf). Default: output.pdf", "required": False, "default": "output.pdf"},
                    {"name": "title", "type": "string", "description": "PDF document title.", "required": False, "default": None},
                    {"name": "upload_source_id", "type": "string", "description": "If set, upload PDF to this source.", "required": False, "default": None},
                    {"name": "upload_folder_id", "type": "string", "description": "If set, upload PDF to this folder.", "required": False, "default": None},
                ],
            },
            {
                "name": "markdown-to-docx",
                "description": "Convert markdown to DOCX; optionally upload to a source or folder. Requires pandoc.",
                "parameters": [
                    {"name": "content", "type": "string", "description": "Markdown content to convert.", "required": False, "default": None},
                    {"name": "path", "type": "string", "description": "Path to markdown file (alternative to --content).", "required": False, "default": None},
                    {"name": "filename", "type": "string", "description": "Output filename (e.g. report.docx). Default: output.docx", "required": False, "default": "output.docx"},
                    {"name": "upload_source_id", "type": "string", "description": "If set, upload DOCX to this source.", "required": False, "default": None},
                    {"name": "upload_folder_id", "type": "string", "description": "If set, upload DOCX to this folder.", "required": False, "default": None},
                ],
            },
            {
                "name": "attach-source-to-agent",
                "description": "Attach a source to an agent.",
                "parameters": [
                    {"name": "agent_id", "type": "string", "description": "Agent ID.", "required": True, "default": None},
                    {"name": "source_id", "type": "string", "description": "Source ID.", "required": True, "default": None},
                ],
            },
            {
                "name": "detach-source-from-agent",
                "description": "Detach a source from an agent.",
                "parameters": [
                    {"name": "agent_id", "type": "string", "description": "Agent ID.", "required": True, "default": None},
                    {"name": "source_id", "type": "string", "description": "Source ID.", "required": True, "default": None},
                ],
            },
            {
                "name": "attach-folder-to-agent",
                "description": "Attach a folder to an agent.",
                "parameters": [
                    {"name": "agent_id", "type": "string", "description": "Agent ID.", "required": True, "default": None},
                    {"name": "folder_id", "type": "string", "description": "Folder ID.", "required": True, "default": None},
                ],
            },
            {
                "name": "detach-folder-from-agent",
                "description": "Detach a folder from an agent.",
                "parameters": [
                    {"name": "agent_id", "type": "string", "description": "Agent ID.", "required": True, "default": None},
                    {"name": "folder_id", "type": "string", "description": "Folder ID.", "required": True, "default": None},
                ],
            },
        ],
    }


def _infer_content_type(filename: str) -> str:
    if not filename:
        return "application/octet-stream"
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return PDF_CONTENT_TYPE
    if lower.endswith(".docx"):
        return DOCX_CONTENT_TYPE
    if lower.endswith(".md") or lower.endswith(".markdown"):
        return "text/markdown"
    if lower.endswith(".txt"):
        return "text/plain"
    return "application/octet-stream"


def cmd_list_sources() -> Dict[str, Any]:
    return list_sources()


def cmd_list_folders() -> Dict[str, Any]:
    return list_folders()


def cmd_create_source(name: str) -> Dict[str, Any]:
    if not (name or "").strip():
        return {"status": "error", "error": "name is required."}
    return create_source(name.strip())


def cmd_create_folder(name: str) -> Dict[str, Any]:
    if not (name or "").strip():
        return {"status": "error", "error": "name is required."}
    return create_folder(name.strip())


def cmd_list_files(source_id: str | None, folder_id: str | None) -> Dict[str, Any]:
    if source_id and folder_id:
        return {"status": "error", "error": "Provide either source_id or folder_id, not both."}
    if source_id:
        return list_source_files(source_id)
    if folder_id:
        return list_folder_files(folder_id)
    return {"status": "error", "error": "Provide source_id or folder_id."}


def cmd_upload_file(
    source_id: str | None,
    folder_id: str | None,
    path: str | None,
    content: str | None,
    filename: str | None,
    content_type: str | None,
) -> Dict[str, Any]:
    if source_id and folder_id:
        return {"status": "error", "error": "Provide either source_id or folder_id, not both."}
    if not source_id and not folder_id:
        return {"status": "error", "error": "Provide source_id or folder_id."}

    file_bytes: bytes
    fn: str
    if path:
        p = Path(path)
        if not p.exists():
            return {"status": "error", "error": f"File not found: {path}"}
        file_bytes = p.read_bytes()
        fn = p.name
        ct = content_type or _infer_content_type(fn)
    elif content and filename:
        try:
            file_bytes = base64.b64decode(content)
        except Exception as e:
            return {"status": "error", "error": f"Invalid base64 content: {e}"}
        fn = filename
        ct = content_type or _infer_content_type(fn)
    else:
        return {"status": "error", "error": "Provide either path to a local file or content (base64) with filename."}

    if source_id:
        out = upload_to_source(source_id, file_bytes, fn, ct)
    else:
        out = upload_to_folder(folder_id, file_bytes, fn, ct)
    return out


def cmd_delete_file(source_id: str | None, folder_id: str | None, file_id: str) -> Dict[str, Any]:
    if source_id and folder_id:
        return {"status": "error", "error": "Provide either source_id or folder_id, not both."}
    if source_id:
        return delete_from_source(source_id, file_id)
    if folder_id:
        return delete_from_folder(folder_id, file_id)
    return {"status": "error", "error": "Provide source_id or folder_id."}


def cmd_get_file(source_id: str | None, folder_id: str | None, file_id: str) -> Dict[str, Any]:
    if source_id and folder_id:
        return {"status": "error", "error": "Provide either source_id or folder_id, not both."}
    if source_id:
        return get_source_file_metadata(source_id, file_id)
    if folder_id:
        return get_folder_file(folder_id, file_id)
    return {"status": "error", "error": "Provide source_id or folder_id."}


def cmd_markdown_to_pdf(
    content: str | None,
    path: str | None,
    filename: str,
    title: str | None,
    upload_source_id: str | None,
    upload_folder_id: str | None,
) -> Dict[str, Any]:
    if content is None and path:
        p = Path(path)
        if not p.exists():
            return {"status": "error", "error": f"File not found: {path}"}
        content = p.read_text(encoding="utf-8", errors="replace")
    if not content:
        return {"status": "error", "error": "Provide content or path to a markdown file."}
    out = markdown_to_pdf(content, title=title)
    if out.get("status") != "success":
        return out
    pdf_bytes = out["pdf_bytes"]
    if not filename.lower().endswith(".pdf"):
        filename = filename if filename.endswith(".pdf") else f"{filename}.pdf"
    if upload_source_id:
        u = upload_to_source(upload_source_id, pdf_bytes, filename, PDF_CONTENT_TYPE)
        if u.get("status") != "success":
            return u
        return {"status": "success", "message": "PDF created and uploaded to source.", "upload_result": u.get("data")}
    if upload_folder_id:
        u = upload_to_folder(upload_folder_id, pdf_bytes, filename, PDF_CONTENT_TYPE)
        if u.get("status") != "success":
            return u
        return {"status": "success", "message": "PDF created and uploaded to folder.", "upload_result": u.get("data")}
    return {"status": "success", "message": "PDF created (not uploaded).", "size_bytes": len(pdf_bytes)}


def cmd_markdown_to_docx(
    content: str | None,
    path: str | None,
    filename: str,
    upload_source_id: str | None,
    upload_folder_id: str | None,
) -> Dict[str, Any]:
    if content is None and path:
        p = Path(path)
        if not p.exists():
            return {"status": "error", "error": f"File not found: {path}"}
        content = p.read_text(encoding="utf-8", errors="replace")
    if not content:
        return {"status": "error", "error": "Provide content or path to a markdown file."}
    out = markdown_to_docx(content)
    if out.get("status") != "success":
        return out
    docx_bytes = out["docx_bytes"]
    if not filename.lower().endswith(".docx"):
        filename = filename if filename.endswith(".docx") else f"{filename}.docx"
    if upload_source_id:
        u = upload_to_source(upload_source_id, docx_bytes, filename, DOCX_CONTENT_TYPE)
        if u.get("status") != "success":
            return u
        return {"status": "success", "message": "DOCX created and uploaded to source.", "upload_result": u.get("data")}
    if upload_folder_id:
        u = upload_to_folder(upload_folder_id, docx_bytes, filename, DOCX_CONTENT_TYPE)
        if u.get("status") != "success":
            return u
        return {"status": "success", "message": "DOCX created and uploaded to folder.", "upload_result": u.get("data")}
    return {"status": "success", "message": "DOCX created (not uploaded).", "size_bytes": len(docx_bytes)}


def main() -> None:
    parser = argparse.ArgumentParser(description="doc_manager SMCP plugin – Letta sources/folders and markdown export.")
    parser.add_argument("--describe", action="store_true", help="Output plugin description in JSON")
    sub = parser.add_subparsers(dest="command", help="Commands")

    sub.add_parser("list-sources", help="List Letta sources")
    sub.add_parser("list-folders", help="List Letta folders")
    p_cs = sub.add_parser("create-source", help="Create a source")
    p_cs.add_argument("--name", required=True, help="Source name")
    p_cf = sub.add_parser("create-folder", help="Create a folder")
    p_cf.add_argument("--name", required=True, help="Folder name")

    p_lf = sub.add_parser("list-files", help="List files in source or folder")
    p_lf.add_argument("--source-id", dest="source_id", default=None, help="Source ID")
    p_lf.add_argument("--folder-id", dest="folder_id", default=None, help="Folder ID")

    p_uf = sub.add_parser("upload-file", help="Upload file to source or folder")
    p_uf.add_argument("--source-id", dest="source_id", default=None)
    p_uf.add_argument("--folder-id", dest="folder_id", default=None)
    p_uf.add_argument("--path", default=None, help="Local file path")
    p_uf.add_argument("--content", default=None, help="Base64 file content")
    p_uf.add_argument("--filename", default=None, help="Filename when using --content")
    p_uf.add_argument("--content-type", dest="content_type", default=None)

    p_df = sub.add_parser("delete-file", help="Delete file from source or folder")
    p_df.add_argument("--source-id", dest="source_id", default=None)
    p_df.add_argument("--folder-id", dest="folder_id", default=None)
    p_df.add_argument("--file-id", dest="file_id", required=True)

    p_gf = sub.add_parser("get-file", help="Get file metadata")
    p_gf.add_argument("--source-id", dest="source_id", default=None)
    p_gf.add_argument("--folder-id", dest="folder_id", default=None)
    p_gf.add_argument("--file-id", dest="file_id", required=True)

    p_m2p = sub.add_parser("markdown-to-pdf", help="Convert markdown to PDF; optionally upload")
    p_m2p.add_argument("--content", default=None, help="Markdown content")
    p_m2p.add_argument("--path", default=None, help="Path to .md file")
    p_m2p.add_argument("--filename", default="output.pdf", help="Output filename")
    p_m2p.add_argument("--title", default=None)
    p_m2p.add_argument("--upload-source-id", dest="upload_source_id", default=None)
    p_m2p.add_argument("--upload-folder-id", dest="upload_folder_id", default=None)

    p_m2d = sub.add_parser("markdown-to-docx", help="Convert markdown to DOCX; optionally upload")
    p_m2d.add_argument("--content", default=None)
    p_m2d.add_argument("--path", default=None)
    p_m2d.add_argument("--filename", default="output.docx")
    p_m2d.add_argument("--upload-source-id", dest="upload_source_id", default=None)
    p_m2d.add_argument("--upload-folder-id", dest="upload_folder_id", default=None)

    p_asa = sub.add_parser("attach-source-to-agent", help="Attach source to agent")
    p_asa.add_argument("--agent-id", dest="agent_id", required=True)
    p_asa.add_argument("--source-id", dest="source_id", required=True)
    p_dsa = sub.add_parser("detach-source-from-agent", help="Detach source from agent")
    p_dsa.add_argument("--agent-id", dest="agent_id", required=True)
    p_dsa.add_argument("--source-id", dest="source_id", required=True)
    p_afa = sub.add_parser("attach-folder-to-agent", help="Attach folder to agent")
    p_afa.add_argument("--agent-id", dest="agent_id", required=True)
    p_afa.add_argument("--folder-id", dest="folder_id", required=True)
    p_dfa = sub.add_parser("detach-folder-from-agent", help="Detach folder from agent")
    p_dfa.add_argument("--agent-id", dest="agent_id", required=True)
    p_dfa.add_argument("--folder-id", dest="folder_id", required=True)

    args = parser.parse_args()

    if args.describe:
        print(json.dumps(get_plugin_description(), indent=2))
        sys.exit(0)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    result: Dict[str, Any]
    if args.command == "list-sources":
        result = cmd_list_sources()
    elif args.command == "list-folders":
        result = cmd_list_folders()
    elif args.command == "create-source":
        result = cmd_create_source(args.name)
    elif args.command == "create-folder":
        result = cmd_create_folder(args.name)
    elif args.command == "list-files":
        result = cmd_list_files(getattr(args, "source_id", None), getattr(args, "folder_id", None))
    elif args.command == "upload-file":
        result = cmd_upload_file(
            getattr(args, "source_id", None),
            getattr(args, "folder_id", None),
            getattr(args, "path", None),
            getattr(args, "content", None),
            getattr(args, "filename", None),
            getattr(args, "content_type", None),
        )
    elif args.command == "delete-file":
        result = cmd_delete_file(getattr(args, "source_id", None), getattr(args, "folder_id", None), args.file_id)
    elif args.command == "get-file":
        result = cmd_get_file(getattr(args, "source_id", None), getattr(args, "folder_id", None), args.file_id)
    elif args.command == "markdown-to-pdf":
        result = cmd_markdown_to_pdf(
            getattr(args, "content", None),
            getattr(args, "path", None),
            getattr(args, "filename", "output.pdf"),
            getattr(args, "title", None),
            getattr(args, "upload_source_id", None),
            getattr(args, "upload_folder_id", None),
        )
    elif args.command == "markdown-to-docx":
        result = cmd_markdown_to_docx(
            getattr(args, "content", None),
            getattr(args, "path", None),
            getattr(args, "filename", "output.docx"),
            getattr(args, "upload_source_id", None),
            getattr(args, "upload_folder_id", None),
        )
    elif args.command == "attach-source-to-agent":
        result = attach_source_to_agent(args.agent_id, args.source_id)
    elif args.command == "detach-source-from-agent":
        result = detach_source_from_agent(args.agent_id, args.source_id)
    elif args.command == "attach-folder-to-agent":
        result = attach_folder_to_agent(args.agent_id, args.folder_id)
    elif args.command == "detach-folder-from-agent":
        result = detach_folder_from_agent(args.agent_id, args.folder_id)
    else:
        result = {"status": "error", "error": f"Unknown command: {args.command}"}

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
