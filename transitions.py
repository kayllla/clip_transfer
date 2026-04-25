import json
import os
import subprocess
import tempfile

# FFmpeg xfade transitions available for Claude to choose from
TRANSITIONS = {
    "fade":        "柔和淡入淡出，适合情绪平稳的切换",
    "fadeblack":   "黑场过渡，适合场景强烈切换或时间跳跃",
    "dissolve":    "溶解融合，适合同场景不同时刻",
    "zoom_in":     "画面推进，适合从宏观到微观",
    "wipe_left":   "向左擦除，适合叙事向前推进",
    "wipe_right":  "向右擦除，适合回忆或倒叙",
    "slide_left":  "向左滑动，适合动感节奏",
    "pixelize":    "像素化消散，适合科技感或故障风",
    "radial":      "放射状扫描，适合戏剧性时刻",
    "circle_open": "圆形展开，适合聚焦或揭示",
}

# Map to FFmpeg xfade transition names
XFADE_MAP = {
    "fade":        "fade",
    "fadeblack":   "fadeblack",
    "dissolve":    "dissolve",
    "zoom_in":     "zoomin",
    "wipe_left":   "wipeleft",
    "wipe_right":  "wiperight",
    "slide_left":  "slideleft",
    "pixelize":    "pixelize",
    "radial":      "radial",
    "circle_open": "circleopen",
}


def get_duration(path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", path],
        capture_output=True, text=True, check=True,
    )
    streams = json.loads(result.stdout)["streams"]
    return float(streams[0]["duration"])


def render_preview(clip_a: str, clip_b: str, transition: str, trans_duration: float) -> str:
    """Render a ~5s preview clip: last 2s of A + transition + first 2s of B."""
    dur_a = get_duration(clip_a)
    dur_b = get_duration(clip_b)

    pre_a = min(2.0, dur_a)
    pre_b = min(2.0, dur_b)
    xfade = XFADE_MAP.get(transition, "fade")

    # Clamp trans_duration so it fits within the trimmed clips
    td = min(trans_duration, pre_a, pre_b, 1.5)
    offset = pre_a - td

    out = tempfile.mktemp(suffix=".mp4", prefix="preview_")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", str(dur_a - pre_a), "-t", str(pre_a), "-i", clip_a,
        "-t", str(pre_b), "-i", clip_b,
        "-filter_complex",
        f"[0:v][1:v]xfade=transition={xfade}:duration={td}:offset={offset}[v]",
        "-map", "[v]",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        out,
    ]
    subprocess.run(cmd, check=True)
    return out


def render_final(clips: list[str], transitions: list[dict], out_path: str = "output/final.mp4") -> str:
    """Combine all clips with chosen transitions into final video."""
    n = len(clips)
    durations = [get_duration(c) for c in clips]

    inputs = []
    for c in clips:
        inputs += ["-i", c]

    filter_parts = []
    prev_label = "[0:v]"
    offset = 0.0

    for i, trans in enumerate(transitions):
        xfade = XFADE_MAP.get(trans["transition"], "fade")
        td = min(trans["duration"], durations[i], durations[i + 1], 1.5)
        offset += durations[i] - td
        next_label = "[vout]" if i == len(transitions) - 1 else f"[v{i}]"
        filter_parts.append(
            f"{prev_label}[{i+1}:v]xfade=transition={xfade}"
            f":duration={td}:offset={offset}{next_label}"
        )
        prev_label = next_label

    filter_complex = ";".join(filter_parts)

    cmd = (
        ["ffmpeg", "-y", "-loglevel", "error"]
        + inputs
        + [
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            out_path,
        ]
    )
    subprocess.run(cmd, check=True)
    return out_path
