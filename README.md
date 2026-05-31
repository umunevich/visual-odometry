# Monocular Visual Odometry

Real-time **monocular visual odometry** web application: estimate camera motion from a live webcam or video file and visualize the 3D trajectory in the browser.

**Backend:** Python, FastAPI, OpenCV  
**Frontend:** Angular 21, Plotly.js

For a full description of the pipeline, VO algorithm, camera calibration, and EuRoC dataset, see **[ABOUT.md](./ABOUT.md)**.

---

## Prerequisites

| Tool | Version (tested) |
|------|------------------|
| **Docker & Docker Compose** | Optional, for containerized run |
| **Python** | 3.11+ |
| **Node.js** | 20+ |
| **npm** | 11+ |

---

## Quick start (Docker)

From the repository root:

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:4200 |
| **Backend API** | http://localhost:8000 |
| **API docs** | http://localhost:8000/docs |

Open the frontend, choose **Stream** or **From file**, select a **camera calibration profile**, then click **Start VO!**.

To stop:

```bash
docker compose down
```

### Optional: Cloudflare Tunnel

Copy `.env.example` to `.env` and set `CLOUDFLARE_TUNNEL_TOKEN` if you want public access via Cloudflare. The `cloudflared` service starts automatically with `docker compose up`.

---

## Local development (without Docker)

Run the backend and frontend in separate terminals.

### 1. Backend

```bash
cd vo-uav
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at http://localhost:8000.

### 2. Frontend

```bash
cd vo-frontend
npm install
npm start
```

Frontend runs at http://localhost:4200 and expects the backend at `localhost:8000` (see `vo-frontend/src/environments/environment.ts`).

---

## Usage overview

1. **Calibrate (recommended)** — On the Stream or From file tab, click **+** next to the camera profile dropdown, upload chessboard photos, and save a profile. Details: [Camera Calibration](./ABOUT.md#camera-calibration) in ABOUT.md.

2. **Stream mode** — Select a webcam and calibration profile → **Start VO!** → live 3D trajectory.

3. **From file mode** — Upload a video (e.g. EuRoC `V1_01_easy.mp4`) → select profile → **Start VO!** → optionally **Compute global scale** against EuRoC ground truth and **Export TUM**.

Default profile **EuRoC MAV (default)** uses intrinsics from the [EuRoC dataset](./ABOUT.md#euroc-mav-dataset); calibrate your own camera for best results with a webcam.

---

## Project structure

```text
Coursework/
├── README.md              # This file — how to run
├── ABOUT.md               # Pipeline, algorithm, calibration, dataset
├── docker-compose.yml
├── scripts/
│   ├── make_video.py      # Convert image folders to MP4 for testing
│   └── run_vo_eval.py     # Batch VO run + EuRoC GT evaluation (TUM, ATE, scale)
├── vo-uav/                # FastAPI backend (VO + calibration)
└── vo-frontend/           # Angular SPA
```

---

## Useful commands

```bash
# Convert EuRoC (or other) frame folders to video
python scripts/make_video.py -i path/to/frames/ -o output.mp4

# Run VO on video and evaluate vs EuRoC ground truth (TUM export, global scale s, ATE)
EUROC_DATASETS_PATH=./Datasets python3 scripts/run_vo_eval.py \
  --video Datasets/vicon_room1/V1_01_easy.mp4 \
  --sequence V1_01_easy

# Frontend lint / tests
cd vo-frontend && npm run lint && npm test
```

---

## Documentation

| Document | Contents |
|----------|----------|
| **[ABOUT.md](./ABOUT.md)** | System pipeline, VO algorithm, calibration process, EuRoC dataset, tech stack |
| **http://localhost:8000/docs** | Interactive OpenAPI (Swagger) for backend endpoints |

---

## License & dataset

EuRoC MAV sequences and default camera intrinsics come from ETH Zurich. See citation and download link in [ABOUT.md — EuRoC MAV Dataset](./ABOUT.md#euroc-mav-dataset).
