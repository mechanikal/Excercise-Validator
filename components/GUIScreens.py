from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPainter, QPen, QColor, QPixmap, QFont
from PySide6.QtCore import QTimer, QRectF, QUrl
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton

def set_background(widget, color="#076e27"):
    widget.setAutoFillBackground(True)
    palette = widget.palette()
    palette.setColor(widget.backgroundRole(), QColor(color))
    widget.setPalette(palette)

def insert_logo(layout,size):
    image_label = QLabel()
    pixmap = QPixmap("assets/cyber-trener-logo.png")
    pixmap = pixmap.scaledToWidth(size, Qt.SmoothTransformation)
    image_label.setPixmap(pixmap)
    image_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(image_label)

def insert_button(layout,text,signal):
    btn = QPushButton(text)
    btn.setMinimumHeight(80)
    btn.setMaximumHeight(80)
    btn.setMinimumWidth(600)
    btn.setMaximumWidth(600)
    btn.setStyleSheet("""
                            QPushButton {
                                background-color: #faf6f1;
                                color: #076e27;
                                border-radius: 15px;
                                padding: 10px 20px;
                                font-family: "Arial";
                                font-weight: bold;
                                font-size: 30px;
                            }
                            QPushButton:hover {
                                background-color: #fcfcfc;
                            }
                            QPushButton:pressed {
                                background-color: #e8e6e6;
                            }
                        """)
    btn.clicked.connect(signal)
    layout.addWidget(btn, alignment=Qt.AlignCenter)

