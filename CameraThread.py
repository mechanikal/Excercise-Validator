import dataclasses
import json
import cv2
import threading
import numpy as np
import mediapipe as mp
import os
import copy
import time
import concurrent.futures
import queue  # <--- Potrzebne do buforowania zapisu

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

os.environ['LD_LIBRARY_PATH'] = '/usr/lib/wsl/lib:' + os.environ.get('LD_LIBRARY_PATH', '')

import frame_data 

LANDMARK_NAMES = {i: name for i, name in enumerate([
    "Nose", "L. eye (inner)", "L. eye", "L. eye (outer)", "R. eye (inner)", "R. eye", "R. eye (outer)",
    "L. ear", "R. ear", "Mouth (left)", "Mouth (right)", "L. shoulder", "R. shoulder", "L. elbow", 
    "R. elbow", "L. wrist", "R. wrist", "L. pinky", "R. pinky", "L. index", "R. index", "L. thumb", 
    "R. thumb", "L. hip", "R. hip", "L. knee", "R. knee", "L. ankle", "R. ankle", "L. heel", "R. heel", 
    "L. foot index", "R. foot index"
])}

JOINT_DEFINITIONS = {
    "L_elbow": ["L. shoulder", "L. elbow", "L. wrist"],
    "R_elbow": ["R. shoulder", "R. elbow", "R. wrist"],
    "L_knee": ["L. hip", "L. knee", "L. ankle"],
    "R_knee": ["R. hip", "R. knee", "R. ankle"],
    "L_shoulder": ["L. elbow", "L. shoulder", "L. hip"],
    "R_shoulder": ["R. elbow", "R. shoulder", "R. hip"],
    "L_hip": ["L. shoulder", "L. hip", "L. knee"],
    "R_hip": ["R. shoulder", "R. hip", "R. knee"],
}

def calc_angle(a, b, c):
    ba = a - b
    bc = c - b
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba == 0 or norm_bc == 0: return 0
    cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    return np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.bool_, bool)): return bool(obj)
        if hasattr(obj, 'name') and hasattr(obj, 'value'): return obj.name
        if dataclasses.is_dataclass(obj): return dataclasses.asdict(obj)
        try:
            return {k: v for k, v in vars(obj).items() if not k.startswith('_')}
        except TypeError:
            return {s: getattr(obj, s) for s in dir(obj) if not s.startswith('_') and not callable(getattr(obj, s))}

