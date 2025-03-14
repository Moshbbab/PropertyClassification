'''This script demonstrates how to build a variational autoencoder
with Keras and deconvolution layers.
# Reference
- Auto-Encoding Variational Bayes
  https://arxiv.org/abs/1312.6114
'''
from __future__ import print_function

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

from keras.layers import Input, Dense, Lambda, Flatten, Reshape
from keras.layers import Conv2D, Conv2DTranspose
from keras.models import Model
from keras import backend as K
from keras import metrics
from keras.datasets import mnist

# input image dimensions
img_rows, img_cols, img_chns = 128, 128, 3
# number of convolutional filters to use
filters = 64
# convolution kernel size
num_conv = 3

batch_size = 100
if K.image_data_format() == 'channels_first':
    original_img_size = (img_chns, img_rows, img_cols)
else:
    original_img_size = (img_rows, img_cols, img_chns)
latent_dim = 64
intermediate_dim = 128
epsilon_std = 1.0
epochs = 5


x = Input(shape=original_img_size)
print ('X ', x)
conv_1 = Conv2D(img_chns,
                kernel_size=(2, 2),
                padding='same', activation='relu')(x)
print ('conv_1 ', conv_1.shape)
conv_2 = Conv2D(filters,
                kernel_size=(2, 2),
                padding='same', activation='relu',
                strides=(2, 2))(conv_1)
print ('conv_2 ', conv_2.shape)
conv_3 = Conv2D(filters,
                kernel_size=num_conv,
                padding='same', activation='relu',
                strides=1)(conv_2)
print ('conv_3 ', conv_3.shape)
conv_4 = Conv2D(filters,
                kernel_size=num_conv,
                padding='same', activation='relu',
                strides=1)(conv_3)
print ('conv_4 ', conv_4.shape)

flat = Flatten()(conv_4)
print ('flattened ', flat.shape)
hidden = Dense(intermediate_dim, activation='relu')(flat)
print ('hidden ', hidden.shape)

z_mean = Dense(latent_dim)(hidden)
z_log_var = Dense(latent_dim)(hidden)


def sampling(args):
    z_mean, z_log_var = args
    epsilon = K.random_normal(shape=(K.shape(z_mean)[0], latent_dim),
                              mean=0., stddev=epsilon_std)
    return z_mean + K.exp(z_log_var) * epsilon

# note that "output_shape" isn't necessary with the TensorFlow backend
# so you could write `Lambda(sampling)([z_mean, z_log_var])`
z = Lambda(sampling, output_shape=(latent_dim,))([z_mean, z_log_var])
print ('z.shape ', z.shape)
# we instantiate these layers separately so as to reuse them later
decoder_hid = Dense(intermediate_dim, activation='relu')

decoder_upsample = Dense(filters * 32 * 32, activation='relu')

if K.image_data_format() == 'channels_first':
    output_shape = (batch_size, filters, 32, 32)
else:
    output_shape = (batch_size, 32, 32, filters)
#
decoder_reshape = Reshape(output_shape[1:])
decoder_deconv_1 = Conv2DTranspose(filters,
                                   kernel_size=num_conv,
                                   padding='same',
                                   strides=1,
                                   activation='relu')

decoder_deconv_2 = Conv2DTranspose(filters,
                                   kernel_size=num_conv,
                                   padding='same',
                                   strides=1,
                                   activation='relu')
if K.image_data_format() == 'channels_first':
    output_shape = (batch_size, filters, 29, 29)
else:
    output_shape = (batch_size, 29, 29, filters)
decoder_deconv_3_upsamp = Conv2DTranspose(filters,
                                          kernel_size=(3, 3),
                                          strides=(2, 2),
                                          padding='valid',
                                          activation='relu')
decoder_mean_squash = Conv2D(img_chns,
                             kernel_size=2,
                             padding='valid',
                             activation='sigmoid')
#
hid_decoded = decoder_hid(z)
print ('hid_decoded ', hid_decoded.shape)
up_decoded = decoder_upsample(hid_decoded)
print ('up_decoded ', up_decoded.shape)
reshape_decoded = decoder_reshape(up_decoded)
print ('reshape_decoded ', reshape_decoded.shape)
deconv_1_decoded = decoder_deconv_1(reshape_decoded)
print ('deconv_1_decoded ', deconv_1_decoded.shape)
deconv_2_decoded = decoder_deconv_2(deconv_1_decoded)
print ('deconv_2_decoded ', deconv_2_decoded.shape)
x_decoded_relu = decoder_deconv_3_upsamp(deconv_2_decoded)
print ('x_decoded_relu ', x_decoded_relu.shape)
x_decoded_mean_squash = decoder_mean_squash(x_decoded_relu)
print ('x_decoded_mean_squash ', x_decoded_mean_squash.shape)
# instantiate VAE model
vae = Model(x, x_decoded_mean_squash)

# Compute VAE loss
xent_loss = img_rows * img_cols * metrics.binary_crossentropy(
    K.flatten(x),
    K.flatten(x_decoded_mean_squash))
kl_loss = - 0.5 * K.sum(1 + z_log_var - K.square(z_mean) - K.exp(z_log_var), axis=-1)
vae_loss = K.mean(xent_loss + kl_loss)
aaa = vae.add_loss(vae_loss)

vae.compile(optimizer='rmsprop', loss=aaa)
vae.summary()



import tensorflow as tf
from config import pathDict
from data_transformation.data_io import getH5File
import seaborn as sns
from data_transformation.preprocessing import Preprocessing

sns.set_style("whitegrid")

