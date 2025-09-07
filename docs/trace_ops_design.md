# Trace Ops Design

The Trace Ops module provides a lightweight interface around Unreal's tracing
infrastructure.  It manages a Trace Server lifecycle, builds client connection
flags, lists collected traces, and launches Unreal Insights for analysis.

## Goals

- Offer one-click helpers with copyable CLI previews.
- Keep the UI non-blocking while streaming logs to the central Log panel.
- Avoid destructive actions without a dry-run preview.

## Server Lifecycle

`TraceOpsController` starts `UnrealTraceServer.exe` from the Engine binaries
directory. It automatically searches platform subdirectories to locate the
correct executable. The process runs in the background and can be stopped from
the UI. The default port is `1981` and an optional store directory may be
specified.

## Client Helpers

The page exposes common tracing channels (Bookmark, Frame, CPU, GPU, etc.) and a
host field.  Toggling options updates a copyable snippet like:

```
-trace=Bookmark,Frame,CPU -tracehost=127.0.0.1 -statnamedevents -cpuprofilertrace
```

## Trace Listing and Insights

Collected `.utrace` files in a store directory can be listed and opened in
Unreal Insights with one click.  Batch exports use response files (`.rsp`) to run
Insights headlessly and write CSVs for automation workflows.

## Future Work

The current implementation is intentionally small.  Future revisions may add
store pruning, Android helpers, richer export presets, and tighter integration
with the global artifact tracking system.
