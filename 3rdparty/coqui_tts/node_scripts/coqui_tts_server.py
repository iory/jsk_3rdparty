#!/usr/bin/env python

import contextlib
import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
import threading
import time

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
import rospy
from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer
import uvicorn
from uvicorn import Config as UvicornConfig


# refer https://github.com/encode/uvicorn/issues/742#issuecomment-674411676
class UvicornThreadServer(uvicorn.Server):

    def install_signal_handlers(self):
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()


def generate_app():
    __version__ = '0.0.1'

    SERVICE = {
        "name": "coqui_tts_server",
        "version": __version__,
        "libraries": {
            "coqui_tts_server": __version__
        },
    }

    app = fastapi.FastAPI(
        title="COQUI TTS Server",
        description="text to speech server using coqui",
        version=__version__,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    path = Path(__file__).parent / "../bin/models.json"
    manager = ModelManager(path)
    model_name = 'tts_models/en/ljspeech/tacotron2-DDC_ph'
    model_path, config_path, model_item = manager.download_model(
        model_name)
    vocoder_name = model_item["default_vocoder"]
    vocoder_path, vocoder_config_path, _ = manager.download_model(
        vocoder_name)

    speakers_file_path = None
    language_ids_file_path = None
    encoder_path = None
    encoder_config_path = None
    use_cuda = False
    synthesizer = Synthesizer(
        model_path,
        config_path,
        speakers_file_path,
        language_ids_file_path,
        vocoder_path,
        vocoder_config_path,
        encoder_path,
        encoder_config_path,
        use_cuda,
    )
    synthesizer.tts_model.decoder.max_decoder_steps = 10000

    @app.get("/")
    async def get_root():
        return {
            "service": SERVICE,
            "time": int(datetime.datetime.now().timestamp() * 1000),
        }

    @app.get('/info', tags=['Utility'])
    async def info():
        about = dict(
            version=__version__,
        )
        return about

    @app.post("/tts", response_class=fastapi.responses.FileResponse)
    async def tts(text):
        if len(text) == 0:
            # return empty sound.
            segment = AudioSegment.silent(duration=0)
            with NamedTemporaryFile(delete=False, suffix='.wav') as f:
                segment.export(f.name, format="wav")
            print(f.name)
            return fastapi.responses.FileResponse(
                f.name, media_type="audio/wav",
                filename=f.name)
        if text[-1] not in ['.', '?', '!']:
            text += '.'
        speaker_idx = None
        language_idx = None
        speaker_wav = None
        reference_wav = None
        reference_speaker_idx = None
        wav = synthesizer.tts(
            text,
            speaker_idx,
            language_idx,
            speaker_wav,
            reference_wav=reference_wav,
            reference_speaker_name=reference_speaker_idx,
        )
        with NamedTemporaryFile(delete=False, suffix='.wav') as f:
            synthesizer.save_wav(wav, f.name)
        return fastapi.responses.FileResponse(
            f.name, media_type="audio/wav",
            filename=f.name)

    return app


if __name__ == '__main__':
    rospy.init_node('coqui_tts_server')
    host = rospy.get_param('~host', "127.0.0.1")
    port = rospy.get_param('~port', 50023)
    config = UvicornConfig(
        generate_app(),
        host=host, port=port, log_level="info")
    server = UvicornThreadServer(config=config)
    with server.run_in_thread():
        rospy.spin()
