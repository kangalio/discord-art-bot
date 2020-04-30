from typing import *

import os, sys, time, urllib, asyncio
from io import BytesIO

import requests, discord
from PIL import Image
from discord.ext import commands

import convert
from convert import image_to_discord_messages


"""
This bot needs permissions:
- Send Messages
Permissions Integer: 2048
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
app_info = None # will be set from on_ready
pending_stops_channels: List[discord.TextChannel] = [] # list of channels where user requested operation stop
running_channels: List[discord.TextChannel] = [] # list of channels where an operation is running

async def update(ctx) -> None:
	import subprocess
	
	try:
		output_bytes = subprocess.check_output(["git", "pull"])
		return_code = 0
	except subprocess.CalledProcessError as e:
		return_code = e.returncode
		output_bytes = e.output
	output = output_bytes.decode("UTF-8", errors="replace").strip()
	await ctx.message.channel.send(output[:2000])
	if return_code != 0:
		await ctx.message.channel.send(f"Aborting update (Exit code {return_code})")
		return
	
	print("Updated. Relaunching...")
	await ctx.message.channel.send("Relaunching python...")
	os.execv(sys.executable, ["python3"] + sys.argv) # no idea why this works

async def draw_operation(ctx, url: str, mode: str, max_chars_per_line: int, should_send_image: bool, spaced: bool):
	message_write_start = time.time()
	
	image = Image.open(BytesIO(requests.get(url).content))
	tempimage = BytesIO() if should_send_image else None
	lines = image_to_discord_messages(image,
			mode=mode, max_chars_per_line=max_chars_per_line,
			output=tempimage, spaced=spaced)
	
	if tempimage:
		tempimage.seek(0) # go back to beginning of file to be able to read the entirety of it
		await ctx.message.channel.send(file=discord.File(tempimage, "quantized_image.png"))
	
	line_lengths = [len(line) for line in lines]
	if max(line_lengths) > 2000:
		await ctx.message.channel.send(f"Uh oh the resulting image is too big. The lines range from "
				f"{min(line_lengths)} to {max(line_lengths)} characters. Maximum is 2000")
		return
	
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
	global app_info
	app_info = await bot.application_info()
	print(f"{bot.user} has connected to Discord!")

@bot.command()
async def art(ctx):
	args = ctx.message.content.split()[1:] # [1:] to exclude the command itself
	args = [arg.lower() for arg in args]
	
	is_admin = ctx.message.author == app_info.owner
	
	if "ping" in args:
		await ctx.message.channel.send(f"Pong! {round(bot.latency*1000)}ms")
		return
	
	if "update" in args:
		if is_admin:
			await update(ctx)
		else:
			await ctx.message.channel.send("Admin privileges required")
		return
	
	if "stop" in args or "abort" in args or "cancel" in args:
		if ctx.message.channel in running_channels:
			pending_stops_channels.append(ctx.message.channel)
		else:
			await ctx.message.channel.send("There's no operation running here :thinking:")
		return
	
	# At this point this is definitely a draw operation
	url = get_url_from_msg(ctx.message)
	if url is None:
		await ctx.message.channel.send("Please attach a single image file to your message")
		print("Warning: no image url found in message")
		return
	
	# NOW THE DRAW OPERATION STUFF BEGINS
	
	# default parameters
	should_send_image = False
	mode = "circle"
	spaced = False
	max_chars_per_line = 20
	
	# extract parameters from args
	unknown_args = []
	for arg in args:
		if arg == "outputimage":
			should_send_image = True
		elif arg in convert.discord_colorsets:
			mode = arg
		elif arg in ["spaced"]:
			spaced = True
		else:
			try: max_chars_per_line = int(arg)
			except ValueError:
				print(f"Warning: unknown arg \"{arg}\"")
				unknown_args.append(arg)
	
	if len(unknown_args) > 0:
		params_string = ", ".join(f'"{arg}"' for arg in unknown_args)
		await ctx.message.channel.send(f"Warning: ignored unknown parameters {params_string}")
	
	if max_chars_per_line > 1000:
		await ctx.message.channel.send("Those are quite many characters per line.. you sure you typed that in right?")
		return
	
	# after having extracted the parameters, pass it to draw_operation to handle the actual business
	running_channels.append(ctx.message.channel)
	await draw_operation(ctx, url, mode, max_chars_per_line, should_send_image, spaced)
	running_channels.remove(ctx.message.channel)

def test():
	mode = "food"
	output_path = "test/output.png"
	max_chars_per_line = 100
	
	image = Image.open("test/image.jpg")
	lines = image_to_discord_messages(image, mode=mode, max_chars_per_line=max_chars_per_line,
			output_path=output_path)
	with open("test/output.txt", "w") as f:
		for line in lines:
			print(line, file=f)

# ~ test()
with open("token.txt") as f:
	token = f.read().strip()
bot.run(token)
