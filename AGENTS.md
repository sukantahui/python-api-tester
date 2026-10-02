# PyRestForge — AI Agent Operating Guidelines & Development Standards

> **Document Type**: Agent Directives, Coding Protocols & Implementation Guardrails  
> **Status**: Active Mandate for all AI & Human Contributors  
> **Applies To**: All code, tests, docs, and configurations within this repository

---

## 1. Primary Directives & Mission

`PyRestForge` is a professional-grade **Desktop REST & GraphQL API Client in Python (PySide6)** designed to match and exceed the visual organization, fluid workflow, and features of **Insomnia**.

As an AI Agent or Developer contributing to this repository, you must maintain:
1. **Insomnia-Level Polish & Arrangement**: Deep hierarchical collections, vivid method badges, rich response inspection, and responsive splitters.
2. **Universal YAML & JSON Fluency**: Robust parsing and export of native YAML/JSON collections, OpenAPI 3.0/3.1 specs, Insomnia v4 bundles, and Postman v2.1 collections.
3. **Decoupled Headless Core**: All models, network execution, serialization, and scripting logic in `src/core/` must remain 100% independent of GUI modules.
4. **100% Non-Blocking UI**: Network calls, file I/O, and script runs must execute on background threads via `QThreadPool` / `QRunnable`, never freezing the main Qt event loop.

---

## 2. Authoritative Documentation Index (`doc/`)

