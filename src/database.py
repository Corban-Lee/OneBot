"""
Use this file to setup the database
"""

import sqlite3
import logging

from constants import DATABASE


log = logging.getLogger(__name__)

def setup():
    """
    Setup the database file and tables
    """
    
    t_debug = lambda msg: log.debug(f'Creating Table: {msg}')
    log.info('Setting up database...')

    db = sqlite3.connect(DATABASE)
    cur = db.cursor()

    # Create the table for report tickets
    t_debug('user_report_tickets')
    cur.execute(
        """CREATE TABLE IF NOT EXISTS user_report_tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            accused_user_id INTEGER NOT NULL,
            channel_id INTEGER,
            reason_msg TEXT NOT NULL
        )"""
    )

    # Create the table for suggestion tickets
    t_debug('user_suggestion_tickets')
    cur.execute(
        """CREATE TABLE IF NOT EXISTS user_suggestion_tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            channel_id INTEGER,
            suggestion_msg TEXT NOT NULL
            )
        """
    )
    
    # Table for profiles
    t_debug('user_profiles')
    cur.execute(
        """CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            level INTEGER NOT NULL,
            exp INTEGER NOT NULL,
            banner_colour TEXT NOT NULL
            )
        """
    )

    log.debug('Commiting Changes...')
    db.commit()
    db.close()
    
    log.info('Database setup complete')

if __name__ == '__main__':
    setup()