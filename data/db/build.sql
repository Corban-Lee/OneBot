
-- Store the birthday of the user
CREATE TABLE IF NOT EXISTS user_birthdays (
    user_id INTEGER PRIMARY KEY,
    birthday TEXT NOT NULL
);

-- Used as a foreign key in many tables
CREATE TABLE IF NOT EXISTS guilds (
    guild_id INTEGER PRIMARY KEY,
    prefix TEXT NOT NULL DEFAULT '!'
);

-- Level/XP system
CREATE TABLE IF NOT EXISTS member_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL,
    experience INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEy (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);

-- Guild mute list
CREATE TABLE IF NOT EXISTS guild_mutes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL,
    reason TEXT,
    end_datetime TEXT NOT NULL,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);

-- Purpose types are discord objects that a purpose can be assigned to
-- e.g. a channel or a role
CREATE TABLE IF NOT EXISTS purpose_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL
);

-- Add the default purpose types
INSERT OR IGNORE INTO purpose_types (name, description) VALUES
    ('category', 'Category'),
    ('channel', 'Channel'),
    ('role', 'Role');

-- Table to store purposes
-- A purpose just tells the bot what an object is for
CREATE TABLE IF NOT EXISTS purposes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purpose_type_id INTEGER NOT NULL,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    FOREIGN KEY (purpose_type_id) REFERENCES purpose_types(id) ON DELETE CASCADE
);

-- Add the default purposes
INSERT OR IGNORE INTO purposes (purpose_type_id, name, description) VALUES 
    ((SELECT id FROM purpose_types WHERE name = 'category'), 'tickets', 'Ticket channels are created here'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'general', 'The general conversation channel'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'announcements', 'Location to find server announcements'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'rules', 'Location to find server rules'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'welcome', 'Send "member joinged" notifications here'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'goodbye', 'Send "member left" notifications here'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'botlogs', 'Logs for Bot Actions'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'guildlogs', 'Logs for the Server'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'member', 'Auto-assigned Member Role'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'muted', 'Muted'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'mod', 'Moderator'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'admin', 'Administrator'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'owner', 'Server Owner'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'birthday', "Signifies a user's birthday");

-- Table to store the purpose of a discord object
CREATE TABLE IF NOT EXISTS purposed_objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purpose_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL,
    FOREIGN KEY (purpose_id) REFERENCES purposes(id) ON DELETE CASCADE,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
    UNIQUE (purpose_id, object_id) ON CONFLICT REPLACE
);

-- Settings --------------------------------------------------------------------

-- Table to store settings (not settings values)
CREATE TABLE IF NOT EXISTS settings_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    default_text_value TEXT NOT NULL,
    default_int_value INTEGER NOT NULL,
    is_guild_setting INTEGER NOT NULL DEFAULT 0
);

-- Insert the settings options
INSERT OR IGNORE INTO settings_options (name, description, default_text_value, default_int_value, is_guild_setting) VALUES
    ("lvl_alert", "Level Up Alert", "", 1, 0),
    ("join_msg", "Member join notifications message", "Welcome to the server!", "", 1),
    ("leave_msg", "Member left notifications message", "Goodbye!", "", 1),
    ("hide_bot_cmd", "Hide bot commands outside bot channels", "", 0, 1);

-- Alternative names for settings option values
CREATE TABLE IF NOT EXISTS settings_value_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    option_id INTEGER NOT NULL,
    name TEXT NOT NULL UNIQUE,
    text_value TEXT NOT NULL,
    int_value INT NOT NULL,
    FOREIGN KEY (option_id) REFERENCES settings_options(id) ON DELETE CASCADE
);

-- use these as values, if none are found then it's a string input type
INSERT OR IGNORE INTO settings_value_types (option_id, name, text_value, int_value) VALUES
    ((SELECT id FROM settings_options WHERE name = "lvl_alert"), "enabled", "", 1),
    ((SELECT id FROM settings_options WHERE name = "lvl_alert"), "disabled", "", 0);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER NOT NULL UNIQUE, -- Guild ID or User ID
    option_id INTEGER NOT NULL,
    text_value TEXT NOT NULL,
    int_value INTEGER NOT NULL,
    FOREIGN KEY (option_id) REFERENCES settings_options(id) ON DELETE CASCADE,
    UNIQUE (object_id, option_id) ON CONFLICT REPLACE
);

--------------------------------------------------------------------------------

-- #36 - Rewrite tickets system
-- Store user created tickets
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    timestamp INTEGER NOT NULL,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);

-- #76 - Add Reaction Roles
-- Store Reaction Roles Here
CREATE TABLE IF NOT EXISTS reaction_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    emoji TEXT NOT NULL, 
    role_id INTEGER NOT NULL,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);

-- #77 Write Economy System
-- Store User Balances Here
CREATE TABLE IF NOT EXISTS balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    balance INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
);
