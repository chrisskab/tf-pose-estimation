import tensorflow as tf
import network_base

class MobilenetV2(network_base.BaseNetwork):
    def __init__(self, inputs, trainable=True, conv_width=1.0, conv_width2=0.5):
        self.conv_width = conv_width
        self.conv_width2 = conv_width2 if conv_width2 else conv_width
        network_base.BaseNetwork.__init__(self, inputs, trainable)

    def setup(self):
        min_depth = 8
        depth = lambda d: max(int(d * self.conv_width), min_depth)
        depth2 = lambda d: max(int(d * self.conv_width2), min_depth)

        (self.feed('image'))
        prefix = 'MConv_Stage1'
        feature_lv = 'feature'
        (self.feed('conv4_7_linear_bn',
                   'conv5_1_linear_bn')
         .add(name='feature')
         .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_1')
         .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_2')
         .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_3')
         .separable_conv(1, 1, depth2(512), 1, name=prefix + '_L1_4')
         .separable_conv(1, 1, 38, 1, relu=False, name=prefix + '_L1_5'))

        (self.feed(feature_lv)
         .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_1')
         .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_2')
         .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_3')
         .separable_conv(1, 1, depth2(512), 1, name=prefix + '_L2_4')
         .separable_conv(1, 1, 19, 1, relu=False, name=prefix + '_L2_5'))

        for stage_id in range(5):
            prefix_prev = 'MConv_Stage%d' % (stage_id + 1)
            prefix = 'MConv_Stage%d' % (stage_id + 2)
            (self.feed(prefix_prev + '_L1_5',
                       prefix_prev + '_L2_5',
                       feature_lv)
             .concat(3, name=prefix + '_concat')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_1')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_2')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_3')
             .separable_conv(1, 1, depth2(128), 1, name=prefix + '_L1_4')
             .separable_conv(1, 1, 38, 1, relu=False, name=prefix + '_L1_5'))

            (self.feed(prefix + '_concat')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_1')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_2')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_3')
             .separable_conv(1, 1, depth2(128), 1, name=prefix + '_L2_4')
             .separable_conv(1, 1, 19, 1, relu=False, name=prefix + '_L2_5'))

        # final result
        (self.feed('MConv_Stage6_L2_5',
                   'MConv_Stage6_L1_5')
         .concat(3, name='concat_stage7'))

    def loss_l1_l2(self):
        l1s = []
        l2s = []
        for layer_name in sorted(self.layers.keys()):
            if '_L1_5' in layer_name:
                l1s.append(self.layers[layer_name])
            if '_L2_5' in layer_name:
                l2s.append(self.layers[layer_name])

        return l1s, l2s

    def loss_last(self):
        return self.get_output('MConv_Stage6_L1_5'), self.get_output('MConv_Stage6_L2_5')

    def restorable_variables(self):
        return None

