import cv2
from PySide6.QtCore import QThread, Signal

import frame_data as fd

class VideoRenderer(QThread):
    finished = Signal()
    def __init__(self):
        super().__init__()
        self.last_position_match = 0
        self.watch_OK = cv2.imread("watch_ok.png", cv2.IMREAD_UNCHANGED)
        self.watch_TOO_SLOW = cv2.imread("watch_slow.png", cv2.IMREAD_UNCHANGED)
        self.watch_TOO_FAST = cv2.imread("watch_fast.png", cv2.IMREAD_UNCHANGED)
        self.filenames = None
        self.datas = None

    # relic
    def run(self):
        self.process_files(self.filenames,self.datas)

    def set_input(self,filenames,datas):
        self.filenames = filenames
        self.datas = datas

    def overlay_icon(self, frame, icon, scale=0.25, margin=10):
        if icon is None:
            return frame
        frame_h, frame_w = frame.shape[:2]
        icon_h, icon_w = icon.shape[:2]
        new_w = int(icon_w * scale)
        new_h = int(icon_h * scale)
        if new_w > frame_w - margin:
            new_w = frame_w - margin
        if new_h > frame_h - margin:
            new_h = frame_h - margin
        icon_resized = cv2.resize(icon, (new_w, new_h), interpolation=cv2.INTER_AREA)
        x = margin
        y = frame_h - new_h - margin
        roi = frame[y:y + new_h, x:x + new_w]

        if icon_resized.shape[2] == 4:  # alpha channel
            icon_rgb = icon_resized[:, :, :3]
            alpha = icon_resized[:, :, 3] / 255.0
            alpha_inv = 1.0 - alpha
            for c in range(3):
                roi[:, :, c] = (alpha * icon_rgb[:, :, c] + alpha_inv * roi[:, :, c])
        else:
            roi[:] = icon_resized

        frame[y:y + new_h, x:x + new_w] = roi
        return frame

    #relic
    def process_files(self,filenames,video_datas):
        for filename,video_data in zip(filenames,video_datas):
            self.process_file(filename,video_data)
        self.finished.emit()

    def process_file(self, filename,video_data,side_view):
        full_filename = 'camera_recordings/' + filename
        cap = cv2.VideoCapture(full_filename)
        if not cap.isOpened():
            print("ERROR: file not found ", full_filename)
            return
        # writer
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        new_filename = filename.replace('.mp4','_report.mp4')
        new_filename = 'video_reports\\' + new_filename
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(new_filename, fourcc, fps, (width, height))
        frame_index = 0
        frames = (item for sublist1 in video_data for sublist2 in sublist1 for item in sublist2)
        for frame_data in frames:
            frame = None
            while frame_index < frame_data.frame_index:
                ret, frame = cap.read()
                frame_index += 1
            writer_frame = self.process_frame(frame, frame_data,side_view)
            writer.write(writer_frame)

        cap.release()
        writer.release()

    def overlay_text(self, frame, text, scale=1.0, color=(255, 255, 255), thickness=2, margin=10):
        frame_h, frame_w = frame.shape[:2]
        (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
        x = frame_w - text_w - margin
        y = text_h + margin
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_DUPLEX, scale, color, thickness, cv2.LINE_AA)
        return frame

    def process_frame(self,frame,frame_data,side_view):
        text = f"{self.last_position_match:.2f}"
        self.overlay_text(frame, text,scale=3)
        if frame_data.tempo == fd.TempoEnum.OK:
            icon = self.watch_OK
        elif frame_data.tempo == fd.TempoEnum.TOO_FAST:
            icon = self.watch_TOO_SLOW
        else:
            icon = self.watch_TOO_FAST
        frame = self.overlay_icon(frame, icon, scale=2)
        frame = self.draw_keypoints(frame, frame_data,side_view)
        return frame

    def draw_keypoints(self, frame,frame_data,side_view):
        point_radius = 5
        wrong_angle_radius = 12
        thickness = 2
        if side_view:
            keypoints = frame_data.keypoints_side
        else:
            keypoints = frame_data.keypoints
        for i, kp in enumerate(keypoints):
            x = int(kp[0])
            y = int(kp[1])
            if x <= 0 or y <= 0:
                continue
            if frame_data.joints_moving[i]:
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)
            cv2.circle(frame, (x, y), point_radius, color, -1)
            if frame_data.joints_wrong_angles[i]:
                cv2.circle(frame,(x, y),wrong_angle_radius,(0, 0, 255),thickness)
        return frame

# if __name__ == "__main__":
#     data = fd.FrameData(
#         frame_index=0,
#         set_number=0,
#         repetition_number=0,
#         keypoints=None,  # np. np.zeros((20,3), dtype=np.float32)
#         phase=fd.PhaseEnum.START,
#         tempo=fd.TempoEnum.OK,
#         percent_match=0.5,
#         key_position_flag=True,
#         joints_moving=None  # np.zeros((20,), dtype=bool)
#     )
#     datas = []
#     for i in range(1000):
#         datas.append(fd.FrameData(
#         frame_index=0,
#         set_number=0,
#         repetition_number=0,
#         keypoints=None,  # np. np.zeros((20,3), dtype=np.float32)
#         phase=fd.PhaseEnum.START,
#         tempo=fd.TempoEnum.OK,
#         percent_match=0.5,
#         key_position_flag=True,
#         joints_moving=None  # np.zeros((20,), dtype=bool)
#          ))
#     filename = "bok - uginanie ramion.mp4"
#     vr = VideoRenderer()
#     vr.process_file(filename,datas)


