#!/usr/bin/env python3
"""Generate thesis figure 2: Lucas–Kanade optical flow between two frames."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
except ImportError as exc:
    raise SystemExit(
        "matplotlib is required: pip install matplotlib"
    ) from exc

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FRAMES_DIR = (
    REPO_ROOT
    / "Datasets/calibration_datasets/cam_checkerboard/cam_checkerboard/mav0/cam0/data"
)
DEFAULT_OUTPUT = REPO_ROOT / "thesis/images/fig-02-optical-flow.png"

# Same defaults as vo-uav/src/vo.py
FEATURE_PARAMS = dict(
    maxCorners=200,
    qualityLevel=0.015,
    minDistance=10,
    blockSize=7,
)
LK_PARAMS = dict(
    winSize=(21, 21),
    maxLevel=4,
    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
)
FORWARD_BACKWARD_THRESHOLD = 4.0


def list_frame_paths(frames_dir: Path) -> list[Path]:
    paths = sorted(
        p
        for p in frames_dir.iterdir()
        if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )
    if len(paths) < 2:
        raise FileNotFoundError(f"Need at least 2 images in {frames_dir}")
    return paths


def track_features(
    prev_gray: np.ndarray,
    cur_gray: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return prev_pts, cur_pts, accepted mask (forward–backward consistent)."""
    pts = cv2.goodFeaturesToTrack(prev_gray, mask=None, **FEATURE_PARAMS)
    if pts is None or len(pts) < 8:
        raise RuntimeError("Not enough features detected in the first frame.")

    cur_pts, status, _ = cv2.calcOpticalFlowPyrLK(
        prev_gray, cur_gray, pts, None, **LK_PARAMS
    )
    fb_pts, fb_status, _ = cv2.calcOpticalFlowPyrLK(
        cur_gray, prev_gray, cur_pts, None, **LK_PARAMS
    )

    if cur_pts is None or fb_pts is None or status is None or fb_status is None:
        raise RuntimeError("Optical flow failed.")

    fb_dist = np.linalg.norm(fb_pts - pts, axis=2).reshape(-1)
    status_flat = status.reshape(-1).astype(bool)
    fb_flat = fb_status.reshape(-1).astype(bool)
    accepted = status_flat & fb_flat & (fb_dist < FORWARD_BACKWARD_THRESHOLD)

    return pts.reshape(-1, 2), cur_pts.reshape(-1, 2), accepted


