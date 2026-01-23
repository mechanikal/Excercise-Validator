from frame_data import *
from CameraThread import DFL

class CorrectExercise:
    def __init__(self, number_of_phases):
        self.number_of_phases = number_of_phases #int
        self.correct_tempos = [] #int (frame_number) (first value insignificant
        self.correct_angles = [] #np.array (angles for each joint)
        self.angle_tolerancies  = [] #np.array (tolerancies for each angle)
        self.immovable_keypoints = [] # joints that should stay immobile
        self.movement_tolerancy = 5 # int
        self.joints = [] #key joints
        self.tempo_tolerancy = 5

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
        #lat
        lat_key_joints = np.array(
                [[DFL.RIGHT_HEEL, DFL.RIGHT_KNEE, DFL.RIGHT_HIP], [DFL.LEFT_HEEL, DFL.LEFT_KNEE, DFL.LEFT_HIP],
                [DFL.RIGHT_WRIST, DFL.RIGHT_ELBOW, DFL.RIGHT_SHOULDER], [DFL.LEFT_WRIST, DFL.LEFT_ELBOW, DFL.LEFT_SHOULDER],
                [DFL.RIGHT_WRIST, DFL.RIGHT_SHOULDER, DFL.LEFT_SHOULDER], [DFL.LEFT_WRIST, DFL.LEFT_SHOULDER, DFL.RIGHT_SHOULDER],
                [DFL.RIGHT_KNEE, DFL.RIGHT_HIP, DFL.RIGHT_SHOULDER], [DFL.LEFT_KNEE, DFL.LEFT_HIP, DFL.LEFT_SHOULDER]])
        lat_down_angles = np.array([170,170, 150,150, 90,90, 170,170])
        lat_up_angles = np.array([170,170, 150,150, 170,170, 170,170])
        lat_tolerancies = np.array([20,20, 10,10, 10,10, 10,10])/180
        lat_immovable = np.array([DFL.RIGHT_KNEE,DFL.LEFT_KNEE,DFL.LEFT_HIP,DFL.RIGHT_HIP,DFL.RIGHT_SHOULDER,DFL.LEFT_SHOULDER])
        lat_tempos = [-1,40,30,70]
        #row
        row_key_joints = np.array(
                [[DFL.RIGHT_HEEL, DFL.RIGHT_KNEE, DFL.RIGHT_HIP], [DFL.LEFT_HEEL, DFL.LEFT_KNEE, DFL.LEFT_HIP],
                 [DFL.RIGHT_WRIST, DFL.RIGHT_ELBOW, DFL.RIGHT_SHOULDER],[DFL.LEFT_WRIST, DFL.LEFT_ELBOW, DFL.LEFT_SHOULDER],
                 [DFL.RIGHT_HEEL, DFL.RIGHT_HIP, DFL.RIGHT_SHOULDER],[DFL.LEFT_HEEL, DFL.LEFT_HIP, DFL.LEFT_SHOULDER]])
        row_down_angles = np.array([165,165, 160,160, 120,120])
        row_up_angles = np.array([140,140, 100,100, 120,120])
        row_tolerancies = np.array([10,10, 20,20, 15,15])/180
        row_immovable = np.array([DFL.RIGHT_KNEE,DFL.LEFT_KNEE,DFL.LEFT_HIP,DFL.RIGHT_HIP,DFL.RIGHT_SHOULDER,DFL.LEFT_SHOULDER])
        row_tempos = [-1, 45, 15, 90]
        #curl
        crl_key_joints = np.array(
                [[DFL.RIGHT_HEEL, DFL.RIGHT_KNEE, DFL.RIGHT_HIP], [DFL.LEFT_HEEL, DFL.LEFT_KNEE, DFL.LEFT_HIP],
                 [DFL.RIGHT_WRIST, DFL.RIGHT_ELBOW, DFL.RIGHT_SHOULDER],[DFL.LEFT_WRIST, DFL.LEFT_ELBOW, DFL.LEFT_SHOULDER],
                 [DFL.RIGHT_ELBOW, DFL.RIGHT_SHOULDER, DFL.RIGHT_HIP],[DFL.LEFT_ELBOW, DFL.LEFT_SHOULDER, DFL.LEFT_HIP],
                 [DFL.RIGHT_HEEL, DFL.RIGHT_HIP, DFL.RIGHT_SHOULDER],[DFL.LEFT_HEEL, DFL.LEFT_HIP, DFL.LEFT_SHOULDER]])
        crl_down_angles = np.array([170,170, 170,170, 15,15, 170,170])
        crl_up_angles = np.array([170,170, 35,35, 15,15, 170,170])
        crl_tolerancies = np.array([10,10, 10,10, 10,10, 10,10])/180
        crl_immovable = np.array([DFL.RIGHT_KNEE,DFL.LEFT_KNEE,DFL.LEFT_HIP,DFL.RIGHT_HIP,DFL.RIGHT_SHOULDER,DFL.LEFT_SHOULDER])
        crl_tempos = [-1, 45, 15, 90]
        # phase START, pos start
        self.lat_CE.add_correct_position_for_phase(lat_key_joints,lat_down_angles,lat_tolerancies,lat_tempos[0],lat_immovable)
        self.row_CE.add_correct_position_for_phase(row_key_joints,row_down_angles,row_tolerancies,row_tempos[0],row_immovable)
        self.curl_CE.add_correct_position_for_phase(crl_key_joints,crl_down_angles,crl_tolerancies,crl_tempos[0],crl_immovable)
        # phase LIFT, pos up start
        self.lat_CE.add_correct_position_for_phase(lat_key_joints, lat_up_angles, lat_tolerancies, lat_tempos[1],lat_immovable)
        self.row_CE.add_correct_position_for_phase(row_key_joints, row_up_angles, row_tolerancies, row_tempos[1],row_immovable)
        self.curl_CE.add_correct_position_for_phase(crl_key_joints, crl_up_angles, crl_tolerancies, crl_tempos[1],crl_immovable)
        # phase PAUSE, pos up end
        self.lat_CE.add_correct_position_for_phase(lat_key_joints, lat_up_angles, lat_tolerancies, lat_tempos[2],lat_immovable)
        self.row_CE.add_correct_position_for_phase(row_key_joints, row_up_angles, row_tolerancies, row_tempos[2],row_immovable)
        self.curl_CE.add_correct_position_for_phase(crl_key_joints, crl_up_angles, crl_tolerancies, crl_tempos[2],crl_immovable)
        # phase LOWER, pos finish (same as start)
        self.lat_CE.add_correct_position_for_phase(lat_key_joints, lat_down_angles, lat_tolerancies, lat_tempos[3],lat_immovable)
        self.row_CE.add_correct_position_for_phase(row_key_joints, row_down_angles, row_tolerancies, row_tempos[3],row_immovable)
        self.curl_CE.add_correct_position_for_phase(crl_key_joints, crl_down_angles, crl_tolerancies, crl_tempos[3],crl_immovable)

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
        wrong_angles = np.zeros_like(frame_data.joints_wrong_angles)
        result = 0.0
        n = len(joints)
        for i in range(0, n):
            correct_joints = []
            for j in joints[i]:
                correct_joints.append(frame_keypoints[j])
            p1, q1, r1 = correct_joints
            match = self.angle_match_percent(self.angle(p1, q1, r1), correct_position[i])
            if (1 - match) > correct_exercise.angle_tolerancies[exercise_phase][i]:
                wrong_angles[joints[i][1]] = True
            result += match
        return result / n , wrong_angles

    def check_tempo(self, number_of_frames, exercise_phase, correct_exercise):
        if exercise_phase == 0: # start is always ok
            return TempoEnum.OK
        if abs(correct_exercise.correct_tempos[exercise_phase] - number_of_frames) > correct_exercise.tempo_tolerancy:
            if correct_exercise.correct_tempos[exercise_phase] > number_of_frames:
                return TempoEnum.TOO_SLOW
            else:
                return TempoEnum.TOO_FAST
        else:
            return TempoEnum.OK

    def validate(self, frames: list[FrameData], exercise):
        if exercise == 'lateral':
            correct_exercise = self.lat_CE
        elif exercise == 'row':
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
                frames[i+1].percent_match, frames[i+1].joints_wrong_angles = self.check_frame_position(frames[i+1], phase_tmp, correct_exercise)
                frames[i+1].tempo = self.check_tempo(frame_tmp, phase_tmp,correct_exercise)
                for j in range(i-frame_tmp, i):
                    frames[j].tempo = frames[i+1].tempo
                    if phase_tmp == 2:
                        frames[j].joints_wrong_angles = frames[i + 1].joints_wrong_angles
                phase_tmp += 1
                frame_tmp = 0