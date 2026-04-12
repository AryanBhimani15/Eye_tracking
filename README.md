# Eye Tracking Consumer Attention Analysis

## Overview

This project is a **computer vision–based eye tracking system** designed to analyze where users focus their visual attention when viewing an advertisement, website layout, or product design.

The system detects eye landmarks from a camera feed, estimates the user's gaze position, records gaze coordinates over time, and generates a **heatmap visualization** showing which areas of the design receive the most attention.

This type of analysis is widely used in **UX research, marketing analytics, and user interface optimization**.

---

# Project Objective

The main goal of this project is to build a **low-cost eye tracking system** using a Raspberry Pi and computer vision techniques to study **consumer attention patterns**.

The system identifies:

* Where users look first
* Which areas attract the most visual attention
* Which parts of a design are ignored

The final output is a **visual heatmap** representing user focus.

---

# Features

* Real-time eye landmark detection
* Gaze position estimation
* Continuous gaze coordinate logging
* Attention heatmap generation
* Heatmap overlay on advertisement or design image
* Works with Raspberry Pi camera, webcam, or iPhone Continuity Camera

---

# System Architecture

Camera Input
↓
Face Detection (MediaPipe)
↓
Eye Landmark Detection
↓
Gaze Estimation
↓
Gaze Coordinate Logging
↓
Heatmap Generation
↓
Overlay Heatmap on Advertisement

---

# Tech Stack

### Programming Language

Python

### Computer Vision

OpenCV

### Facial Landmark Detection

MediaPipe Face Mesh

### Data Processing

NumPy

### Data Visualization

Matplotlib
Seaborn

### Development Environment

Visual Studio Code
macOS Terminal

---

# Hardware Requirements

* Raspberry Pi 4 (recommended)
* Raspberry Pi Camera Module or USB webcam
* Display screen
* Optional: iPhone camera using Continuity Camera (for development)

---

# Software Requirements

Install dependencies using pip:

```
pip install opencv-python mediapipe numpy matplotlib seaborn
```

---

# Project Setup

1. Clone or download the repository

2. Navigate to the project directory

```
cd eye_tracking_project
```

3. Install dependencies

```
pip install opencv-python mediapipe numpy matplotlib seaborn
```

4. Run the program

```
python eye_tracking_ad_heatmap.py
```

---

# How It Works

1. The camera captures the user's face in real time.

2. MediaPipe Face Mesh detects **468 facial landmarks**, including eye positions.

3. Eye corner landmarks are used to estimate the user's **gaze direction**.

4. The system records gaze coordinates for every frame.

5. After tracking ends, the recorded points are analyzed using **Kernel Density Estimation (KDE)**.

6. A heatmap is generated showing areas with the highest visual attention.

---

# Example Use Cases

This system can be used in:

* UX/UI design testing
* Advertisement effectiveness studies
* Website layout optimization
* Product packaging evaluation
* Marketing research

---

# Limitations

* Approximate gaze estimation (not as precise as professional eye trackers)
* Accuracy affected by lighting conditions
* Head movement may reduce tracking stability
* Requires calibration for higher precision

---

# Future Improvements

* Calibration system for more accurate gaze mapping
* Multi-user aggregated heatmaps
* Fixation detection (first object the user looks at)
* Attention percentage analysis for specific design elements
* Machine learning based gaze estimation

---

# Author

Aryan Bhimani

Project: Eye Tracking Consumer Attention Analysis
Field: Computer Vision / UX Analytics
