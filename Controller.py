import enum
import sys
from PySide6.QtWidgets import QApplication, QStackedWidget
from PySide6.QtCore import Qt

from components import VideoRenderer, ExerciseValidator, CameraThread, GUIScreens as gui
from voice_interface import voice
from voice_interface import state
from PySide6.QtCore import Slot

FRONTAL_CAMERA = 0
LATERAL_CAMERA = "http://192.168.138.221:8080/video"

class State(enum.IntEnum):
  START = 0
  CHOOSE_COMMAND = enum.auto()
  CHOOSE_EXERCISE = enum.auto()
  TRAINING_IN_PROGRESS = enum.auto()
  FINISH = enum.auto()

class App(QStackedWidget):
    def __init__(self):
        super().__init__()
        # components
        self.voice_interface = voice.Voice()  # receives and validates voice commands sending appropriate signals to appropriate component
        self.video_processor = CameraThread.VideoProcessor(FRONTAL_CAMERA, LATERAL_CAMERA)  # processes camera feed from 2 cameras, saves the video and produces DataFrame objects
        self.graphical_renderer = VideoRenderer.VideoRenderer()  # reads video from file, annotates each frame with feedback based on completed DataFrame objects, saves modified frames as video
        self.exercise_validator = ExerciseValidator.ExerciseValidator()  # completes FrameData objects

        # GUI SCREENS
        self.menu = gui.MainMenu()
        self.timer_screen = gui.CircleTimer(duration_seconds=100) # rest duration
        self.video_list = gui.VideoList()
        self.player = gui.VideoPlayer()
        self.gif_screen = gui.GifWindow()
        self.idle = gui.IdleScreen()
        self.selector = gui.ExerciseSelector()
        self.loading_screen = gui.LoadingScreen()

        self.addWidget(self.menu)           # index 0
        self.addWidget(self.timer_screen)   # index 1
        self.addWidget(self.video_list)     # index 2
        self.addWidget(self.player)         # index 3
        self.addWidget(self.gif_screen)     # index 4
        self.addWidget(self.idle)           # index 5
        self.addWidget(self.selector)       # index 6
        self.addWidget(self.loading_screen) # index 7

        # shared data
        self.recordings_filenames = None  # filenames recordings of each exercise before video processing
        self.video_data = None  # list of frame_data objects, the objects are created by video_processor and supplied with data by exercise_validator
        # start
        self.setCurrentIndex(0)

        self.menu.launch_trainer.connect(self.goto_idle)
        self.menu.exit_app.connect(self.turn_off)
        self.menu.open_docs.connect(lambda: print("docs TODO"))
        self.menu.open_saved.connect(self.goto_list)
        self.idle.choose_exercise.connect(self.goto_selector)
        self.idle.finish.connect(self.goto_menu)
        self.selector.lateral.connect(self.start_lateral)
        self.selector.curl.connect(self.start_curl)
        self.selector.row.connect(self.start_row)
        self.gif_screen.finish.connect(self.goto_idle)
        self.video_list.list_widget.itemDoubleClicked.connect(self.open_video)
        self.video_list.back.connect(self.goto_menu)
        self.player.back.connect(self.goto_list)
        self.timer_screen.finished.connect(self.start_last_exercise)
        self.graphical_renderer.finished.connect(self.goto_list)
        self.voice_interface.text_signal.connect(self.voice_command_handler)
        self.voice_interface.start()
        self.last_exercise = None
        self.video_processor.rep_finished_signal.connect(self.counter_rep)
        self.video_processor.set_finished_signal.connect(self.counter_set)

        self.exercise_waiting = False
        self.filename_front = None
        self.filename_side = None

        self.frames = None

    def turn_off(self):
        self.voice_interface.stop()
        self.video_processor.stop()
        QApplication.quit()
    def goto_menu(self):
        if self.video_processor.running:
            self.video_processor.stop()
            self.process_exercise()
        self.setCurrentIndex(0)
        self.voice_interface.set_state(State.CHOOSE_COMMAND)
    def goto_idle(self):
        if self.video_processor.running:
            self.video_processor.stop()
            self.process_exercise()
        self.setCurrentIndex(5)
        self.voice_interface.set_state(State.CHOOSE_COMMAND)
    def goto_selector(self):
        if self.video_processor.running:
            self.video_processor.stop()
            self.process_exercise()
        self.setCurrentIndex(6)
        self.voice_interface.set_state(State.CHOOSE_EXERCISE)
    def goto_gif(self):
        self.setCurrentIndex(4)
    def goto_timer(self):
        self.setCurrentIndex(1)
        self.timer_screen.start()
    def goto_loading(self):
        self.setCurrentIndex(7)
    def goto_list(self):
        self.setCurrentIndex(2)
    def open_video(self, item):
        filename = item.data(Qt.UserRole)
        self.player.play_file(filename)
        self.setCurrentIndex(3)
    def start_lateral(self):
        self.gif_screen.change_gif(1)
        self.last_exercise = 'lateral'
        self.video_processor.start(0)
        self.goto_gif()
        self.exercise_waiting = True
    def start_curl(self):
        self.gif_screen.change_gif(2)
        self.last_exercise = 'curl'
        self.video_processor.start(2)
        self.goto_gif()
        self.exercise_waiting = True
    def start_row(self):
        self.gif_screen.change_gif(3)
        self.last_exercise = 'row'
        self.video_processor.start(1)
        self.goto_gif()
        self.exercise_waiting = True
    def start_last_exercise(self):
        self.voice_interface.set_state(State.TRAINING_IN_PROGRESS)
        if self.last_exercise == 'lateral':
            self.start_lateral()
        elif self.last_exercise == 'curl':
            self.start_curl()
        elif self.last_exercise == 'row':
            self.start_row()

    def process_exercise(self):
        if self.exercise_waiting:
            self.goto_loading()
            self.video_data = self.video_processor.get_frames()
            if len(self.video_data) == 0:
                self.exercise_waiting = False
                return
            if self.last_exercise == 'curl':
                for rep_list in self.video_data:
                    even = 0
                    for rep in rep_list:
                        even = even + 1
                        if even % 2 == 0:
                            self.exercise_validator.validate(rep, 'curl right')
                        else:
                            self.exercise_validator.validate(rep, 'curl left')

            else:
                for rep_list in self.video_data:
                    for rep in rep_list:
                        self.exercise_validator.validate(rep,self.last_exercise)
            self.filename_front = self.video_processor.fname_f
            self.filename_side = self.video_processor.fname_s
            self.graphical_renderer.process_file(self.filename_front, self.video_data,False)
            self.graphical_renderer.process_file(self.filename_side, self.video_data,True)
            self.goto_loading()
        self.exercise_waiting = False



    @Slot(str)
    def voice_command_handler(self,command):
        self.voice_interface.say(command)
        #print(command)
        if command == state.FINISH_TRAINING_CMD:
            self.voice_interface.set_state(State.FINISH)
            self.goto_menu()
        if command == state.CHOOSE_EXERCISE_CMD:
            self.voice_interface.set_state(State.CHOOSE_EXERCISE)
            self.goto_selector()
        if command == state.CURL_CMD:
            self.voice_interface.set_state(State.TRAINING_IN_PROGRESS)
            self.start_curl()
        if command == state.LATERAL_CMD:
            self.voice_interface.set_state(State.TRAINING_IN_PROGRESS)
            self.start_lateral()
        if command == state.ROW_CMD:
            self.voice_interface.set_state(State.TRAINING_IN_PROGRESS)
            self.start_row()
        if command == state.FINISH_EXERCISE_CMD:
            self.voice_interface.set_state(State.CHOOSE_EXERCISE)
            self.goto_selector()

    @Slot(int)
    def counter_rep(self, rep):
        self.voice_interface.say(str(rep))

    @Slot(int)
    def counter_set(self, rep):
        self.voice_interface.say("seria: "+str(rep))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
