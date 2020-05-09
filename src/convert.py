from typing import *
from PIL import Image
import emoji

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

# PUBLIC
# parameters:
# - emojiset: a dict of "emoji string" -> "emoji colorhex"
# - chars_per_line: emojis per line. Discord desktop servers can show max 56 (67 in dms)
# - output_path: an optional path where the quantized image should be stored to
# - spaced: boolean; whether emojis should be separated by spaces
def image_to_emoji_lines(image: Image,
		emojiset: Dict[str, str],
		max_chars_per_line: int=67,
		output: Optional[Any]=None,
		spaced: bool=False) -> List[str]:
	
	palette, emoji_names = zip(*[(colorhex_to_tuple(c), e) for e, c in emojiset.items()])
	palette = list(palette)
	emoji_names = list(emoji_names)

	# pad palette to 256 elements, because PIL needs it like that
	if len(palette) < 256:
		palette += [palette[0]] * (256 - len(palette))

	if image.width > max_chars_per_line:
		image = resize_to_width(image, max_chars_per_line)
	image = quantize(image, palette)
	if output:
		image.save(output, "PNG")

	pix = image.load()
	lines: List[str] = []
	for y in range(image.height):
		emojis = []
		for x in range(image.width):
			# pix[x, y] returns a palette index
			emojis.append(emoji_names[pix[x, y]])
		lines.append((" " if spaced else "").join(emojis))

	return lines