Before implementing or modifying code, consult the authoritative specification documents located in [`doc/`](file:///e:/python%20api%20tester%20like%20insomnia/doc):

| Document | Purpose & Key Contents |
| :--- | :--- |
| [`doc/system_architecture.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/system_architecture.md) | High-level system architecture, data flow pipelines, Mermaid sequence diagrams, threading model, and modular layout |
| [`doc/feature_specifications.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/feature_specifications.md) | Detailed specifications for all 8 Epics: Sidebar Tree, Request Builder, Response Viewer, Environments, YAML/JSON Engine, Scripting, Code Gen, History |
| [`doc/tech_stack_and_engine.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/tech_stack_and_engine.md) | Tech stack rationale (`PySide6`, `httpx`, `pydantic v2`, `ruamel.yaml`, `pygments`), network engine, and performance benchmarks |
| [`doc/ui_ux_design.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/ui_ux_design.md) | Dark mode design tokens, layout wireframes, Method Badges, component hierarchy, and keyboard shortcuts |
| [`doc/testing_and_verification.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/testing_and_verification.md) | Test suite strategy, unit tests, `respx` HTTP mocking, `pytest-qt` GUI tests, and YAML/JSON round-trip verification |
| [`doc/user_manual.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/user_manual.md) | End-user installation, workspace management, environment variables, request chaining, and troubleshooting FAQ |
| [`doc/project_documentation.md`](file:///e:/python%20api%20tester%20like%20insomnia/doc/project_documentation.md) | Phased implementation roadmap, file-by-file task checklist, module matrix, and Definition of Done |

---

## 3. Directory Layout & Code Organization

Every contribution must strictly follow this modular layout:

```text
python-api-tester/
│
├── AGENTS.md                        # AI Agent Operating Guidelines (this file)
├── PROJECT_SPEC.md                  # Master Architectural Blueprint & Core Specs
├── README.md                        # User setup, installation, and quickstart guide
├── requirements.txt                 # Pinned dependencies
├── pyproject.toml                   # Packaging configuration
├── run.bat / run.ps1 / run.sh       # One-click startup scripts
├── setup.bat                        # Virtual environment setup script
│
├── doc/                             # Authoritative Documentation Suite
│   ├── system_architecture.md       # High-level architecture & diagrams
│   ├── feature_specifications.md    # Functional specs & parameter schemas
│   ├── tech_stack_and_engine.md     # Technology choices & performance targets
│   ├── ui_ux_design.md              # UI wireframes & design tokens
│   ├── testing_and_verification.md  # Test suite strategy & fixtures
│   ├── user_manual.md               # User guide & troubleshooting
│   └── project_documentation.md     # Implementation roadmap & task checklist
│
├── src/
│   ├── __init__.py
│   ├── main.py                      # Application entry point & Qt event loop
│   │
│   ├── core/                        # Headless Core Business Logic (Zero GUI dependencies)
│   │   ├── __init__.py
│   │   ├── models/                  # Pydantic v2 domain schemas
│   │   │   ├── __init__.py
│   │   │   ├── workspace.py         # Workspace & project schemas
│   │   │   ├── folder.py            # Hierarchical folder structure
│   │   │   ├── request.py           # HTTP Request model (URL, method, headers, auth, body)
│   │   │   ├── response.py          # HTTP Response model (status, headers, body, timings)
│   │   │   ├── environment.py       # Global, workspace, and sub-environment variables
│   │   │   ├── auth.py              # Auth models (Basic, Bearer, APIKey, OAuth2, Digest)
│   │   │   └── history.py           # Execution history entry schemas
│   │   │
│   │   ├── engine/                  # Network & Execution Engine
│   │   │   ├── __init__.py
│   │   │   ├── http_client.py       # Async HTTP/1.1 & HTTP/2 client using httpx
│   │   │   ├── interpolator.py      # Variable interpolation engine {{var}} & generators
│   │   │   ├── script_runner.py     # Python script execution sandbox for pre/post scripts
│   │   │   ├── cookie_manager.py    # RFC 6265 cookie jar manager
│   │   │   ├── cert_manager.py      # SSL certificate & client cert handler
│   │   │   └── network_timing.py    # Detailed DNS, TLS, TTFB network timeline profiler
│   │   │
│   │   ├── serializers/             # Multi-Format Ingestion & Export Engine
│   │   │   ├── __init__.py
│   │   │   ├── yaml_serializer.py   # High-fidelity YAML serializer/deserializer
│   │   │   ├── json_serializer.py   # Fast JSON serializer/deserializer
│   │   │   ├── openapi_parser.py    # OpenAPI 3.0 / 3.1 & Swagger 2.0 importer/exporter
│   │   │   ├── insomnia_parser.py   # Insomnia v4 Export YAML/JSON parser & generator
│   │   │   ├── postman_parser.py    # Postman Collection v2.1 importer & exporter
│   │   │   └── curl_parser.py       # cURL command parser & multi-language code generator
│   │   │
│   │   └── storage/                 # Data Persistence & File I/O
│   │       ├── __init__.py
│   │       ├── workspace_store.py   # Local workspace file storage manager
│   │       ├── history_store.py     # Execution history storage
│   │       └── config_store.py      # User preferences and app settings
│   │
│   ├── gui/                         # Presentation Layer (PySide6 / Qt6)
│   │   ├── __init__.py
│   │   ├── app.py                   # Main Window & primary layout orchestration
│   │   ├── theme.py                 # Design tokens, dark/light palette, QSS stylesheets
│   │   ├── state.py                 # Application state controller & Qt signals
│   │   │
│   │   ├── components/              # Modular Reusable UI Widgets
│   │   │   ├── __init__.py
│   │   │   ├── sidebar.py           # Workspace, Folder, and Request TreeView
│   │   │   ├── url_bar.py           # Method selector, URL input, Send/Cancel buttons
│   │   │   ├── request_tabs.py      # Tab container (Params, Headers, Auth, Body, Scripts)
│   │   │   ├── key_value_table.py   # Reusable Key-Value-Description table with checkboxes
│   │   │   ├── auth_widget.py       # Multi-type Authentication configuration widget
│   │   │   ├── body_widget.py       # Multi-mode Body editor (JSON, Form, Raw, GraphQL, File)
│   │   │   ├── response_viewer.py   # Response Inspector, Pretty/Raw/Preview, Status, Timings
│   │   │   ├── code_editor.py       # Syntax-highlighted code editor (JSON/YAML/Python)
│   │   │   └── history_widget.py    # Request execution history drawer
│   │   │
│   │   └── dialogs/                 # Modal & Configuration Windows
│   │       ├── __init__.py
│   │       ├── env_dialog.py        # Environment variables manager dialog
│   │       ├── import_export.py     # Import/Export wizard (YAML, JSON, OpenAPI, Postman)
│   │       ├── code_gen_dialog.py   # Multi-language code snippet generator modal
│   │       ├── settings_dialog.py   # App settings (Proxy, SSL, Timeout, Font size)
│   │       └── cert_dialog.py       # Client SSL Certificates manager
│   │
│   └── utils/                       # Shared Utilities
│       ├── __init__.py
│       ├── logger.py                # Structured rotating logger
│       ├── syntax_highlighter.py    # PySide6 QSyntaxHighlighter for JSON, YAML, XML, Python
│       ├── formatters.py            # Data size (KB/MB), latency (ms), JSON/XML pretty printers
│       └── helpers.py               # Path helpers, platform detection, clipboard wrappers
│
├── tests/                           # Comprehensive Test Suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures, mock HTTP servers, sample YAML/JSON
│   ├── test_http_engine.py          # Network client, methods, headers, auth, timeouts
│   ├── test_interpolator.py         # Variable interpolation & generator tests
│   ├── test_yaml_serializer.py      # YAML import/export fidelity tests
│   ├── test_json_serializer.py      # JSON import/export tests
│   ├── test_openapi_parser.py       # OpenAPI 3.0/3.1 import/export tests
│   ├── test_insomnia_parser.py      # Insomnia v4 import/export tests
│   ├── test_postman_parser.py       # Postman v2.1 import/export tests
│   ├── test_curl_parser.py          # cURL parsing & code generation tests
│   ├── test_script_runner.py        # Pre-request and test assertion sandbox tests
│   └── test_gui_components.py       # PySide6 widget tests with pytest-qt
│
└── samples/                         # Sample Collections & Specs
    ├── sample_collection.yaml       # PyRestForge native YAML collection sample
    ├── sample_collection.json       # PyRestForge native JSON collection sample
    ├── sample_openapi.yaml          # Sample OpenAPI 3.1 specification
    ├── sample_insomnia_export.json  # Sample Insomnia v4 export file
    └── sample_postman_v21.json      # Sample Postman v2.1 collection
```

---

## 4. Coding Standards & Implementation Rules

1. **Strict Type Annotations**: Every function, method, argument, and return value must have Python 3.10+ type hints (`typing.Optional`, `typing.List`, `typing.Dict`, `pathlib.Path`, `pydantic.BaseModel`).
2. **Headless Decoupling**: Never import `PySide6`, `PyQt6`, or GUI modules in `src/core/` or `src/utils/`. The core engine must be runnable from CLI or automated test runners headlessly.
3. **Thread Safety**: Never block the Qt GUI thread. Dispatch network requests, heavy YAML/JSON parsing, and scripting tasks to `QThreadPool` worker threads, communicating status via Qt signals.
4. **No Incomplete Implementations / Placeholders**: Write complete, production-ready code with proper exception handling, parameter validation, and meaningful log messages. Do not use `# TODO` or `pass` shortcuts for core functionality.
5. **Robust Error Handling**: Wrap network calls, file reading/writing, and deserialization in `try-except` blocks, logging errors with `src/utils/logger.py` and dispatching user-friendly error banners in the GUI.
6. **Test-Driven Verification**: Every new engine, parser, or feature must be accompanied by unit tests in `tests/` and validated against real sample YAML/JSON files.
