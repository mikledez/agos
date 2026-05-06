import mediapipe as mp
import cv2

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def get_pose_landmarks(image):
    with mp_pose.Pose(static_image_mode=True) as pose:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if not results.pose_landmarks:
            return None, None

        return results.pose_landmarks.landmark, results.pose_landmarks

def draw_landmarks_on_image(image, pose_landmarks):
    image_with_landmarks = image.copy()
    mp_drawing.draw_landmarks(
        image_with_landmarks,
        pose_landmarks,
        mp_pose.POSE_CONNECTIONS
    )
    return image_with_landmarks