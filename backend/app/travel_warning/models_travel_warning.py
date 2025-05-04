from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator

class TravelWarning(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_field_name=True)

    id: str
    last_modified: int = Field(..., alias="lastModified")
    effective: int = Field(..., alias="effective")
    title: str = Field(..., alias="title")
    country_code: str = Field(..., alias="countryCode")
    iso3_country_code: Optional[str] = Field(None, alias="iso3CountryCode")
    country_name: str = Field(..., alias="countryName")
    warning: bool
    partial_warning: bool = Field(..., alias="partialWarning")
    situation_warning: bool = Field(..., alias="situationWarning")
    situation_part_warning: bool = Field(..., alias="situationPartWarning")
    last_changes: str = Field(..., alias="lastChanges")
    content: str
    disclaimer: str

class TravelWarningResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    response: Dict[str, Union[TravelWarning, List[str]]]

    @model_validator(mode="before")
    def _unwrap_and_preprocess(cls, data):
        resp = data.get("response", {})

        # some endpoints wrap under another "response"
        if isinstance(resp, dict) and "response" in resp:
            resp = resp["response"]

        content_list = resp.get("contentList")
        details: Dict[str, dict] = {}

        # inject 'id' into each detail dict
        for key, val in resp.items():
            if isinstance(val, dict):
                val["id"] = key
                details[key] = val

        # re-attach contentList if present
        if isinstance(content_list, list):
            details["contentList"] = content_list

        data["response"] = details
        return data
