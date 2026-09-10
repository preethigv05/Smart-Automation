# Smart Resource Intelligence & Automation Platform
### AICTE Smart India Hackathon (SIH) 2026 &bull; Theme: Smart Automation

> **An Autonomous, Closed-Loop Resource Optimization & Intelligence System** that continuously analyzes multi-source campus telemetry, detects anomalies and wastage via local statistical machine learning, and executes real-time smart automation rules to conserve power, water, network bandwidth, and compute infrastructure.

---

## 1. Problem Statement
Modern institutional campuses, enterprise facilities, and smart cities face rampant resource wastage:
* **Energy Inefficiency:** Unoccupied laboratories and seminar halls continue to consume high baseline power ("ghost loads").
* **Undetected Water Leakage:** Nocturnal pipe ruptures or faulty fixtures run unchecked for hours or days, wasting thousands of liters of treated water.
* **Network & Compute Bottlenecks:** Bandwidth-heavy non-essential traffic starves critical academic servers, while underutilized compute nodes idle at high power.
* **Siloed Manual Systems:** Most facilities rely on disparate meters and delayed monthly utility bills rather than continuous, real-time autonomous intelligence.

---

## 2. Proposed Solution
The **Smart Resource Intelligence & Automation Platform** delivers an end-to-end, edge-ready, closed-loop software solution that unifies monitoring, analysis, decision-making, and execution:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  MULTI-SOURCE   │       │  LOCAL STAT-ML  │       │  AI INSIGHT     │
│ TELEMETRY INPUT ├──────►│ ANOMALY ENGINE  ├──────►│ & DIAGNOSTIC    │
│ (IoT/CSV/PIR)   │       │ (Z-Score & IQR) │       │ ENGINE          │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                             │
┌─────────────────┐       ┌─────────────────┐                │
│ EFFICIENCY GAIN │       │ CLOSED-LOOP     │                ▼
│ & AUDIT REPORT  │◄──────┤ SMART ACTUATORS │◄──────┌─────────────────┐
│ (Score: 0-100)  │       │ (Shed/Cutoff)   │       │ SMART AUTOMATION│
└─────────────────┘       └─────────────────┘       │ RULES ENGINE    │
                                                    └─────────────────┘
