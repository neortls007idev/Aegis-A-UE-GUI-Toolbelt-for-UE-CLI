# Coding Standards

Applies across this repo (UE modules/plugins and local tooling). Prefer clarity over cleverness and consistency over preference.

> **Highlights:** **Allman braces**, **spaces inside parentheses** (`if ( condition )`), **methods PascalCase**, **variables camelCase**, **members `mXxx`**, **files PascalCase**. UE types keep `U/A/F/S/I/T/E` prefixes.

---

## General
- UTF-8 (no BOM), LF endings, 4 spaces, soft wrap at 120.
- One class/struct per file (except tiny PODs/private details).
- No trailing whitespace; newline at EOF.
- Avoid UB; initialize everything; explicit casts.
- Third‑party code stays pristine; document patches at file top.

## C++ (Unreal)
- **Dialect**: C++17+ supported by current UE toolchain.
- **Warnings**: treat new warnings as errors (CI); disable with local, commented pragmas only.
- **Naming**: UE classes `U/A/F/S/I/T/E` + PascalCase; other classes PascalCase; methods/free functions PascalCase; vars camelCase; members `m`+PascalCase; globals `gXxx` (rare); constants `kXxx` or `static constexpr`; enums `EType` with PascalCase enumerators; booleans positive names.
- **Includes/IWYU**: `#pragma once`; include order: matched header → local module → project → third‑party → std; forward‑declare in headers; avoid `using namespace` in headers; follow IWYU.
- **Formatting**: Allman braces; spaces inside parens; pointer/reference bind to type; `switch` always has `default:`; multiline initializer lists = one member/line.
- **Classes**: `final` when appropriate; `override` always; members `private` by default; `= delete`/`= default` where helpful; init in‑class or ctor list; avoid virtual dtor unless needed.
- **Functions**: pass non‑trivials by `const&`; trivials by value; use `const`/`constexpr`/`noexcept`; prefer returns over out‑params; mark single‑arg ctors `explicit`.
- **Variables**: initialize on declaration; judicious `auto`; prefer `FDateTime/FTimespan` or `std::chrono`.
- **Enums**: prefer `enum class`; set underlying type when ABI matters; do not rely on order.
- **Memory (UE)**: never `delete` UObjects; use `UPROPERTY` + `TObjectPtr` (UE5+). For non‑UObject: `TUniquePtr`, `TSharedPtr/Ref`, `TWeakPtr`. Prefer `TArray/TMap/TSet` in engine‑facing code. `FText` (localized), `FString`, `FName`.
- **Errors/Logs**: programmer errors via `check/checkf/ensure`; runtime failures via status types (no spam). Use `UE_LOG` with categories; minimal logs in Shipping (`#if !UE_BUILD_SHIPPING`).
- **Concurrency**: UE primitives (`AsyncTask`, `FRunnable`, `Tasks::`); do not touch UObjects off game thread; marshal with `AsyncTask( ENamedThreads::GameThread, … )`.
- **Modules**: one `*Module` (IModuleInterface); export with `AegisToolbelt_API` (or module API macro); keep private code under **Private**; keep Build.cs lean.
- **Reflection/Gameplay**: macros directly above members; Blueprint callable names are verbs; pure nodes have no side effects; editor‑only code behind `#if WITH_EDITOR`; set up replication explicitly.

## Python Tooling
- Python 3.11+; `snake_case` functions/vars, `PascalCase` classes; files `snake_case`.
- Format with `black` (≤100 cols); type‑check with `mypy`; lint with `ruff`.
- No `shell=True`; pass argv lists; stream stdout/err; propagate exit codes.
- Never block UI threads; run long tasks on workers and marshal results back.
- Redact secrets in logs; echo external commands in verbose/debug.

## Build/Docs/Git
- Scripts idempotent and non‑interactive by default; parameterize paths.
- JSON/YAML/TOML: 2‑space indent; stable key order; newline at EOF.
- Doxygen‑style headers for public C++ APIs; comments explain *why*.
- Branches: `feat/`, `fix/`, `chore/`, `docs/`, `refactor/`; conventional commits.
- PRs small and single‑purpose; screenshots for UI diffs; CI must pass.

---

## Porting Aegis to C++ (Gradual)
1. **Stable CLI boundary**: new C++/UE tools read JSON (`-Input=path.json`) and emit JSON to stdout.
2. **Schemas** under `schemas/` define requests/responses; version them and keep backward compatibility for ≥1 minor.
3. **Feature parity switch**: Python orchestrator accepts `--impl={python,cxx}` per feature; promote `cxx` to default when ready.
4. **Commandlets** for long UE tasks; expose succinct status JSON.
5. **Exit codes**: `0 OK, 2 UserError, 3 EnvError, 4 ToolError, 5 Internal`.
