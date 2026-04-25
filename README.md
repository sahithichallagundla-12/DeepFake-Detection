# 🛡️ DeepFake Identity Guard

A lightweight MVP web application for detecting deepfake and manipulated images — built to help protect digital identities, especially for women targeted by non-consensual synthetic imagery.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip or conda

### Installation & Running

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**
   ```bash
   streamlit run app.py
   ```
   The app opens automatically at **http://localhost:8501**

---

## 📁 Project Structure

```
code4her/
│
├── app.py                   # Streamlit main application
├── image_analysis.py        # OpenCV/PIL analysis (ELA, blur, face, synthetic indicators)
├── similarity.py            # ImageHash similarity & stability detection
├── report.py                # Report generation + safety guidance
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 🔍 Detection Techniques

The application uses multiple heuristic-based analysis methods to identify manipulation signals:

| Detection Method         | Technique                                     | What It Identifies                                  |
| ------------------------ | --------------------------------------------- | --------------------------------------------------- |
| **Face Inconsistency**   | Haar cascade + skin-tone YCrCb analysis       | Swapped/blended faces, unusual skin-tone variance   |
| **Pixel Anomaly (ELA)**  | Error Level Analysis via JPEG re-compression  | Spliced or edited regions, inconsistent compression |
| **Blur Artifacts**       | Laplacian variance + JPEG block discontinuity | Seam-hiding blur, over-compression, smoothing       |
| **Synthetic Indicators** | Noise uniformity + histogram smoothness       | GAN-generated images, AI-created content            |
| **Hash Stability**       | Perceptual hash comparison under augmentation | Composited regions, unstable image elements         |

### 🌡️ Innovative Feature – Manipulation Heatmap

Combines Error Level Analysis (ELA) and Laplacian gradient computation into a visual overlay using a color heat map (JET palette). Suspicious regions are highlighted in red, allowing users to instantly identify where potential manipulation occurred in the image.

---

## 📊 Risk Scoring System

The app provides a **0–100% risk score** with actionable guidance:

| Score Range | Risk Level      | Interpretation                                   |
| ----------- | --------------- | ------------------------------------------------ |
| **0–29%**   | 🟢 **Low**      | No strong manipulation signals detected          |
| **30–54%**  | 🟡 **Moderate** | Moderate signals present; further review advised |
| **55–100%** | 🔴 **High**     | Strong indicators of manipulation detected       |

Each result includes tailored **safety guidance** appropriate to the detected risk level.

---

## 📋 Features

✅ **Instant Analysis** – Upload an image and get results within seconds  
✅ **Multi-Method Detection** – Combines 5+ detection techniques for accuracy  
✅ **Visual Heatmap** – See exactly where manipulation is suspected  
✅ **Risk-Based Guidance** – Get actionable next steps based on risk level  
✅ **Detailed Report** – Download a comprehensive analysis report  
✅ **Offline Processing** – Works without sending data to external services

---

## 🛡️ Safety Resources & Support

**Report non-consensual imagery:**

- 🇮🇳 India: [cybercrime.gov.in](https://cybercrime.gov.in) or call **1930**
- 🇺🇸 USA: [ic3.gov](https://ic3.gov) (FBI Internet Crime Complaint Center)
- 🇬🇧 UK: [actionfraud.police.uk](https://actionfraud.police.uk)
- 🌐 Global: [StopNCII.org](https://stopncii.org) – Free hash-based removal tool

**Emotional & Legal Support:**

- 💜 [Cyber Civil Rights Initiative](https://cybercivilrights.org)
- 🌐 [International Women's Media Foundation](https://www.iwmf.org/)

---

## ⚠️ Disclaimer & Limitations

This tool uses **heuristic analysis only** and is **NOT** a replacement for professional digital forensic examination.

**Important notes:**

- Results are indicative and should be treated as a starting point for further investigation
- No single detection method is 100% accurate
- Some legitimate images may trigger alerts due to image compression or editing
- For legal matters, always consult with certified digital forensics experts

---

## 🔧 Technical Stack

- **Framework:** [Streamlit](https://streamlit.io/) – Fast, interactive web app
- **Image Processing:** [OpenCV](https://opencv.org/), [Pillow](https://python-pillow.org/)
- **Hashing:** [imagehash](https://github.com/JohannesBuchner/imagehash) – Perceptual hashing
- **Deployment:** Python 3.8+

---

## 📝 License

This project is built with the intent to protect vulnerable individuals. Use and modify freely for non-commercial, protective purposes.

---

## 🤝 Contributing

This prototype was developed as part of the **Code4Her** initiative to combat digital abuse. Feedback, improvements, and bug reports are welcome.

---

**Built with ❤️ to protect digital identity and dignity.**
# DeepFake-Detection
