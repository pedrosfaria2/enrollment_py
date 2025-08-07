import uvicorn

from src.infra.api import APIBuilder
from src.settings import cfg

apis = APIBuilder(cfg)
apis.build_stack()
app = apis.app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, access_log=True, reload=True)
