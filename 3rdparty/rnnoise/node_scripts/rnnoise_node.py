#!/usr/bin/env python
import rospy
from audio_common_msgs.msg import AudioData
import numpy as np

from rnnoise import RNNoise


class RNNoiseNode(object):

    def __init__(self):
        self.denoiser = RNNoise()
        self.subscribe()

    def subscribe(self):
        self.sub_audio = rospy.Subscriber(
            '~audio', AudioData,
            callback=self.callback,
            queue_size=1)

    def callback(self, audio_msg):
        # self.dtype = 'int16'
        # audio_buffer = np.frombuffer(audio_msg.data, dtype=self.dtype)
        # audio_buffer = audio_buffer[0::self.n_channel]
        # print(len(audio_buffer), len(audio_msg.data))
        pass
        # voice_prob_threshold = 0.8
        # for i in range(buffer_size_ms, len(audio), buffer_size_ms):
        #     denoised_audio += self.denoiser.filter(audio[i-buffer_size_ms:i].raw_data, sample_rate=audio.frame_rate,
        #                                       voice_prob_threshold=voice_prob_threshold)
        # if len(audio) % buffer_size_ms != 0:
        #     denoised_audio += self.denoiser.filter(audio[len(audio)-(len(audio)%buffer_size_ms):].raw_data, sample_rate=audio.frame_rate,
        #                                       voice_prob_threshold=voice_prob_threshold)

        # self.denoiser.write_wav('test_denoised_stream.wav', denoised_audio, sample_rate=audio.frame_rate)


if __name__ == '__main__':
    rospy.init_node('rnnoise_node')
    RNNoiseNode()
    rospy.spin()
