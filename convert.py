from PIL import Image

def flatten(l):
	return [item for sublist in l for item in sublist]

# Converts a color string like "31373d 55acee c1694f" to a color palette list that PIL expects.
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

discord_colors = [
	("aa8ed6", "purple"),
	("31373d", "black"),
	("55acee", "blue"),
	("c1694f", "brown"),
	("78b159", "green"),
	("ffac33", "orange"),
	("dd2e44", "red"),
	("fdcb58", "yellow"),
	("e6e7e8", "white"),
]

# mode: either "circle" or "square". decides if the program uses Discord's square or circle emojis
# chars_per_line: emojis per line. Discord desktop can show max 67
def image_to_discord_messages(image: Image, mode: str="square", max_chars_per_line: int=67):
	def colorname_to_emoji(name):
		if mode == "square" and (name == "white" or name == "black"):
			name += "_large"
		return f":{name}_{mode}:"
	colors = [colorhex_to_tuple(pair[0]) for pair in discord_colors]
	emoji_names = [colorname_to_emoji(pair[1]) for pair in discord_colors]

	# pad palette to 256 elements, because PIL needs it like that
	palette = colors.copy()
	if len(palette) < 256:
		palette += [palette[0]] * (256 - len(palette))

	if image.width > max_chars_per_line:
		image = resize_to_width(image, max_chars_per_line)
	image = quantize(image, palette)
	# ~ image.save("converted.png", "png")

	pix = image.load()
	lines = []
	for y in range(image.height):
		line = ""
		for x in range(image.width):
			# pix[x, y] returns a palette index
			line += emoji_names[pix[x, y]]
		lines.append(line)

	return lines
