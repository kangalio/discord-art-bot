from typing import *

import os, json
from glob import glob

import emoji as emoji_util
import emojis as emoji_util_2
import numpy as np
from PIL import Image

categories = {}
for category_name in emoji_util_2.db.get_categories():
	emojis = [emoji.emoji for emoji in emoji_util_2.db.get_emojis_by_category(category_name)]
	categories[category_name] = emojis
def get_category(emoji: str) -> Optional[str]:
	for category_name, emojis in categories.items():
		if emoji in emojis:
			return category_name
	if len(emoji) > 1:
		return get_category(emoji[0])
	return None

def mix_color(a: List[float], b: List[float], weight_a: float, weight_b: float) -> List[float]:
	output = []
	for component_a, component_b in zip(a, b):
		print(component_a, weight_a)
		print(component_b, weight_b)
		output_component = (component_a * weight_a + component_b * weight_b) / (weight_a + weight_b)
		print(output_component)
		print()
		output.append(output_component)
	return output

def color_to_hexcode(components: List[float]) -> str:
	return "".join(f"{round(component):02x}" for component in components)

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
		
		print("shortcode:", emoji_util.demojize(unicode_string))
		# ~ print("image_path", image_path)
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

def filter_emoji_index(json_path: str) -> None:
	with open(json_path) as f:
		index = json.load(f)
	
	emojis = []
	for emoji in index:
		name = emoji_util.demojize(emoji["unicode_string"])[1:-1].lower()
		category = get_category(emoji["unicode_string"])
		display = name + " " + emoji["unicode_string"]
		avg_opacity = emoji["avg_opacity"] / 255
		
		if emoji["unicode_string"] in "😶😡🥵🥶😈🤡💀🤢🕵🎃":
			emojis.append(emoji)
		# ~ if category and "Food" in category:
			# ~ #emoji["dominant_color_prop"] > 0.7
			# ~ if avg_opacity > 0.5:
				# ~ emojis.append(emoji)
				# ~ print(display)
	
	return emojis
		
def create_emojiset(emojis: List[Dict[str, Any]]) -> Dict[str, str]:
	discord_bg = [54, 57, 63]
	
	opacities = [emoji["avg_opacity"]/255 for emoji in emojis]
	
	# normalize opacities
	# ~ min_opacity = min(opacities)
	# ~ range_opacity = max(opacities) - min_opacity
	# ~ opacities = [(opacity - min_opacity) / range_opacity for opacity in opacities]
	
	emojiset = {}
	for emoji, opacity in zip(emojis, opacities):
		print(f'Mixing {emoji["avg_color"]} with {opacity:.2f}')
		color = mix_color(emoji["avg_color"], discord_bg, opacity, 1 - opacity)
		print(color)
		print()
		emojiset[emoji["unicode_string"]] = color_to_hexcode(color)
	
	return emojiset

# ~ assemble_emoji_index("result.json")
emojis = filter_emoji_index("result.json")
emojiset = create_emojiset(emojis)
print(json.dumps(emojiset, indent=2))
