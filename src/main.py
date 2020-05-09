from typing import *

import os, sys, time, urllib, asyncio, logging, time, json
from io import BytesIO

import requests, discord
from PIL import Image

import convert
from convert import image_to_emoji_lines


"""
This bot needs permissions:
- Send Messages
Permissions Integer: 2048
"""

MSG_INTERVAL = 1.5 # the minimum delay inbetweeen messages, in seconds

with open("emojisets.json") as f:
	emojisets = json.load(f)

def get_url_from_msg(msg) -> Optional[str]:
	# TODO: detect url in message
	if len(msg.attachments) == 0:
		print("ahhhh how to extract valid url from text message")
		return None
	elif len(msg.attachments) == 1:
		return msg.attachments[0].url
	else:
		print(f"Multiple attachments :/ {msg.attachments}")
		return None

client = discord.Client()
logger = logging.getLogger()
app_info = None # will be set from on_ready
pending_stops_channels: List[discord.TextChannel] = [] # list of channels where user requested operation stop
running_channels: List[discord.TextChannel] = [] # list of channels where an operation is running

async def update(msg) -> None:
	import subprocess
	
	try:
		output_bytes = subprocess.check_output(["git", "pull"])
		return_code = 0
	except subprocess.CalledProcessError as e:
		return_code = e.returncode
		output_bytes = e.output
	output = output_bytes.decode("UTF-8", errors="replace").strip()
	await msg.channel.send(output[:2000])
	if return_code != 0:
		await msg.channel.send(f"Aborting update (Exit code {return_code})")
		return
	
	print("Updated. Relaunching...")
	await msg.channel.send("Relaunching python...")
	os.execv(sys.executable, ["python3"] + sys.argv) # no idea why this works

async def draw_operation(msg, url: str, emojiset: Dict[str, str],
		max_chars_per_line: int, should_send_image: bool, spaced: bool):
	
	message_write_start = time.time()
	
	if max_chars_per_line > 198:
		await msg.channel.send("That's too big. Discord has a hard limit of 198 emojis per line")
		return
	
	image = Image.open(BytesIO(requests.get(url).content))
	tempimage = BytesIO() if should_send_image else None
	lines = image_to_emoji_lines(image,
			emojiset=emojiset, max_chars_per_line=max_chars_per_line,
			output=tempimage, spaced=spaced)
	
	if tempimage:
		tempimage.seek(0) # go back to beginning of file to be able to read the entirety of it
		await msg.channel.send(file=discord.File(tempimage, "quantized_image.png"))
	
	last_message_time = 0.0 # this is 1970 or something like that
	for i, line in enumerate(lines):
		# rate-limit according to MSG_INTERVAL
		how_long_since_last_message = time.time() - last_message_time
		if how_long_since_last_message < MSG_INTERVAL:
			time.sleep(MSG_INTERVAL - how_long_since_last_message)
		last_message_time = time.time()
		
		print(f"Sending line {i+1}/{len(lines)} ({len(line)} chars)...")
		last_message = await msg.channel.send(line)
		
		# check abort request
		if msg.channel in pending_stops_channels:
			pending_stops_channels.remove(msg.channel)
			await last_message.delete()
			print("Aborted operation")
			return
	
	message_write_duration = time.time() - message_write_start
	if message_write_duration > 10: # at 10s upwards we'll write a confirmation message
		await msg.channel.send(f"Done in {message_write_duration:.2f}s")
	
	print("Completed operation")

async def write_help(msg) -> None:
	text = """
Summon this bot with `$art` and an image file attached.

Several optional parameters are possible (case-insensitive, order doesn't matter):
- **An integer number** sets the converted image's size in emojis-per-row
  _(default is 20)_
- **circle**, **square**, **heart** or **food** sets the emoji type used for the conversion
  _(default is circle)_
- **outputimage** makes the bot output its temporary image
  _(disabled by default)_
- **spaced** separates all emojis with a single space. Better aspect ratio, but less maximum emojis-per-row
  _(disabled by default)_

Use `$art abort` (or `$art stop` or `$art cancel`) to interrupt the drawing process.

**Example commands**:
- `$art 20 square`
- `$art 100 outputimage circle`
- `$art 50 food`
""".strip()
	await msg.channel.send(embed=discord.Embed(title="Help", description=text))

@client.event
async def on_ready():
	global app_info
	app_info = await client.application_info()
	print(f"{client.user} has connected to Discord!")

@client.event
async def on_message(msg) -> None:
	try:
		if msg.content.startswith("$art"):
			args = msg.content[4:].strip().split()
			args = [arg.lower() for arg in args]
			await art(msg, args)
	except Exception as e:
		logger.exception("Exception in on_message")
		await msg.channel.send(f"Something went wrong: {e}")

async def art(msg, args):
	# I wanna see if my bot has actual users :)
	print(f"Art command was called by {msg.author.name} with args {args}!")
	
	is_admin = msg.author == app_info.owner
	
	if "help" in args:
		await write_help(msg)
		return
	
	if "ping" in args:
		await msg.channel.send(f"Pong! {round(client.latency*1000)}ms")
		return
	
	if "update" in args:
		if is_admin:
			await update(msg)
		else:
			await msg.channel.send("Admin privileges required")
		return
	
	if "stop" in args or "abort" in args or "cancel" in args:
		if msg.channel in running_channels:
			pending_stops_channels.append(msg.channel)
		else:
			await msg.channel.send("There's no operation running here :thinking:")
		return
	
	# At this point this is definitely a draw operation
	url = get_url_from_msg(msg)
	if url is None:
		await msg.channel.send("Please attach a single image file to your message")
		print("Warning: no image url found in message")
		return
	
	# NOW THE DRAW OPERATION STUFF BEGINS
	
	# default parameters
	should_send_image = False
	emojiset = emojisets["circle"]
	spaced = False
	max_chars_per_line = 20
	
	# extract parameters from args
	unknown_args = []
	for arg in args:
		if arg == "outputimage":
			should_send_image = True
		elif arg in emojisets:
			emojiset = emojisets[arg]
		elif arg in ["spaced"]:
			spaced = True
		else:
			try: max_chars_per_line = int(arg)
			except ValueError:
				print(f"Warning: unknown arg \"{arg}\"")
				unknown_args.append(arg)
	
	if len(unknown_args) > 0:
		params_string = ", ".join(f'"{arg}"' for arg in unknown_args)
		await msg.channel.send(f"Warning: ignored unknown parameters {params_string}")
	
	if max_chars_per_line > 1000:
		await msg.channel.send("Those are quite many characters per line.. you sure you typed that in right?")
		return
	
	# after having extracted the parameters, pass it to draw_operation to handle the actual business
	running_channels.append(msg.channel)
	await draw_operation(msg, url, emojiset, max_chars_per_line, should_send_image, spaced)
	running_channels.remove(msg.channel)

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
client.run(token)
