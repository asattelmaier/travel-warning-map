from datetime import datetime
from typing import Optional, Dict, Union, List, Any

from pydantic import BaseModel, Field, ConfigDict, model_validator, computed_field


class TravelWarning(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_field_name=True,
    )

    id: str
    country: str = Field(..., alias="countryName")
    country_code: str = Field(..., alias="countryCode")
    iso3_country_code: Optional[str] = Field(None, alias="iso3CountryCode")
    title: str = Field(..., alias="title")
    last_updated: datetime = Field(..., alias="lastModified")
    effective: datetime = Field(..., alias="effective")
    warning: bool = Field(..., alias="warning")
    partial_warning: bool = Field(..., alias="partialWarning")
    situation_warning: bool = Field(..., alias="situationWarning")
    situation_part_warning: bool = Field(..., alias="situationPartWarning")

    @model_validator(mode="before")
    def _convert_timestamps(cls, data):
        if not isinstance(data, dict):
            return data
        for key in ("lastModified", "effective"):
            v = data.get(key)
            if isinstance(v, (int, float)):
                data[key] = datetime.fromtimestamp(v)
        return data

    @computed_field
    def warning_level(self) -> str:
        if self.warning:
            return "red"
        if self.partial_warning or self.situation_part_warning:
            return "yellow"
        if self.situation_warning:
            return "orange"
        return "green"


class TravelWarningsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # TravelWarning first so dicts parse as TravelWarning; contentList as List[str]
    response: Dict[str, Union[TravelWarning, List[str]]]

    @model_validator(mode="before")
    def _preprocess_response(cls, data):
        raw = data.get("response", {}) or {}
        filtered: Dict[str, Any] = {}
        content_list = raw.get("contentList")

        # inject id then keep each warning dict
        for key, val in raw.items():
            if isinstance(val, dict):
                val["id"] = key
                filtered[key] = val

        # reattach contentList
        if isinstance(content_list, list):
            filtered["contentList"] = content_list

        data["response"] = filtered
        return data