out_img_shape = [128 ,128 ,3]
def run_preprocessor(sess, dataIN, preprocess_graph, is_training):
    out_shape = [dataIN.shape[0]] + out_img_shape
    pp_imgs = np.ndarray(shape=(out_shape), dtype='float32')
    for img_no in np.arange(dataIN.shape[0]):
        feed_dict = {
            preprocess_graph['imageIN']: dataIN[img_no, :],
            preprocess_graph['is_training']: is_training
        }
        pp_imgs[img_no, :] = sess.run(
                preprocess_graph['imageOUT'],
                feed_dict=feed_dict
        )

    return pp_imgs


def load_batch_data(image_type, which_data='cvalid'):
    if image_type not in ['bing_aerial', 'google_aerial', 'assessor', 'google_streetside', 'bing_streetside',
                          'google_overlayed', 'assessor_code']:
        raise ValueError('Can not identify the image type %s, Please provide a valid one' % (str(image_type)))

    data_path = pathDict['%s_batch_path' % (str(image_type))]
    batch_file_name = '%s' % (which_data)

    # LOAD THE TRAINING DATA FROM DISK
    dataX, dataY = getH5File(data_path, batch_file_name)

    return dataX, dataY



preprocess_graph = Preprocessing(inp_img_shape=[250,300,3],
                                 crop_shape=[196,128,3],
                                 out_img_shape=[128,128,3]).preprocessImageGraph()


trainX = []
trainY = []
batch_size = 15
with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())

    cvalidX, cvalidY = load_batch_data(image_type='assessor_code', which_data='cvalid')
    print('cvalid_shape: ', cvalidX.shape)
    cvpreprocessed_data = run_preprocessor(sess, cvalidX, preprocess_graph, is_training=False)
    
    for batch_num in range(0, batch_size):
        print ('running batch  number: ', batch_num)
        batchX, batchY = load_batch_data(image_type='assessor_code', which_data='train_%s' % (batch_num))
        preprocessed_data = run_preprocessor(sess, batchX, preprocess_graph, is_training=True)
        if batch_num == 0:
            trainX = preprocessed_data
            trainY = batchY
        else:
            trainX = np.vstack((trainX, preprocessed_data))
            trainY = np.append(trainY, batchY)
        
print (trainX.shape, trainY.shape, cvpreprocessed_data.shape)

#
vae.fit(trainX,
        shuffle=True,
        epochs=5,
        batch_size=batch_size,
        validation_data=(cvpreprocessed_data, None))

encoder = Model(x, z_mean)
x_test_encoded = encoder.predict(cvpreprocessed_data, batch_size=batch_size)

from sklearn.cluster import KMeans

kmeans = KMeans(n_clusters=2, n_init=100, random_state=443)
kmeans = kmeans.fit(x_test_encoded)
labels = kmeans.predict(x_test_encoded)
centroids = kmeans.cluster_centers_
#                 print (labels)
#                 labels[labels == 0] = 6
#                 labels[labels == 1] = 8

from conv_net.utils import Score
scr = Score.accuracy(cvalidY, labels)

#
#
#
#


#
# # train the VAE on MNIST digits
# (x_train, _), (x_test, y_test) = mnist.load_data()
#
# x_train = x_train.astype('float32') / 255.
# x_train = x_train.reshape((x_train.shape[0],) + original_img_size)
# x_test = x_test.astype('float32') / 255.
# x_test = x_test.reshape((x_test.shape[0],) + original_img_size)
#
# print('x_train.shape:', x_train.shape)
#

#
# # build a model to project inputs on the latent space
# encoder = Model(x, z_mean)
#
# # # display a 2D plot of the digit classes in the latent space
# x_test_encoded = encoder.predict(x_test, batch_size=batch_size)
# plt.figure(figsize=(6, 6))
# plt.scatter(x_test_encoded[:, 0], x_test_encoded[:, 1], c=y_test)
# plt.colorbar()
# plt.show()
#
# # build a digit generator that can sample from the learned distribution
# decoder_input = Input(shape=(latent_dim,))
# _hid_decoded = decoder_hid(decoder_input)
# _up_decoded = decoder_upsample(_hid_decoded)
# _reshape_decoded = decoder_reshape(_up_decoded)
# _deconv_1_decoded = decoder_deconv_1(_reshape_decoded)
# _deconv_2_decoded = decoder_deconv_2(_deconv_1_decoded)
# _x_decoded_relu = decoder_deconv_3_upsamp(_deconv_2_decoded)
# _x_decoded_mean_squash = decoder_mean_squash(_x_decoded_relu)
# generator = Model(decoder_input, _x_decoded_mean_squash)
#
# # display a 2D manifold of the digits
# n = 15  # figure with 15x15 digits
# digit_size = 28
# figure = np.zeros((digit_size * n, digit_size * n))
# # linearly spaced coordinates on the unit square were transformed through the inverse CDF (ppf) of the Gaussian
# # to produce values of the latent variables z, since the prior of the latent space is Gaussian
# grid_x = norm.ppf(np.linspace(0.05, 0.95, n))
# grid_y = norm.ppf(np.linspace(0.05, 0.95, n))
#
# for i, yi in enumerate(grid_x):
#     for j, xi in enumerate(grid_y):
#         z_sample = np.array([[xi, yi]])
#         z_sample = np.tile(z_sample, batch_size).reshape(batch_size, 2)
#         x_decoded = generator.predict(z_sample, batch_size=batch_size)
#         digit = x_decoded[0].reshape(digit_size, digit_size)
#         figure[i * digit_size: (i + 1) * digit_size,
#                j * digit_size: (j + 1) * digit_size] = digit
#
# plt.figure(figsize=(10, 10))
# plt.imshow(figure, cmap='Greys_r')
# plt.show()