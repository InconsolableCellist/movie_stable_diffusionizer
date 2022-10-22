import base64
import json
import math
import os
import requests

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
  704,
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
    for image in images:
        prompt_file = os.path.join('input_images', image + '.txt')
        if os.path.exists(prompt_file):
            continue
        image_lock_file = os.path.join('input_images', image + '.lock')
        if os.path.exists(image_lock_file):
            continue

        open(image_lock_file, 'w').close()
        print(f'Processing {image}')
        data = interrogate_clip(image)
        print(f'CLIP returned: {data}')
        data = data[:data.rfind(',')+1]
        data = data + ' from The Office'
        with open(prompt_file, 'w') as f:
            f.write(data)
        os.remove(image_lock_file)

def sd_img2img(image, prompt, denoising_strength, cfg_strength):
    request_body = img2img_header
    request_body['data'][1] = prompt
    request_body['data'][5] = "data:image/jpeg;base64," + base64.b64encode(image).decode('utf-8')
    request_body['data'][19] = denoising_strength
    request_body['data'][18] = cfg_strength
    r = requests.post(HOST, json=request_body)
    return r.json()['data'][0]

def generate_frame(image_name):
    if os.path.exists(os.path.join('output_images', image_name.split('.')[0] + '.png')):
        print(f'_', end='', flush=True)
        return

    input_file_name = os.path.join('input_images', image_name)
    image = open(input_file_name, 'rb').read()
    output_file_name = os.path.join('output_images', image_name.split('.')[0] + '.png')
    output_lock_file_name = output_file_name + '.lock'
    if os.path.exists(output_lock_file_name):
        return
    open(output_lock_file_name, 'w').close()

    prompt_file_name = os.path.join('input_images', image_name + '.txt')
    if not os.path.exists(prompt_file_name):
        print(f'No prompt for {image_name}')
        return

    frame_num = int(image_name.split('.')[0])
    denoising_strength = (math.sin(frame_num/24)+2.5)/7
    # denoising_strength = 0.30
    cfg_strength = 10.5
    frame = sd_img2img(image, clip_prompt, denoising_strength, cfg_strength)
    with open(output_file_name, 'wb') as f:
        f.write(base64.b64decode(frame[0].split(',')[1]))
    os.remove(output_lock_file_name)

    print(f'# {denoising_strength}')

if not os.path.exists('output_images'):
    os.mkdir('output_images')

images = os.listdir('input_images')
# only jpg
images = [image for image in images if image.endswith('.jpg')]
images.sort()

# generate_prompts(images)
for image in images:
    generate_frame(image)