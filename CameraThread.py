from datetime import datetime
import time
from enum import IntEnum
import copy
import cv2
import numpy as np
import mediapipe as mp
from PySide6.QtCore import QThread, QObject
from PySide6.QtCore import Signal
from mediapipe.python.solutions.pose import PoseLandmark
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import frame_data
import queue

DATAFRAME_LANDMARKS = [
    PoseLandmark.LEFT_HEEL,
    PoseLandmark.RIGHT_HEEL,
    PoseLandmark.LEFT_KNEE,
    PoseLandmark.RIGHT_KNEE,
    PoseLandmark.LEFT_HIP,
    PoseLandmark.RIGHT_HIP,
    PoseLandmark.LEFT_SHOULDER,
    PoseLandmark.RIGHT_SHOULDER,
    PoseLandmark.LEFT_ELBOW,
    PoseLandmark.RIGHT_ELBOW,
    PoseLandmark.LEFT_WRIST,
    PoseLandmark.RIGHT_WRIST,
    PoseLandmark.LEFT_EYE,
    PoseLandmark.RIGHT_EYE,
    PoseLandmark.NOSE,
]
class DFL(IntEnum):
    LEFT_HEEL = 0
    RIGHT_HEEL = 1
    LEFT_KNEE = 2
    RIGHT_KNEE = 3
    LEFT_HIP = 4
    RIGHT_HIP = 5
    LEFT_SHOULDER = 6
    RIGHT_SHOULDER = 7
    LEFT_ELBOW = 8
    RIGHT_ELBOW = 9
    LEFT_WRIST = 10
    RIGHT_WRIST = 11
    LEFT_EYE = 12
    RIGHT_EYE = 13
    NOSE = 14


