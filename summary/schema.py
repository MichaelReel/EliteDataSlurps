from eddn.commodity_v3.schema import BaseSchema
from marshmallow import Schema, fields, EXCLUDE, post_load
from typing import Any, Mapping, Optional

from summary.model import Commodity, CostSnapshot, StockSummary, Station, DockSummary


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class CostSnapshotSchema(BaseSchema):
    system_name = fields.String(required=True)
    station_name = fields.String(required=True)
    timestamp = fields.String(required=True)
    buy_price = fields.Integer(required=True)
    stock = fields.Integer(required=True)
    sell_price = fields.Integer(required=True)
    demand = fields.Integer(required=True)

    market_id = fields.Integer(allow_none=True)
    star_pos = fields.List(fields.Float(), allow_none=True)
    station_type = fields.String(allow_none=True)
    system_address = fields.Integer(allow_none=True)
    dist_from_star_ls = fields.Float(allow_none=True)
    station_allegiance = fields.String(allow_none=True)

    @post_load
    def to_domain(self, data, **kwargs) -> CostSnapshot:
        return CostSnapshot(**data)


class CommoditySchema(BaseSchema):
    name = fields.String(required=True)
    best_buys = fields.List(fields.Nested(CostSnapshotSchema), required=True)
    best_sales = fields.List(fields.Nested(CostSnapshotSchema), required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> Commodity:
        return Commodity(**data)


class StockSummarySchema(BaseSchema):
    commodities = fields.List(fields.Nested(CommoditySchema), Required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> StockSummary:
        return StockSummary(**data)


class StationSchema(BaseSchema):
    market_id = fields.Integer(required=True)
    star_pos = fields.List(fields.Float(), required=True)
    station_name = fields.String(required=True)
    station_type = fields.String(required=True)
    system_address = fields.Integer(required=True)
    system_name = fields.String(required=True)
    timestamp = fields.String(required=True)
    dist_from_star_ls = fields.Float(allow_none=True)
    station_allegiance = fields.String(allow_none=True)

    @post_load
    def to_domain(self, data, **kwargs) -> Station:
        return Station(**data)


class DockSummarySchema(BaseSchema):
    stations = fields.Dict(fields.String(), fields.Nested(StationSchema), Required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> DockSummary:
        return DockSummary(**data)
