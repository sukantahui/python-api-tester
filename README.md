# PyRestForge — Desktop API Client & Testing Studio

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=for-the-badge&logo=python&logoColor=white)
![UI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![HTTP Engine](https://img.shields.io/badge/Engine-httpx%20(HTTP%2F2)-9B51E0?style=for-the-badge)
![Format Support](https://img.shields.io/badge/Formats-YAML%20%7C%20JSON%20%7C%20OpenAPI%20%7C%20Insomnia%20%7C%20Postman-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A modern, high-performance, cross-platform Desktop API Client and Testing Studio written in Python, featuring the refined organization and visual elegance of Insomnia with native YAML/JSON collection management, OpenAPI sync, and Python-native script assertions.**

[Key Features](#key-features) • [Quickstart](#quickstart--installation) • [Architecture](#system-architecture) • [Documentation](#authoritative-documentation) • [Shortcuts](#keyboard-shortcuts)

</div>

---

## Overview

**PyRestForge** is built for developers who love the clean arrangement, intuitive hierarchy, and dark aesthetic of **Insomnia**, but need the power of a **pure Python stack**, instant **YAML and JSON collection import/export**, native **OpenAPI 3.0/3.1** synchronization, asynchronous **HTTP/2 multiplexing**, and scriptable **Python test assertions**.

```text
+---------------------------------------------------------------------------------------------------------------+
|  PyRestForge   [Workspace: Billing Service v1 v]  [Env: Production v]  [+ New Request]  [Import] [Export] [⚙]  |
+------------------------------------+------------------------------------------+-------------------------------+
| SIDEBAR (Collections & Folders)    | REQUEST BUILDER                          | RESPONSE INSPECTOR            |
|                                    |                                          |                               |
| [🔍 Filter requests...]            | [POST v] [https://api.example.com/v1/auth/login ]  [Send (Ctrl+Enter)] |
|                                    +------------------------------------------+-------------------------------+
| v 📁 Authentication               | [Params (2)] [Headers (3)] [Auth] [Body*]| [200 OK]  [142 ms]  [3.2 KB]  |
|    [POST] Login User               +------------------------------------------+-------------------------------+
|    [POST] Refresh Token            | Mode: (o) JSON  ( ) Form  ( ) Raw  ( ) GQL| [Pretty] [Raw] [Preview] [Hdr]|
|    [GET]  Get Current User         | 1  {                                     | 1  {                          |
| v 📁 Users Management              | 2    "email": "{{user_email}}",          | 2    "status": "success",     |
|    [GET]  List Users               | 3    "password": "{{SECRET:user_pwd}}"   | 3    "access_token": "eyJ...",|
|    [POST] Create User              | 4  }                                     | 4    "expires_in": 3600       |
|    [PUT]  Update Profile           |                                          | 5  }                          |
|    [DEL]  Delete Account           |                                          |                               |
| > 📁 Subscriptions & Payments     |                                          |                               |
+------------------------------------+------------------------------------------+-------------------------------+
| Status: Connected | HTTP/2 | SSL: Verified | Proxy: Off                      | JSONPath: [$.access_token   ] |
+---------------------------------------------------------------------------------------------------------------+
```

---

## Key Features

- 🗂️ **Insomnia-Grade Collection Arrangement**: Deeply nested folders, requests, vibrant HTTP method badges, drag-and-drop reordering, and instant fuzzy search.
- 📄 **YAML & JSON Ingestion & Export**:
  - Native **YAML** & **JSON** collection format with round-trip comment and order preservation.
  - **OpenAPI 3.0 / 3.1 & Swagger 2.0** YAML/JSON import and export.
  - **Insomnia v4** Export bundle parser and generator.
  - **Postman Collection v2.1** import and export.
  - **cURL** command parser (paste cURL to request) and multi-language code generation (Python, cURL, JS, Go, Java, PHP).
- ⚡ **Asynchronous HTTP/2 Network Engine**: Built on `httpx` with persistent connection pooling, streaming uploads/downloads, SSL client certificate management, proxy support, and detailed network timeline diagnostics (DNS, TLS, TTFB, transfer duration).
- 🌍 **Hierarchical Environments & Dynamic Variables**:
  - Global, Workspace, and Sub-Environments (`Local`, `Staging`, `Production`).
  - Double-curly syntax (`{{baseUrl}}/users/{{userId}}`) with syntax highlighting and autocomplete.
  - Built-in dynamic data generators: `{{$guid}}`, `{{$timestamp}}`, `{{$isoTimestamp}}`, `{{$randomEmail}}`, `{{$randomInt, 1, 100}}`.
  - Sensitive variable masking (`{{SECRET:api_key}}`).
- 🐍 **Python-Powered Scripting & Chaining**:
  - Pre-request script hooks to compute hashes, signatures, and dynamic parameters.
  - Post-response test assertion suites (e.g. `assert res.status_code == 200`).
  - Automatic token capture into active environment variables for subsequent requests.
- 🎨 **Modern Dark-Mode Qt GUI**: High-DPI, ultra-responsive UI built with PySide6, custom QSS styling, syntax-highlighted code editors with code folding, and zero Electron bloat.

---

## Authoritative Documentation

All architectural decisions, technical specifications, and user manuals are fully documented in the [`doc/`](file:///e:/python%20api%20tester%20like%20insomnia/doc) directory:

- 🏛️ [`doc/system_architecture.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/system_architecture.md): Subsystems, async pipelines, Mermaid sequence diagrams, threading model.
- 📋 [`doc/feature_specifications.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/feature_specifications.md): In-depth specs for all 8 Epics, data schemas, and badging.
- ⚙️ [`doc/tech_stack_and_engine.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/tech_stack_and_engine.md): Technology rationale, performance benchmarks, and engine details.
- 🎨 [`doc/ui_ux_design.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/ui_ux_design.md): Dark/Light theme design tokens, layout wireframes, and shortcuts.
- 🧪 [`doc/testing_and_verification.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/testing_and_verification.md): Test suite strategy, HTTP mocking with `respx`, and `pytest-qt`.
- 📖 [`doc/user_manual.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/user_manual.md): End-user guide, variable interpolation, chaining, and FAQ.
- 🗺️ [`doc/project_documentation.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/project_documentation.md): Phased roadmap, agent task breakdown, and definition of done.
- 🤖 [`AGENTS.md`](file:///e:/python%20api%20tester%20like%20insomnia/AGENTS.md): AI Agent Operating Guidelines & implementation guardrails.
- 📐 [`PROJECT_SPEC.md`](file:///e:/python%20api%20tester%20like%20insomnia/PROJECT_SPEC.md): Master Architectural Blueprint & Core Specs.

---

## Quickstart & Installation

### 1. Prerequisites
- Python 3.10+ (Python 3.10, 3.11, 3.12, or 3.13)
- Windows 10/11, macOS, or Linux

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/your-org/pyrestforge.git
cd pyrestforge

# Create and activate virtual environment
python -m venv .venv
# On Windows (PowerShell / Command Prompt):
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launching Application
```bash
# Launch via Python
python src/main.py

# Or use one-click scripts
# Windows:
.\run.bat
# Linux / macOS:
./run.sh
```

---

## Keyboard Shortcuts

| Shortcut (Win/Linux) | Shortcut (macOS) | Action |
| :--- | :--- | :--- |
| `Ctrl + Enter` | `Cmd + Return` | **Send Request** |
| `Ctrl + N` | `Cmd + N` | **New Request** |
| `Ctrl + Shift + N` | `Cmd + Shift + N` | **New Folder** |
| `Ctrl + F` | `Cmd + F` | **Filter / Search Requests** |
| `Ctrl + E` | `Cmd + E` | **Manage Environments** |
| `Ctrl + I` | `Cmd + I` | **Import Collection (YAML / JSON / OpenAPI)** |
| `Ctrl + Shift + E` | `Cmd + Shift + E` | **Export Collection** |
| `Ctrl + Shift + C` | `Cmd + Shift + C` | **Copy Request as cURL** |
| `Ctrl + Shift + F` | `Cmd + Shift + F` | **Format / Prettify JSON Body** |
| `Ctrl + \` | `Cmd + \` | **Toggle Sidebar** |

---

## License

This project is licensed under the MIT License.
