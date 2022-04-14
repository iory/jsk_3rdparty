#!/usr/bin/env python

from copy import deepcopy

import rospy
from audio_common_msgs.msg import AudioData
import numpy as np

from rnnoise import RNNoise
from pydub import AudioSegment
from pydub import effects


class RNNoiseNode(object):

    def __init__(self):
        self.denoiser = RNNoise()
        self.denoiser.channels = 1
        # self.denoiser.sample_rate = 16000
        self.audio_buffer = b''
        self.tmp_audio_buffer = b''
        self.pub = rospy.Publisher(
            '~output', AudioData,
            queue_size=1)
        self.subscribe()

    def subscribe(self):
        self.sub_audio = rospy.Subscriber(
            '~audio', AudioData,
            callback=self.callback,
            queue_size=100)

    def callback(self, audio_msg):
        tmp = deepcopy(audio_msg.data)
        seg = AudioSegment(audio_msg.data,
                           metadata={'channels': 1,
                                     'sample_width': 2,
                                     'frame_rate': 16000,
                                     'frame_width': 2})
        normalized_sound = effects.normalize(seg, 1.0)
        n_channel = self.denoiser.channels
        # print(len(normalized_sound.raw_data), len(audio_msg.data))
        norm_tmp = normalized_sound.raw_data

        sample_rate = 16000
        buffer_size_ms = 10
        sample_width = 16 // 8
        buffer_size_s = buffer_size_ms * 0.001
        n_frame = (len(tmp) // sample_width) // n_channel
        required_frame_count = int(buffer_size_s * sample_rate)
        self.audio_buffer += tmp
        self.tmp_audio_buffer += norm_tmp
        voice_prob_threshold = 0.2
        step = required_frame_count * n_channel * sample_width
        i = 0
        # print(len(self.audio_buffer))
        for i in range(step, len(self.audio_buffer), step):
            denoised_audio = self.denoiser.filter(
                self.audio_buffer[i - step:i],
                sample_rate=sample_rate,
                voice_prob_threshold=voice_prob_threshold)
            # denoised_audio = self.denoiser.filter_with_audio(
            #     self.tmp_audio_buffer[i - step:i],
            #     self.audio_buffer[i - step:i],
            #     sample_rate=sample_rate,
            #     voice_prob_threshold=voice_prob_threshold)
            self.pub.publish(AudioData(data=denoised_audio))
        self.audio_buffer = self.audio_buffer[i:]
        self.tmp_audio_buffer = self.tmp_audio_buffer[i:]


if __name__ == '__main__':
    rospy.init_node('rnnoise_node')
    RNNoiseNode()
    rospy.spin()
