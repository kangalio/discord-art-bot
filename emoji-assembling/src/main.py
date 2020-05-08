from typing import *

import os, json
from dataclasses import dataclass
from glob import glob

import emoji
import numpy as np
from PIL import Image


@dataclass
class Emoji:
	shortcode: str
	unicode_string: str
	image_path: str

def get_shortcode_unicode_mapping() -> Dict[str, str]:
	with open("discord-emoji-mapping/emoji-formatted-fixed.json") as f:
		json_data = json.load(f)
	
	mapping = {}
	for section in json_data.values():
		for emoji in section:
			shortcode = min(emoji["names"], key=len)
			unicode_string = emoji["surrogates"]
			mapping[shortcode] = unicode_string
	
	return mapping

# returns dict of `unicode string` -> `image file path`
def get_unicode_image_mapping() -> Dict[str, str]:
	# 12.1.4 is the one Discord uses (source emojipedia.org/discord)
	image_paths = glob("twemoji/v/12.1.4/72x72/*.png")

	emojis = {}
	for path in image_paths:
		basename = os.path.basename(path)[:-4] # strip ".png"
		charcodes = [int(hexcode, 16) for hexcode in basename.split("-")]
		string = "".join(map(chr, charcodes))
		
		emojis[string] = path
	
	return emojis

def assemble_emoji_list() -> List[Emoji]:
	# cryptic variable names intensify (not really though)
	s_u_mapping = get_shortcode_unicode_mapping()
	u_i_mapping = get_unicode_image_mapping()
	emojis = []
	for s, u in s_u_mapping.items():
		i = u_i_mapping.get(u)
		if i:
			emojis.append(Emoji(s, u, i))
	return emojis

def assemble_emoji_index(json_output_path: str) -> None:
	discord_bg_color = "36393f"
	discord_bg_color = [int(discord_bg_color[i:i+2], 16) for i in (0, 2, 4)]

	result = []

	np.set_printoptions(threshold=np.inf)
	for emoji in assemble_emoji_list():
		# load image
		img = Image.open(emoji.image_path).convert("RGBA") # palettized
		width, height = img.size
		
		# set up numpy arrays and values
		pixel_arr = np.array(img).reshape(width * height, 4)
		opacities = pixel_arr[:, 3]
		alphas = 255 - opacities
		num_non_transparent_pixels = np.sum(opacities >= 128)
		
		# find dominant color
		d = {}
		total_count = 0
		for unique_rgb_color in np.unique(pixel_arr[:, :3], axis=0):
			pixels_matching_rgb_color = np.sum(pixel_arr[:, :3] * [65536, 256, 1], axis=1) == np.sum(unique_rgb_color * [65536, 256, 1])
			avg_opacity = np.average(pixel_arr[:, 3], weights=pixels_matching_rgb_color)
			count = avg_opacity / 255 * pixels_matching_rgb_color.sum()
			total_count += count
			d[count] = unique_rgb_color
		dominant_color = d[max(d.keys())]
		dominant_color_prop = max(d.keys()) / total_count
		
		# find avg color
		avg_color = [None, None, None]
		for i in range(3):
			avg_color[i] = np.average(pixel_arr[:, i], weights=alphas)
		
		avg_opacity = np.average(opacities)
		
		print("shortcode:", emoji.shortcode)
		# ~ print("dominant color:", dominant_color)
		# ~ print(f"dominant color prop: {dominant_color_prop*100:.2f}%")
		# ~ print("average color:", avg_color)
		# ~ print("average opacity:", avg_opacity)
		# ~ print()
		
		result.append({
			"shortcode": emoji.shortcode,
			"unicode_string": emoji.unicode_string,
			"image_path": emoji.image_path,
			"dominant_color": dominant_color.tolist(),
			"dominant_color_prop": dominant_color_prop,
			"avg_color": avg_color,
			"avg_opacity": avg_opacity,
		})

	with open(json_output_path, "w") as f:
		json.dump(result, f)

def analyze_emoji_index(json_path: str) -> None:
	with open(json_path) as f:
		index = json.load(f)
	
	for emoji in index:
		if emoji["dominant_color_prop"] == 1 and emoji["avg_opacity"] > 0.7:
			print(emoji["shortcode"])

# ~ assemble_emoji_index("result.json")
analyze_emoji_index("result.json")
