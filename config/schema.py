from marshmallow import Schema, fields, EXCLUDE, post_load

from config.model import Config


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class ConfigSchema(BaseSchema):
    eddn_relay_url = fields.String(required=True)
    eddn_timeout = fields.Integer(required=True)
    cmd_line_print_wait = fields.Integer(required=True)
    dock_file_path = fields.String(required=True)
    stock_file_path = fields.String(required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> Config:
        return Config(**data)
