"""Database enums"""

from enum import Enum

from db import db


# using a dynamic value for the enum name is not good practice.
# TODO: fix

# Settings
_settings_data = db.records("SELECT id, safe_name FROM settings")
_settings_map = {name: _id for _id, name in _settings_data}
UserSettingsNames = Enum("UserSettingsNames", _settings_map)

# Category Purposes
_cat_purposes_data = db.records(
    "SELECT id, name FROM purposes WHERE purpose_type_id = "
    "(SELECT id FROM purpose_types WHERE name = 'category')"
)
_cat_purposes_map = {name: _id for _id, name in _cat_purposes_data}
CategoryPurposes = Enum("RolePurposes", _cat_purposes_map)

# Channel Purposes
_channel_purposes_data = db.records(
    "SELECT id, name FROM purposes WHERE purpose_type_id = "
    "(SELECT id FROM purpose_types WHERE name = 'channel')"
)
_channel_purposes_map = {name: _id for _id, name in _channel_purposes_data}
ChannelPurposes = Enum("ChannelPurposes", _channel_purposes_map)

# Role Purposes
_role_purposes_data = db.records(
    "SELECT id, name FROM purposes WHERE purpose_type_id = "
    "(SELECT id FROM purpose_types WHERE name = 'role')"
)
_role_purposes_map = {name: _id for _id, name in _role_purposes_data}
RolePurposes = Enum("RolePurposes", _role_purposes_map)