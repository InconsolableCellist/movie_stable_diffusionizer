#!/usr/bin/python3
import glob
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap

def gen_caption(text, font_path, font_size, width, height):
    image = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    lines = textwrap.wrap(text, width=width/21)

    y_text = 0
    for line in lines:
        draw.text((0, y_text), line, font=font, fill=(255, 255, 255))
        y_text += font_size
    return image

if not os.path.exists("input_images"):
    print(f"input_images directory not found")
    os.sys.exit(1)

if not os.path.exists("captions"):
    os.mkdir("captions")

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
if not os.path.exists(font_path):
    print(f"DejaVuSans.ttf not found")
    os.sys.exit(1)

prompts = glob.glob(os.path.join("input_images", "*.txt"))
prompts.sort()
for prompt in prompts:
    if os.path.exists(os.path.join("captions", os.path.basename(prompt) + ".jpg")):
        print('👌', end='')
        continue
    text = open(prompt, 'r').read()
    image = gen_caption(text, font_path, 40, 1920, 100)
    image.save(os.path.join("captions", os.path.basename(prompt) + ".jpg"))
    print(f"📋", end="", flush=True)
