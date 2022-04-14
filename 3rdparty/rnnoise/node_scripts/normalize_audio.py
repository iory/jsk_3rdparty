#!/usr/bin/env python
import rospy
from audio_common_msgs.msg import AudioData
import numpy as np

from pydub import AudioSegment


def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)


class NormalizeAudioNode(object):

    def __init__(self):
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
        for i in range(step, len(self.audio_buffer), step):
            denoised_audio = self.denoiser.filter(
                self.audio_buffer[i - step:i],
                sample_rate=sample_rate,
                voice_prob_threshold=voice_prob_threshold)
            self.pub.publish(AudioData(data=denoised_audio))
        self.audio_buffer = self.audio_buffer[i:]


if __name__ == '__main__':
    rospy.init_node('normalize_audio_node')
    NormalizeAudioNode()
    rospy.spin()
