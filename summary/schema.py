from eddn.schema import BaseSchema
from marshmallow import Schema, fields, EXCLUDE, post_load
from typing import Any, Mapping, Optional

from summary.model import Commodity, CostSnapshot, StockSummary


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
