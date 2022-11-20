"""Views module for the dashboard app."""

from quart import redirect, url_for, render_template


async def index():
    """Index page"""

    return await render_template("index.html")

async def dashboard():
    """Dashboard page"""

    return await render_template("dashboard.html")

async def my_servers():
    """My servers page"""

    return await render_template("servers.html")

async def documentation():
    """Documentation page"""

    return await render_template("docs.html")

async def command_list():
    """Command list page"""

    return await render_template("commands.html")

async def help_page():
    """Help page"""

    return await render_template("help.html")


async def callback():
    """Callback function"""

    # try:
    #     await discord.callback()
    # except Exception as err:
    #     print(err)
    #     return redirect(url_for("login"))
