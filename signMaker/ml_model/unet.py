from __future__ import print_function
from __future__ import absolute_import

import tensorflow as tf
import numpy as np
import scipy.misc as misc
import os
import time
from collections import namedtuple
from ops import conv2d, deconv2d, lrelu, fc, batch_norm, init_embedding, conditional_instance_norm
from dataset import InjectDataProvider
from utils import scale_back, merge, save_concat_images


LossHandle = namedtuple("LossHandle", ["d_loss", "g_loss", "const_loss", "l1_loss",
                                       "category_loss", "cheat_loss", "tv_loss"])
InputHandle = namedtuple("InputHandle", ["real_data", "embedding_ids", "no_target_data", "no_target_ids"])
EvalHandle = namedtuple("EvalHandle", ["encoder", "generator", "target", "source", "embedding"])
SummaryHandle = namedtuple("SummaryHandle", ["d_merged", "g_merged"])


class UNet(object):
    def __init__(self, experiment_id=0, batch_size=16, input_width=256, output_width=256,
                 generator_dim=64, discriminator_dim=64, L1_penalty=100, Lconst_penalty=15, Ltv_penalty=0.0,
                 Lcategory_penalty=1.0, embedding_num=1, embedding_dim=866, input_filters=3, output_filters=3):
        self.experiment_id = experiment_id
        self.batch_size = batch_size
        self.input_width = input_width
        self.output_width = output_width
        self.generator_dim = generator_dim
        self.discriminator_dim = discriminator_dim
        self.L1_penalty = L1_penalty
        self.Lconst_penalty = Lconst_penalty
        self.Ltv_penalty = Ltv_penalty
        self.Lcategory_penalty = Lcategory_penalty
        self.embedding_num = embedding_num
        self.embedding_dim = embedding_dim
        self.input_filters = input_filters
        self.output_filters = output_filters
        self.sess = None

    def encoder(self, images, is_training, reuse=False):
        with tf.variable_scope("generator"):
            if reuse:
                tf.get_variable_scope().reuse_variables()

            encode_layers = dict()

            def encode_layer(x, output_filters, layer):
                act = lrelu(x)
                conv = conv2d(act, output_filters=output_filters, scope="g_e%d_conv" % layer)
                enc = batch_norm(conv, is_training, scope="g_e%d_bn" % layer)
                encode_layers["e%d" % layer] = enc
                return enc

            e1 = conv2d(images, self.generator_dim, scope="g_e1_conv")
            encode_layers["e1"] = e1
            e2 = encode_layer(e1, self.generator_dim * 2, 2)
            e3 = encode_layer(e2, self.generator_dim * 4, 3)
            e4 = encode_layer(e3, self.generator_dim * 8, 4)
            e5 = encode_layer(e4, self.generator_dim * 8, 5)
            e6 = encode_layer(e5, self.generator_dim * 8, 6)
            e7 = encode_layer(e6, self.generator_dim * 8, 7)
            e8 = encode_layer(e7, self.generator_dim * 8, 8)

            return e8, encode_layers

    def decoder(self, encoded, encoding_layers, ids, inst_norm, is_training, reuse=False):
        with tf.variable_scope("generator"):
            if reuse:
                tf.get_variable_scope().reuse_variables()

            s = self.output_width
            s2, s4, s8, s16, s32, s64, s128 = int(s / 2), int(s / 4), int(s / 8), int(s / 16), int(s / 32), int(
                s / 64), int(s / 128)

            def decode_layer(x, output_width, output_filters, layer, enc_layer, dropout=False, do_concat=True):
                dec = deconv2d(tf.nn.relu(x), [self.batch_size, output_width,
                                               output_width, output_filters], scope="g_d%d_deconv" % layer)
                if layer != 8:
                    if inst_norm:
                        dec = conditional_instance_norm(dec, ids, self.embedding_num, scope="g_d%d_inst_norm" % layer)
                    else:
                        dec = batch_norm(dec, is_training, scope="g_d%d_bn" % layer)
                if dropout:
                    dec = tf.nn.dropout(dec, 0.5)
                if do_concat:
                    dec = tf.concat([dec, enc_layer], 3)
                return dec

            d1 = decode_layer(encoded, s128, self.generator_dim * 8, layer=1, enc_layer=encoding_layers["e7"],
                              dropout=True)
            d2 = decode_layer(d1, s64, self.generator_dim * 8, layer=2, enc_layer=encoding_layers["e6"], dropout=True)
            d3 = decode_layer(d2, s32, self.generator_dim * 8, layer=3, enc_layer=encoding_layers["e5"], dropout=True)
            d4 = decode_layer(d3, s16, self.generator_dim * 8, layer=4, enc_layer=encoding_layers["e4"])
            d5 = decode_layer(d4, s8, self.generator_dim * 4, layer=5, enc_layer=encoding_layers["e3"])
            d6 = decode_layer(d5, s4, self.generator_dim * 2, layer=6, enc_layer=encoding_layers["e2"])
            d7 = decode_layer(d6, s2, self.generator_dim, layer=7, enc_layer=encoding_layers["e1"])
            d8 = decode_layer(d7, s, self.output_filters, layer=8, enc_layer=None, do_concat=False)

            output = tf.nn.tanh(d8)
            return output

    def generator(self, images, embeddings, embedding_ids, inst_norm, is_training, reuse=False):
        e8, enc_layers = self.encoder(images, is_training=is_training, reuse=reuse)
        local_embeddings = tf.nn.embedding_lookup(embeddings, ids=embedding_ids)
        local_embeddings = tf.reshape(local_embeddings, [self.batch_size, 1, 1, self.embedding_dim])
        embedded = tf.concat([e8, local_embeddings], 3)
        output = self.decoder(embedded, enc_layers, embedding_ids, inst_norm, is_training=is_training, reuse=reuse)
        return output, e8

    def discriminator(self, image, is_training, reuse=False):
        with tf.variable_scope("discriminator"):
            if reuse:
                tf.get_variable_scope().reuse_variables()
            h0 = lrelu(conv2d(image, self.discriminator_dim, scope="d_h0_conv"))
            h1 = lrelu(batch_norm(conv2d(h0, self.discriminator_dim * 2, scope="d_h1_conv"),
                                  is_training, scope="d_bn_1"))
            h2 = lrelu(batch_norm(conv2d(h1, self.discriminator_dim * 4, scope="d_h2_conv"),
                                  is_training, scope="d_bn_2"))
            h3 = lrelu(batch_norm(conv2d(h2, self.discriminator_dim * 8, sh=1, sw=1, scope="d_h3_conv"),
                                  is_training, scope="d_bn_3"))
            # real or fake binary loss
            fc1 = fc(tf.reshape(h3, [self.batch_size, -1]), 1, scope="d_fc1")
            # category loss
            fc2 = fc(tf.reshape(h3, [self.batch_size, -1]), self.embedding_num, scope="d_fc2")

            return tf.nn.sigmoid(fc1), fc1, fc2

    def build_model(self, is_training=True, inst_norm=False):
        real_data = tf.placeholder(tf.float32,
                                   [self.batch_size, self.input_width, self.input_width, self.input_filters + self.output_filters],
                                   name='real_A_and_B_images')
        embedding_ids = tf.placeholder(tf.int64, shape=None, name="embedding_ids")
        no_target_data = tf.placeholder(tf.float32,
                                        [self.batch_size, self.input_width, self.input_width, self.input_filters + self.output_filters],
                                        name='no_target_A_and_B_images')
        no_target_ids = tf.placeholder(tf.int64, shape=None, name="no_target_embedding_ids")

        # target images
        real_B = real_data[:, :, :, :self.input_filters]
        # source images
        real_A = real_data[:, :, :, self.input_filters:self.input_filters + self.output_filters]

        embedding = init_embedding(self.embedding_num, self.embedding_dim)
        fake_B, encoded_real_A = self.generator(real_A, embedding, embedding_ids, is_training=is_training,
                                                inst_norm=inst_norm)
        real_AB = tf.concat([real_A, real_B], 3)
        fake_AB = tf.concat([real_A, fake_B], 3)

        real_D, real_D_logits, real_category_logits = self.discriminator(real_AB, is_training=is_training, reuse=False)
        fake_D, fake_D_logits, fake_category_logits = self.discriminator(fake_AB, is_training=is_training, reuse=True)

        # encoding constant loss
        encoded_fake_B = self.encoder(fake_B, is_training, reuse=True)[0]
        const_loss = (tf.reduce_mean(tf.square(encoded_real_A - encoded_fake_B))) * self.Lconst_penalty

        # category loss
        true_labels = tf.reshape(tf.one_hot(indices=embedding_ids, depth=self.embedding_num), shape=[self.batch_size, self.embedding_num])
        real_category_loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=real_category_logits, labels=true_labels))
        fake_category_loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=fake_category_logits, labels=true_labels))
        category_loss = self.Lcategory_penalty * (real_category_loss + fake_category_loss)

        # binary real/fake loss
        d_loss_real = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=real_D_logits, labels=tf.ones_like(real_D)))
        d_loss_fake = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=fake_D_logits, labels=tf.zeros_like(fake_D)))

        # L1 loss between real and generated images
        l1_loss = self.L1_penalty * tf.reduce_mean(tf.abs(fake_B - real_B))

        # total variation loss
        width = self.output_width
        tv_loss = (tf.nn.l2_loss(fake_B[:, 1:, :, :] - fake_B[:, :width - 1, :, :]) / width
                   + tf.nn.l2_loss(fake_B[:, :, 1:, :] - fake_B[:, :, :width - 1, :]) / width) * self.Ltv_penalty

        cheat_loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=fake_D_logits, labels=tf.ones_like(fake_D)))

        d_loss = d_loss_real + d_loss_fake + category_loss / 2.0
        g_loss = cheat_loss + l1_loss + self.Lcategory_penalty * fake_category_loss + const_loss + tv_loss

        d_loss_real_summary = tf.summary.scalar("d_loss_real", d_loss_real)
        d_loss_fake_summary = tf.summary.scalar("d_loss_fake", d_loss_fake)
        category_loss_summary = tf.summary.scalar("category_loss", category_loss)
        cheat_loss_summary = tf.summary.scalar("cheat_loss", cheat_loss)
        l1_loss_summary = tf.summary.scalar("l1_loss", l1_loss)
        fake_category_loss_summary = tf.summary.scalar("fake_category_loss", fake_category_loss)
        const_loss_summary = tf.summary.scalar("const_loss", const_loss)
        d_loss_summary = tf.summary.scalar("d_loss", d_loss)
        g_loss_summary = tf.summary.scalar("g_loss", g_loss)
        tv_loss_summary = tf.summary.scalar("tv_loss", tv_loss)

        d_merged_summary = tf.summary.merge([d_loss_real_summary, d_loss_fake_summary, category_loss_summary, d_loss_summary])
        g_merged_summary = tf.summary.merge([cheat_loss_summary, l1_loss_summary, fake_category_loss_summary,
                                             const_loss_summary, g_loss_summary, tv_loss_summary])

        input_handle = InputHandle(real_data=real_data, embedding_ids=embedding_ids, no_target_data=no_target_data, no_target_ids=no_target_ids)
        loss_handle = LossHandle(d_loss=d_loss, g_loss=g_loss, const_loss=const_loss, l1_loss=l1_loss,
                                 category_loss=category_loss, cheat_loss=cheat_loss, tv_loss=tv_loss)
        eval_handle = EvalHandle(encoder=encoded_real_A, generator=fake_B, target=real_B, source=real_A, embedding=embedding)
        summary_handle = SummaryHandle(d_merged=d_merged_summary, g_merged=g_merged_summary)

        setattr(self, "input_handle", input_handle)
        setattr(self, "loss_handle", loss_handle)
        setattr(self, "eval_handle", eval_handle)
        setattr(self, "summary_handle", summary_handle)

    def register_session(self, sess):
        self.sess = sess

    def retrieve_generator_vars(self):
        all_vars = tf.global_variables()
        generate_vars = [var for var in all_vars if 'embedding' in var.name or "g_" in var.name]
        return generate_vars

    def retrieve_handles(self):
        input_handle = getattr(self, "input_handle")
        loss_handle = getattr(self, "loss_handle")
        eval_handle = getattr(self, "eval_handle")
        summary_handle = getattr(self, "summary_handle")

        return input_handle, loss_handle, eval_handle, summary_handle

    def get_model_id_and_dir(self):
        model_id = "experiment_%d_batch_%d" % (self.experiment_id, self.batch_size)
        model_dir = os.path.join(self.checkpoint_dir, model_id)
        return model_id, model_dir

    def restore_model(self, saver, model_dir):
        ckpt = tf.train.get_checkpoint_state(model_dir)
        if ckpt:
            saver.restore(self.sess, ckpt.model_checkpoint_path)
            print("restored model %s" % model_dir)
        else:
            print("fail to restore model %s" % model_dir)

    def generate_fake_samples(self, input_images, embedding_ids):
        input_handle, loss_handle, eval_handle, summary_handle = self.retrieve_handles()
        fake_images, real_images, \
        d_loss, g_loss, l1_loss = self.sess.run([eval_handle.generator,
                                                 eval_handle.target,
                                                 loss_handle.d_loss,
                                                 loss_handle.g_loss,
                                                 loss_handle.l1_loss],
                                                feed_dict={
                                                    input_handle.real_data: input_images,
                                                    input_handle.embedding_ids: embedding_ids,
                                                    input_handle.no_target_data: input_images,
                                                    input_handle.no_target_ids: embedding_ids
                                                })
        return fake_images, real_images, d_loss, g_loss, l1_loss

    def infer(self, source_obj, embedding_ids, model_dir, save_dir):
        source_provider = InjectDataProvider(source_obj)

        if isinstance(embedding_ids, int) or len(embedding_ids) == 1:
            embedding_id = embedding_ids if isinstance(embedding_ids, int) else embedding_ids[0]
            source_iter = source_provider.get_single_embedding_iter(self.batch_size, embedding_id)
        else:
            source_iter = source_provider.get_random_embedding_iter(self.batch_size, embedding_ids)

        tf.global_variables_initializer().run()
        saver = tf.train.Saver(var_list=self.retrieve_generator_vars())
        self.restore_model(saver, model_dir)

        def save_imgs(imgs, count):
            p = os.path.join(save_dir, "inferred_%04d.png" % count)
            save_concat_images(imgs, img_path=p)
            print("generated images saved at %s" % p)

        count = 0
        batch_buffer = list()
        for labels, source_imgs in source_iter:
            fake_imgs = self.generate_fake_samples(source_imgs, labels)[0]
            merged_fake_images = merge(scale_back(fake_imgs), [self.batch_size, 1])
            batch_buffer.append(merged_fake_images)
            if len(batch_buffer) == 10:
                save_imgs(batch_buffer, count)
                batch_buffer = list()
            count += 1
        if batch_buffer:
            # last batch
            save_imgs(batch_buffer, count)
