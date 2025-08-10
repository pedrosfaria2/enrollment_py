from datetime import datetime

from pydantic import BaseModel, Field

from infra.utils.timezone import tz


class HealthOutput(BaseModel):
    "Is app alive?"

    datetime: str = Field(default_factory=lambda: datetime.now(tz=tz).strftime("%d-%m-%Y %H:%M:%S"), description="Current server timestamp in DD-MM-YYYY HH:MM:SS format")
    status: str = Field(default="ok", description="Application health status indicator")
    environment: str = Field(description="Current deployment environment (dev, test, prod, etc.)")
