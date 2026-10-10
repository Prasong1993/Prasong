# IRIS Control v0.6.18 Plugin Release

Plugin ID: `plugins_6ac62091066c8191beaece899cdc8b8c`

Version: `0.6.18`

Release ID: `pluginrel_6acaa3ae68f08191b192017f2525e78b`

Status: private plugin updated; source read-back confirmed the version, runtime status MCP tool, persisted tool-call telemetry, REST status endpoint, and latest-event ordering fix.

Local validation: isolated SQLite persistence test passed (1 test); Python syntax compilation passed for the database, controller, MCP server, and REST modules.

Not verified: ChatGPT host handshake and host execution. The local environment lacked the Python `mcp` dependency. `route_tool` remains selection-only and does not invoke external providers.

The GitHub branch contains the corresponding database event-ordering fix and regression test. The full plugin package is not claimed to be byte-for-byte synchronized with repository source.