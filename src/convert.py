from typing import *
from PIL import Image

def flatten(l):
	return [item for sublist in l for item in sublist]

# Converts a color string like "31373d" to a color tuple that PIL expects.
def colorhex_to_tuple(color_string):
	return (int(color_string[0:2], 16),
			int(color_string[2:4], 16),
			int(color_string[4:6], 16))

def resize_to_width(image, new_width):
	size_multiplier = new_width / image.width
	new_height = round(image.height * size_multiplier)
	return image.resize((new_width, new_height))

def quantize(image, palette):
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(flatten(palette))
    return image.convert("RGB").quantize(palette=palette_image)

def gen_emoji_set_from_default_colors(emoji_name_fn) -> Dict[str, str]:
	return {
		(emoji_name_fn)("purple"): "aa8ed6",
		(emoji_name_fn)("black"): "31373d",
		(emoji_name_fn)("blue"): "55acee",
		(emoji_name_fn)("brown"): "c1694f",
		(emoji_name_fn)("green"): "78b159",
		(emoji_name_fn)("orange"): "ffac33",
		(emoji_name_fn)("red"): "dd2e44",
		(emoji_name_fn)("yellow"): "fdcb58",
		(emoji_name_fn)("white"): "e6e7e8",
	}

# PUBLIC
discord_colorsets = {
	"circle": gen_emoji_set_from_default_colors(
			lambda name: f":{name}_circle:"),
	"square": gen_emoji_set_from_default_colors(
			lambda name: f":{name}_large_square:" if name in ("black", "white") else f":{name}_square:"),
	"heart": gen_emoji_set_from_default_colors(
			lambda name: ":heart:" if name == "red" else f":{name}_heart:"),
}

# PUBLIC
# mode: either "circle" or "square". decides if the program uses Discord's square or circle emojis
# chars_per_line: emojis per line. Discord desktop can show max 67
# output_path: an optional path where the quantized image should be stored to
def image_to_discord_messages(image: Image,
		mode: str="square",
		max_chars_per_line: int=67,
		output_path: Optional[str]=None):
	
	palette, emoji_names = zip(*[(colorhex_to_tuple(c), e) for e, c in discord_colorsets[mode].items()])
	palette = list(palette)
	emoji_names = list(emoji_names)

	# pad palette to 256 elements, because PIL needs it like that
	if len(palette) < 256:
		palette += [palette[0]] * (256 - len(palette))

	if image.width > max_chars_per_line:
		image = resize_to_width(image, max_chars_per_line)
	image = quantize(image, palette)
	if output_path:
		image.save(output_path)

	pix = image.load()
	lines = []
	for y in range(image.height):
		line = ""
		for x in range(image.width):
			# pix[x, y] returns a palette index
			line += emoji_names[pix[x, y]]
		lines.append(line)

	return lines
