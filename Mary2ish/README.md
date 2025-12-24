## Mary2ish Runtime Notes

- The container uses the prebuilt virtual environment at `/app/.venv`.
- Entry point runs `streamlit run main.py` (no `uv run`) so installed packages like `mcp_agent` resolve correctly from the venv.
- Rebuild after changes: `podman-compose build --no-cache && podman-compose up -d`.
