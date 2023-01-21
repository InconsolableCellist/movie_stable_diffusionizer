import base64
import glob
import json
import math
import os
import time
from datetime import datetime

import requests

# 1 = prompt
# 2 = negative prompt
# 21 = cfg scale
# 22 = denoising str
# 28 = height
# 29 = width
INDEX_PROMPT = 2
INDEX_NEGATIVE_PROMPT = 3
INDEX_CFG_STRENGTH = 21
INDEX_DENOISING_STRENGTH = 22
INDEX_HEIGHT = 28
INDEX_WIDTH = 29
INDEX_IMAGE = 5

NEGATIVE_PROMPT = "worst quality, low quality, what has science done, what, nightmare fuel, eldritch horror, where is your god now, why"

img2img_header = {
    "fn_index": 130,
    "session_hash": "b8s3udj15yp",
    "data":
[
        "task(p4bcvsl1kjtembc)",
        0,
        "prompt",
        "negative prompt",
        [],
        "data:image/jpeg;base64,",
        None,
        None,
        None,
        None,
        None,
        None,
        20,
        "Euler a",
        4,
        0,
        "original",
        False,
        False,
        1,
        1,
        7,
        0.45,
        -1,
        -1,
        0,
        0,
        0,
        False,
        512,
        960,
        "Just resize",
        "Whole picture",
        32,
        "Inpaint masked",
        "",
        "",
        "None",
        "",
        True,
        True,
        "",
        "",
        True,
        50,
        True,
        1,
        0,
        False,
        4,
        1,
        "",
        128,
        8,
        ["left","right","up","down"],
        1,
        0.05,
        128,
        4,
        "fill",
        ["left","right","up","down"],
        False,
        False,
        False,
        False,
        "",
        "",
        64,
        "None",
        2,
        "Seed",
        "",
        "Nothing",
        "",
        True,
        False,
        False,
        [{"data":"", "is_file":False, "name":""}],
        "",
        "",
        "",
    ]
}

HOST = 'http://' + os.environ.get('HOSTNAME_AND_PORT') + '/run/predict/'

def interrogate_clip(filename):
    with open(os.path.join('input_images', filename), 'rb') as f:
        b64 = base64.b64encode(f.read())
    request_body = {
        "fn_index": 131,
        "data": [
            0,
            "",
            "",
            "data:image/jpeg;base64," + b64.decode('utf-8'),
            None,
            None,
            None,
            None
        ],
        "session_hash": "20zbc7lw2rc"
    }
    r = requests.post(HOST, json=request_body)
    # if data not in r
    d = r.json()
    if 'data' not in d:
        print("Unexpected response from server")
        print(d)
    return d['data'][0]

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
        data = data + ' from Bee Movie by Dreamworks'
        with open(prompt_file, 'w') as f:
            f.write(data)
        os.remove(image_lock_file)

def sd_img2img(image, prompt, denoising_strength, cfg_strength):
    request_body = img2img_header
    request_body['data'][INDEX_PROMPT] = prompt
    request_body['data'][INDEX_NEGATIVE_PROMPT] = NEGATIVE_PROMPT
    request_body['data'][INDEX_IMAGE] = "data:image/jpeg;base64," + base64.b64encode(image).decode('utf-8')
    request_body['data'][INDEX_DENOISING_STRENGTH] = denoising_strength
    request_body['data'][INDEX_CFG_STRENGTH] = cfg_strength
    r = requests.post(HOST, json=request_body)
    d = r.json()
    if 'data' not in d:
        print("Unexpected response from server")
        print(d)
    filename = d['data'][0][0]['name']
    print(f'Generated {filename}')
    # perform a GET to http://HOSTNAME_AND_PORT/file=filename
    r = requests.get('http://' + os.environ.get('HOSTNAME_AND_PORT') + '/file=' + filename)
    return r.content

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
    # denoising_strength = 0.42
    # cfg_strength = 14
    # cfg_strength = 23
    cfg_strength = 16
    clip_prompt = open(prompt_file_name, 'r').read()
    frame = sd_img2img(image, clip_prompt, denoising_strength, cfg_strength)
    with open(output_file_name, 'wb') as f:
        f.write(frame)
    os.remove(output_lock_file_name)

    print(f'# {denoising_strength}')

if not os.path.exists('output_images'):
    os.mkdir('output_images')

if not os.path.exists(os.path.join('input_images', 'done')):
    os.mkdir(os.path.join('input_images', 'done'))

looptime = datetime.now()
loop_count = 0
while True:
    try:
        lockfiles = glob.glob(os.path.join('input_images', '*.lock'))
        lockfiles = [f for f in lockfiles if time.time() - os.path.getctime(f) > 60]
        for f in lockfiles:
            print(f"Removing stuck lockfile {f}")
            os.remove(f)
    except Exception as e:
        print(f"Error removing lockfiles: {e}. Perhaps they were removed by another process?")

    images = os.listdir('input_images')
    images = [image for image in images if image.endswith('.jpg')]
    images.sort()

    failure = False
    for image in images:
        try:
            generate_frame(image)
            generate_prompts(images)
        except Exception as e:
            failure = True
            break

    if (datetime.now() - looptime).total_seconds() < 30:
        print("Loop took less than 30s")
        loop_count += 1
        if loop_count > 3:
            print("Loop took less than 30s 3 times in a row. Exiting.")
            break
    else:
        loop_count = 0
    looptime = datetime.now()

print("Process exited normally.")
