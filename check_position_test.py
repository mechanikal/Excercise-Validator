import numpy as np
from frame_data import *
from check_position import CorrectExercise, fill_FrameData

# --- Tworzymy obiekt CorrectExercise z 2 fazami ---
correct_exercise = CorrectExercise(number_of_phases=2)

# faza 0
correct_exercise.add_correct_position_for_phase(
    angle_value=np.random.rand(20).astype(np.float32) * 180,  # 20 kątów
    angles='a',
    tempo=3,
    joints=np.array([[0,1,2], [3,4,5], [6,7,8]])  # przykładowe trójki jointów
)

# faza 1
correct_exercise.add_correct_position_for_phase(
    angle_value=np.random.rand(20).astype(np.float32) * 180,
    angles='b',
    tempo=4,
    joints=np.array([[0,1,2], [3,4,5], [6,7,8]])
)

# --- Tworzymy listę FrameData (klatki) ---
num_frames = 6
frames = []
for i in range(num_frames):
    phase = i // 3  # zmiana fazy co 3 klatki
    keypoints = np.random.rand(20, 3).astype(np.float32)  # 20 punktów x 3
    frames.append(FrameData(
        frame_index=i,
        set_number=0,
        repetition_number=0,
        keypoints=keypoints,
        phase=phase,
        tempo=0,
        percent_match=np.float32(0.0),
        key_position_flag=False,
        joints_moving=np.zeros(20, dtype=bool)
    ))

# --- Dla porownania ---

for f in frames:
    print(f"Frame {f.frame_index}:")
    print(f"  Key position flag: {f.key_position_flag}")
    print(f"  Percent match: {f.percent_match}")
    print(f"  Tempo: {f.tempo}")
    print(f"  Joints moving: {f.joints_moving}\n")

# --- Wywołanie fill_FrameData ---
fill_FrameData(frames, correct_exercise, num_frames)

# --- Wyświetlamy wyniki ---
for f in frames:
    print(f"Frame {f.frame_index}:")
    print(f"  Key position flag: {f.key_position_flag}")
    print(f"  Percent match: {f.percent_match}")
    print(f"  Tempo: {f.tempo}")
    print(f"  Joints moving: {f.joints_moving}\n")