def mean_flow_magnitude(prev_pts: np.ndarray, cur_pts: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return 0.0
    delta = cur_pts[mask] - prev_pts[mask]
    return float(np.mean(np.linalg.norm(delta, axis=1)))


def pick_frame_pair(
    frames_dir: Path,
    index: int | None,
    search_limit: int,
    gap: int,
) -> tuple[Path, Path, np.ndarray, np.ndarray]:
    paths = list_frame_paths(frames_dir)
    gap = max(1, gap)

    if index is not None:
        j = index + gap
        if index < 0 or j >= len(paths):
            raise IndexError(f"index {index} with gap {gap} invalid; max {len(paths) - gap - 1}")
        p0 = cv2.imread(str(paths[index]), cv2.IMREAD_GRAYSCALE)
        p1 = cv2.imread(str(paths[j]), cv2.IMREAD_GRAYSCALE)
        if p0 is None or p1 is None:
            raise RuntimeError("Could not read selected frame pair.")
        return paths[index], paths[j], p0, p1

    best: tuple[float, int, Path, Path, np.ndarray, np.ndarray] | None = None
    limit = min(len(paths) - gap, search_limit)

    for i in range(limit):
        g0 = cv2.imread(str(paths[i]), cv2.IMREAD_GRAYSCALE)
        g1 = cv2.imread(str(paths[i + gap]), cv2.IMREAD_GRAYSCALE)
        if g0 is None or g1 is None:
            continue
        try:
            prev_pts, cur_pts, accepted = track_features(g0, g1)
        except RuntimeError:
            continue

        n_ok = int(np.sum(accepted))
        n_bad = int(np.sum(~accepted))
        if n_ok < 20:
            continue

        score = mean_flow_magnitude(prev_pts, cur_pts, accepted)
        if not (0.8 <= score <= 35.0):
            continue

        # Prefer pairs with some rejected tracks (better for the figure legend).
        reject_ratio = n_bad / max(1, n_ok + n_bad)
        quality = abs(reject_ratio - 0.12) + abs(score - 8.0) * 0.05
        if best is None or quality < best[0]:
            best = (quality, i, paths[i], paths[i + gap], g0, g1)

    if best is not None:
        _, _, path0, path1, g0, g1 = best
        return path0, path1, g0, g1

    g0 = cv2.imread(str(paths[0]), cv2.IMREAD_GRAYSCALE)
    g1 = cv2.imread(str(paths[gap]), cv2.IMREAD_GRAYSCALE)
    if g0 is None or g1 is None:
        raise RuntimeError("Could not read fallback frame pair.")
    return paths[0], paths[gap], g0, g1


def bgr_from_gray(gray: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def render_figure(
    prev_bgr: np.ndarray,
    cur_bgr: np.ndarray,
    prev_pts: np.ndarray,
    cur_pts: np.ndarray,
    accepted: np.ndarray,
    frame0_name: str,
    frame1_name: str,
    output: Path,
    dpi: int,
) -> None:
    h, w = prev_bgr.shape[:2]
    combined = np.hstack([prev_bgr, cur_bgr])

    fig, ax = plt.subplots(figsize=(12, 4.5), dpi=dpi)
    ax.imshow(cv2.cvtColor(combined, cv2.COLOR_BGR2RGB))
    ax.axis("off")

    rejected = ~accepted
    for i in np.where(rejected)[0]:
        x0, y0 = prev_pts[i]
        x1, y1 = cur_pts[i]
        ax.plot([x0, x1 + w], [y0, y1], color="#e53935", linewidth=0.8, alpha=0.85)
        ax.scatter([x0], [y0], s=18, c="#e53935", edgecolors="white", linewidths=0.3)

    for i in np.where(accepted)[0]:
        x0, y0 = prev_pts[i]
        x1, y1 = cur_pts[i]
        ax.plot([x0, x1 + w], [y0, y1], color="#1e88e5", linewidth=0.9, alpha=0.9)
        ax.scatter([x0], [y0], s=20, c="#43a047", edgecolors="white", linewidths=0.3)
        ax.scatter([x1 + w], [y1], s=20, c="#1e88e5", edgecolors="white", linewidths=0.3)

    ax.axvline(w - 0.5, color="white", linewidth=1.2, alpha=0.8)
    ax.text(
        w * 0.5,
        h * 0.04,
        f"Кадр t−1 ({frame0_name})",
        ha="center",
        va="top",
        color="white",
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="black", alpha=0.55),
    )
    ax.text(
        w * 1.5,
        h * 0.04,
        f"Кадр t ({frame1_name})",
        ha="center",
        va="top",
        color="white",
        fontsize=11,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="black", alpha=0.55),
    )

    legend = [
        Patch(facecolor="#43a047", edgecolor="white", label="Ознака (кадр t−1)"),
        Patch(facecolor="#1e88e5", edgecolor="white", label="Відстежена ознака"),
        Patch(facecolor="#e53935", edgecolor="white", label="Відхилена (forward–backward)"),
    ]
    ax.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=10)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create fig-02-optical-flow.png for the coursework thesis."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_FRAMES_DIR,
        help="Folder with consecutive frames",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output PNG path",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=None,
        help="Use frames[index] and frames[index+1]; default: auto-pick",
    )
    parser.add_argument(
        "--gap",
        type=int,
        default=3,
        help="Frame spacing: use frames[index] and frames[index+gap] (default: 3)",
    )
    parser.add_argument(
        "--search-limit",
        type=int,
        default=300,
        help="How many consecutive pairs to scan in auto mode",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Output image DPI",
    )
    args = parser.parse_args()

    if not args.input.is_dir():
        print(f"Error: input directory not found: {args.input}", file=sys.stderr)
        return 1

    try:
        path0, path1, gray0, gray1 = pick_frame_pair(
            args.input, args.index, args.search_limit, args.gap
        )
        prev_pts, cur_pts, accepted = track_features(gray0, gray1)
        n_ok = int(np.sum(accepted))
        n_bad = int(np.sum(~accepted))
        if n_ok < 5:
            raise RuntimeError(
                f"Too few accepted tracks ({n_ok}). Try --index or another folder."
            )

        render_figure(
            bgr_from_gray(gray0),
            bgr_from_gray(gray1),
            prev_pts,
            cur_pts,
            accepted,
            path0.name,
            path1.name,
            args.output,
            args.dpi,
        )
        print(f"Frame pair: {path0.name} -> {path1.name}")
        print(f"Tracks: {n_ok} accepted, {n_bad} rejected")
        print(f"Saved: {args.output}")
        return 0
    except (FileNotFoundError, IndexError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
