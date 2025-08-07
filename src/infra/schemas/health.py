from datetime import datetime

from pydantic import BaseModel

from infra.utils.timezone import tz


class HealthOutput(BaseModel):
    "Is app alive?"

    datetime: str = datetime.now(tz=tz).strftime("%d-%m-%Y %H:%M:%S")
    status: str = "ok"
    environment: str
