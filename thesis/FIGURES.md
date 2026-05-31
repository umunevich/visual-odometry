# Інструкція: рисунки для курсової роботи

Збережіть файли в каталозі `thesis/images/` з **точними іменами** нижче.
Формат: **PNG** або **PDF**, роздільність не менше **1200 px** по ширині для скріншотів.

Після додання файлів:
```bash
cd thesis
xelatex kursova.tex
xelatex kursova.tex
```

---

## Рисунок 1 — `fig-01-pinhole.png`

**Де в тексті:** розділ 1, п. «Пін-hole модель камери»  
**Підпис у PDF:** «Pin-hole модель камери та система координат OpenCV»

**Що намалювати:**
- Зліва: 3D-точка **P(X, Y, Z)** у світовій системі.
- Центр проєкції (оптичний центр камери) — маленька точка **O**.
- Площина зображення (прямокутник) праворуч від O, перпендикулярна оптичній осі **Z**.
- Промінь від **P** через **O** до точки **p(u, v)** на площині зображення.
- Підписати осі OpenCV біля камери: **X** — вправо, **Y** — вниз, **Z** — углиб сцени (стрілки).
- Опційно: позначити **f** (фокусну відстань) між O і площиною; **cu, cv** — головний пункт на зображенні.

**Інструменти:** draw.io, Excalidraw, PowerPoint, TikZ.

---

## Рисунок 2 — `fig-02-optical-flow.png`

**Де в тексті:** розділ 1, п. «Детекція та відстеження ознак»  
**Підпис:** «Відстеження ознак методом Lucas–Kanade між двома кадрами»

**Скрипт:** `scripts/generate_fig_02_optical_flow.py`

```bash
pip install matplotlib opencv-python-headless numpy
python3 scripts/generate_fig_02_optical_flow.py
# інші параметри:
python3 scripts/generate_fig_02_optical_flow.py --index 100 --gap 5
python3 scripts/generate_fig_02_optical_flow.py -i Datasets/calibration_datasets/cam_checkerboard/cam_checkerboard/mav0/cam0/data
```

Скрипт автоматично підбирає пару кадрів EuRoC з помірним рухом і частиною відхилених треків (forward–backward). Зелені точки — ознаки на кадрі t−1, сині — відстежені, червоні — відхилені.

---

## Рисунок 3 — `fig-03-architecture.png`

**Де в тексті:** розділ 2, п. «Загальна архітектура»  
**Підпис:** «Логічна архітектура системи»

**Що намалювати (блок-схема, два великі блоки):**

**Блок «Frontend (Angular)»:**
- Webcam / Video file → Frame capture → Base64 JPEG
- Camera profile selector → WebSocket client
- Plotly 3D trajectory ← координати (x, y, z)

**Блок «Backend (FastAPI)»:**
- WebSocket `/ws/vo-stream?config_id=...`
- Decode frame → Visual Odometry (vo.py)
- YAML profiles ← REST `/api/configs/calibrate`

**Стрілки між блоками:** WebSocket (кадри ↓, JSON ↑).

**Інструменти:** Mermaid → PNG (https://mermaid.live), draw.io. Готова схема є в `ABOUT.md`.

---

## Рисунок 4 — `fig-04-vo-pipeline.png`

**Де в тексті:** розділ 3, п. «Конвеєр обробки кадру»  
**Підпис:** «Блок-схема конвеєра візуальної одометрії»

**Що намалювати (вертикальна flowchart):**
1. Вхідний кадр (grayscale)
2. Масштабування K + undistort
3. Bootstrap / відстеження (LK optical flow + forward–backward)
4. Розгалуження: **Essential matrix + RANSAC** | fallback: **Affine partial 2D**
5. Оцінка масштабу кроку
6. Інтеграція пози (R, t)
7. Поповнення ознак + keyframe refresh
8. Pose smoother (EMA)
9. Вихід: x, y, z, confidence, tracking

**Стиль:** прямокутники, стрілки вниз, ромб біля п.4 для умови fallback.

---

## Рисунок 5 — `fig-05-ui.png`

**Де в тексті:** розділ 3, п. «Frontend та розгортання»  
**Підпис:** «Головний інтерфейс системи (вкладка Stream)»

**Що зняти на скріншоті:**
- Браузер на `http://localhost:4200`
- Вкладка **Stream** (або From file)
- Видимі елементи: вибір **камери**, dropdown **профілю калібрування**, кнопка **Start VO!**
- Якщо можливо — відкритий workspace з **3D-графіком Plotly** (траєкторія)

**Поради:** прибрати зайві вкладки браузера; режим світлої теми; PNG без стиснення.

---

## Рисунок 6 — `fig-06-calibration.png`

**Де в тексті:** розділ 4, п. «Результати калібрування»  
**Підпис:** «Детекція внутрішніх кутів шахової дошки 6×7 (EuRoC cam_checkerboard)»

**Скрипт:** `scripts/generate_fig_06_calibration.py`

```bash
python3 scripts/generate_fig_06_calibration.py
python3 scripts/generate_fig_06_calibration.py --start-index 500
```

Шукає перший кадр із детектованою дошкою **6×7** у EuRoC `cam_checkerboard/cam0/data` і зберігає результат з `drawChessboardCorners`.

---

## Рисунок 7 — `fig-07-trajectory.png`

**Де в тексті:** розділ 4, п. «Оцінювання VO»  
**Підпис:** «Тривимірна траєкторія, побудована системою VO (Plotly scatter3d)»

**Що зняти:**
- Workspace після сеансу VO (відео EuRoC або webcam).
- 3D-графік з лінією/точками траєкторії.
- Підписи осей: **X (Right), Y (Down), Z (Forward)** — як у системі.
- Бажано: видно поле tracking = ok або confidence.

**Порада:** прогнати коротке відео EuRoC з профілем `dataset.yaml` через From file.