```

---

## 3. Key Features
* **Executive Smart Dashboard:** High-impact KPI scorecard, interactive circular Resource Efficiency Score gauge (0–100), real-time asset utilization bars, and live anomaly streams.
* **Full CRUD Resource Management:** Comprehensive catalog for Electricity, Water, Computing Labs, Classrooms, and Network Bandwidth with live capacity tracking.
* **Multi-Source Data Ingestion:** Integrated support for manual telemetry entry, batch CSV dataset ingestion, and an autonomous Virtual IoT Sensor Simulator.
* **Autonomous AI Insight Engine:** Gaussian Z-Score anomaly detection ($\pm 2.5\sigma$), non-parametric Interquartile Range (IQR) outlier screening, and zero-occupancy ghost load correlation.
* **Closed-Loop Smart Automation Engine:** Real-time rule evaluation (IF-THEN triggers) with simulated actuators that clamp runaway consumption and log actions in an immutable SQLite audit trail.
* **Predictive Analytics & Forecasting:** Time-series regression with 24-hour diurnal seasonal decomposition and 95% Gaussian confidence intervals.
* **Incident Alert Center:** Multi-tier severity triage (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) with one-click resolution tools.
* **Actionable Recommendation Center:** Quantified ROI advisories with one-click "Apply Optimization" workflows.
* **Executive Compliance Reporting:** One-click CSV audit export and print-ready executive compliance sheets.
* **⚡ 1-Click Judge Demo Mode:** Automated 4-step pipeline demonstration specifically engineered for hackathon evaluations.

---

## 4. System Architecture & Technology Stack

### Tech Stack
| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons | Responsive, ultra-fast, zero-build dependency |
| **Data Visualization** | Chart.js 4.4 | Hardware-accelerated canvas charts for gauges, lines, and bars |
| **Backend** | Python 3.14 / Flask 3.1 | Lightweight, high-throughput RESTful micro-framework |
| **Local Machine Learning**| NumPy, SciPy, Scikit-Learn | Robust statistical inference without paid cloud API dependencies |
| **Database** | SQLite 3 (WAL mode enabled) | Zero-configuration, ACID-compliant local embedded relational store |
| **Authentication** | Secure Session Cookies & SHA-256 | Role-based access control (Admin / Evaluator) |

---

## 5. AI & Statistical Intelligence Methodology

### 1. Gaussian Z-Score Anomaly Detection
Calculates the normalized standard score of real-time telemetry $x$ against a rolling 72-reading baseline ($\mu, \sigma$):
$$Z = \frac{x - \mu}{\sigma}$$
* If $|Z| \ge 3.5$: Classified as **`CRITICAL`** anomaly.
* If $2.8 \le |Z| < 3.5$: Classified as **`HIGH`** anomaly.
* If $2.2 \le |Z| < 2.8$: Classified as **`MEDIUM`** anomaly.

### 2. Non-Parametric Interquartile Range (IQR)
Protects against skewed non-Gaussian distributions:
$$IQR = Q_3 - Q_1$$
$$\text{Outlier Bounds} = [Q_1 - 1.5 \times IQR, \quad Q_3 + 1.5 \times IQR]$$

### 3. Ghost Load Correlation
Identifies energy wastage by evaluating multi-modal sensor inputs:
$$\text{Wastage Flag} = (\text{Occupancy}_{PIR} == 0) \land (\text{Usage} > 0.25 \times \text{Capacity})$$

### 4. Predictive Time-Series Forecasting
Combines hour-of-day seasonal harmonics with linear autoregressive drift:
$$\hat{y}(t + h) = \bar{y}_{\text{hour}(t+h)} + \beta \cdot h$$
With 95% confidence bands computed as $\pm 1.96 \times \sigma_{\text{baseline}} \times (1 + 0.02h)$.

### 5. Holistic Resource Efficiency Score (0–100)
A composite index reflecting facility health:
$$\text{Score} = \text{Utilization Health (40)} + \text{Anomaly Safety (25)} + \text{Wastage Mitigation (20)} + \text{Automation Bonus (15)}$$

---

## 6. Smart Automation Rules

| Rule Identifier | Target Resource | Trigger Condition | Automated Actuation Executed |
| :--- | :--- | :--- | :--- |
| **Peak Demand Load-Shedding** | Electricity | Usage $> 85\%$ of Capacity | Dims non-critical perimeter circuits & modulates chiller stage |
| **Zero-Occupancy Ghost Cutoff** | Computing / Labs | Occupancy $== 0$ AND Usage $> 25\%$ | Dispatches Wake-on-LAN standby, clamping PCs to Eco-Sleep (0.8W) |
| **Surge Leakage Emergency Cutoff**| Water | Flow $> 75$ L/min OR $Z > 2.8\sigma$ | Triggers virtual solenoid isolation valve on Sub-manifold B |
| **Dynamic QoS Bandwidth Shaper** | Network | Bandwidth $> 90\%$ of Cap | Enforces QoS queue prioritizing LMS & video conferencing |
| **Underutilized Node Consolidator**| Computing | 3-Day Average Usage $< 20\%$ | Reallocates active containers and suspends redundant server blades |

---

## 7. Database Design
The embedded SQLite database schema comprises 9 relational tables:
* `users`: Authentication credentials and role privileges.
* `resources`: Asset inventory, category, rated capacity, unit, current usage, and location.
* `readings`: High-resolution time-series sensor telemetry indexed by resource and timestamp.
* `insights`: AI-generated diagnostics, severity rankings, and recommendations.
* `alerts`: Real-time incident registry with active/resolved status flags.
* `automation_rules`: Configurable condition-action rules and toggle switches.
* `automation_actions`: Immutable audit log recording triggers, executed actions, and timestamps.
* `recommendations`: Actionable operational advisories with quantified savings.
* `system_settings`: Real-time thresholds for peak limits, timeouts, and Z-score sensitivity.

---

## 8. REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/dashboard` | Aggregated KPIs, circular efficiency score, and recent feeds |
| `GET / POST` | `/api/resources` | List all resources or register a new asset |
| `GET / PUT / DELETE` | `/api/resources/<id>` | Fetch, update, or remove a monitored asset |
| `GET / POST` | `/api/readings` | Query historical telemetry or log a new sensor reading |
| `POST` | `/api/readings/upload-csv` | Ingest batch CSV telemetry spreadsheets |
| `GET` | `/api/insights` | Retrieve AI insights with severity and category filtering |
| `POST` | `/api/insights/analyze` | Trigger an on-demand statistical ML diagnostic scan |
| `GET` | `/api/automation` | List automation rules and execution audit logs |
| `PUT` | `/api/automation/rules/<id>` | Toggle autonomous rule states |
| `POST` | `/api/automation/run` | Evaluate rules and execute simulated actuations |
| `GET` | `/api/analytics` | Fetch historical vs 24h/48h forecasted time-series |
| `GET` | `/api/alerts` | Filter incidents by severity (`CRITICAL`, `HIGH`, `MEDIUM`) |
| `PUT` | `/api/alerts/<id>/resolve`| Mark an active incident as resolved |
| `POST` | `/api/alerts/resolve-all` | Resolve all active incidents simultaneously |
| `GET` | `/api/recommendations` | List optimization advisories |
| `PUT` | `/api/recommendations/<id>/apply` | Apply an optimization and log automated mitigation |
| `POST` | `/api/simulate` | Stream realistic sensor fluctuations or inject test spikes |
| `POST` | `/api/demo-mode` | Execute the 1-Click Judge Demonstration Pipeline |
| `POST` | `/api/reports/generate` | Generate structured audit scorecard |
| `GET` | `/api/reports/download-csv` | Download complete audit data in CSV format |
| `GET / POST` | `/api/settings` | Query or update global system thresholds |
| `POST` | `/api/reset-database` | Reset database to pristine demonstration seed data |

