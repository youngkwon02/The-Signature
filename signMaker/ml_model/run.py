from __future__ import print_function
from __future__ import absolute_import

import sys
import numpy as np
import cv2
import os
from PIL import Image
from PIL import ImageColor
from PIL import ImageDraw
from PIL import ImageFont
import json
import collections
import glob
import pickle
import random
import argparse

import tensorflow as tf

from unet import UNet
from utils import compile_frames_to_gif

import applyAlpha
import addLogo


def crop_image(img):
    image = np.array(img)
    blur = cv2.GaussianBlur(image, ksize=(3,3), sigmaX=0)
    ret, thresh1 = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY)
    edged = cv2.Canny(blur, 10, 250)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7,7))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed.copy(),cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    total = 0
    contours_xy = np.array(contours)
    x_min, x_max = 0,0
    value = list()
    for i in range(len(contours_xy)):
      for j in range(len(contours_xy[i])):
        value.append(contours_xy[i][j][0][0])
        x_min = min(value)
        x_max = max(value)
 
    y_min, y_max = 0,0
    value = list()
    for i in range(len(contours_xy)):
      for j in range(len(contours_xy[i])):
        value.append(contours_xy[i][j][0][1])
        y_min = min(value)
        y_max = max(value)

    x = x_min
    y = y_min
    w = x_max-x_min
    h = y_max-y_min

    return x, y, w, h


def process_image(img, x, y, w, h, canvas_size):
    new_width = int(canvas_size * 0.9)
    new_height = int(new_width * h / w)
    if new_height > canvas_size - 10:
        new_height = int(canvas_size * 0.8)
        new_width = int(new_height * w / h)
    img = img.crop((x-1, y-1, x+w+1, y+h+1)).resize((new_width,new_height))
    new_left = int((canvas_size - img.width) / 2)
    new_top = int((canvas_size - img.height) / 2)
    result = Image.new("L", (canvas_size, canvas_size), color=255)
    result.paste(img, (new_left, new_top))

    return result


