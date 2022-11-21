"""Routes for the dashboard blueprint."""

from quart import Blueprint, render_template, redirect, url_for
from quart_discord import DiscordOAuth2Session, Unauthorized, AccessDenied, requires_authorization
from quart_discord.models.guild import Guild


blueprint = Blueprint("dashboard", __name__)
blueprint.discord: DiscordOAuth2Session = None


async def default_context():
    """Default context for all routes."""

    try:
        return {
            "user": await blueprint.discord.fetch_user()
        }
    except Unauthorized:
        return {}

@blueprint.route("/")
async def index():
    """Index page"""

    context = await default_context()
    return await render_template("index.html", **context)

@blueprint.route("/dashboard/")
@requires_authorization
async def dashboard():
    """Dashboard page"""

    context = await default_context()
    return await render_template("dashboard.html", **context)

@blueprint.route("/my-servers/")
@requires_authorization
async def my_servers():
    """My servers page"""

    context = await default_context()

    # Get all use guilds
    guilds: list[Guild] = await blueprint.discord.fetch_guilds()
    guilds = sorted(guilds, key=lambda g: g.name)
    context["guilds"] = guilds

    return await render_template("servers.html", **context)

@blueprint.route("/docs/")
async def documentation():
    """Documentation page"""

    context = await default_context()
    return await render_template("docs.html", **context)

@blueprint.route("/commands/")
async def command_list():
    """Command list page"""

    context = await default_context()
    return await render_template("commands.html", **context)

@blueprint.route("/help/")
async def help_page():
    """Help page"""

    context = await default_context()
    return await render_template("help.html", **context)

@blueprint.route("/login/")
async def login():
    """Login function"""

    return await blueprint.discord.create_session()

@blueprint.route("/logout/")
async def logout():
    """Logout function"""

    blueprint.discord.revoke()
    return redirect(url_for("dashboard.index"))

@blueprint.route("/callback/")
async def callback():
    """Callback function"""

    await blueprint.discord.callback()
    return redirect(url_for("dashboard.index"))

@blueprint.errorhandler(Unauthorized)
async def redirect_unauthorized(error):
    """Redirect unauthorized users"""

    print(error)
    return redirect(url_for("dashboard.login"))

@blueprint.errorhandler(AccessDenied)
async def redirect_access_denied(error):
    """Redirect users who denied access"""

    print(error)
    return redirect(url_for("dashboard.index"))
