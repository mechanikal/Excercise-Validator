import enum

class State(enum.IntEnum):
  START = 0
  CHOOSE_COMMAND = enum.auto()
  CHOOSE_EXERCISE = enum.auto()
  TRAINING_IN_PROGRESS = enum.auto()
  FINISH = enum.auto()

OK_TRAINER_CMD = "OK Trener"
FINISH_TRAINING_CMD = "Zakończ trening"
CHOOSE_EXERCISE_CMD = "Wybierz ćwiczenie"
CURL_CMD = "Uginanie ramion z hantlami"
LATERAL_CMD = "Wznosy bokiem"
ROW_CMD = "Wiosłowanie sztangą"
FINISH_TRAINING_CMD = "Zakończ trening"
FINISH_EXERCISE_CMD = "Zakończ ćwiczenie"
UNRECOGNIZED_CMD = "Komenda nierozpoznana"

state_transitions = {
  State.CHOOSE_COMMAND: [FINISH_TRAINING_CMD, CHOOSE_EXERCISE_CMD],
  State.CHOOSE_EXERCISE: [CURL_CMD, ROW_CMD, LATERAL_CMD,FINISH_TRAINING_CMD],
  State.TRAINING_IN_PROGRESS: [FINISH_EXERCISE_CMD, FINISH_TRAINING_CMD],
}