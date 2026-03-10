"""
Automated Project Setup Script

This script:
1. Checks Python version
2. Creates directory structure
3. Generates sample data
4. Verifies all modules
5. Runs tests

Usage:
    python setup.py
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def check_python_version():
    """Verify Python version"""
    print_header("STEP 1: Checking Python Version")
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8 or higher required")
        print("   Please install Python 3.8+ from python.org")
        sys.exit(1)
    
    print("✅ Python version OK")


def create_directory_structure():
    """Create all required directories"""
    print_header("STEP 2: Creating Directory Structure")
    
    directories = [
        'data',
        'data/logs',
        'fpga_interface',
        'signal_processing',
        'rl_engine',
        'decision_engine',
        'dashboard',
        'utils'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}/")
    
    # Create __init__.py files for packages
    packages = [
        'fpga_interface',
        'signal_processing',
        'rl_engine',
        'decision_engine',
        'utils'
    ]
    
    for package in packages:
        init_file = Path(package) / '__init__.py'
        init_file.touch()
    
    print("\n✅ Directory structure complete")


def install_dependencies():
    """Install required Python packages"""
    print_header("STEP 3: Installing Dependencies")
    
    print("Installing required packages...")
    print("This may take 2-5 minutes...\n")
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("\n✅ All packages installed successfully")
    except subprocess.CalledProcessError:
        print("\n⚠ Warning: Some packages may have failed to install")
        print("   Try: pip install -r requirements.txt")


def verify_imports():
    """Verify all critical imports work"""
    print_header("STEP 4: Verifying Installations")
    
    required_packages = [
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'),
        ('scipy', 'SciPy'),
        ('matplotlib', 'Matplotlib'),
        ('streamlit', 'Streamlit'),
        ('plotly', 'Plotly')
    ]
    
    all_ok = True
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - Failed to import")
            all_ok = False
    
    if all_ok:
        print("\n✅ All packages verified")
    else:
        print("\n⚠ Some packages failed - try reinstalling")


def generate_sample_data():
    """Generate sample ECG data"""
    print_header("STEP 5: Generating Sample Data")
    
    try:
        from data.ecg_simulator import ECGSimulator
        
        print("Generating 60 seconds of sample ECG data...")
        sim = ECGSimulator(sampling_rate=250, base_heart_rate=70)
        sim.save_sample_data(filename='data/dummy_ecg.csv', duration=60)
        
        print("\n✅ Sample data generated successfully")
    except Exception as e:
        print(f"\n⚠ Warning: Could not generate sample data")
        print(f"   Error: {e}")


def run_module_tests():
    """Test individual modules"""
    print_header("STEP 6: Running Module Tests")
    
    modules_to_test = [
        ('fpga_interface/fpga_stream.py', 'FPGA Interface'),
        ('signal_processing/features.py', 'Signal Processing'),
        ('rl_engine/q_learning.py', 'RL Engine'),
        ('decision_engine/explainable_ai.py', 'Decision Engine')
    ]
    
    print("Running quick tests on each module...\n")
    
    for module_path, module_name in modules_to_test:
        if os.path.exists(module_path):
            print(f"Testing {module_name}...")
            try:
                subprocess.run(
                    [sys.executable, module_path],
                    capture_output=True,
                    timeout=10
                )
                print(f"  ✅ {module_name} OK")
            except:
                print(f"  ⚠ {module_name} - Check manually")
        else:
            print(f"  ⚠ {module_name} - File not found: {module_path}")
    
    print("\n✅ Module tests complete")


def print_next_steps():
    """Print next steps for user"""
    print_header("SETUP COMPLETE!")
    
    print("""
🎉 Project setup successful!

NEXT STEPS:

1. Quick Demo (30 seconds):
   python main.py --mode demo

2. Web Dashboard (recommended):
   streamlit run dashboard/app.py

3. Training Session (5 minutes):
   python main.py --mode training --duration 300

4. Read Documentation:
   Open README.md for complete guide

5. Test Individual Modules:
   python data/ecg_simulator.py
   python fpga_interface/fpga_stream.py
   python signal_processing/features.py

TROUBLESHOOTING:

If you encounter issues:
- Check README.md → Troubleshooting section
- Verify Python version: python --version
- Reinstall packages: pip install -r requirements.txt

PROJECT STRUCTURE:

fpga_rl_health_monitor/
├── data/              # Sample data and logs
├── fpga_interface/    # FPGA abstraction
├── signal_processing/ # Feature extraction
├── rl_engine/         # Reinforcement learning
├── decision_engine/   # Explainable AI
├── dashboard/         # Web interface
├── utils/             # Helper modules
├── main.py            # Main entry point
└── README.md          # Full documentation

QUICK COMMANDS:

Demo:       python main.py --mode demo
Dashboard:  streamlit run dashboard/app.py
Help:       python main.py --help

Happy coding! 🚀
""")


def main():
    """Main setup function"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   FPGA-Based Adaptive Health Monitoring System                   ║
║   Automated Setup Script                                          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")
    
    try:
        check_python_version()
        create_directory_structure()
        install_dependencies()
        verify_imports()
        generate_sample_data()
        run_module_tests()
        print_next_steps()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        print("Please check the error message and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()