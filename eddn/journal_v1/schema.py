from marshmallow import Schema, fields, EXCLUDE, post_load

from eddn.journal_v1.model import JournalV1, Header, Message


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


class MessageSchema(BaseSchema):
    event = fields.String(required=True)
    star_pos = fields.List(fields.Float(), Required=True, data_key="StarPos")
    system_name = fields.String(required=True, data_key="StarSystem")
    system_address = fields.Integer(required=True, data_key="SystemAddress")
    timestamp = fields.DateTime(required=True)

    dist_from_star_ls = fields.Float(allow_none=True, data_key="DistFromStarLS")
    market_id = fields.Integer(allow_none=True, data_key="MarketID")
    station_allegiance = fields.String(allow_none=True, data_key="StationAllegiance")
    station_name = fields.String(allow_none=True, data_key="StationName")
    station_type = fields.String(allow_none=True, data_key="StationType")

    @post_load
    def to_domain(self, data, **kwargs) -> Message:
        return Message(**data)


class JournalV1Schema(BaseSchema):
    header = fields.Nested(HeaderSchema, required=True)
    message = fields.Nested(MessageSchema, required=True)

    @post_load
    def to_domain(self, data, **kwargs) -> JournalV1:
        return JournalV1(**data)
