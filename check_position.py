from frame_data import *

class CorrectExercise:
    def __init__(self, number_of_phases):
        self.correct_tempo = [] #int (ilosc klatek)
        self.correct_angle = [] #np.array (kat)
        self.important_angle = [] #tablica z 'a', 'b' lub 'c'
        self.number_of_phases = number_of_phases #int
        self.joints = [] #wybrane stawy

    def add_correct_position_for_phase(self, angle_value, angles, tempo, joints):
        self.correct_angle.append(angle_value)
        self.important_angle.append(angles)
        self.correct_tempo.append(tempo)
        self.joints.append(joints)

    def file_read(self, file_name):
        with open(file_name, "r") as file:
            for _ in range(self.number_of_phases):
                line_1 = np.array([float(x) for x in file.readline().strip().split()])
                line_2 = file.readline().strip()
                line_3 = int(file.readline().strip())
                line_4 = file.readline().strip().split()
                numbers = np.array([int(x) for x in line_4])
                self.add_correct_position_for_phase(line_1, line_2, line_3, numbers.reshape(-1, 3))

    def check_frame_position(self, frame_data: FrameData, exercise_phase):
        if frame_data.key_position_flag:
            frame_data.percent_match = check_position(self.correct_angle[exercise_phase], frame_data.keypoints, self.joints[exercise_phase], self.important_angle[exercise_phase])
        else:
            frame_data.percent_match = None

    def check_tempo(self, number_of_frames, exercise_phase):
        if np.abs(self.correct_tempo[exercise_phase] - number_of_frames) > 10:
            if self.correct_tempo[exercise_phase] < number_of_frames:
                return TempoEnum.TOO_SLOW
            else:
                return TempoEnum.TOO_FAST
        else:
            return TempoEnum.OK


def correctness_percent(a, b):
    if a > b:
        return (180 - (a - b))/180
    else:
        return (180 - (b - a))/180

#angle
# p, q, r - punkty
# x = kat a, b lub c


def angle(p, q, r, x):
    if x == 'a':
        v1 = q - p
        v2 = r - p
    elif x == 'b':
        v1 = p - q
        v2 = r - q
    elif x == 'c':
        v1 = p - r
        v2 = q - r
    else:
        raise ValueError("Parametr x musi być 'a', 'b' lub 'c'")
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    cosang = np.dot(v1, v2) / (norm_v1 * norm_v2)
    cosang = np.clip(cosang, -1.0, 1.0)

    return np.degrees(np.arccos(cosang))

#n - ilosc punktow (powinna byc z gory ustalona)
#x - kat ktory chcemy sprawdzic


def check_position(correct_position, frame_keypoints, joints, x):
    result = 0.0
    n = len(joints)
    for i in range(0, n):
        correct_joints = []
        for j in joints[i]:
            correct_joints.append(frame_keypoints[j])
        p1, q1, r1 = correct_joints
        result += correctness_percent(angle(p1, q1, r1, x), correct_position[i])
    return result/n


def is_key_position(phase1, phase2):
    if phase1 != phase2:
        return True
    else:
        return False


def is_joints_moving(frame_data_1: FrameData, frame_data_2: FrameData, n):
    result = []
    for i in range(n):
        p1, q1, r1 = frame_data_1.keypoints[i]
        p2, q2, r2 = frame_data_2.keypoints[i]
        if np.abs((p1 + q1 + r1) - (p2 + q2 + r2)) > 1:
            result.append(True)
        else:
            result.append(False)
    frame_data_2.joints_moving = np.array(result, dtype=bool)


def fill_FrameData(frames: list[FrameData], correct_exercise: CorrectExercise, number_of_frames):
    frames[0].key_position_flag = False
    phase_tmp = 0
    frame_tmp = 0

    for i in range(number_of_frames - 1):
        frame_tmp += 1
        frames[i+1].key_position_flag = is_key_position(frames[i].phase, frames[i+1].phase)
        is_joints_moving(frames[i], frames[i+1], 20)
        if frames[i+1].key_position_flag:
            correct_exercise.check_frame_position(frames[i+1], phase_tmp)
            frames[i+1].tempo = correct_exercise.check_tempo(frame_tmp, phase_tmp)
            phase_tmp += 1
            frame_tmp = 0
