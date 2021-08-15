from marshmallow import Schema, fields, EXCLUDE, post_load
from marshmallow.validate import Length

from config.model import Config, DockConfig, StockConfig, CmdLineConfig


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class CmdLineConfigSchema(BaseSchema):
    print_wait = fields.Integer(required=True)
    station_highlights = fields.Dict(fields.String(), fields.String(), required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> CmdLineConfig:
        return CmdLineConfig(**data)


class DockConfigSchema(BaseSchema):
    file_path = fields.String(required=True)
    autosave_wait = fields.Integer(required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> DockConfig:
        return DockConfig(**data)


class StockConfigSchema(BaseSchema):
    file_path = fields.String(required=True)
    autosave_wait = fields.Integer(required=True)
    max_best = fields.Integer(required=True)
    min_stock = fields.Integer(required=True)
    min_demand = fields.Integer(required=True)
    acceptable_station_types = fields.List(fields.String(), required=True)
    origin_coords = fields.List(
        fields.Float(), validate=Length(min=3, max=3), required=True
    )
    max_from_origin = fields.Float(required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> StockConfig:
        return StockConfig(**data)


class ConfigSchema(BaseSchema):
    eddn_relay_url = fields.String(required=True)
    eddn_timeout = fields.Integer(required=True)
    cmd_line = fields.Nested(CmdLineConfigSchema, required=True)
    dock = fields.Nested(DockConfigSchema, required=True)
    stock = fields.Nested(StockConfigSchema, required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> Config:
        return Config(**data)
