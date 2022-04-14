#!/usr/bin/env python
import rospy
from audio_common_msgs.msg import AudioData
import numpy as np

from rnnoise import RNNoise


class RNNoiseNode(object):

    def __init__(self):
        self.denoiser = RNNoise()
        self.denoiser.channels = 1
        # self.denoiser.sample_rate = 16000
        self.audio_buffer = b''
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
        n_channel = self.denoiser.channels
        sample_rate = 16000
        buffer_size_ms = 10
        sample_width = 16 // 8
        buffer_size_s = buffer_size_ms * 0.001
        n_frame = (len(audio_msg.data) // sample_width) // n_channel
        required_frame_count = int(buffer_size_s * sample_rate)
        self.audio_buffer += audio_msg.data
        voice_prob_threshold = 0.8
        step = required_frame_count * n_channel * sample_width
        i = 0
        # print(len(self.audio_buffer))
        for i in range(step, len(self.audio_buffer), step):
            denoised_audio = self.denoiser.filter(
                self.audio_buffer[i - step:i],
                sample_rate=sample_rate,
                voice_prob_threshold=voice_prob_threshold)
            print(len(denoised_audio))
            self.pub.publish(AudioData(data=denoised_audio))
        self.audio_buffer = self.audio_buffer[i:]


if __name__ == '__main__':
    rospy.init_node('rnnoise_node')
    RNNoiseNode()
    rospy.spin()
