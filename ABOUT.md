# About the Project

## Real-Time Monocular Visual Odometry System for UAVs

This project is a high-performance web-based software suite designed for autonomous **Unmanned Aerial Vehicle (UAV)** navigation in GPS-denied environments. By utilizing state-of-the-art computer vision algorithms, the system estimates the 3D trajectory of a drone in real time using a **single (monocular) video stream** as its primary input sensor.

---

## 🚀 Key Features

* **Feature-Based Optical Flow:** Tracks distinct spatial landmarks across frames using the Lucas-Kanade method, eliminating the need for expensive per-frame descriptor matching.
* **Keyframe Management:** Implements an anchor-based frame system to dramatically reduce cumulative tracking error and pose drift over long trajectories.
* **Robust Pose Estimation:** Recovers relative rotation ($R$) and translation ($t$) via Epipolar Geometry (Essential Matrix computation) combined with RANSAC outlier rejection to filter out visual noise.
* **Asynchronous Client-Server Architecture:** Heavy mathematical computations are fully decoupled from the user interface, running in isolated OS threads on the backend.
* **Real-Time 3D Visualization:** Streamed coordinates are rendered dynamically into an interactive 3D trajectory graph in the browser at a fluid 60 FPS.

---

## 🛠 Technical Architecture & Tech Stack

The system is built on top of a highly modular, containerized client-server model communicating via a full-duplex persistent **WebSocket** connection.

### Backend (Perception & Math Engine)
* **Python & OpenCV:** Handles image preprocessing, Shi-Tomasi corner detection, and geometric pose recovery.
* **FastAPI:** Manages asynchronous WebSocket connections via an event loop, utilizing `asyncio.to_thread` for CPU-bound computer vision tasks to ensure non-blocking network I/O.
* **NumPy:** Maximizes performance for vector matrix operations and spatial coordinate updates.

### Frontend (Control & Visualization)
* **Angular & TypeScript:** Provides a responsive Single Page Application (SPA) dashboard built with a decoupled architecture (View components vs Reactive Stream Services).
* **Angular Signals:** Manages application state and system readiness smoothly, ensuring optimal change detection.
* **Plotly.js:** Utilizes GPU-accelerated WebGL layers (`scatter3d`) to append trajectory points efficiently without heavy DOM re-renders.

### Infrastructure & DevOps
* **Docker & Docker Compose:** Standardizes environments for multi-stage Angular static builds (Nginx) and Python services.
* **Cloudflare Tunnels:** Exposes local server instances safely to the public web via secure outbound encrypted tunnels.

---

## 🔬 Mathematical Overview

The core localization pipeline processes 2D pixels and converts them to 3D spatial points based on the **Pinhole Camera Model**. The projective transformation matrix $K$ maps the world coordinates into pixels:

$$K = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}$$

For every incoming frame, the optical flow engine tracks pixels relative to the active **Keyframe**. The geometric constraints between two camera views are constrained by the **Essential Matrix ($E$)**, processed using the formula:

$$E = [t]_{\times} R$$

The relative motion is then extracted through Singular Value Decomposition (SVD) of $E$, scaling stable steps linearly, and continuously integrating them into the global UAV pose trajectory matrix.

---

## 📂 Testing & Validation

The system has been strictly evaluated using the **EuRoC MAV Dataset** (specifically sequences recorded inside industrial halls using Micro Aerial Vehicles). Testing shows high fidelity in replicating ground-truth flight path proportions, loop contours, and sharp turns, proving the viability of using lightweight monocular setups over heavy LiDAR hardware.