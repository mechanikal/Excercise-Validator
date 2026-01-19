import sys
from PySide6.QtWidgets import QApplication, QStackedWidget
from PySide6.QtCore import Qt, QThread
import GUIScreens as gui
import VideoRenderer
import voice_interface
from voice_interface import voice
from voice_interface import state
from PySide6.QtCore import Slot

class App(QStackedWidget):
    def __init__(self):
        super().__init__()
        # components
        # TODO: connect all components
        self.voice_interface = voice.Voice()  # receives and validates voice commands sending appropriate signals to appropriate component
        self.counter = None  # dictates exercise tempo with voice ques, counts times between sets
        self.video_processor = None  # processes camera feed from 2 cameras, saves the video and produces DataFrame objects
        self.graphical_renderer = VideoRenderer.VideoRenderer()  # reads video from file, annotates each frame with feedback based on completed DataFrame objects, saves modified frames as video
        self.exercise_validator = None  # completes FrameData objects

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
        self.menu.exit_app.connect(lambda: sys.exit(0))
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
        # TODO: connect voice interface and timer
        self.voice_interface.text_signal.connect(self.voice_command_handler)
        self.voice_interface.start()
        self.last_exercise = None

    def goto_menu(self):
        self.setCurrentIndex(0)
    def goto_idle(self):
        self.setCurrentIndex(5)
    def goto_selector(self):
        self.setCurrentIndex(6)
    def goto_gif(self):
        self.setCurrentIndex(4)
    def goto_timer(self):
        self.setCurrentIndex(1)
        self.timer_screen.start()
    def goto_loading(self):
        self.graphical_renderer.set_input(self.recordings_filenames,self.video_data)
        self.graphical_renderer.start()
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
        #self.video_processor.start(1)
        self.goto_gif()
        self.voice_interface.start_set(1, 2, 1, 5, 10, 3)
    def start_curl(self):
        self.gif_screen.change_gif(2)
        self.last_exercise = 'curl'
        #self.video_processor.start(2)
        self.goto_gif()
        self.voice_interface.start_set(1, 2, 1, 5, 10, 3)
    def start_row(self):
        self.gif_screen.change_gif(3)
        self.last_exercise = 'row'
        #self.video_processor.start(3)
        self.goto_gif()
        self.voice_interface.start_set(1, 2, 1, 5, 10, 3)
    def start_last_exercise(self):
        if self.last_exercise == 'lateral':
            self.start_lateral()
        elif self.last_exercise == 'curl':
            self.start_curl()
        elif self.last_exercise == 'row':
            self.start_row()
    @Slot(str)
    def voice_command_handler(self,command):
        self.voice_interface.say(command)
        #print(command)
        if command == state.FINISH_TRAINING_CMD:
            self.goto_menu()
        if command == state.CHOOSE_EXCERCISE_CMD:
            self.goto_selector()
        if command == state.CURL_CMD:
            self.start_curl()
        if command == state.LATERAL_CMD:
            self.start_lateral()
        if command == state.ROW_CMD:
            self.start_row()
        if command == state.FINISH_EXCERCISE_CMD:
            self.goto_selector()
        if command == state.UNRECOGNIZED_CMD:
          pass
            #TODO say unrecognised command


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
