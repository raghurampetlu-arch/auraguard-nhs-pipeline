import numpy as np

class Config:
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    ALERT_CHANNEL = "nhs_ward_alerts"
    STREAM_CHANNEL = "nhs_ward_telemetry"
    
    # 4 Calibration points from CCTV frame [x, y]
    CCTV_POINTS = np.array([[150, 480], [1130, 480], [50, 1000], [1230, 1000]], dtype=np.float32)
    
    # Matching coordinates on the 2D Ward Blueprints Map [x, y]
    WARD_MAP_POINTS = np.array([[100, 100], [700, 100], [100, 900], [700, 900]], dtype=np.float32)
    
    @classmethod
    def get_homography_matrix(cls):
        import cv2
        H, _ = cv2.findHomography(cls.CCTV_POINTS, cls.WARD_MAP_POINTS)
        return H
