#!/usr/bin/env python3
"""Run monocular VO on a video file and evaluate against EuRoC ground truth."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
VO_UAV = REPO_ROOT / "vo-uav"
sys.path.insert(0, str(VO_UAV))
os.environ.setdefault("VO_CONFIG_STORAGE", str(VO_UAV / "storage/configs"))
os.environ.setdefault("EUROC_DATASETS_PATH", str(REPO_ROOT / "Datasets"))

from src.config_store import load_vo_profile  # noqa: E402
from src.trajectory_eval import evaluate_against_euroc  # noqa: E402
from src.vo import VisualOdometry  # noqa: E402


def run_vo_on_video(
    video_path: Path,
    profile_id: str,
    max_frames: int | None = None,
    skip: int = 1,
) -> dict:
    profile = load_vo_profile(profile_id)
    vo = VisualOdometry.from_profile(profile)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    samples: list[dict] = []
    tracking_states: list[str] = []
    frame_idx = 0
    processed = 0
    t0 = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % skip != 0:
            frame_idx += 1
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        pose = vo.process_frame(gray)
        flat = pose.flatten()
        samples.append(
            {
                "frame_index": processed,
                "x": float(flat[0]),
                "y": float(flat[1]),
                "z": float(flat[2]),
                "confidence": vo.confidence,
                "tracking": vo.tracking_state,
            }
        )
        tracking_states.append(vo.tracking_state)
        processed += 1
        frame_idx += 1

        if max_frames is not None and processed >= max_frames:
            break

    cap.release()
    elapsed = time.perf_counter() - t0

    return {
        "samples": samples,
        "tracking_states": tracking_states,
        "video_meta": {
            "total_frames": total_frames,
            "processed_frames": processed,
            "fps": fps,
            "width": width,
            "height": height,
            "elapsed_s": elapsed,
            "processing_fps": processed / elapsed if elapsed > 0 else 0.0,
        },
        "profile_id": profile_id,
        "profile_name": profile.get("name", profile_id),
    }


def tracking_summary(states: list[str]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for state in states:
        summary[state] = summary.get(state, 0) + 1
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run VO on video and evaluate trajectory.")
    parser.add_argument(
        "--video",
        type=Path,
        default=REPO_ROOT / "Datasets/vicon_room1/V1_01_easy.mp4",
    )
    parser.add_argument(
        "--sequence",
        default="V1_01_easy",
        help="EuRoC sequence id for GT evaluation",
    )
    parser.add_argument(
        "--profile",
        default="euroc_default",
        help="VO config profile id (euroc_default or dataset)",
    )
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--skip", type=int, default=1, help="Process every Nth frame")
    parser.add_argument(
        "--tum-out",
        type=Path,
        default=None,
        help="Write scaled TUM trajectory to this path",
    )
    parser.add_argument(
        "--plot",
        type=Path,
        default=REPO_ROOT / "thesis/images/vo-eval-V1_01_easy.png",
    )
    args = parser.parse_args()

    if not args.video.is_file():
        print(f"Error: video not found: {args.video}", file=sys.stderr)
        return 1

    print(f"Video: {args.video}")
    print(f"Profile: {args.profile}")
    print(f"EuRoC sequence: {args.sequence}")
    print("Running VO...")

    run = run_vo_on_video(args.video, args.profile, args.max_frames, args.skip)
    meta = run["video_meta"]
    print(
        f"Processed {meta['processed_frames']} frames "
        f"({meta['width']}x{meta['height']}, {meta['fps']:.1f} fps source) "
        f"in {meta['elapsed_s']:.1f}s ({meta['processing_fps']:.1f} fps)"
    )

    metrics = evaluate_against_euroc(run["samples"], args.sequence)
    track = tracking_summary(run["tracking_states"])
    confidences = [s.get("confidence", 0.0) for s in run["samples"]]

    print(f"\nProfile used: {run['profile_name']}")
    print("\n=== Tracking quality ===")
    for state, count in sorted(track.items()):
        pct = 100.0 * count / len(run["tracking_states"])
        print(f"  {state:12s}: {count:5d} ({pct:5.1f}%)")
    if confidences:
        print(
            f"  confidence  : mean={np.mean(confidences):.3f}, "
            f"min={np.min(confidences):.3f}, max={np.max(confidences):.3f}"
        )

    print("\n=== Trajectory (Sim3-aligned vs ground truth) ===")
    print(f"  Samples compared     : {metrics['n_samples']}")
    print(f"  Global scale (s)     : {metrics['global_scale']:.4f}")
    print(f"  GT path length       : {metrics['gt_path_length_m']:.3f} m")
    print(f"  Est. path (raw)      : {metrics['est_path_length_raw']:.3f} (VO units)")
    print(f"  Est. path (scaled)   : {metrics['est_path_length_scaled_m']:.3f} m")
    print(f"  ATE RMSE             : {metrics['ate_rmse_m']:.4f} m")
    print(
        f"  ATE mean / median    : {metrics['ate_mean_m']:.4f} / "
        f"{metrics['ate_median_m']:.4f} m"
    )
    print(f"  ATE max              : {metrics['ate_max_m']:.4f} m")
    print(
        f"  End-point error      : {metrics['end_error_m']:.4f} m "
        f"({metrics['drift_pct']:.2f}% of path)"
    )

    if args.tum_out:
        args.tum_out.parent.mkdir(parents=True, exist_ok=True)
        args.tum_out.write_text(metrics["tum_scaled"], encoding="utf-8")
        print(f"\nScaled TUM saved: {args.tum_out}")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        gt = np.asarray(metrics["ground_truth_positions"])
        est = np.asarray(metrics["scaled_positions"])
        raw = np.asarray([[s["x"], s["y"], s["z"]] for s in run["samples"]])
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        axes[0].plot(gt[:, 0], gt[:, 1], "g-", label="Ground truth", linewidth=2)
        axes[0].plot(est[:, 0], est[:, 1], "b--", label="VO (Sim3-scaled)", linewidth=1.5)
        axes[0].set_xlabel("X [m]")
        axes[0].set_ylabel("Y [m]")
        axes[0].set_title("Top-down (X–Y), meters after Sim(3) alignment")
        axes[0].legend()
        axes[0].axis("equal")
        axes[0].grid(True, alpha=0.3)

        s = metrics["global_scale"]
        fig.suptitle(
            f"{args.sequence} — profile: {run['profile_name']}\n"
            f"Global scale s = {s:.4f} | GT path {metrics['gt_path_length_m']:.1f} m | "
            f"VO scaled {metrics['est_path_length_scaled_m']:.1f} m",
            fontsize=11,
        )

        axes[1].plot(raw[:, 0], raw[:, 2], "r-", label="VO raw")
        axes[1].set_xlabel("X [VO units]")
        axes[1].set_ylabel("Z [VO units]")
        axes[1].set_title("Raw VO trajectory (scale-ambiguous)")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        fig.tight_layout()
        args.plot.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.plot, dpi=150)
        plt.close(fig)
        print(f"Plot saved: {args.plot}")
    except ImportError:
        print("\n(matplotlib not installed — skipping plot)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