class VideoProcessor(QObject):
    rep_finished_signal = Signal(int)
    set_finished_signal = Signal(int)
    def __init__(self,cam_front,cam_side):
        super().__init__()
        self.running = False
        cap_f = cv2.VideoCapture(cam_front)
        cap_s = cv2.VideoCapture(cam_side)
        self.w_f = int(cap_f.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.h_f = int(cap_f.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.w_s = int(cap_s.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.h_s = int(cap_s.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.cam_front = cam_front
        self.cam_side = cam_side
        fps_f = cap_f.get(cv2.CAP_PROP_FPS)
        fps_s = cap_s.get(cv2.CAP_PROP_FPS)
        cap_f.release()
        cap_s.release()
        if fps_f <= 0: fps_f = 30.0
        if fps_s <= 0: fps_s = 30.0

        self.recorder_fps = min(fps_f, fps_s)

        self.synchronizer = None
        self.queue_synchronized= None
        self.rep_counter = None
        self.writer_f = None
        self.writer_s = None
        self.front_cam = None
        self.side_cam = None

        self.fname_f = None
        self.fname_s = None

        self.finished_frames = None

    def start(self,exercise):
        cam_queue_front = queue.Queue()
        cam_queue_side = queue.Queue()
        self.queue_synchronized = queue.Queue()
        dir = "camera_recordings/"
        prefix = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_")
        if exercise == 0:
            prefix = prefix + "lateral_raise"
        elif exercise == 1:
            prefix = prefix + "dumbbell_curl"
        else:
            prefix = prefix + "barbell_row"

        filename_f = prefix + "_front.mp4"
        filename_s = prefix + "_side.mp4"
        self.fname_f = filename_f
        self.fname_s = filename_s
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer_f = cv2.VideoWriter(dir + filename_f, fourcc, self.recorder_fps, (self.w_f, self.h_f))
        self.writer_s = cv2.VideoWriter(dir + filename_s, fourcc, self.recorder_fps, (self.w_s, self.h_s))

        self.synchronizer = VideoSynchronizerAndWriter(cam_queue_front, cam_queue_side, self.queue_synchronized,self.writer_f,self.writer_s)
        self.rep_counter = RepCounterThread(self.queue_synchronized, exercise)
        self.rep_counter.rep_finished_signal.connect(self.rep_finished_signal.emit)
        self.rep_counter.set_finished_signal.connect(self.set_finished_signal.emit)
        self.front_cam = CameraReader(self.cam_front, cam_queue_front)
        self.side_cam = CameraReader(self.cam_side, cam_queue_side)

        self.front_cam.start()
        self.side_cam.start()
        self.synchronizer.start()
        self.rep_counter.start()
        self.running = True

    def get_frames(self):
        return self.finished_frames


    def stop(self):
        if not self.running:
            return
        if self.front_cam:
            self.front_cam.stop()
            self.front_cam.wait()

        if self.side_cam:
            self.side_cam.stop()
            self.side_cam.wait()

        if self.synchronizer:
            self.synchronizer.stop()
            self.synchronizer.wait()

        if self.rep_counter:
            self.rep_counter.stop()
            self.queue_synchronized.put((None,None,None))
            self.rep_counter.wait()

        self.finished_frames = self.rep_counter.sets_arr

        if self.writer_f:
            self.writer_f.release()
        if self.writer_s:
            self.writer_s.release()
        self.running = False

class RepCounterThread(QThread):
    set_finished_signal = Signal(int)
    rep_finished_signal = Signal(int)
    def __init__(self, frame_queue, current_exercise):
        super().__init__()

        # key joint structure:
        # 0-landmark A, 1-landmark B, 2-landmark-C, 3- tolerancy, 4- angle_down, 5-angle_up
        key_joints_lat = [
            [DFL.LEFT_WRIST, DFL.LEFT_SHOULDER, DFL.LEFT_HIP, 30, 5, 90], # left arm rise
            [DFL.RIGHT_WRIST, DFL.RIGHT_SHOULDER, DFL.RIGHT_HIP, 30, 5, 90], # right arm rise
            [DFL.RIGHT_WRIST, DFL.RIGHT_SHOULDER, DFL.LEFT_SHOULDER, 30, 90, 180], # move must be lateral
            [DFL.LEFT_WRIST, DFL.LEFT_SHOULDER, DFL.RIGHT_SHOULDER, 30, 90, 180]
        ]
        # distance to grow when moving up 0- landmark a 1- landmark b 3- up/down reverse
        move_landmarks_lat = [
            [DFL.LEFT_WRIST, DFL.LEFT_HIP, True],
            [DFL.RIGHT_WRIST, DFL.RIGHT_HIP, True]
        ]
        # which joints must be visible to count exercise 0- joint 1 - min visibility front 2 - min visibility side
        visibility_condition_lat = [
            [DFL.LEFT_WRIST, 0.66, 0],
            [DFL.RIGHT_WRIST, 0.66, 0],
            [DFL.RIGHT_SHOULDER, 0.66, 0],
            [DFL.LEFT_SHOULDER, 0.66, 0],
            [DFL.LEFT_HIP, 0.66, 0],
            [DFL.RIGHT_HIP, 0.66, 0]
        ]

        key_joints_row = [
            [DFL.LEFT_HEEL, DFL.LEFT_HIP, DFL.LEFT_SHOULDER, 50, 130, 130],
            [DFL.RIGHT_HEEL, DFL.RIGHT_HIP, DFL.RIGHT_SHOULDER, 50, 110, 110],
            [DFL.LEFT_WRIST, DFL.LEFT_ELBOW, DFL.LEFT_SHOULDER, 40, 150, 90],
            [DFL.RIGHT_WRIST, DFL.RIGHT_ELBOW, DFL.RIGHT_SHOULDER, 40, 150, 90]
        ]
        move_landmarks_row = [
            [DFL.RIGHT_WRIST, DFL.RIGHT_SHOULDER,False],
            [DFL.LEFT_WRIST, DFL.LEFT_SHOULDER,False],
        ]
        visibility_condition_row = [
            [DFL.LEFT_WRIST, 0.66, 0],
            [DFL.RIGHT_WRIST, 0.66, 0],
            [DFL.RIGHT_SHOULDER, 0.66, 0],
            [DFL.LEFT_SHOULDER, 0.66, 0],
            [DFL.LEFT_HEEL, 0.30, 0],
            [DFL.RIGHT_HEEL, 0.30, 0]
        ]

        key_joints_curl = [
            [DFL.LEFT_WRIST, DFL.LEFT_ELBOW, DFL.LEFT_SHOULDER, 40, 150, 60],
            [DFL.RIGHT_WRIST, DFL.RIGHT_ELBOW, DFL.RIGHT_SHOULDER, 40, 150, 60]
        ]
        move_landmarks_curl = [
            [DFL.LEFT_WRIST, DFL.LEFT_SHOULDER,False],
            [DFL.RIGHT_WRIST, DFL.RIGHT_SHOULDER,False],
        ]
        visibility_condition_curl = [
            [DFL.LEFT_WRIST, 0.66, 0],
            [DFL.RIGHT_WRIST, 0.66, 0],
            [DFL.RIGHT_SHOULDER, 0.66, 0],
            [DFL.LEFT_SHOULDER, 0.66, 0],
            [DFL.LEFT_HIP, 0.66, 0],
            [DFL.RIGHT_HIP, 0.66, 0]
        ]

        self.frames_since_prev_rep = 0
        self.top_reached = False
        self.current_frame_data = None
        self.current_exercise = current_exercise # 0 - raises, 1 - curls, 2 - row
        self.frames_since_last_rep = 0
        self.idle_threshold = 100
        self.prev_frame_move_joints_distance = None
        self.current_repetition_number = 0

        self.temp_frames = []
        self.reps_arr = []
        self.sets_arr = []
        self.move_joints_distance_history = []

        self.queue = frame_queue

        self.movement_threshold = 4
        self.running = False

        if current_exercise == 0:
            self.key_joints = key_joints_lat
            self.move_landmarks = move_landmarks_lat
            self.visibility_condition = visibility_condition_lat
        elif current_exercise == 1:
            self.key_joints = key_joints_row
            self.move_landmarks = move_landmarks_row
            self.visibility_condition = visibility_condition_row
        else:
            self.key_joints = key_joints_curl
            self.move_landmarks = move_landmarks_curl
            self.visibility_condition = visibility_condition_curl

    def run(self):
        self.running = True
        while self.running:
            (frame, v_front, v_side) = self.queue.get()
            if frame is None:
                break
            self.current_frame_data = frame
            self.run_exercise_logic(frame,self.key_joints,self.move_landmarks,v_front,v_side,self.visibility_condition)

    def stop(self):
        self.running = False

    def calc_angle(self, a, b, c):
        ba = a - b
        bc = c - b
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        if norm_ba == 0 or norm_bc == 0: return 0
        cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
        return np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))

    def run_exercise_logic(self,frame,key_joints, move_landmarks,v_front,v_side,visibility_condition):
        starting_check, top_check = [], []
        invisible_flag = False
        moving_any_up, moving_any_down = False, False
        fk = frame.keypoints
        for joint in key_joints:
            try:
                a, b, c = fk[joint[0]], fk[joint[1]], fk[joint[2]]
                angle = self.calc_angle(a, b, c)
                tol = joint[3]
                starting_check.append(abs(angle - joint[4]) < tol)
                top_check.append(abs(angle - joint[5]) < tol)
            except:
                continue
        for jv in visibility_condition:
            joint = jv[0]
            v_f = jv[1]
            v_s = jv[2]
            if v_front[joint.value] < v_f or v_side[joint.value] < v_s:
                invisible_flag = True

        move_distances = [] # replace with np.array?
        for move_landmark in move_landmarks:
            dist = np.linalg.norm(
                frame.keypoints[move_landmark[0]] -
                frame.keypoints[move_landmark[1]]
            )
            move_distances.append(dist)
        diffs = []
        if self.prev_frame_move_joints_distance:  # last frame is actually 4 frames behind current
            for i in range(len(move_distances)):
                diff = self.prev_frame_move_joints_distance[i] - move_distances[i]
                diffs.append(diff)
            if all(df > self.movement_threshold for df in diffs):
                moving_any_up = True
            elif all(df < -self.movement_threshold for df in diffs):
                moving_any_down = True
            if move_landmarks[0][2]: # reverse
                if moving_any_up:
                    moving_any_up = False
                    moving_any_down = True
                elif moving_any_down:
                    moving_any_down = False
                    moving_any_up = True

        self.move_joints_distance_history.insert(0, move_distances)
        if len(self.move_joints_distance_history) >= 4:
            self.prev_frame_move_joints_distance = self.move_joints_distance_history.pop()

        is_starting = all(starting_check) if starting_check and not invisible_flag else False
        is_top = all(top_check) if top_check and not invisible_flag else False

        if is_starting:
            self.current_frame_data.phase = frame_data.PhaseEnum.START
            if self.top_reached:
                if not moving_any_down:
                    self.handle_repetition_complete()
        elif is_top:
            self.current_frame_data.phase = frame_data.PhaseEnum.PAUSE
            self.top_reached = True
        if moving_any_up:
            # print("up up up")
            self.current_frame_data.phase = frame_data.PhaseEnum.LIFT
        elif moving_any_down:
            # print("down down down")
            self.current_frame_data.phase = frame_data.PhaseEnum.LOWER
        elif self.top_reached:
            self.current_frame_data.phase = frame_data.PhaseEnum.PAUSE
            # print("stop")
        else:
            self.current_frame_data.phase = frame_data.PhaseEnum.START
            #print("start")

        self.frames_since_last_rep += 1
        if self.frames_since_last_rep >= self.idle_threshold and self.reps_arr:
            self.finish_set()
        self.temp_frames.append(copy.copy(frame))
        if self.current_frame_data.phase == frame_data.PhaseEnum.START: # maximum of 4 starts
            self.temp_frames = self.temp_frames[-5:]


    def handle_repetition_complete(self):
        #print("repetition complete",self.current_repetition_number)
        self.current_repetition_number += 1
        self.clean_repetition(self.temp_frames)
        self.reps_arr.append(self.temp_frames)
        self.frames_since_last_rep = 0
        self.temp_frames = []
        self.top_reached = False
        self.rep_finished_signal.emit(self.current_repetition_number)

    def finish_set(self):
        if self.reps_arr:
            self.sets_arr.append(list(self.reps_arr))
            set_n = len(self.sets_arr)
            self.reps_arr = []
            self.current_frame_data.set_number += 1
            self.current_frame_data.repetition_number = 0
            self.frames_since_last_rep = 0
            self.set_finished_signal.emit(set_n)
            self.current_frame_data.set_number = 0

    def clean_repetition(self, frames_list):
        self.remove_rep_outliers(frames_list)
        pause_indices = [i for i, f in enumerate(frames_list) if f.phase == frame_data.PhaseEnum.PAUSE]
        if not pause_indices: return frames_list
        first_p, last_p = pause_indices[0], pause_indices[-1]
        for i, frame in enumerate(frames_list):
            if i < first_p and frame.phase != frame_data.PhaseEnum.START:
                frame.phase = frame_data.PhaseEnum.LIFT
            elif i > last_p and frame.phase != frame_data.PhaseEnum.START:
                frame.phase = frame_data.PhaseEnum.LOWER
            elif first_p <= i <= last_p:
                frame.phase = frame_data.PhaseEnum.PAUSE
        return frames_list

    def remove_rep_outliers(self, frames_list):
        for i in range(1, len(frames_list) - 1):
            f_prev = frames_list[i - 1]
            f_curr = frames_list[i]
            f_next = frames_list[i + 1]
            if f_curr != f_prev and f_prev == f_next:
                frames_list[i] = f_prev

class VideoSynchronizerAndWriter(QThread):
    def __init__(self, queue_front, queue_side,output_queue, writer_front, writer_side):
        super().__init__()
        self.output_queue = output_queue
        self.writer_front = writer_front
        self.writer_side = writer_side
        self.queue_front = queue_front
        self.queue_side = queue_side
        self.output_queue = output_queue
        self.running = False

    def run(self):
        self.running = True
        frame_counter = 0
        while self.running:
            if self.queue_front.empty() or self.queue_side.empty():
                time.sleep(0.01)
                continue
            #get oldest frames
            kp_f, ts_f, frame_f = self.queue_front.queue[0]
            kp_s, ts_s, frame_s = self.queue_side.queue[0]
            #if timestamps close process as a pair
            if abs(ts_f - ts_s) <= 35:
                frame_counter += 1
                #remove frames from queue
                self.queue_front.get()
                self.queue_side.get()
                #display
                # cv2.imshow('frame2', frame_f)
                # cv2.imshow('frame', frame_s)
                # cv2.waitKey(1)
                #write to video
                self.writer_front.write(frame_f)
                self.writer_side.write(frame_s)
                # output data for processing
                if kp_f is not None and kp_s is not None:
                    kp_output = self.combine_views(kp_f, kp_s)
                    current_frame_data = frame_data.FrameData(
                        frame_index=frame_counter, set_number=0, repetition_number=0,
                        keypoints=kp_output,
                        keypoints_side = kp_s,
                        phase = frame_data.PhaseEnum.START,
                        tempo = frame_data.TempoEnum.OK,
                        percent_match = np.float32(0), key_position_flag = np.bool_(0),
                        joints_moving = np.zeros(15,dtype=np.bool_),
                        joints_wrong_angles=np.zeros(15, dtype=np.bool_)
                    )
                    v_front = self.get_visibility(kp_f)
                    v_side = self.get_visibility(kp_s)
                    self.output_queue.put((current_frame_data,v_front,v_side))
            #remove older frame
            elif ts_f < ts_s:
                self.queue_front.get()
            else:
                self.queue_side.get()
    def stop(self):
        self.running = False
        cv2.destroyAllWindows()

    def combine_views(self,kp_f,kp_s):
        height_f = kp_f[14][1] - kp_f[0][1] # y delta from nose to heel
        height_s = kp_s[14][1] - kp_s[0][1]
        if height_s == 0:
            correction = 1
        else:
            correction = height_f / height_s
        kp = np.array([
            [kp_f[i,0], kp_f[i,1],kp_s[i,0]*correction]
            for i in range(14)
        ], dtype=np.float32)
        return kp

    def get_visibility(self,kp):
        return np.array([k[2] for k in kp])


class CameraReader(QThread): # process each frame and put to queue
    def __init__(self, cam, cam_queue):
        super().__init__()
        self.cap = None
        self.cap_w = None
        self.cap_h = None
        self.detector = None
        self.keypoints_front = None
        self.keypoints_side = None
        self.init_camera(cam)
        self.queue = cam_queue
        self.init_mediapipe()
        self.running = False

    def init_camera(self,cam = 0):
        self.cap = cv2.VideoCapture(cam)
        self.cap_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cap_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def init_mediapipe(self):
        model_path = 'pose_landmarker_lite.task'
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False,
            running_mode=vision.RunningMode.VIDEO,
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def run(self):
        ctr = 0
        self.running = True
        kp = None
        while self.running:
            ret, frame = self.cap.read()
            ts = int(time.time() * 1000)
            if not ret:
                break
            ctr += 1
            if ctr >= 0:
                ctr = 0
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
                result = self.detector.detect_for_video(img, ts)
                if result.pose_landmarks:
                    avg_visibility = 0
                    rpl = result.pose_landmarks[0]
                    kp = np.array([
                        [rpl[i.value].x * self.cap_w, rpl[i.value].y * self.cap_h,rpl[i.value].visibility]
                        for i in DATAFRAME_LANDMARKS
                    ], dtype=np.float32)
            self.queue.put((kp, ts, frame))
        self.cap.release()

    def stop(self):
        self.running = False

if __name__ == '__main__':
    vp = VideoProcessor(0,"http://192.168.246.46:8080/video")
    vp.start(0)
    ctr = 0
    while True:
        ctr += 1

        print(ctr)
        if ctr >= 100:
            vp.stop()
            break
        time.sleep(0.01)
