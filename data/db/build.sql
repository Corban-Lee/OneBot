
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
    ((SELECT id FROM purpose_types WHERE name = 'category'), 'tickets', 'Designated For Tickets'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'general', 'General Chat'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'announcements', 'Server Annoucements'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'rules', 'Server Rules'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'welcome', 'Member Join Notifications'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'goodbye', 'Member Leave Notifications'),
    ((SELECT id FROM purpose_types WHERE name = 'channel'), 'botlogs', 'Logs for Bot Actions'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'member', 'Auto-assigned Member Role'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'muted', 'Muted'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'mod', 'Moderator'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'admin', 'Administrator'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'owner', 'Server Owner'),
    ((SELECT id FROM purpose_types WHERE name = 'role'), 'birthday', 'Birthday Today');

-- Table to store the purpose of a discord object
CREATE TABLE IF NOT EXISTS purposed_objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purpose_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    FOREIGN KEY (purpose_id) REFERENCES purposes(id) ON DELETE CASCADE,
    UNIQUE (purpose_id, object_id) ON CONFLICT REPLACE
);

-- Settings
-- TODO: rename to config options
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    safe_name TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT
    --for_user INTEGER NOT NULL  -- 0 = guild, 1 = user
);

-- Add default settings here
INSERT OR IGNORE INTO settings (safe_name, name, description) VALUES 
    ('lvl_alert', 'Level Up Alert', 'Send a message when you level up.');

-- Table to store the settings
-- TODO: rename to config values
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    setting_id INTEGER NOT NULL,
    value INTEGER NOT NULL,
    FOREIGN KEY (setting_id) REFERENCES settings(id) ON DELETE CASCADE,
    UNIQUE (user_id, setting_id)
);

-- tickets-#36 - Rewrite tickets system
-- Store user created tickets
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    timestamp INTEGER NOT NULL,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
)
