"""
CREATE THESE __init__.py FILES IN YOUR PROJECT

Save these in the appropriate folders:
"""

# ==========================================
# data/__init__.py
# ==========================================
"""
Data Package - ECG Simulation and Logging
"""

# ==========================================
# fpga_interface/__init__.py
# ==========================================
"""
FPGA Interface Package - Hardware Abstraction Layer
"""

from .fpga_stream import FPGAInterface

__all__ = ['FPGAInterface']


# ==========================================
# signal_processing/__init__.py
# ==========================================
"""
Signal Processing Package - Feature Extraction
"""

from .features import SignalProcessor

__all__ = ['SignalProcessor']


# ==========================================
# rl_engine/__init__.py
# ==========================================
"""
Reinforcement Learning Engine Package
"""

from .q_learning import AdaptiveRLAgent

__all__ = ['AdaptiveRLAgent']


# ==========================================
# decision_engine/__init__.py
# ==========================================
"""
Decision Engine Package - Explainable AI
"""

from .explainable_ai import ExplainableDecisionEngine, AlertLevel

__all__ = ['ExplainableDecisionEngine', 'AlertLevel']


# ==========================================
# utils/__init__.py
# ==========================================
"""
Utils Package - Helper Modules
"""

from .adaptive_controller import AdaptiveController
from .logger import DataLogger, ReplayManager

__all__ = ['AdaptiveController', 'DataLogger', 'ReplayManager']


# ==========================================
# dashboard/__init__.py
# ==========================================
"""
Dashboard Package - Web Interface
"""