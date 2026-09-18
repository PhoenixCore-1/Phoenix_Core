"""Development launcher for the Phoenix Core HTTP API."""

import uvicorn

from phoenix_core.http_api.app import create_development_app


app = create_development_app()


if __name__ == "__main__":
    uvicorn.run("phoenix_core.http_api.__main__:app", host="127.0.0.1", port=8000, reload=True)
