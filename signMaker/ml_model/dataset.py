from __future__ import print_function
from __future__ import absolute_import

import pickle
import numpy as np
import random
import os
from utils import pad_seq, bytes_to_file, read_split_image, shift_and_resize_image, normalize_image


class PickledImageProvider(object):
    def __init__(self, obj_path):
        self.obj_path = obj_path
        self.examples = self.load_pickled_examples()

    def load_pickled_examples(self):
        with open(self.obj_path, "rb") as of:
            examples = list()
            while True:
                try:
                    e = pickle.load(of)
                    examples.append(e)
                except EOFError:
                    break
                except Exception:
                    pass
            return examples


def get_batch_iter(examples, batch_size):
    padded = pad_seq(examples, batch_size)

    def process(img):
        img = bytes_to_file(img)
        try:
            img_A, img_B = read_split_image(img)
            img_A = normalize_image(img_A)
            img_B = normalize_image(img_B)
            return np.concatenate([img_A, img_B], axis=2)
        finally:
            img.close()

    def batch_iter():
        for i in range(0, len(padded), batch_size):
            batch = padded[i: i + batch_size]
            labels = [e[0] for e in batch]
            processed = [process(e[1]) for e in batch]
            yield labels, np.array(processed).astype(np.float32)

    return batch_iter()


class InjectDataProvider(object):
    def __init__(self, obj_path):
        self.data = PickledImageProvider(obj_path)
        print("examples -> %d" % len(self.data.examples))

    def get_single_embedding_iter(self, batch_size, embedding_id):
        examples = self.data.examples[:]
        batch_iter = get_batch_iter(examples, batch_size)
        for _, images in batch_iter:
            # inject specific embedding style here
            labels = [embedding_id] * batch_size
            yield labels, images

    def get_random_embedding_iter(self, batch_size, embedding_ids):
        examples = self.data.examples[:]
        batch_iter = get_batch_iter(examples, batch_size)
        for _, images in batch_iter:
            # inject specific embedding style here
            labels = [random.choice(embedding_ids) for i in range(batch_size)]
            yield labels, images
