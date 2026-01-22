from frame_data import *
from CameraThread import DFL

class CorrectExercise:
    def __init__(self, number_of_phases):
        self.number_of_phases = number_of_phases #int
        self.correct_tempos = [] #int (frame_number)
        self.correct_angles = [] #np.array (angles for each joint)
        self.angle_tolerancies  = [] #np.array (tolerancies for each angle)
        self.immovable_keypoints = [] # joints that should stay immobile
        self.movement_tolerancy = 10 # int
        self.joints = [] #key joints
        self.tempo_tolerancy = 10

    def add_correct_position_for_phase(self, key_joints, correct_angles,angle_tolerancies, tempo, immovable_keypoints):
        self.correct_angles.append(correct_angles)
        self.angle_tolerancies.append(angle_tolerancies)
        self.correct_tempos.append(tempo)
        self.joints.append(key_joints)
        self.immovable_keypoints.append(immovable_keypoints)


#exercise: 1 - lat, 2 - row, 3 - curl
class ExerciseValidator:
    def __init__(self):
        self.lat_CE = CorrectExercise(4)
        self.row_CE = CorrectExercise(4)
        self.curl_CE = CorrectExercise(4)
        #todo: add correct positions for each phase for the exercises

        # phase START, pos start
        self.lat_CE.add_correct_position_for_phase(
            key_joints = np.array([[DFL.RIGHT_HEEL,DFL.RIGHT_KNEE,DFL.RIGHT_HIP], [DFL.LEFT_HEEL,DFL.LEFT_KNEE,DFL.LEFT_HIP]]), # 3 points for each joint
            correct_angles = np.array([]), # for each joint in key joints, degree
            angle_tolerancies = np.array([]), # for each angle, degree
            tempo = 4, # number of frames (30 fps)
            immovable_keypoints= np.array([[], [], []]) # 3 points for each joint that should not move
        )
        # phase LIFT, pos up start

        # phase PAUSE, pos up end

        # phase LOWER, pos finish (same as start)


    def angle_match_percent(self,angle_a, angle_b):
        return (180 - abs(angle_a - angle_b))/180

    def angle(self,joint_a, joint_b, joint_c):
        v1 = joint_a - joint_b
        v2 = joint_c - joint_b
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        cos_ang = np.dot(v1, v2) / (norm_v1 * norm_v2)
        cos_ang = np.clip(cos_ang, -1.0, 1.0)
        return np.degrees(np.arccos(cos_ang))

    def is_joints_moving(self,frame_data_1: FrameData, frame_data_2: FrameData,correct_exercise,phase):
        for i in range(len(frame_data_1.keypoints)):
            if i not in correct_exercise.immovable_keypoints[phase]:
                continue
            p1 = frame_data_1.keypoints[i]
            p2 = frame_data_2.keypoints[i]
            delta = np.linalg.norm((p1 - p2))
            if delta > correct_exercise.movement_tolerancy:
                frame_data_2.joints_moving[i] = True
            else:
                frame_data_2.joints_moving[i] = False

    def check_frame_position(self, frame_data: FrameData, exercise_phase, correct_exercise):
        correct_position = correct_exercise.correct_angles[exercise_phase]
        frame_keypoints = frame_data.keypoints
        joints = correct_exercise.joints[exercise_phase]
        result = 0.0
        n = len(joints)
        for i in range(0, n):
            correct_joints = []
            for j in joints[i]:
                correct_joints.append(frame_keypoints[j])
            p1, q1, r1 = correct_joints
            match = self.angle_match_percent(self.angle(p1, q1, r1), correct_position[i])
            if match <= correct_exercise.angle_tolerancies[exercise_phase][i]:
                frame_data.joints_wrong_angles[i] = True
            result += match
        return result / n

    def check_tempo(self, number_of_frames, exercise_phase, correct_exercise):
        if exercise_phase == 0: # start is always ok
            return TempoEnum.OK
        if abs(correct_exercise.correct_tempos[exercise_phase] - number_of_frames) > correct_exercise.tempo_tolerancy:
            if correct_exercise.correct_tempos[exercise_phase] < number_of_frames:
                return TempoEnum.TOO_SLOW
            else:
                return TempoEnum.TOO_FAST
        else:
            return TempoEnum.OK

    def validate(self, frames: list[FrameData], exercise):
        if exercise == 1:
            correct_exercise = self.lat_CE
        elif exercise == 2:
            correct_exercise = self.row_CE
        else:
            correct_exercise = self.curl_CE

        frames[0].key_position_flag = False
        phase_tmp = 0
        frame_tmp = 0
        for i in range(len(frames)-1):
            if phase_tmp >= correct_exercise.number_of_phases:
                break
            frame_tmp += 1
            frames[i+1].key_position_flag = (frames[i].phase != frames[i+1].phase)
            self.is_joints_moving(frames[i], frames[i+1], correct_exercise,phase_tmp)
            if frames[i+1].key_position_flag:
                self.check_frame_position(frames[i+1], phase_tmp, correct_exercise)
                frames[i+1].tempo = self.check_tempo(frame_tmp, phase_tmp,correct_exercise)
                phase_tmp += 1
                frame_tmp = 0