---

## 9. Installation & Setup

### Prerequisites
* Python 3.10+ (Tested on Python 3.14)
* Modern web browser (Chrome, Edge, Firefox, Safari)

### Step 1: Navigate to Project Folder
```bash
cd "C:\Users\preet\OneDrive\Documents\Desktop\AI_Smart_Automation"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Initialize Database & Seed Sample Data
```bash
python database.py
```

### Step 4: Run the Flask Server
```bash
python app.py
```

### Step 5: Access the Web Application
Open your web browser and navigate to:
**`http://127.0.0.1:5000`**

### Default Login Credentials
* **Username:** `admin`
* **Password:** `admin123`

---

## 10. Hackathon Judge Demonstration Script

Follow this 2-minute walkthrough to showcase the platform's closed-loop capabilities to SIH evaluators:

1. **Login & Dashboard Overview:**
   * Log in using `admin` / `admin123`.
   * Point out the **Efficiency Score Gauge (0–100)**, the **Asset Utilization Bars**, and the **Active Anomalies Counter**.
2. **Execute the 1-Click Demo Mode:**
   * Click the glowing red **"⚡ DEMO MODE (JUDGES)"** button in the top navigation bar.
   * Watch the live 4-step modal execute in real-time:
     * **Step 1:** Injects a massive midnight water leak and ghost power load.
     * **Step 2:** AI Engine runs Gaussian Z-score detection and flags a $3.4\sigma$ deviation.
     * **Step 3:** Automation Engine fires virtual solenoid valve isolation and eco-sleep clamps.
     * **Step 4:** Efficiency score recalculates dynamically with quantified savings.
3. **Inspect the AI Insight Engine (`/insights`):**
   * Show judges the categorized insights with **AI Powered** tags and statistical Z-score justifications.
4. **Demonstrate Closed-Loop Automation (`/automation`):**
   * Show the configured rules and point out the timestamped **Autonomous Execution Audit Trail**.
5. **Review Predictive Analytics (`/analytics`):**
   * Showcase the 24-hour forecasted consumption curve with its 95% confidence intervals.
6. **Export Audit Compliance (`/reports`):**
   * Click **"Download CSV Audit File"** or **"Print / Save PDF"** to demonstrate enterprise audit readiness.

---

## 11. Scalability, Impact & Future Enhancements

### Scalability
* **Hardware Interfacing:** The virtual actuator layer is engineered to bind seamlessly with physical Modbus, BACnet, and MQTT IoT brokers.
* **Distributed Cloud Ready:** Designed for containerization via Docker and Kubernetes with PostgreSQL / TimescaleDB support.

### Environmental & Economic Impact
* **$15\% - 28\%$ Energy Reduction:** Immediate mitigation of after-hours ghost loads.
* **Zero Water Wastage:** Rapid sub-manifold solenoid isolation prevents thousands of liters of clean water loss.
* **Extended Hardware Lifespan:** Intelligent thermal and power sleep states reduce equipment wear.

### Future Scope
* LoRaWAN long-range edge meter integration.
* Reinforcement Learning (Q-learning) for dynamic peak-tariff electricity arbitration.
* Native mobile push notifications via Apple APNs / Google FCM.

---

**Developed for AICTE Smart India Hackathon 2026 &bull; Theme: Smart Automation**
#   s m a r t - r e s o u r c e - i n t e l l i g e n c e - p l a t f o r m  
 