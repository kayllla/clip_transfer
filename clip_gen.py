import os
import httpx
import fal_client
from config import FAL_KEY, OUTPUT_DIR

os.environ["FAL_KEY"] = FAL_KEY

# 1.3B model: cheaper and faster, good enough for demo
MODEL = "fal-ai/wan/v2.1/1.3b/text-to-video"


def generate_clip(prompt: str, clip_index: int, duration: int = 3) -> str:
    """Generate a video clip from a text prompt. Returns local file path."""
    # Wan2.1 at 16fps: 3s ≈ 49 frames; use nearest supported value
    num_frames = duration * 16

    result = fal_client.run(
        MODEL,
        arguments={
            "prompt": prompt,
            "num_frames": num_frames,
        },
    )

    video_url = result["video"]["url"]
    out_path = os.path.join(OUTPUT_DIR, f"clip_{clip_index:02d}.mp4")

    with httpx.Client() as client:
        resp = client.get(video_url, follow_redirects=True, timeout=60)
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(resp.content)

    return out_path
