import cv2
import json
import numpy as np
import redis
from ultralytics import YOLO
from config import Config

class EdgeAIProcessor:
    def __init__(self):
        # Using a light, high-speed pose tracking model
        self.model = YOLO("yolov8n-pose.pt") 
        self.redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)
        self.H = Config.get_homography_matrix()

    def process_frame(self, frame):
        # Run ByteTrack multi-object tracking over keypoints
        results = self.model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)
        annotated_frame = frame.copy()
        
        if not results or not results[0].boxes:
            return annotated_frame

        boxes = results[0].boxes.cpu().numpy()
        
        for box in boxes:
            if box.id is None:
                continue
                
            track_id = int(box.id[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # 🛡️ STEP 1: UK GDPR EDGE ANONYMISATION
            # Volatile memory blur layer—zero storage of identifiable faces
            roi = annotated_frame[y1:y2, x1:x2]
            if roi.size > 0:
                blurred_roi = cv2.GaussianBlur(roi, (99, 99), 0)
                annotated_frame[y1:y2, x1:x2] = blurred_roi
            
            # 🗺️ STEP 2: SPATIAL HOMOGRAPHY MAPPING
            feet_x = int((x1 + x2) / 2)
            feet_y = y2
            pixel_point = np.array([[[feet_x, feet_y]]], dtype=np.float32)
            transformed = cv2.perspectiveTransform(pixel_point, self.H)
            ward_x, ward_y = int(transformed[0][0][0]), int(transformed[0][0][1])
            
            # 🏥 STEP 3: BIOMEDICAL FALL RISK MEASUREMENT
            bbox_width = x2 - x1
            bbox_height = y2 - y1
            aspect_ratio = bbox_width / float(bbox_height) if bbox_height > 0 else 0
            
            # Aspect ratio > 1.3 implies the horizontal footprint is wider than vertical height (lying down)
            is_fallen = bool(aspect_ratio > 1.3)
            
            telemetry_payload = {
                "patient_token": track_id,
                "ward_x": ward_x,
                "ward_y": ward_y,
                "status": "FALL_CRITICAL" if is_fallen else "NORMAL"
            }
            
            # Publish data packets down the respective Redis networks asynchronously
            self.redis_client.publish(Config.STREAM_CHANNEL, json.dumps(telemetry_payload))
            if is_fallen:
                self.redis_client.publish(Config.ALERT_CHANNEL, json.dumps(telemetry_payload))
                
            # Graphical tokens layered over streaming output
            color = (0, 0, 255) if is_fallen else (0, 255, 0)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)
            cv2.putText(annotated_frame, f"Patient Token #{track_id}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        
        return annotated_frame
