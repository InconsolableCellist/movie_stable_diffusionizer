import base64
import json
import os
from PIL import Image

img2img_header = {
    "fn_index": 31,
    "session_hash": "8cmeux3oub4",
    "data":
[
  0,
  "example prompt",
  "",
  "None",
  "None",
  "data:image/png;base64,",
  None,
  None,
  None,
  "Draw mask",
  20,
  "Euler a",
  4,
  "original",
  False,
  False,
  1,
  1,
  10.5,
  0.5,
  1234567,
  -1,
  0,
  0,
  0,
  False,
  512,
  1216,
  "Just resize",
  False,
  32,
  "Inpaint masked",
  "",
  "",
  "None",
  "",
  "",
  1,
  50,
  0,
  False,
  4,
  1,
  "",
  128,
  8,
  [
    "left",
    "right",
    "up",
    "down"
  ],
  1,
  0.05,
  128,
  4,
  "fill",
  [
    "left",
    "right",
    "up",
    "down"
  ],
  False,
  False,
  None,
  "",
  "",
  64,
  "None",
  "Seed",
  "",
  "Steps",
  "",
  True,
  False,
  None,
  "",
  ""
]
}

import requests

HOST = 'http://' + os.environ.get('HOSTNAME_AND_PORT') + '/api/predict/'



def interrogate_clip(filename):
    with open(os.path.join('input_images', filename), 'rb') as f:
        b64 = base64.b64encode(f.read())
    request_body = {
        "fn_index": 32,
        "data": [
            "data:image/jpeg;base64," + b64.decode('utf-8')
        ],
        "session_hash": "e9ktrsvepfa"
    }
    r = requests.post(HOST, json=request_body)
    return r.json()['data'][0]

def save_prompts(prompts):
    with open('clip_prompts.json', 'w') as f:
        json.dump(prompts, f)

def generate_prompts(images):
    clip_prompts = {}
    if os.path.exists('clip_prompts.json'):
        with open('clip_prompts.json', 'r') as f:
            clip_prompts = json.load(f)

    for image in images:
        if image in clip_prompts:
            continue
        print(f'Processing {image}')
        data = interrogate_clip(image)
        print(f'CLIP returned: {data}')
        clip_prompts[image] = data
        save_prompts(clip_prompts)

def generate_frame(image, prompt):
    request_body = img2img_header
    request_body['data'][1] = prompt
    request_body['data'][5] = "data:image/jpeg;base64," + base64.b64encode(image).decode('utf-8')
    r = requests.post(HOST, json=request_body)
    return r.json()['data'][0]

def load_clip_prompts_from_disk():
    with open('clip_prompts.json', 'r') as f:
        return json.load(f)

def generate_frames(images):
    clip_prompts = load_clip_prompts_from_disk()
    for image_name in images:
        if os.path.exists(os.path.join('output_images', image_name.split('.')[0] + '.png')):
            print(f'_', end='', flush=True)
            continue

        image = open(os.path.join('input_images', image_name), 'rb').read()
        frame = generate_frame(image, clip_prompts[image_name])
        with open(os.path.join('output_images', image_name.split('.')[0] + '.png'), 'wb') as f:
            f.write(base64.b64decode(frame[0].split(',')[1]))
        print(f'#', end='', flush=True)



if not os.path.exists('output_images'):
    os.mkdir('output_images')

# images = [f for f in sorted(os.listdir('input_images') if f.endswith('.jpg')]
images = os.listdir('input_images')
images.sort()
images = images[:1000]

generate_prompts(images)
generate_frames(images)