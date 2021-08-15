from marshmallow import Schema, fields, EXCLUDE, post_load

from config.model import Config, DockConfig, StockConfig


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class DockConfigSchema(BaseSchema):
    file_path = fields.String(required=True)
    autosave_wait = fields.Integer(required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> DockConfig:
        return DockConfig(**data)


class StockConfigSchema(BaseSchema):
    file_path = fields.String(required=True)
    autosave_wait = fields.Integer(required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> StockConfig:
        return StockConfig(**data)


class ConfigSchema(BaseSchema):
    eddn_relay_url = fields.String(required=True)
    eddn_timeout = fields.Integer(required=True)
    cmd_line_print_wait = fields.Integer(required=True)
    dock = fields.Nested(DockConfigSchema, required=True)
    stock = fields.Nested(StockConfigSchema, required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> Config:
        return Config(**data)
