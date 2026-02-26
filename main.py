from __future__ import annotations

from pipes.config.settings import settings

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "pipes.app:app",
        host="0.0.0.0",  # noqa: S104
        port=8080,
        reload=settings.DEBUG,
        loop="asyncio",
    )
