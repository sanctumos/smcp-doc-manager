# smcp-doc-manager

**Version:** 0.1.0

SMCP plugin for Letta: administer **sources** and **folders** (list, create, list files, upload, delete) and **save markdown as PDF or DOCX** into the Letta file system.

## Requirements

- **Letta API:** `LETTA_BASE_URL` (e.g. `http://127.0.0.1:8284`) and `LETTA_API_KEY` or `LETTA_SERVER_PASSWORD` (Bearer token). SMCP can load these from the Letta server or `~/.letta/.env`.
- **DOCX export:** Pandoc installed on the system (`pandoc` in PATH). Optional if you only use PDF.
- **PDF export:** Uses `markdown-pdf` (pure Python, no LaTeX required).

## Install

Copy this folder into your SMCP `plugins/` directory and make `cli.py` executable:

```bash
cp -r projects/smcp-doc-manager /path/to/smcp/plugins/doc_manager
chmod +x /path/to/smcp/plugins/doc_manager/cli.py
```

Or symlink:

```bash
ln -s /path/to/projects/smcp-doc-manager /path/to/smcp/plugins/doc_manager
```

Install plugin dependencies (in the same env as SMCP or in a venv SMCP can use):

```bash
pip install -r plugins/doc_manager/requirements.txt
```

Restart SMCP so it picks up the plugin.

## Commands (tools)

| Tool | Description |
|------|-------------|
| `doc_manager__list-sources` | List Letta sources |
| `doc_manager__list-folders` | List Letta folders |
| `doc_manager__create-source` | Create a source |
| `doc_manager__create-folder` | Create a folder |
| `doc_manager__list-files` | List files in a source or folder |
| `doc_manager__upload-file` | Upload a file (path or base64) to a source or folder |
| `doc_manager__delete-file` | Delete a file from a source or folder |
| `doc_manager__get-file` | Get file metadata or download URL from a source or folder |
| `doc_manager__markdown-to-pdf` | Convert markdown to PDF; optionally upload to a source or folder |
| `doc_manager__markdown-to-docx` | Convert markdown to DOCX; optionally upload to a source or folder |
| `doc_manager__attach-source-to-agent` | Attach a source to an agent |
| `doc_manager__detach-source-from-agent` | Detach a source from an agent |
| `doc_manager__attach-folder-to-agent` | Attach a folder to an agent |
| `doc_manager__detach-folder-from-agent` | Detach a folder from an agent |

## Usage (via agent)

After attaching the plugin to an agent, the agent can e.g.:

- List sources and folders, create new ones, list files.
- Upload a file from path or from base64 content.
- Convert markdown (inline or from file) to PDF or DOCX and upload to a chosen source or folder.
- Attach/detach sources and folders to/from an agent.

## License

- **Code:** GNU Affero General Public License v3.0 (AGPLv3) — see [LICENSE](LICENSE).
- **Documentation and other non-code:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) — see [LICENSE-DOCS](LICENSE-DOCS).
