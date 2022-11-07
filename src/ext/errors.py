"""Error handling extension"""

import logging

import discord
from discord import (
	app_commands,
	Interaction as Inter
)
from discord.ext import commands

from . import BaseCog


log = logging.getLogger(__name__)


class Errors(BaseCog, name="errors"):
	"""Errors handler cog"""

	__slots__ = ()
	default_err_msg = "I'm sorry, but I've encountered an " \
					  "error while processing your command."

	def __init__(self, bot) -> None:
		super().__init__(bot)
  
		# Register the error handler
		bot.tree.error(coro = self._dispatch_to_app_command_handler)

	def trace_error(self, error: Exception):
		log.error(msg=type(error).__name__, exc_info=error)
		raise error

	async def _dispatch_to_app_command_handler(
		self,
		inter: Inter,
		error: app_commands.AppCommandError
	):
		"""Dispatches the error to the app command handler"""

		self.bot.dispatch("app_command_error", inter, error)

	async def _respond_to_interaction(self, inter: Inter) -> bool:
		"""Respond to an interaction with an error message"""

		try:
			await inter.response.send_message(
				self.default_err_msg,
				ephemeral=True
			)
		except discord.InteractionResponded:
			return

	@commands.Cog.listener("on_app_command_error")
	async def get_app_command_error(
		self,
		inter: Inter,
		error: app_commands.AppCommandError
	):
		"""Handles the application command error.

		Responds with the appropriate error message.
		"""

		try:
			# Send the default error message and create an edit
			# shorthand to add more details to the message once
			# we've figured out what the error is.
			log.error(error.with_traceback(None))
			await self._respond_to_interaction(inter)
			edit = lambda x: inter.edit_original_response(content=x)

			raise error

		except app_commands.CommandInvokeError as _err:

			# The interaction has already been responded to.
			if isinstance(
				_err.original,
				discord.InteractionResponded
			):
				await edit(_err.original)
				return

			# Some other error occurred while invoking the command.
			await edit(
				f"`{type(_err.original).__name__}` " \
				f": {_err.original}"
			)

		except app_commands.CheckFailure as _err:

			# The command is still on cooldown.
			if isinstance(
				_err,
				app_commands.CommandOnCooldown
			):
				await edit(
					f"Woah, slow down! This command is on cooldown, " \
					f"wait `{str(_err).split(' ')[7]}` !"
				)
				return

			if isinstance(
				_err,
				app_commands.MissingPermissions
			):
				await edit(
					"You don't have the required permissions to " \
					"run this command!"
				)
				return

			if isinstance(
				_err,
				app_commands.BotMissingPermissions
			):
				await edit(
					"I don't have the required permissions to " \
					"run this command! Please ask an admin to " \
					"grant me the required permissions."
				)
				return

			# A different check has failed.
			await edit(f"`{type(_err).__name__}` : {_err}")
		
		except app_commands.CommandNotFound:

			# The command could not be found.
			await edit(
				f"I couldn't find the command you were looking for... "
				"\nThis is probably a discord bug related to " \
				"desynchronization between my commands and discord's " \
				"servers. Please try again later."
			)

		except Exception as _err: 
			# Caught here:
				# app_commands.TransformerError
				# app_commands.CommandLimitReached
				# app_commands.CommandAlreadyRegistered
				# app_commands.CommandSignatureMismatch

			self.trace_error(_err)

	# @commands.Cog.listener("on_view_error")
	# async def get_view_error(self, interaction: discord.Interaction, error: Exception, item: any):
	# 	"""View Error Handler"""
	# 	try:
	# 		raise error
	# 	except discord.errors.Forbidden:
	# 		pass
	# 	except Exception as e:
	# 		self.trace_error("get_view_error", e)

	# @commands.Cog.listener("on_modal_error")
	# async def get_modal_error(self, interaction: discord.Interaction, error: Exception):
	# 	"""Modal Error Handler"""
	# 	try:
	# 		raise error
	# 	except discord.errors.Forbidden:
	# 		pass
	# 	except Exception as e:
	# 		self.trace_error("get_modal_error", e)

async def setup(bot):
	if not bot.debug:
		await bot.add_cog(Errors(bot))