class CameraThread:
    def __init__(self, source_front="v_test.mp4", source_side="v_test_bok.mp4", 
                 json_start_pos="wzniosy_3d_start.json", json_top_pos="wzniosy_3d_top.json", side_offset=0, logging=False):
        
        self.logging = logging
        self.set_finished_event = threading.Event()
        
        self.cap_f = cv2.VideoCapture(source_front)
        self.cap_s = cv2.VideoCapture(source_side)
        
        self.w_f = int(self.cap_f.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.h_f = int(self.cap_f.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.w_s = int(self.cap_s.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.h_s = int(self.cap_s.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # --- KONFIGURACJA NAGRYWANIA ---
        fps_f = self.cap_f.get(cv2.CAP_PROP_FPS)
        fps_s = self.cap_s.get(cv2.CAP_PROP_FPS)
        if fps_f <= 0: fps_f = 30.0
        if fps_s <= 0: fps_s = 30.0

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        print(f"[INFO] Inicjalizacja nagrywania: Front {self.w_f}x{self.h_f} @ {fps_f}FPS")
        
        self.writer_f = cv2.VideoWriter('video_front.mp4', fourcc, fps_f, (self.w_f, self.h_f))
        self.writer_s = cv2.VideoWriter('video_side.mp4', fourcc, fps_s, (self.w_s, self.h_s))
        
        ### OPTYMALIZACJA: Kolejka do zapisu wideo ###
        # maxsize=0 oznacza nieskończoną kolejkę (uwaga na RAM przy bardzo wolnym dysku)
        # Jeśli dysk jest wolny, ustaw np. maxsize=100, żeby nie "zjadło" całej pamięci
        self.video_queue = queue.Queue(maxsize=200) 
        
        # Uruchamiamy osobny wątek tylko do zapisywania plików
        self.writer_thread = threading.Thread(target=self._video_writer_worker, daemon=True)
        self.writer_thread.start()

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.cap_f.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap_s.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if side_offset > 0: self.cap_s.set(cv2.CAP_PROP_POS_FRAMES, side_offset)
        elif side_offset < 0: self.cap_f.set(cv2.CAP_PROP_POS_FRAMES, abs(side_offset))

        self.running = True
        self.frame_count = 0
        self.coords = None
        self.reps_arr = []
        self.sets_arr = []
        self.frames_since_last_rep = 0
        self.idle_threshold = 300
        self.temp_frames = []

        self.current_frame_data = frame_data.FrameData(
            frame_index=0, set_number=1, repetition_number=0,
            keypoints=np.zeros((33, 3), dtype=np.float32),
            phase=frame_data.PhaseEnum.START,
            tempo=frame_data.TempoEnum.OK,
            percent_match=None, key_position_flag=False, joints_moving=None
        )
        
        with open(json_start_pos, "r", encoding="utf-8") as f: self.start_pos = json.load(f)
        with open(json_top_pos, "r", encoding="utf-8") as f: self.top_pos = json.load(f)

        self.joint_tolerances = {j: 15 for j in JOINT_DEFINITIONS}
        self.eps = 2

        self.device = "GPU"
        model_path = 'pose_landmarker_lite.task'
        # Inicjalizacja MediaPipe (bez zmian)
        try:
            base_options = python.BaseOptions(model_asset_path=model_path, delegate=python.BaseOptions.Delegate.GPU)
            options = vision.PoseLandmarkerOptions(base_options=base_options, output_segmentation_masks=False, running_mode=vision.RunningMode.VIDEO)
            self.detector_f = vision.PoseLandmarker.create_from_options(options)
            self.detector_s = vision.PoseLandmarker.create_from_options(options)
        except Exception:
            base_options = python.BaseOptions(model_asset_path=model_path, delegate=python.BaseOptions.Delegate.CPU)
            options = vision.PoseLandmarkerOptions(base_options=base_options, output_segmentation_masks=False, running_mode=vision.RunningMode.VIDEO)
            self.detector_f = vision.PoseLandmarker.create_from_options(options)
            self.detector_s = vision.PoseLandmarker.create_from_options(options)

        self.lastFrameAngles = {}
        self.top_reached = False

        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    ### OPTYMALIZACJA: Funkcja wątku zapisującego ###
    def _video_writer_worker(self):
        while True:
            # Pobieramy klatki z kolejki
            item = self.video_queue.get()
            
            # None to sygnał "poison pill" do zatrzymania wątku
            if item is None:
                self.video_queue.task_done()
                break
                
            frame_f, frame_s = item
            
            # Zapis fizyczny na dysk (to jest wolne, ale nie blokuje już głównego wątku)
            if frame_f is not None: self.writer_f.write(frame_f)
            if frame_s is not None: self.writer_s.write(frame_s)
            
            self.video_queue.task_done()

    def _update(self):
        while self.running:
            ret_f, frame_f = self.cap_f.read()
            ret_s, frame_s = self.cap_s.read()
            
            if not ret_f or not ret_s:
                self.running = False
                break
            
            ### OPTYMALIZACJA: Wrzucamy do kolejki zamiast pisać bezpośrednio ###
            # Jeśli kolejka jest pełna (wolny dysk), pomijamy zapis, żeby nie zwiesić analizy
            if not self.video_queue.full():
                # Kopiujemy (copy), aby uniknąć błędów pamięci, jeśli OpenCV nadpisze bufor
                self.video_queue.put((frame_f.copy(), frame_s.copy()))
            
            ts = int(time.time() * 1000)
            img_f = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_f)
            img_s = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_s)
            
            future_f = self.executor.submit(self.detector_f.detect_for_video, img_f, ts)
            future_s = self.executor.submit(self.detector_s.detect_for_video, img_s, ts)

            res_f = future_f.result()
            res_s = future_s.result()

            if res_f.pose_landmarks and res_s.pose_landmarks:
                self._process_results(res_f.pose_landmarks[0], res_s.pose_landmarks[0])

            self.frame_count += 1

    def _process_results(self, lms_f, lms_s):
        kp = np.array([
            [lms_f[i].x * self.w_f, lms_f[i].y * self.h_f, lms_s[i].x * self.w_f]
            for i in range(33)
        ], dtype=np.float32)
        
        self.current_frame_data.keypoints = kp
        self.coords = {LANDMARK_NAMES[i]: kp[i] for i in range(33)}
        self._run_exercise_logic()

    def _run_exercise_logic(self):
        # (Bez zmian w logice)
        starting_check, top_check = [], []
        moving_any_up, moving_any_down = False, False

        for j_name, idx_names in JOINT_DEFINITIONS.items():
            try:
                a, b, c = self.coords[idx_names[0]], self.coords[idx_names[1]], self.coords[idx_names[2]]
                angle = calc_angle(a, b, c)
                tol = self.joint_tolerances.get(j_name, 15)
                starting_check.append(abs(angle - self.start_pos.get(j_name, 0)) < tol)
                top_check.append(abs(angle - self.top_pos.get(j_name, 0)) < tol)
                if j_name in self.lastFrameAngles:
                    diff = angle - self.lastFrameAngles[j_name]
                    if diff > self.eps: moving_any_up = True
                    if diff < -self.eps: moving_any_down = True
                self.lastFrameAngles[j_name] = angle
            except: continue
        
        isStarting = all(starting_check) if starting_check else False
        isTop = all(top_check) if top_check else False

        if isStarting:
            self.current_frame_data.phase = frame_data.PhaseEnum.START
            if self.top_reached: self._handle_repetition_complete()
        elif isTop:
            self.current_frame_data.phase = frame_data.PhaseEnum.PAUSE
            self.top_reached = True
        elif moving_any_up:
            self.current_frame_data.phase = frame_data.PhaseEnum.LIFT
        elif moving_any_down:
            self.current_frame_data.phase = frame_data.PhaseEnum.LOWER

        self.frames_since_last_rep += 1
        if self.frames_since_last_rep >= self.idle_threshold and self.reps_arr:
            self._finish_set()

        self.current_frame_data.frame_index = self.frame_count
        self.current_frame_data.key_position_flag = (isStarting or isTop)
        self.temp_frames.append(copy.copy(self.current_frame_data))

    def _handle_repetition_complete(self):
        self.current_frame_data.repetition_number += 1
        cleaned_rep = self._process_repetition(self.temp_frames)
        self.reps_arr.append(cleaned_rep)
        self.frames_since_last_rep = 0
        rep_n, set_n = self.current_frame_data.repetition_number, self.current_frame_data.set_number
        if self.logging:
            def save_task(data, r, s):
                try:
                    with open(f"rep_{r}_set{s}.json", "w") as f: json.dump(data, f, cls=CustomEncoder)
                except Exception: pass
            threading.Thread(target=save_task, args=(cleaned_rep, rep_n, set_n)).start()
        self.temp_frames = []
        self.top_reached = False

    def _finish_set(self):
        if self.reps_arr:
            self.sets_arr.append(list(self.reps_arr))
            set_n = len(self.sets_arr)
            if self.logging:
                try:
                    with open(f"set_{set_n}.json", "w") as f: json.dump(self.reps_arr, f, cls=CustomEncoder)
                except Exception: pass
            self.reps_arr = []
            self.current_frame_data.set_number += 1
            self.current_frame_data.repetition_number = 0
            self.frames_since_last_rep = 0
            print(f"[THREAD] Wykryto koniec serii nr {set_n}. Wysyłam sygnał.")
            self.set_finished_event.set()

    def _process_repetition(self, frames_list):
        pause_indices = [i for i, f in enumerate(frames_list) if f.phase == frame_data.PhaseEnum.PAUSE]
        if not pause_indices: return frames_list
        first_p, last_p = pause_indices[0], pause_indices[-1]
        for i, frame in enumerate(frames_list):
            if i < first_p and frame.phase != frame_data.PhaseEnum.START: frame.phase = frame_data.PhaseEnum.LIFT
            elif i > last_p and frame.phase != frame_data.PhaseEnum.START: frame.phase = frame_data.PhaseEnum.LOWER
            elif first_p <= i <= last_p: frame.phase = frame_data.PhaseEnum.PAUSE
        return frames_list

    def stop(self):
        self.running = False
        self.thread.join()
        
        ### OPTYMALIZACJA: Sprzątanie wątku zapisu ###
        print("[INFO] Czekam na zakończenie zapisu wideo z bufora...")
        self.video_queue.put(None) # Wysyłamy sygnał stopu
        self.writer_thread.join()  # Czekamy aż wszystko się zapisze
        
        if hasattr(self, 'writer_f'): self.writer_f.release()
        if hasattr(self, 'writer_s'): self.writer_s.release()
        self.cap_f.release()
        self.cap_s.release()
        print("[INFO] Zakończono nagrywanie i analizę.")

if __name__ == "__main__":
    cam = CameraThread(side_offset=15)
    print("\n" + "="*85)
    print(f" ANALIZA + NAGRYWANIE (ASYNC) | URZĄDZENIE: {cam.device}")
    print(" Naciśnij Ctrl+C, aby zakończyć.")
    print("="*85 + "\n")

    prev_frame_count, prev_time, fps = 0, time.time(), 0

    try:
        while cam.running:
            current_time = time.time()
            f_idx = cam.frame_count
            if cam.set_finished_event.is_set():
                print(f"\n[EVENT] KONIEC SERII! (Suma: {len(cam.sets_arr)})")
                cam.set_finished_event.clear()
            
            if current_time - prev_time > 0.5:
                fps = (f_idx - prev_frame_count) / (current_time - prev_time)
                prev_frame_count, prev_time = f_idx, current_time
            
            # Info o wielkości kolejki zapisu pozwala monitorować czy dysk wyrabia
            q_size = cam.video_queue.qsize()
            
            phase = str(cam.current_frame_data.phase)
            if hasattr(cam.current_frame_data.phase, 'name'): phase = cam.current_frame_data.phase.name
            
            print(f"| FPS: {fps:.1f} | Q: {q_size} | Seria: {cam.current_frame_data.set_number} | Powt: {cam.current_frame_data.repetition_number} | {phase.ljust(6)}", end="\r", flush=True)
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n\n[ZATRZYMANO PRZEZ UŻYTKOWNIKA]")
    finally:
        cam.stop()