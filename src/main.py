import uvicorn

from src.infra.api import APIBuilder
from src.settings import cfg

builder = APIBuilder(cfg)
builder.build_stack()
app = builder()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True, access_log=True)
