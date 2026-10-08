import cv2
import threading
import time
from edge_processor import EdgeAIProcessor

class RealTimeVideoStream:
    def __init__(self, src=0):
        """
        src = 0 opens your local laptop webcam.
        For a production NHS deployment, change this to an RTSP security feed string,
        e.g., 'rtsp://admin:password@192.168.1.100:554/stream1'
        """
        self.stream = cv2.VideoCapture(src)
        
        # Optimize internal frame buffer parameters to minimize network latency
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False

    def start(self):
        # Spawn the dedicated background worker thread to read camera memory
        t = threading.Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
                break
            # Continuously flush old packets and pull the newest active hardware frame
            self.grabbed, self.frame = self.stream.read()
            time.sleep(0.01) # Avoid 100% CPU lock on the thread listener loop

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

# --- MAIN REAL-TIME DEPLOYMENT EXECUTION LOOP ---
if __name__ == "__main__":
    print("⏳ Initializing AuraGuard Edge-AI Inference Component...")
    processor = EdgeAIProcessor()
    
    # 0 = Default Webcam. Swap this out with your custom testing video clip path if needed.
    video_source = 0 
    
    print(f"🔌 Connecting to Real-Time Feed Source: Source Index ({video_source})")
    live_stream = RealTimeVideoStream(src=video_source).start()
    
    # Allow the camera hardware sensor time to warm up and balance exposure
    time.sleep(2.0)
    print("🚀 Real-Time Deployment Pipeline Online. Processing live frames...")

    try:
        while True:
            frame = live_stream.read()
            if frame is None:
                continue
            
            # Send the real-time frame through the GDPR blur, tracking, and mapping matrix
            processed_frame = processor.process_frame(frame)
            
            # Optional: Display the local video tracking feedback on the Edge box monitor
            cv2.imshow("AuraGuard Edge AI - Anonymised Monitor View", processed_frame)
            
            # Break out cleanly if 'q' is pressed on the local display monitor
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down deployment component.")
    finally:
        live_stream.stop()
        cv2.destroyAllWindows()
