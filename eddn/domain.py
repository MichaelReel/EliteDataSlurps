from marshmallow import Schema, fields, EXCLUDE
from marshmallow.exceptions import ValidationError
from typing import Any, Mapping, Optional


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class HeaderSchema(BaseSchema):
    uploader_id = fields.String(required=True, data_key="uploaderID")
    software_name = fields.String(required=True, data_key="softwareName")
    software_version = fields.String(required=True, data_key="softwareVersion")
    gateway_timestamp = fields.DateTime(allow_none=True, data_key="gatewayTimestamp")


class Bracket(fields.Field):
    """
    Field to accept bracket 0, 1, 2, 3 or "" info
    """
    def _deserialize(self, value: Any, attr: Optional[str], data: Optional[Mapping[str, Any]], **kwargs):
        if isinstance(value, str) or isinstance(value, int):
            return super()._deserialize(value, attr, data, **kwargs)
        else:
            raise ValidationError("Bracket should be int or \"\"")


class CommoditySchema(BaseSchema):
    name = fields.String(required=True)
    mean_price = fields.Integer(required=True, data_key="meanPrice")
    buy_price = fields.Integer(required=True, data_key="buyPrice")
    stock = fields.Integer(required=True)
    stock_bracket = Bracket(required=True, data_key="stockBracket")
    sell_price = fields.Integer(required=True, data_key="sellPrice")
    demand = fields.Integer(required=True)
    demand_bracket = Bracket(required=True, data_key="demandBracket")
    status_flags = fields.List(fields.String(required=True), allow_none=True, data_key="statusFlags")

class EconomySchema(BaseSchema):
    name = fields.String(required=True)
    proportion = fields.Decimal(required=True)

class MessageSchema(BaseSchema):
    system_name = fields.String(required=True, data_key="systemName")
    station_name = fields.String(required=True, data_key="stationName")
    market_id = fields.Integer(required=True, data_key="marketId")
    timestamp = fields.DateTime(required=True)
    commodities = fields.List(fields.Nested(CommoditySchema), required=True)
    economies = fields.List(fields.Nested(EconomySchema), allow_none=True)
    prohibited = fields.List(fields.String(), allow_none=True)
    horizons = fields.Bool(allow_none=True)
    odyssey = fields.Bool(allow_none=True)


class CommodityV3Schema(BaseSchema):
    header = fields.Nested(HeaderSchema, required=True)
    message = fields.Nested(MessageSchema, required=True)


