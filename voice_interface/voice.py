from enum import Enum
import threading
import time
from time import sleep

import speech_recognition as sr
from speech_recognition.exceptions import UnknownValueError
from PySide6.QtCore import Signal, QThread
from threading import Event
import pyttsx3
from voice_interface import state
from voice_interface import voice_utils as utils

class Voice(QThread):
  text_signal = Signal(str)

  def __init__(self):
    super().__init__()
    self.stop_recognizing = False
    self.stop_exercise_set = Event()
    self.sayer_lock = threading.Lock()
    self.last_tts_thread = None
    self.state = state.State.START
    self.active = True
    self.mic = sr.Microphone()
    self.voice_source = self.mic.__enter__()

  def set_state(self, state):
    self.state = state

  def say(self, text):
    def _say(text):
      with self.sayer_lock:
        pyttsx3.speak(text)
    tts_thread = threading.Thread(
      target=_say,
      args=(text,),
      daemon=True
    )
    tts_thread.start()
    self.last_tts_thread = tts_thread

  def stop(self):
    self.stop_recognizing = True
    self.mic.__exit__(None, None, None)

  def run(self):
    recognizer = sr.Recognizer()
    voice_source = self.voice_source
    recognizer.adjust_for_ambient_noise(voice_source, duration=2)

    while not self.stop_recognizing:
      try:
       audio = recognizer.listen(voice_source, timeout=3)
       text = recognizer.recognize_google(audio, language="pl-PL")
      except UnknownValueError:
        continue
      except sr.WaitTimeoutError:
        print("Timeout. Deactivating")
        self.active = False
        continue

      if utils.string_similarity(text, [state.OK_TRAINER_CMD]) is not None:
        self.active = True
        self.text_signal.emit(state.OK_TRAINER_CMD)
        if self.state == state.State.START:
          self.state = state.OK_TRAINER_CMD
        continue

      if not self.active:
        continue

      possible_commands = state.state_transitions.get(self.state)
      command = utils.string_similarity(text, possible_commands)
      if command is not None:
        self.text_signal.emit(command)
      else:
        self.text_signal.emit(state.UNRECOGNIZED_CMD)