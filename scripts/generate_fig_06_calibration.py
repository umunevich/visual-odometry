#!/usr/bin/env python3
"""Generate thesis figure 6: chessboard corner detection (6×7 EuRoC pattern)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FRAMES_DIR = (
    REPO_ROOT
    / "Datasets/calibration_datasets/cam_checkerboard/cam_checkerboard/mav0/cam0/data"
)
DEFAULT_OUTPUT = REPO_ROOT / "thesis/images/fig-06-calibration.png"

# EuRoC cam_checkerboard: 6 inner corners along width, 7 along height.
INNER_COLS = 6
INNER_ROWS = 7


def find_chessboard_corners(gray: np.ndarray) -> tuple[bool, np.ndarray | None]:
    pattern = (INNER_COLS, INNER_ROWS)
    if hasattr(cv2, "findChessboardCornersSB"):
        found, corners = cv2.findChessboardCornersSB(
            gray, pattern, cv2.CALIB_CB_ACCURACY
        )
        if found and corners is not None:
            return True, corners.reshape(-1, 1, 2).astype(np.float32)

    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
    found, corners = cv2.findChessboardCorners(gray, pattern, flags)
    if found and corners is not None:
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.001)
        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        return True, corners
    return False, None


def list_frame_paths(frames_dir: Path) -> list[Path]:
    paths = sorted(
        p
        for p in frames_dir.iterdir()
        if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )
    if not paths:
        raise FileNotFoundError(f"No images found in {frames_dir}")
    return paths


def pick_frame_with_board(frames_dir: Path, start_index: int) -> tuple[Path, np.ndarray]:
    paths = list_frame_paths(frames_dir)
    if start_index < 0 or start_index >= len(paths):
        raise IndexError(
            f"start_index {start_index} out of range (0..{len(paths) - 1})"
        )

    for path in paths[start_index:]:
        image = cv2.imread(str(path))
        if image is None:
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        found, _ = find_chessboard_corners(gray)
        if found:
            return path, image

    raise RuntimeError(
        f"No frame with a {INNER_COLS}×{INNER_ROWS} chessboard found in {frames_dir}. "
        "Try another folder or check the dataset path."
    )


def render_figure(image: np.ndarray, corners: np.ndarray) -> np.ndarray:
    vis = image.copy()
    cv2.drawChessboardCorners(vis, (INNER_COLS, INNER_ROWS), corners, True)

    label = f"EuRoC cam_checkerboard - inner corners {INNER_COLS}x{INNER_ROWS}"
    cv2.rectangle(vis, (0, 0), (vis.shape[1], 42), (0, 0, 0), -1)
    cv2.putText(
        vis,
        label,
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return vis


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create fig-06-calibration.png for the coursework thesis."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_FRAMES_DIR,
        help="Folder with EuRoC cam_checkerboard frames (cam0/data)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output PNG path",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Start searching for a valid chessboard frame from this index",
    )
    args = parser.parse_args()

    if not args.input.is_dir():
        print(f"Error: input directory not found: {args.input}", file=sys.stderr)
        return 1

    try:
        frame_path, image = pick_frame_with_board(args.input, args.start_index)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        found, corners = find_chessboard_corners(gray)
        if not found or corners is None:
            raise RuntimeError("Chessboard detection failed on selected frame.")

        vis = render_figure(image, corners)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(args.output), vis):
            raise RuntimeError(f"Failed to write {args.output}")

        print(f"Used frame: {frame_path.name}")
        print(f"Saved: {args.output}")
        return 0
    except (FileNotFoundError, IndexError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
