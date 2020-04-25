from typing import *

import os, time, urllib
from PIL import Image
from io import BytesIO

import requests, discord
from discord.ext import commands

from convert import image_to_discord_messages 


"""
This bot needs permissions:
- Send Messages
Permissions Integer: 2048


Ideas:
- optional flag to isnert spaces inbetween emojis. That way we'd have the same horizontal margin
  as vertically (Discord puts a bit of margin between messages, coincidentally equating to exactly
  1 space)
  Disadvantage: less chars per row
- optional flag to condense multiple lines into a single message
  Disadvantage: irregular spacing inbetween lines
"""


def letter_to_regional_indicator(letter):
	letter_index = ord(letter.upper()) - ord("A")
	unicode_char = chr(ord("\N{REGIONAL INDICATOR SYMBOL LETTER A}") + letter_index)
	print(f"got {unicode_char}")
	return unicode_char

def get_url_from_msg(msg) -> Optional[str]:
	if len(msg.attachments) == 0:
		print("ahhhh how to extract valid url from text message")
		return None
	elif len(msg.attachments) == 1:
		return msg.attachments[0].url
	else:
		print(f"Multiple attachments :/ {msg.attachments}")
		return None

bot = commands.Bot(command_prefix="$", description='A bot that does beautiful art')
pending_stops_channels: List[discord.TextChannel] = [] # list of channels where user requested operation stop
running_channels: List[discord.TextChannel] = [] # list of channels where an operation is running

async def draw_operation(ctx, url: str, mode: str, max_chars_per_line: int):
	message_write_start = time.time()
	
	image = Image.open(BytesIO(requests.get(url).content))
	lines = image_to_discord_messages(image, mode=mode, max_chars_per_line=max_chars_per_line)
	for i, line in enumerate(lines):
		print(f"Sending line {i+1}/{len(lines)} ({len(line)} chars)...")
		last_message = await ctx.message.channel.send(line)
		
		# check abort request
		if ctx.message.channel in pending_stops_channels:
			pending_stops_channels.remove(ctx.message.channel)
			await last_message.delete()
			print("Aborted operation")
			return
	
	message_write_duration = time.time() - message_write_start
	if message_write_duration > 10: # at 10s upwards we'll write a confirmation message
		await ctx.message.channel.send(f"Done in {message_write_duration:.2f}s")
	
	print("Completed operation")

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
async def art(ctx):
	args = ctx.message.content.split()[1:] # [1:] to exclude the command itself
	args = [arg.lower() for arg in args]
	
	if "stop" in args or "abort" in args or "cancel" in args:
		if ctx.message.channel in running_channels:
			pending_stops_channels.append(ctx.message.channel)
		else:
			await ctx.message.channel.send("There's no operation running here :thinking:")
		return
	
	# At this point this is definitely a draw operation
	url = get_url_from_msg(ctx.message)
	if url is None:
		print("Warning: no image url found in message")
		return
	
	# Start extracting parameters from the args
	
	# Extract mode parameter
	if "square" in args:
		mode = "square"
	elif "circle" in args:
		mode = "circle"
	else:
		mode = "circle" # default
	
	# if user has any integer value as an arg, use that as max_chars_per_line
	max_chars_per_line = 20
	for arg in args:
		try:
			max_chars_per_line = int(arg)
		except ValueError:
			continue
	
	running_channels.append(ctx.message.channel)
	await draw_operation(ctx, url, mode, max_chars_per_line)
	running_channels.remove(ctx.message.channel)

with open("token.txt") as f:
	token = f.read().strip()
bot.run(token)
