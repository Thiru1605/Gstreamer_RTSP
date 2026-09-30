import gi
import os
import cv2
import numpy as np

gi.require_version("Gst", "1.0")
from gi.repository import Gst

Gst.init(None)

RTSP_URL = "rtsp://localhost:8554/camera1"
OUTPUT_DIR = "frames"

os.makedirs(OUTPUT_DIR, exist_ok=True)

pipeline = Gst.parse_launch(
    f'rtspsrc location={RTSP_URL} protocols=tcp latency=100 ! '
    'rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! '
    'video/x-raw,format=BGR ! '
    'appsink name=sink emit-signals=false sync=false max-buffers=1 drop=true'
)

appsink = pipeline.get_by_name("sink")

pipeline.set_state(Gst.State.PLAYING)

print("Connected to RTSP stream")
print("Extracting frames...")

frame_count = 0

try:
    while frame_count < 100:

        sample = appsink.emit("pull-sample")

        if sample is None:
            print("Failed to receive frame")
            break

        caps = sample.get_caps()
        structure = caps.get_structure(0)

        width = structure.get_value("width")
        height = structure.get_value("height")

        buffer = sample.get_buffer()

        success, map_info = buffer.map(Gst.MapFlags.READ)

        if not success:
            print("Failed to map buffer")
            continue

        frame = np.ndarray(
            (height, width, 3),
            dtype=np.uint8,
            buffer=map_info.data
        ).copy()

        buffer.unmap(map_info)

        filename = os.path.join(
            OUTPUT_DIR,
            f"frame_{frame_count:04d}.jpg"
        )

        cv2.imwrite(filename, frame)

        frame_count += 1

        print(f"Saved: {filename}")

finally:
    pipeline.set_state(Gst.State.NULL)

print(f"\nCompleted: {frame_count} frames saved.")