def draw_single_char(st, font, canvas_size, final_canvas_size, x_offset, y_offset, type):
    img = Image.new("RGB", (canvas_size, canvas_size), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    if type == 0:
        draw.text((x_offset, y_offset), st, (0, 0, 0), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
    else:
        draw.text((x_offset, y_offset), st, (0, 0, 0), font=font)
    x, y, w, h = crop_image(img)
    img = process_image(img, x, y, w, h, final_canvas_size)
    return img


def draw_example(ch, src_font, dst_font, canvas_size, final_canvas_size, x_offset, y_offset):
    if num == 19:
        dst_img = draw_single_char(ch, dst_font, canvas_size, final_canvas_size, x_offset, y_offset, 0)
    else:
        dst_img = draw_single_char(ch, dst_font, canvas_size, final_canvas_size, x_offset, y_offset, 1)
    src_img = draw_single_char(ch, src_font, canvas_size, final_canvas_size, x_offset, y_offset, 1)
    example_img = Image.new("RGB", (final_canvas_size * 2, final_canvas_size), (255, 255, 255))
    example_img.paste(dst_img, (0, 0))
    example_img.paste(src_img, (final_canvas_size, 0))
    return example_img


def font2img(src, dst, stringset, char_size, canvas_size, final_canvas_size, x_offset, y_offset, sample_dir, label):
    src_font = ImageFont.truetype(src, size=char_size)
    dst_font = ImageFont.truetype(dst, size=char_size)
    count = 0
    for s in stringset:
        e = draw_example(' '+s, src_font, dst_font, canvas_size, final_canvas_size, x_offset, y_offset)
        if e:
            e.save(os.path.join(sample_dir, "%02d_%04d.jpg" % (label, count)))
            count += 1


def pickle_tests(paths, test_path):
    with open(test_path, 'wb') as fv:
        for p in paths:
            label = int(os.path.basename(p).split("_")[0])
            with open(p, 'rb') as f:
                print("img %s" % p, label)
                img_bytes = f.read()
                example = (label, img_bytes)
                pickle.dump(example, fv)


def imageModify(path,colorhex,style):
    img = cv2.imread(path)
    r, g, b = ImageColor.getcolor(colorhex, "RGB")
    whiteimg = np.zeros([img.shape[0], img.shape[1], 3], dtype=np.uint8)
    whiteimg.fill(255)
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            if img[i][j][0] < 180 and img[i][j][1] < 180 and img[i][j][2] < 180:
                img[i][j] = b, g, r

    if style=='flat':
        img = cv2.resize(img, dsize=(0, 0), fx=1.4, fy=0.8)  # flat
        img = cv2.resize(img, dsize=(0, 0), fx=(10 / 14), fy=(10 / 14))  # flat
        Dy = int((whiteimg.shape[0] - img.shape[0]) / 2)
        whiteimg[Dy:Dy + img.shape[0], 0:0 + img.shape[1]] = img
        cv2.imwrite(path, whiteimg)
    elif style == 'long':
        img = cv2.resize(img,dsize=(0,0),fx=0.6,fy=1.8) # long
        img = cv2.resize(img,dsize=(0,0),fx=(10/18),fy=(10/18)) # long
        Dx = int((whiteimg.shape[1]-img.shape[1])/2)
        whiteimg[0:0 + img.shape[0], Dx:Dx + img.shape[1]] = img
        cv2.imwrite(path, whiteimg)
    else:
        cv2.imwrite(path, img)


def make_result(data, sequence, f_index):
    name = []
    email = data.get("email")
    input_name = data.get("name")
    name.append(input_name)

    src_font = './signMaker/ml_model/font/DancingScript-Regular.ttf'
    dst_fonts_path = './signMaker/ml_model/font/'
    f = open(dst_fonts_path + "dst_font.txt", 'r')
    dst_fonts =  f.readlines()

    num = f_index
    char_size, canvas_size, final_canvas_size = 100, 2000, 256
    x_offset, y_offset = 400, 400
    label = 1

    sample_dir = './signMaker/ml_model/samples/'
    if not os.path.isdir(sample_dir):
        os.mkdir(sample_dir)

    obj_dir = './signMaker/ml_model/obj/'
    if not os.path.isdir(obj_dir):
        os.mkdir(obj_dir)

    model_dir = './signMaker/ml_model/model/' + str(num) + '/'
    source_obj = obj_dir + 'test.obj'
    batch_size = 1
    embedding_ids = '0'
    embedding_num, embedding_dim = 1, 866
    inst_norm = 0

    save_dir = './signMaker/static/ml_result/' + email
    if not os.path.isdir(save_dir):
        os.mkdir(save_dir)

    font2img(src_font, dst_fonts_path + dst_fonts[num-1], name, char_size, canvas_size, final_canvas_size, x_offset, y_offset, sample_dir, label)

    test_path = os.path.join(obj_dir, "test.obj")
    pickle_tests(sorted(glob.glob(os.path.join(sample_dir, "*.jpg"))), test_path=test_path)

    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True

    tf.reset_default_graph()

    with tf.Session(config=config) as sess:
        model = UNet(batch_size=batch_size, embedding_num=embedding_num, embedding_dim=embedding_dim)
        model.register_session(sess)
        model.build_model(is_training=False, inst_norm=inst_norm)
    
        embedding_ids = [int(i) for i in embedding_ids.split(",")]
        embedding_ids = embedding_ids[0]

        model.infer(model_dir=model_dir, source_obj=source_obj, embedding_ids=embedding_ids, save_dir=save_dir)
    
    saved_path = './signMaker/static/ml_result/' + email + '/handwriting_name' + sequence + '.png'
    
    if len(data.get('option')) > 1:
        if sequence == "01":
            imageModify(saved_path, data.get('color'), 'long')
        elif sequence == "02":
            imageModify(saved_path, data.get('color'), 'flat')
        else:
            imageModify(saved_path, data.get('color'), 'long')
    else:
        imageModify(saved_path, data.get('color'), data.get('option'))
    applyAlpha.applyAlphaValue(email, saved_path, sequence)
    addLogo.putLogo(email, saved_path, sequence)
