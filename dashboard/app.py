"""
FPGA-Based Adaptive Health Monitor with Reinforcement Learning
A research demo showcasing real-time health monitoring with adaptive decision-making
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from collections import deque
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """System configuration parameters"""
    SAMPLING_RATE = 100  # Hz
    WINDOW_SIZE = 500    # Data points to display
    ECG_BASELINE = 0.0
    HEART_RATE_NORMAL = 75  # BPM
    
    # RL Parameters
    LEARNING_RATE = 0.1
    DISCOUNT_FACTOR = 0.95
    EPSILON = 0.1  # Exploration rate
    
    # States: Normal, Elevated, Critical
    STATES = ['Normal', 'Elevated', 'Critical']
    # Actions: Monitor, Alert, Emergency
    ACTIONS = ['Monitor', 'Alert', 'Emergency']
    
    # Thresholds
    HR_ELEVATED = 100  # BPM
    HR_CRITICAL = 120  # BPM

# ============================================================================
# SIGNAL GENERATION
# ============================================================================

class ECGSimulator:
    """Simulates realistic ECG signals with anomalies"""
    
    def __init__(self, sampling_rate=100):
        self.sampling_rate = sampling_rate
        self.time = 0
        self.anomaly_probability = 0.05
        self.current_hr = Config.HEART_RATE_NORMAL
        
    def generate_heartbeat(self, heart_rate):
        """Generate one heartbeat cycle"""
        # Time for one beat (in seconds)
        beat_duration = 60.0 / heart_rate
        samples_per_beat = int(beat_duration * self.sampling_rate)
        
        t = np.linspace(0, beat_duration, samples_per_beat)
        
        # P wave (atrial depolarization)
        p_wave = 0.15 * np.exp(-((t - 0.1) ** 2) / 0.002)
        
        # QRS complex (ventricular depolarization)
        qrs_q = -0.1 * np.exp(-((t - 0.15) ** 2) / 0.0001)
        qrs_r = 1.0 * np.exp(-((t - 0.17) ** 2) / 0.0001)
        qrs_s = -0.2 * np.exp(-((t - 0.19) ** 2) / 0.0001)
        
        # T wave (ventricular repolarization)
        t_wave = 0.3 * np.exp(-((t - 0.35) ** 2) / 0.005)
        
        ecg = p_wave + qrs_q + qrs_r + qrs_s + t_wave
        
        # Add baseline noise
        noise = np.random.normal(0, 0.01, len(ecg))
        ecg += noise
        
        return ecg
    
    def generate_sample(self):
        """Generate next ECG sample with possible anomalies"""
        # Randomly induce anomalies
        if np.random.random() < self.anomaly_probability:
            # Temporary heart rate change
            self.current_hr = np.random.uniform(Config.HEART_RATE_NORMAL - 20, 
                                                Config.HR_CRITICAL + 20)
        else:
            # Gradual return to normal
            self.current_hr = 0.95 * self.current_hr + 0.05 * Config.HEART_RATE_NORMAL
        
        # Generate heartbeat
        heartbeat = self.generate_heartbeat(self.current_hr)
        
        # Return one sample
        self.time += 1.0 / self.sampling_rate
        sample_index = int(self.time * self.sampling_rate) % len(heartbeat)
        
        return heartbeat[sample_index], self.current_hr

# ============================================================================
# FEATURE EXTRACTION
# ============================================================================

class FeatureExtractor:
    """Extract health features from ECG signal"""
    
    def __init__(self, window_size=50):
        self.window_size = window_size
        self.ecg_buffer = deque(maxlen=window_size)
        
    def update(self, ecg_sample):
        """Add new sample and compute features"""
        self.ecg_buffer.append(ecg_sample)
        
        if len(self.ecg_buffer) < self.window_size:
            return None
        
        # Compute features
        ecg_array = np.array(self.ecg_buffer)
        
        features = {
            'mean': np.mean(ecg_array),
            'std': np.std(ecg_array),
            'peak_amplitude': np.max(np.abs(ecg_array)),
            'zero_crossings': np.sum(np.diff(np.sign(ecg_array)) != 0)
        }
        
        return features
    
    def estimate_heart_rate(self, actual_hr):
        """Estimate heart rate from ECG"""
        # In a real system, this would use peak detection
        # For demo, we add some measurement noise
        return actual_hr + np.random.normal(0, 2)

# ============================================================================
# REINFORCEMENT LEARNING AGENT
# ============================================================================

class QLearningAgent:
    """Q-Learning agent for adaptive health monitoring"""
    
    def __init__(self):
        self.q_table = np.zeros((len(Config.STATES), len(Config.ACTIONS)))
        self.learning_rate = Config.LEARNING_RATE
        self.discount_factor = Config.DISCOUNT_FACTOR
        self.epsilon = Config.EPSILON
        
        self.state_history = []
        self.action_history = []
        self.reward_history = []
        
    def get_state_index(self, heart_rate):
        """Map heart rate to state index"""
        if heart_rate < Config.HR_ELEVATED:
            return 0  # Normal
        elif heart_rate < Config.HR_CRITICAL:
            return 1  # Elevated
        else:
            return 2  # Critical
    
    def select_action(self, state_index):
        """Select action using epsilon-greedy policy"""
        if np.random.random() < self.epsilon:
            # Exploration
            action_index = np.random.randint(len(Config.ACTIONS))
        else:
            # Exploitation
            action_index = np.argmax(self.q_table[state_index, :])
        
        return action_index
    
    def calculate_reward(self, state_index, action_index):
        """Calculate reward based on state-action pair"""
        # Reward matrix: correct actions get positive rewards
        reward_matrix = {
            0: [10, -5, -10],   # Normal: Monitor good, Alert/Emergency bad
            1: [-5, 10, -5],    # Elevated: Alert good
            2: [-10, -5, 10]    # Critical: Emergency good
        }
        
        return reward_matrix[state_index][action_index]
    
    def update_q_value(self, state, action, reward, next_state):
        """Update Q-table using Q-learning update rule"""
        current_q = self.q_table[state, action]
        max_next_q = np.max(self.q_table[next_state, :])
        
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state, action] = new_q
    
    def step(self, heart_rate):
        """Execute one RL step"""
        # Get current state
        state = self.get_state_index(heart_rate)
        
        # Select action
        action = self.select_action(state)
        
        # Calculate reward
        reward = self.calculate_reward(state, action)
        
        # Store for visualization
        self.state_history.append(state)
        self.action_history.append(action)
        self.reward_history.append(reward)
        
        # For next update (simplified for demo)
        next_state = state  # Will be updated on next iteration
        self.update_q_value(state, action, reward, next_state)
        
        return {
            'state': Config.STATES[state],
            'action': Config.ACTIONS[action],
            'reward': reward,
            'q_values': self.q_table[state, :].copy()
        }

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.running = False
        st.session_state.iteration = 0
        
        # Data buffers
        st.session_state.ecg_buffer = deque(maxlen=Config.WINDOW_SIZE)
        st.session_state.hr_buffer = deque(maxlen=Config.WINDOW_SIZE)
        st.session_state.time_buffer = deque(maxlen=Config.WINDOW_SIZE)
        
        # Components
        st.session_state.ecg_sim = ECGSimulator()
        st.session_state.feature_extractor = FeatureExtractor()
        st.session_state.rl_agent = QLearningAgent()
        
        # Metrics
        st.session_state.total_rewards = 0
        st.session_state.decisions = []
        st.session_state.anomaly_count = 0
        
        # Current values
        st.session_state.current_hr = Config.HEART_RATE_NORMAL
        st.session_state.current_state = 'Normal'
        st.session_state.current_action = 'Monitor'

# ============================================================================
# MONITORING LOOP
# ============================================================================

def execute_monitoring_step():
    """Execute one monitoring iteration"""
    # Generate ECG sample
    ecg_sample, actual_hr = st.session_state.ecg_sim.generate_sample()
    
    # Update feature extractor
    features = st.session_state.feature_extractor.update(ecg_sample)
    
    if features is not None:
        # Estimate heart rate
        estimated_hr = st.session_state.feature_extractor.estimate_heart_rate(actual_hr)
        
        # RL decision
        rl_result = st.session_state.rl_agent.step(estimated_hr)
        
        # Update buffers
        st.session_state.ecg_buffer.append(ecg_sample)
        st.session_state.hr_buffer.append(estimated_hr)
        st.session_state.time_buffer.append(st.session_state.iteration * 0.01)
        
        # Update metrics
        st.session_state.current_hr = estimated_hr
        st.session_state.current_state = rl_result['state']
        st.session_state.current_action = rl_result['action']
        st.session_state.total_rewards += rl_result['reward']
        
        # Detect anomalies
        if rl_result['state'] in ['Elevated', 'Critical']:
            st.session_state.anomaly_count += 1
        
        # Log decision
        decision_log = {
            'time': st.session_state.iteration * 0.01,
            'hr': estimated_hr,
            'state': rl_result['state'],
            'action': rl_result['action'],
            'reward': rl_result['reward']
        }
        st.session_state.decisions.append(decision_log)
        
        # Keep only recent decisions
        if len(st.session_state.decisions) > 50:
            st.session_state.decisions.pop(0)
    
    st.session_state.iteration += 1

# ============================================================================
# VISUALIZATION
# ============================================================================

def create_ecg_plot():
    """Create real-time ECG plot"""
    if len(st.session_state.ecg_buffer) == 0:
        return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(st.session_state.time_buffer),
        y=list(st.session_state.ecg_buffer),
        mode='lines',
        name='ECG Signal',
        line=dict(color='#00ff00', width=2)
    ))
    
    fig.update_layout(
        title='Real-Time ECG Signal',
        xaxis_title='Time (s)',
        yaxis_title='Amplitude (mV)',
        height=300,
        template='plotly_dark',
        hovermode='x unified'
    )
    
    return fig

def create_heart_rate_plot():
    """Create real-time heart rate plot"""
    if len(st.session_state.hr_buffer) == 0:
        return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(st.session_state.time_buffer),
        y=list(st.session_state.hr_buffer),
        mode='lines',
        name='Heart Rate',
        line=dict(color='#ff6b6b', width=2)
    ))
    
    # Add threshold lines
    fig.add_hline(y=Config.HR_ELEVATED, line_dash="dash", 
                  line_color="yellow", annotation_text="Elevated")
    fig.add_hline(y=Config.HR_CRITICAL, line_dash="dash", 
                  line_color="red", annotation_text="Critical")
    
    fig.update_layout(
        title='Heart Rate Monitor',
        xaxis_title='Time (s)',
        yaxis_title='Heart Rate (BPM)',
        height=300,
        template='plotly_dark',
        hovermode='x unified'
    )
    
    return fig

def create_q_table_heatmap():
    """Visualize Q-table as heatmap"""
    fig = go.Figure(data=go.Heatmap(
        z=st.session_state.rl_agent.q_table,
        x=Config.ACTIONS,
        y=Config.STATES,
        colorscale='RdYlGn',
        text=np.round(st.session_state.rl_agent.q_table, 2),
        texttemplate='%{text}',
        textfont={"size": 14},
        colorbar=dict(title="Q-Value")
    ))
    
    fig.update_layout(
        title='RL Q-Table (State-Action Values)',
        height=300,
        template='plotly_dark'
    )
    
    return fig

def create_reward_plot():
    """Plot cumulative rewards"""
    if len(st.session_state.rl_agent.reward_history) == 0:
        return go.Figure()
    
    cumulative_rewards = np.cumsum(st.session_state.rl_agent.reward_history)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=cumulative_rewards,
        mode='lines',
        name='Cumulative Reward',
        line=dict(color='#4ecdc4', width=2)
    ))
    
    fig.update_layout(
        title='RL Learning Progress (Cumulative Reward)',
        xaxis_title='Iteration',
        yaxis_title='Cumulative Reward',
        height=300,
        template='plotly_dark'
    )
    
    return fig

# ============================================================================
# MAIN UI
# ============================================================================

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="FPGA Health Monitor with RL",
        page_icon="❤️",
        layout="wide"
    )
    
    # Initialize
    initialize_session_state()
    
    # Header
    st.markdown("""
        <h1 style='text-align: center; color: #ff6b6b;'>
            🫀 FPGA-Based Adaptive Health Monitor with RL
        </h1>
        <p style='text-align: center; color: #888;'>
            Real-time ECG Monitoring with Reinforcement Learning Decision Making
        </p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Control Panel
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        if st.button("▶️ Start" if not st.session_state.running else "⏸️ Pause", 
                     use_container_width=True):
            st.session_state.running = not st.session_state.running
    
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    with col3:
        speed = st.selectbox("Speed", ["Slow", "Normal", "Fast"], index=1)
        refresh_interval = {"Slow": 0.5, "Normal": 0.1, "Fast": 0.05}[speed]
    
    with col4:
        st.markdown(f"""
            <div style='background-color: {"#00ff00" if st.session_state.running else "#ff0000"}; 
                        padding: 8px; border-radius: 5px; text-align: center;'>
                <b>Status: {"RUNNING" if st.session_state.running else "STOPPED"}</b>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Metrics Row
    met1, met2, met3, met4, met5 = st.columns(5)
    
    met1.metric("❤️ Heart Rate", f"{st.session_state.current_hr:.1f} BPM")
    met2.metric("📊 State", st.session_state.current_state)
    met3.metric("🎯 Action", st.session_state.current_action)
    met4.metric("🏆 Total Reward", f"{st.session_state.total_rewards:.0f}")
    met5.metric("⚠️ Anomalies", st.session_state.anomaly_count)
    
    st.markdown("---")
    
    # Main visualization area
    tab1, tab2, tab3 = st.tabs(["📈 Live Monitoring", "🤖 RL Learning", "📋 Decision Log"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            ecg_plot = create_ecg_plot()
            st.plotly_chart(ecg_plot, use_container_width=True)
        
        with col2:
            hr_plot = create_heart_rate_plot()
            st.plotly_chart(hr_plot, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            q_heatmap = create_q_table_heatmap()
            st.plotly_chart(q_heatmap, use_container_width=True)
        
        with col2:
            reward_plot = create_reward_plot()
            st.plotly_chart(reward_plot, use_container_width=True)
    
    with tab3:
        if st.session_state.decisions:
            df = pd.DataFrame(st.session_state.decisions)
            st.dataframe(
                df.tail(20),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No decisions logged yet. Start monitoring to see decisions.")
    
    # Execute monitoring step if running
    if st.session_state.running:
        execute_monitoring_step()
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()