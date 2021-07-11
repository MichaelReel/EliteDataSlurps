from marshmallow import Schema, fields, EXCLUDE, post_load
from marshmallow.exceptions import ValidationError
from typing import Any, Mapping, Optional

from eddn.commodity_v3.model import Commodity, CommodityV3, Economy, Header, Message


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class HeaderSchema(BaseSchema):
    uploader_id = fields.String(required=True, data_key="uploaderID")
    software_name = fields.String(required=True, data_key="softwareName")
    software_version = fields.String(required=True, data_key="softwareVersion")
    gateway_timestamp = fields.DateTime(allow_none=True, data_key="gatewayTimestamp")

    @post_load
    def to_domain(self, data, **kwargs) -> Header:
        return Header(**data)


class Bracket(fields.Field):
    """
    Field to accept bracket 0, 1, 2, 3 or "" info
    """
    def _deserialize(self, value: Any, attr: Optional[str], data: Optional[Mapping[str, Any]], **kwargs):
        if isinstance(value, int):
            value = str(value)
        if isinstance(value, str):
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

    @post_load
    def to_domain(self, data, **kwargs) -> Commodity:
        return Commodity(**data)


class EconomySchema(BaseSchema):
    name = fields.String(required=True)
    proportion = fields.Decimal(required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> Economy:
        return Economy(**data)


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

    @post_load
    def to_domain(self, data, **kwargs) -> Message:
        return Message(**data)


class CommodityV3Schema(BaseSchema):
    header = fields.Nested(HeaderSchema, required=True)
    message = fields.Nested(MessageSchema, required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> CommodityV3:
        return CommodityV3(**data)