class MainMenu(QWidget):
    launch_trainer = Signal()
    open_saved = Signal()
    open_docs = Signal()
    exit_app = Signal()
    def __init__(self):
        super().__init__()
        set_background(widget=self)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 30)
        insert_logo(layout=layout, size = 200)
        # add buttons
        labels = ["ROZPOCZNIJ", "RAPORTY", "DOKUMENTACJA", "WYJDŹ"]
        i = 0
        for text in labels:
            if i == 0:
                insert_button(layout=layout, text=text, signal=self.launch_trainer)
            elif i == 1:
                insert_button(layout=layout, text=text, signal=self.open_saved)
            elif i == 2:
                insert_button(layout=layout, text=text, signal=self.open_docs)
            elif i == 3:
                insert_button(layout=layout, text=text, signal=self.exit_app)
            i += 1

        # footer
        footer = QLabel("© 2025 Projekt PSIO: Cyber-Trener. Politechnika Łódzka")
        footer.setStyleSheet("color: #faf6f1; font-size: 12px;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
        self.setLayout(layout)


class CircleTimer(QWidget):
    finished = Signal()
    def __init__(self, duration_seconds=10):
        super().__init__()
        set_background(widget=self)
        self.duration = duration_seconds
        self.time_left = duration_seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        layout = QVBoxLayout(self)
        layout.addStretch(1)
        layout.setContentsMargins(10, 10, 10, 30)
        insert_button(layout,"POMIŃ", self.finished)

    def start(self):
        self.time_left = self.duration
        self.timer.start(1000)
        self.update()

    def tick(self):
        self.time_left -= 1
        self.update()
        if self.time_left <= 0:
            self.timer.stop()
            self.finished.emit()

    def stop(self):
        self.time_left = 5

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        size = 300
        x = (w - size) / 2
        y = (h - size) / 2 - 100
        # circle indicator
        rect = QRectF(x, y + 60, size, size)
        ratio = self.time_left / self.duration
        angle = int(360 * ratio * 16)
        pen_fg = QPen(QColor("#faf6f1"), 20)
        painter.setPen(pen_fg)
        painter.drawArc(rect, 90 * 16, -angle)
        # time
        painter.setPen(QColor("#faf6f1"))
        font = QFont("Arial", 40, QFont.Bold)
        painter.setFont(font)
        text = f"{self.time_left // 60:02d}:{self.time_left % 60:02d}"
        text_rect = painter.boundingRect(rect, Qt.AlignCenter, text)
        painter.drawText(text_rect, Qt.AlignCenter, text)

class VideoList(QWidget):
    back = Signal()
    video_selected = Signal(str)
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 20, 50, 100)
        layout.setSpacing(50)
        set_background(widget=self)
        # video list
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
            font-family: "Arial";
            font-weight: bold;
            font-size: 20px;
            color: #076e27;
            background-color: #faf6f1;
            }
        """)
        insert_logo(layout,200)
        layout.addWidget(self.list_widget)
        insert_button(layout=layout, text="POWRÓT", signal=self.back)
        self.load_videos_from_folder("video_reports")
        self.setLayout(layout)
        # double-click -> sygnał
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

    def load_videos_from_folder(self, folder_path):
        self.list_widget.clear()
        video_extensions = (".mp4", ".avi", ".mov", ".mkv")
        for file_name in os.listdir(folder_path):
            if file_name.lower().endswith(video_extensions):
                item = QListWidgetItem(file_name)
                item.setData(Qt.UserRole, os.path.join(folder_path, file_name))
                self.list_widget.addItem(item)

    def on_item_double_clicked(self, item):
        filename = item.data(Qt.UserRole)
        self.video_selected.emit(filename)

class VideoPlayer(QWidget):
    back = Signal()
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        set_background(self)

        self.video_widget = QVideoWidget()
        self.video_widget.setMaximumSize(2000, 1000)
        self.video_widget.setMinimumSize(800,600)
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        insert_logo(layout,100)
        layout.addWidget(self.video_widget,alignment=Qt.AlignCenter)
        insert_button(layout,"POWRÓT",self.back)
        self.setLayout(layout)

    def play_file(self, filename):
        url = QUrl.fromLocalFile(filename)
        self.player.setSource(url)
        self.player.play()

class GifWindow(QWidget):
    finish = Signal()
    def __init__(self):
        super().__init__()
        set_background(widget=self)
        self.video_path = "assets/curl_gif.gif"
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(0, 20, 20, 20)
        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setFixedSize(600,600)
        self.video_widget.setAutoFillBackground(True)
        layout.addWidget(self.video_widget,alignment=Qt.AlignCenter)
        # Media player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        # Load video
        self.media_player.setSource(QUrl.fromLocalFile(self.video_path))
        self.media_player.setLoops(-1)  # Loop indefinitely
        self.media_player.play()
        insert_button(layout,"ZAKOŃCZ ĆWICZENIE",self.finish)
        self.setLayout(layout)

    def change_gif(self,code):
        if code == 1:
            self.video_path = "assets/lateral_gif.gif"
        elif code == 2:
            self.video_path = "assets/curl_gif.gif"
        elif code == 3:
            self.video_path = "assets/row_gif.gif"
        self.media_player.setSource(QUrl.fromLocalFile(self.video_path))
        self.media_player.setLoops(-1)
        self.media_player.play()

class IdleScreen(QWidget):
    finish = Signal()
    choose_exercise = Signal()
    def __init__(self):
        super().__init__()
        set_background(widget=self)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 30)  # left, top, right, bottom
        insert_logo(layout,400)
        # add buttons
        labels = ["WYBIERZ ĆWICZENIE", "ZAKOŃCZ TRENING"]
        i = 0
        for text in labels:
            if i == 0:
                insert_button(layout, text, self.choose_exercise)
            elif i == 1:
                insert_button(layout, text, self.finish)
            i += 1
        layout.addStretch(1)
        self.setLayout(layout)

class LoadingScreen(QWidget):
    def __init__(self):
        super().__init__()
        set_background(widget=self)
        layout = QVBoxLayout(self)
        # header
        self.header_label = QLabel("ŁADOWANIE...")
        self.header_label.setAlignment(Qt.AlignCenter)
        header_font = QFont("Arial", 40, QFont.Bold)
        self.header_label.setFont(header_font)
        self.header_label.setStyleSheet("color: #faf6f1;")
        self.layout().addWidget(self.header_label)
        insert_logo(layout,600)
        self.setLayout(layout)

class ExerciseSelector(QWidget):
    lateral = Signal()
    row = Signal()
    curl = Signal()
    def __init__(self):
        super().__init__()
        set_background(widget=self)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 30)  # left, top, right, bottom
        insert_logo(layout,400)
        # add buttons
        labels = ["WZNOSY W BOK", "UGINANIE RAMION PODCHWYTEM","WIOSŁOWANIE SZTANGĄ"]
        i = 0
        for text in labels:
            if i == 0:
                insert_button(layout, text, self.lateral)
            elif i == 1:
                insert_button(layout, text, self.curl)
            elif i == 2:
                insert_button(layout, text, self.row)
            i += 1
        self.setLayout(layout)
