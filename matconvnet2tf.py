# Copyright 2017 Stanislav Pidhorskyi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# This code based on the code taken from https://github.com/cuixue/vgg-f-tensorflow.

import numpy as np
import scipy.io
import tensorflow as tf


class MatConvNet2TF:
    """Reads matconvnet file creates tensorflow graph."""
    def __init__(self, data_path, do_debug_print=False):
        data = scipy.io.loadmat(data_path, struct_as_record=False, squeeze_me=True)
        layers = data['layers']
        self.mean = np.array(data['meta'].normalization.averageImage, ndmin=4)
        self.net = {}
        self.weight_decay_losses = []
        self.net['classes'] = data['meta'].classes.description
        self.do_debug_print = do_debug_print
        input_shape = tuple(data['meta'].inputs.size[:3])
        input_shape = (None,) + input_shape
        self.input = tf.placeholder('float32', input_shape)

        self.layer_types = {
            'conv': self._conv_layer,
            'relu': self._relu_layer,
            'pool': self._pool_layer,
            'lrn': self._lrn_layer,
            'softmax': self._softmax_layer,
        }

        current = self.input - self.mean
        for i, layer in enumerate(layers):
            current = self.layer_types[layer.type](current, layer)
            self.net[layer.name] = current
        self.output = current
        self.weight_decay = tf.add_n(self.weight_decay_losses)

    @staticmethod
    def _convert_pad(pad):
        return [[0, 0], [pad[0], pad[1]], [pad[2], pad[3]], [0, 0]]

    @staticmethod
    def _convert_stride(stride):
        return [1, stride[0], stride[1], 1]

    def _softmax_layer(self, input, layer):
        if self.do_debug_print:
            print("{0:6} {1:6}. dim: {2}".format(layer.name, 'softmax', input.get_shape()))
        return tf.nn.softmax(input, name=layer.name)

    def _relu_layer(self, input, layer):
        if self.do_debug_print:
            print("{0:6} {1:6}. dim: {2}".format(layer.name, 'relu', input.get_shape()))
        return tf.nn.relu(input, name=layer.name)

    def _lrn_layer(self, input, layer):
        # depth_radius = (N - 1) / 2; PARAM = [N KAPPA ALPHA BETA]
        n = layer.param[0]
        depth = int((n-1)//2)
        bias = layer.param[1]
        alpha = layer.param[2]
        beta = layer.param[3]
        if self.do_debug_print:
            print("{0:6} {1:6}. dim: {2}. depth: {3}, bias: {4}, alpha: {5}, beta: {5}".format(
                layer.name,
                'lrn',
                input.get_shape(),
                depth,
                bias,
                alpha,
                beta))
        return tf.nn.local_response_normalization(input,
                                                  depth_radius=depth,
                                                  bias=bias,
                                                  alpha=alpha,
                                                  beta=beta,
                                                  name=layer.name)

    def _conv_layer(self, input, layer):
        with tf.name_scope(layer.name):
            weights, biases = layer.weights
            biases = biases.reshape(-1)
            output = input
            if (layer.pad != [0, 0, 0, 0]).all():
                output = tf.pad(input, self._convert_pad(layer.pad), "CONSTANT")
            if ((layer.size[:2] == [1, 1]).all() or layer.size[:3] == input.get_shape().as_list()[1:]).all():
                if len(output.shape) != 2:
                    shape = output.get_shape().as_list()[1:]
                    output = tf.reshape(output, [-1, shape[0] * shape[1] * shape[2]])
                weights = weights.reshape([output.get_shape()[-1], -1])
                w = tf.Variable(weights, name='weights', dtype='float32')
                b = tf.Variable(biases, name='biases', dtype='float32')
                self.weight_decay_losses.append(tf.nn.l2_loss(w))
                output = tf.matmul(output, w)
                if self.do_debug_print:
                    print("{0:6} {1:6}. dim-in: {2} dim-out: {3}".format(
                        layer.name,
                        'fcn',
                        input.get_shape(),
                        output.get_shape()))
            else:
                weights = np.array(weights, ndmin=4)
                w = tf.Variable(weights, name='weights', dtype='float32')
                b = tf.Variable(biases, name='biases', dtype='float32')
                self.weight_decay_losses.append(tf.nn.l2_loss(w))
                output = tf.nn.conv2d(output,
                                    w,
                                    strides=self._convert_stride(layer.stride),
                                    padding='VALID',
                                    name=layer.name)
                if self.do_debug_print:
                    print("{0:6} {1:6}. dim-in: {2} dim-out: {3} padding: {4}, strides: {5} ksize {6}".format(
                        layer.name,
                        'conv',
                        input.get_shape(),
                        output.get_shape(),
                        layer.pad,
                        layer.stride,
                        w.get_shape()))
            return tf.nn.bias_add(output, b, name='add')

    def _pool_layer(self, input, layer):
        with tf.name_scope(layer.name):
            input = tf.pad(input, self._convert_pad(layer.pad), "CONSTANT")
            output = tf.nn.max_pool(input,
                                  ksize=self._convert_stride(layer.pool),
                                  strides=self._convert_stride(layer.stride),
                                  padding='VALID')
        if self.do_debug_print:
            print("{0:6} {1:6}. dim-in: {2} dim-out: {3} ksize: {4}, strides: {5}".format(
                layer.name,
                'pool',
                input.get_shape(),
                output.get_shape(),
                layer.pool,
                layer.stride))
        return output
