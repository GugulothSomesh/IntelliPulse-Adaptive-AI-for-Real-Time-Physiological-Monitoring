# ⚡ QUICK START CHEAT SHEET

## One-Page Command Reference

---

## 🚀 FIRST TIME SETUP (5 minutes)

```bash
# 1. Create project folder
mkdir fpga_rl_health_monitor
cd fpga_rl_health_monitor

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# 4. Install packages
pip install -r requirements.txt

# 5. Run automated setup
python setup.py
```

---

## 🎬 RUN THE SYSTEM (Choose One)

### Option 1: Quick Demo (30 seconds)
```bash
python main.py --mode demo --duration 30
```

### Option 2: Web Dashboard (BEST!)
```bash
streamlit run dashboard/app.py
# → Opens browser at http://localhost:8501
# → Click "Initialize" → "Start"
```

### Option 3: Training Mode (5 minutes)
```bash
python main.py --mode training --duration 300
```

### Option 4: Evaluation
```bash
python main.py --mode evaluation --duration 60
```

---

## 🔧 TEST INDIVIDUAL MODULES

```bash
# Test each module independently
python data/ecg_simulator.py
python fpga_interface/fpga_stream.py
python signal_processing/features.py
python rl_engine/q_learning.py
python decision_engine/explainable_ai.py
```

---

## 📊 FILE LOCATIONS

```
├── data/dummy_ecg.csv           ← Sample ECG data
├── data/logs/                   ← All logged data
│   ├── ecg_*.csv               ← Raw sensor data
│   ├── features_*.csv          ← Extracted features
│   ├── decisions_*.csv         ← AI decisions
│   └── rl_actions_*.csv        ← Learning log
├── rl_engine/trained_model.json ← Saved RL model
└── README.md                    ← Full documentation
```

---

## 🐛 TROUBLESHOOTING

### Python not found
```bash
# Check installation
python --version

# Add to PATH (Windows)
setx PATH "%PATH%;C:\Python311"
```

### Module not found
```bash
# Activate environment first!
venv\Scripts\activate

# Reinstall packages
pip install -r requirements.txt
```

### Port already in use
```bash
# Use different port
streamlit run dashboard/app.py --server.port 8502
```

### Permission denied
```bash
# Run as Administrator (Windows)
# Right-click Command Prompt → "Run as Administrator"

# Fix permissions (Linux/Mac)
chmod -R 755 .
```

---

## 🎯 KEY PARAMETERS TO MODIFY

### Learning Rate (rl_engine/q_learning.py)
```python
learning_rate=0.1   # Default
learning_rate=0.2   # Learn faster
learning_rate=0.05  # Learn slower (more stable)
```

### Alert Thresholds (decision_engine/explainable_ai.py)
```python
'hr_max': 100,  # Max heart rate threshold
'hr_min': 50,   # Min heart rate threshold
'hrv_min': 20,  # Min HRV threshold
```

### Simulation States (data/ecg_simulator.py)
```python
state="NORMAL"     # Resting
state="EXERCISE"   # Elevated HR
state="STRESS"     # Elevated HR, low HRV
state="ANOMALY"    # Random variations
```

---

## 📈 VIEW RESULTS

### In Python
```python
import pandas as pd

# Load decisions
df = pd.read_csv('data/logs/decisions_*.csv')
print(df.head())
print(df['level'].value_counts())

# Load features
features = pd.read_csv('data/logs/features_*.csv')
print(features.describe())
```

### In Excel
```
1. Open Excel
2. File → Open
3. Navigate to: data/logs/
4. Open any CSV file
```

---

## 🔄 FPGA INTEGRATION (Future)

### Change data source (fpga_interface/fpga_stream.py)
```python
# BEFORE (dummy data):
fpga = FPGAInterface(source_type='dummy')

# AFTER (real FPGA):
fpga = FPGAInterface(
    source_type='uart',
    port='COM3',      # Your UART port
    baudrate=115200
)
```

---

## 📝 COMMON COMMANDS

```bash
# Start dashboard
streamlit run dashboard/app.py

# Run with specific duration
python main.py --mode demo --duration 60

# Generate new sample data
python data/ecg_simulator.py

# Check installed packages
pip list

# Update a package
pip install --upgrade streamlit

# Deactivate virtual environment
deactivate

# Reactivate virtual environment
venv\Scripts\activate
```

---

## 🎓 PROJECT STRUCTURE

```
fpga_rl_health_monitor/
├── data/                    ← Data and logs
│   ├── ecg_simulator.py    ← ECG data generator
│   └── logs/               ← Session logs
│
├── fpga_interface/         ← Hardware abstraction
│   └── fpga_stream.py      ← FPGA interface
│
├── signal_processing/      ← Feature extraction
│   └── features.py         ← Signal processor
│
├── rl_engine/              ← AI learning
│   └── q_learning.py       ← RL agent
│
├── decision_engine/        ← Decision making
│   └── explainable_ai.py   ← Decision engine
│
├── utils/                  ← Helper modules
│   ├── adaptive_controller.py  ← Control loop
│   └── logger.py           ← Data logging
│
├── dashboard/              ← Web interface
│   └── app.py             ← Streamlit app
│
├── main.py                 ← Main entry point
├── setup.py                ← Automated setup
├── requirements.txt        ← Dependencies
└── README.md              ← Full documentation
```

---

## ✅ SYSTEM STATUS INDICATORS

| Symbol | Meaning |
|--------|---------|
| ✅ | Normal - All good |
| ⚠️ | Warning - Minor issue |
| 🚨 | Alert - Attention needed |
| 🧠 | RL Action - System learning |
| 📊 | Data - Metrics displayed |
| ❤️ | Heart Rate |
| 🎯 | Confidence/Quality |

---

## 🆘 QUICK HELP

**Something not working?**

1. Check README.md
2. Run: `python setup.py`
3. Test modules individually
4. Check logs in `data/logs/`
5. Verify Python version: `python --version`
6. Reinstall packages: `pip install -r requirements.txt`

---

## 📞 RESOURCES

- **Full Documentation**: README.md
- **Step-by-Step Guide**: IMPLEMENTATION_GUIDE.md
- **Module Details**: Each .py file has docstrings
- **Sample Data**: data/dummy_ecg.csv

---

## 🎯 MINIMUM REQUIREMENTS

- Python 3.8+
- 4GB RAM
- 500MB disk space
- Any modern OS (Windows/Mac/Linux)

---

## ⚡ PERFORMANCE

- Sampling Rate: 250 Hz
- Processing Latency: < 10ms
- Loop Time: < 50ms
- Dashboard Update: 1-10 Hz (configurable)

---

**Print this page and keep it handy! 📄**

*Last updated: 2025*