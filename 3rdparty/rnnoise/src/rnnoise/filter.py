import os
import platform
import time
import ctypes
import pkg_resources
import numpy as np
from pydub import AudioSegment
import roslib.packages

PACKAGE_NAME = 'rnnoise'


class RNNoise(object):

    sample_width = 2
    channels = 1
    sample_rate = 48000
    frame_duration_ms = 10

    def __init__(self, f_name_lib=None):
        rnnoise_lib_path = os.path.join(
            roslib.packages.get_pkg_dir(PACKAGE_NAME),
            'lib', 'librnnoise.so.0.4.1')
        self.rnnoise_lib = ctypes.cdll.LoadLibrary(rnnoise_lib_path)
        self.rnnoise_lib.rnnoise_process_frame.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_float)]
        self.rnnoise_lib.rnnoise_process_frame.restype = ctypes.c_float
        self.rnnoise_lib.rnnoise_create.restype = ctypes.c_void_p
        self.rnnoise_lib.rnnoise_destroy.argtypes = [ctypes.c_void_p]
        self.rnnoise_obj = self.rnnoise_lib.rnnoise_create(None)

    def reset(self):
        self.rnnoise_lib.rnnoise_destroy(self.rnnoise_obj)
        self.rnnoise_obj = self.rnnoise_lib.rnnoise_create(None)

    def filter_frame(self, frame):
        frame_buf = np.ndarray((480,), 'h', frame).astype(ctypes.c_float)
        frame_buf_ptr = frame_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

        vad_probability = self.rnnoise_lib.rnnoise_process_frame(self.rnnoise_obj, frame_buf_ptr, frame_buf_ptr)
        return vad_probability, frame_buf.astype(ctypes.c_short).tobytes()

    def filter(self, audio, sample_rate=None, voice_prob_threshold=0.0, save_source_sample_rate=True):
        frames, source_sample_rate = self.__get_frames(audio, sample_rate)
        if not save_source_sample_rate:
            source_sample_rate = None

        denoised_audio = self.__filter_frames(frames, voice_prob_threshold, source_sample_rate)

        if isinstance(audio, AudioSegment):
            return denoised_audio
        else:
            return denoised_audio.raw_data

    def __filter_frames(self, frames, voice_prob_threshold=0.0, sample_rate=None):
        denoised_frames_with_probability = [self.filter_frame(frame) for frame in frames]
        denoised_frames = []
        for frame_with_prob in denoised_frames_with_probability:
            if frame_with_prob[0] >= voice_prob_threshold:
                denoised_frames.append(frame_with_prob[1])
            else:
                denoised_frames.append(len(frame_with_prob[1]) * b'\x00')
        denoised_audio_bytes = b''.join(denoised_frames)

        denoised_audio = AudioSegment(data=denoised_audio_bytes, sample_width=self.sample_width, frame_rate=self.sample_rate, channels=self.channels)

        if sample_rate:
            denoised_audio = denoised_audio.set_frame_rate(sample_rate)
        return denoised_audio


    def filter_with_audio(self, audio, another_audio, sample_rate=None, voice_prob_threshold=0.0, save_source_sample_rate=True):
        frames, source_sample_rate = self.__get_frames(audio, sample_rate)
        another_frames, another_source_sample_rate = self.__get_frames(
            another_audio, sample_rate)
        if not save_source_sample_rate:
            source_sample_rate = None

        denoised_audio = self.__filter_frames_with(
            frames, another_frames, voice_prob_threshold, source_sample_rate)

        if isinstance(audio, AudioSegment):
            return denoised_audio
        else:
            return denoised_audio.raw_data

    def __filter_frames_with(self, frames, another_frames, voice_prob_threshold=0.0, sample_rate=None):
        denoised_frames_with_probability = [self.filter_frame(frame) for frame in frames]
        another_denoised_frames_with_probability = [self.filter_frame(frame) for frame in another_frames]
        denoised_frames = []
        for frame_with_prob, another_frame_with_prob in zip(denoised_frames_with_probability,
                                                            another_denoised_frames_with_probability):
            if frame_with_prob[0] >= voice_prob_threshold:
                denoised_frames.append(another_frame_with_prob[1])
            else:
                denoised_frames.append(len(another_frame_with_prob[1]) * b'\x00')
        denoised_audio_bytes = b''.join(denoised_frames)

        denoised_audio = AudioSegment(data=denoised_audio_bytes, sample_width=self.sample_width, frame_rate=self.sample_rate, channels=self.channels)

        if sample_rate:
            denoised_audio = denoised_audio.set_frame_rate(sample_rate)
        return denoised_audio

    def __get_frames(self, audio, sample_rate=None):
        if isinstance(audio, AudioSegment):
            sample_rate = source_sample_rate = audio.frame_rate
            if sample_rate != self.sample_rate:
                audio = audio.set_frame_rate(self.sample_rate)
            audio_bytes = audio.raw_data
        elif isinstance(audio, bytes):
            if not sample_rate:
                raise ValueError("when type(audio) = 'bytes', 'sample_rate' can not be None")
            audio_bytes = audio
            source_sample_rate = sample_rate
            if sample_rate != self.sample_rate:
                audio = AudioSegment(data=audio_bytes, sample_width=self.sample_width, frame_rate=sample_rate, channels=self.channels)
                audio = audio.set_frame_rate(self.sample_rate)
                audio_bytes = audio.raw_data
        else:
            raise TypeError("'audio' can only be AudioSegment or bytes")

        frame_width = int(self.sample_rate * (self.frame_duration_ms / 1000.0) * 2)
        if len(audio_bytes) % frame_width != 0:
            silence_duration = frame_width - len(audio_bytes) % frame_width
            audio_bytes += b'\x00' * silence_duration

        offset = 0
        frames = []
        while offset + frame_width <= len(audio_bytes):
            frames.append(audio_bytes[offset:offset + frame_width])
            offset += frame_width
        return frames, source_sample_rate

    def write_wav(self, f_name_wav, audio_data, sample_rate=None):
        if isinstance(audio_data, AudioSegment):
            self.write_wav_from_audiosegment(f_name_wav, audio_data, sample_rate)
        elif isinstance(audio_data, bytes):
            if not sample_rate:
                raise ValueError("when type(audio_data) = 'bytes', 'sample_rate' can not be None")
            self.write_wav_from_bytes(f_name_wav, audio_data, sample_rate)
        else:
            raise TypeError("'audio_data' is of an unsupported type. Supported:\n" + \
                            "\t- pydub.AudioSegment with audio\n" + \
                            "\t- byte string with audio data (without wav header)")

    def write_wav_from_audiosegment(self, f_name_wav, audio, desired_sample_rate=None):
        if desired_sample_rate:
            audio = audio.set_frame_rate(desired_sample_rate)
        audio.export(f_name_wav, format='wav')

    def write_wav_from_bytes(self, f_name_wav, audio_bytes, sample_rate, desired_sample_rate=None):
        audio = AudioSegment(data=audio_bytes, sample_width=self.sample_width, frame_rate=sample_rate, channels=self.channels)
        if desired_sample_rate and desired_sample_rate != sample_rate:
            audio = audio.set_frame_rate(desired_sample_rate)

        audio.export(f_name_wav, format='wav')
