from typing import *

import os, json
from glob import glob

import emoji
import numpy as np
from PIL import Image


def assemble_emoji_index(json_output_path: str) -> None:
	np.set_printoptions(threshold=np.inf)
	
	image_paths = glob("twemoji/v/12.1.4/72x72/*.png")
	
	result = []
	for image_path in image_paths:
		# convert image filename to unicode string
		basename = os.path.basename(image_path)[:-4] # strip extension
		charcodes = [int(hexcode, 16) for hexcode in basename.split("-")]
		unicode_string = "".join(map(chr, charcodes))
		
		# load image
		img = Image.open(image_path).convert("RGBA") # palettized
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
		
		print("shortcode:", emoji.demojize(unicode_string))
		# ~ print("dominant color:", dominant_color)
		# ~ print(f"dominant color prop: {dominant_color_prop*100:.2f}%")
		# ~ print("average color:", avg_color)
		# ~ print("average opacity:", avg_opacity)
		# ~ print()
		
		result.append({
			"unicode_string": unicode_string,
			"image_path": image_path,
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

assemble_emoji_index("result.json")
# ~ analyze_emoji_index("result.json")
