from enum import Enum
import threading
import time
import speech_recognition as sr
from speech_recognition.exceptions import UnknownValueError
from PySide6.QtCore import QObject, Signal, Slot, QThread
from PySide6.QtWidgets import QApplication
import sys
from threading import Event
import pyttsx3
from voice_interface import state
from voice_interface import voice_utils as utils

class Voice(QThread):
  text_signal = Signal(str)

  def __init__(self):
    super().__init__()
    self.stop_recognizing = Event()
    self.stop_excercise_set = Event()
    self.sayer_lock = threading.Lock()
    self.last_tts_thread = None
    self.state = state.State.START
    self.active = True

  def getNextState(self, command=None):

    if command == state.FINISH_EXCERCISE_CMD:
      self.stop_excercise_set.set()
      return state.State.CHOOSE_EXCERCISE

    if command == state.FINISH_TRAINING_CMD:
      self.stop_excercise_set.set()
      return state.State.CHOOSE_COMMAND

    return state.State(int(self.state) + 1)

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

  def start_set(self, lift_time, hold_time, lower_time, repeats, break_time, set_count):
    self.stop_excercise_set.clear()

    self.say(f"Ćwiczenie składa się z {set_count} serii. Przygotuj się")
    self.last_tts_thread.join()

    def _do():
      for set in range(set_count):
        print(f"Set: {set + 1} / {set_count}")

        for i in range(3, 0, -1):
          self.say(str(i))
          self.last_tts_thread.join()

        self.say("Start")
        for rep in range(repeats):
          self.say("Podnieś")
          self.last_tts_thread.join()

          if self.stop_excercise_set.is_set():
            break

          time.sleep(lift_time)
          self.say("Trzymaj")
          self.last_tts_thread.join()

          if self.stop_excercise_set.is_set():
            break

          time.sleep(hold_time)
          self.say("Opuść")
          self.last_tts_thread.join()

          if self.stop_excercise_set.is_set():
            break

          time.sleep(lower_time)
          print(f"Rep: {rep + 1} / {repeats}")

          if self.stop_excercise_set.is_set():
            break

        if set + 1 == set_count:
          break

        if self.stop_excercise_set.is_set():
          break

        self.say(f"Seria {set + 1} zakończona. Przerwa {break_time} sekund")
        self.last_tts_thread.join()

        if self.stop_excercise_set.is_set():
          break

        time.sleep(break_time // 2)
        self.say(f"Przygotuj się, za {break_time//2} sekund zaczynamy")

        if self.stop_excercise_set.is_set():
          break

        self.last_tts_thread.join()
        time.sleep(break_time // 2)
      self.say("Trening zakończono")
      self.last_tts_thread.join()

    th = threading.Thread(
      target=_do,
      daemon=True
    )
    th.start()

  def run(self):
    recognizer = sr.Recognizer()
    with sr.Microphone() as voice_source:
      recognizer.adjust_for_ambient_noise(voice_source, duration=2)

      while not self.stop_recognizing.is_set():
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
            self.state = self.getNextState()
          continue

        if not self.active:
          continue

        possible_commands = state.state_transitions.get(self.state)
        command = utils.string_similarity(text, possible_commands)
        if command is not None:
          self.text_signal.emit(command)
          self.state = self.getNextState(command)
        else:
          self.text_signal.emit(state.UNRECOGNIZED_CMD)