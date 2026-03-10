"""
MODULE 8: Data Logging & Replay System

This module handles:
- Comprehensive data logging
- Decision history tracking
- Replay mode for analysis
- Export functionality

Benefits:
- Debug system behavior
- Research and analysis
- Training data collection
- Performance evaluation
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime


class DataLogger:
    """
    Comprehensive data logger for the adaptive system.
    
    Logs:
    - Raw ECG data
    - Processed features
    - Decisions made
    - RL rewards and actions
    - System adaptations
    """
    
    def __init__(self, log_dir='data/logs'):
        """
        Initialize data logger.
        
        Args:
            log_dir (str): Directory for log files
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Create session ID
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize log buffers
        self.ecg_buffer = []
        self.feature_buffer = []
        self.decision_buffer = []
        self.rl_buffer = []
        self.adaptation_buffer = []
        
        # Log files
        self.files = {
            'ecg': os.path.join(log_dir, f'ecg_{self.session_id}.csv'),
            'features': os.path.join(log_dir, f'features_{self.session_id}.csv'),
            'decisions': os.path.join(log_dir, f'decisions_{self.session_id}.csv'),
            'rl_actions': os.path.join(log_dir, f'rl_actions_{self.session_id}.csv'),
            'adaptations': os.path.join(log_dir, f'adaptations_{self.session_id}.json'),
            'metadata': os.path.join(log_dir, f'metadata_{self.session_id}.json')
        }
        
        # Metadata
        self.metadata = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'total_samples': 0,
            'total_decisions': 0,
            'total_adaptations': 0
        }
        
        print(f"📝 Data Logger Initialized")
        print(f"   Session ID: {self.session_id}")
        print(f"   Log Directory: {log_dir}")
    
    def log_ecg_data(self, ecg_batch, loop_number):
        """
        Log raw ECG data.
        
        Args:
            ecg_batch (pd.DataFrame): Raw FPGA data
            loop_number (int): Control loop iteration
        """
        ecg_batch = ecg_batch.copy()
        ecg_batch['loop_number'] = loop_number
        ecg_batch['log_timestamp'] = datetime.now().isoformat()
        
        self.ecg_buffer.append(ecg_batch)
        self.metadata['total_samples'] += len(ecg_batch)
    
    def log_features(self, features, loop_number):
        """
        Log extracted features.
        
        Args:
            features (dict): Extracted signal features
            loop_number (int): Control loop iteration
        """
        feature_record = {
            'loop_number': loop_number,
            'timestamp': features.get('timestamp', 0),
            'heart_rate_bpm': features['heart_rate_bpm'],
            'hrv_ms': features['hrv_ms'],
            'quality_score': features['signal_quality']['quality_score'],
            'quality_label': features['signal_quality']['quality_label'],
            'num_peaks': features['signal_quality']['num_peaks'],
            'hr_stable': features['hr_stable'],
            'rhythm_regular': features['rhythm_regular'],
            'log_timestamp': datetime.now().isoformat()
        }
        
        self.feature_buffer.append(feature_record)
    
    def log_decision(self, decision, loop_number):
        """
        Log AI decision.
        
        Args:
            decision (dict): Decision object
            loop_number (int): Control loop iteration
        """
        decision_record = {
            'loop_number': loop_number,
            'timestamp': decision['timestamp'],
            'level': decision['level'],
            'level_numeric': decision['level_numeric'],
            'confidence': decision['confidence'],
            'short_explanation': decision['short_explanation'],
            'hr': decision['measurements']['hr'],
            'hrv': decision['measurements']['hrv'],
            'quality': decision['measurements']['quality'],
            'log_timestamp': datetime.now().isoformat()
        }
        
        self.decision_buffer.append(decision_record)
        self.metadata['total_decisions'] += 1
    
    def log_rl_action(self, rl_feedback, loop_number):
        """
        Log RL action and reward.
        
        Args:
            rl_feedback (dict): RL feedback information
            loop_number (int): Control loop iteration
        """
        rl_record = {
            'loop_number': loop_number,
            'state': str(rl_feedback['state']),
            'action': rl_feedback['action'],
            'reward': rl_feedback['reward'],
            'q_value': rl_feedback['q_value'],
            'baseline_hr': rl_feedback['baseline_hr'],
            'sensitivity': rl_feedback['sensitivity'],
            'log_timestamp': datetime.now().isoformat()
        }
        
        self.rl_buffer.append(rl_record)
    
    def log_adaptation(self, adaptation_info):
        """
        Log system adaptation event.
        
        Args:
            adaptation_info (dict): Adaptation information
        """
        self.adaptation_buffer.append(adaptation_info)
        self.metadata['total_adaptations'] += 1
    
    def flush(self):
        """
        Write all buffers to files.
        """
        print(f"\n💾 Flushing logs to disk...")
        
        # ECG data
        if self.ecg_buffer:
            ecg_df = pd.concat(self.ecg_buffer, ignore_index=True)
            ecg_df.to_csv(self.files['ecg'], index=False)
            print(f"   ✓ ECG data: {len(ecg_df)} samples")
        
        # Features
        if self.feature_buffer:
            features_df = pd.DataFrame(self.feature_buffer)
            features_df.to_csv(self.files['features'], index=False)
            print(f"   ✓ Features: {len(features_df)} records")
        
        # Decisions
        if self.decision_buffer:
            decisions_df = pd.DataFrame(self.decision_buffer)
            decisions_df.to_csv(self.files['decisions'], index=False)
            print(f"   ✓ Decisions: {len(decisions_df)} records")
        
        # RL actions
        if self.rl_buffer:
            rl_df = pd.DataFrame(self.rl_buffer)
            rl_df.to_csv(self.files['rl_actions'], index=False)
            print(f"   ✓ RL actions: {len(rl_df)} records")
        
        # Adaptations
        if self.adaptation_buffer:
            with open(self.files['adaptations'], 'w') as f:
                json.dump(self.adaptation_buffer, f, indent=2)
            print(f"   ✓ Adaptations: {len(self.adaptation_buffer)} events")
        
        # Clear buffers
        self.ecg_buffer = []
        self.feature_buffer = []
        self.decision_buffer = []
        self.rl_buffer = []
    
    def close(self):
        """
        Close logger and save metadata.
        """
        # Final flush
        self.flush()
        
        # Update metadata
        self.metadata['end_time'] = datetime.now().isoformat()
        
        # Save metadata
        with open(self.files['metadata'], 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        print(f"\n✅ Data logging complete")
        print(f"   Session: {self.session_id}")
        print(f"   Total samples: {self.metadata['total_samples']}")
        print(f"   Total decisions: {self.metadata['total_decisions']}")
        print(f"   Total adaptations: {self.metadata['total_adaptations']}")


class ReplayManager:
    """
    Replay logged sessions for analysis and testing.
    """
    
    def __init__(self, session_id, log_dir='data/logs'):
        """
        Initialize replay manager.
        
        Args:
            session_id (str): Session ID to replay
            log_dir (str): Log directory
        """
        self.session_id = session_id
        self.log_dir = log_dir
        
        # Load data
        self.ecg_data = None
        self.features = None
        self.decisions = None
        self.rl_actions = None
        self.adaptations = None
        self.metadata = None
        
        self._load_data()
        
        print(f"🔄 Replay Manager Initialized")
        print(f"   Session: {session_id}")
    
    def _load_data(self):
        """Load all logged data"""
        # base_path = os.path.join(self.log_dir, f'{{}_{self.session_id}')
        base_path = os.path.join(self.log_dir, '{}_' + self.session_id)


        try:
            self.ecg_data = pd.read_csv(base_path.format('ecg') + '.csv')
            self.features = pd.read_csv(base_path.format('features') + '.csv')
            self.decisions = pd.read_csv(base_path.format('decisions') + '.csv')
            self.rl_actions = pd.read_csv(base_path.format('rl_actions') + '.csv')
            
            with open(base_path.format('adaptations') + '.json', 'r') as f:
                self.adaptations = json.load(f)
            
            with open(base_path.format('metadata') + '.json', 'r') as f:
                self.metadata = json.load(f)
            
            print(f"   ✓ Loaded {len(self.decisions)} decisions")
            
        except Exception as e:
            print(f"   ⚠ Error loading data: {e}")
    
    def get_summary(self):
        """
        Get session summary.
        
        Returns:
            dict: Summary statistics
        """
        if self.metadata is None:
            return {}
        
        return {
            'session_id': self.session_id,
            'start_time': self.metadata['start_time'],
            'end_time': self.metadata['end_time'],
            'duration': self._calculate_duration(),
            'total_samples': self.metadata['total_samples'],
            'total_decisions': self.metadata['total_decisions'],
            'total_adaptations': self.metadata['total_adaptations'],
            'alert_rate': self._calculate_alert_rate(),
            'avg_hr': self.features['heart_rate_bpm'].mean() if self.features is not None else 0,
            'avg_confidence': self.decisions['confidence'].mean() if self.decisions is not None else 0
        }
    
    def _calculate_duration(self):
        """Calculate session duration"""
        if self.metadata['end_time']:
            start = datetime.fromisoformat(self.metadata['start_time'])
            end = datetime.fromisoformat(self.metadata['end_time'])
            return (end - start).total_seconds()
        return 0
    
    def _calculate_alert_rate(self):
        """Calculate alert rate"""
        if self.decisions is None or len(self.decisions) == 0:
            return 0
        
        alerts = len(self.decisions[self.decisions['level'] != 'NORMAL'])
        return (alerts / len(self.decisions)) * 100
    
    def get_decision_at_time(self, loop_number):
        """
        Get decision at specific loop iteration.
        
        Args:
            loop_number (int): Loop iteration number
            
        Returns:
            dict: Decision information
        """
        if self.decisions is None:
            return None
        
        decision = self.decisions[self.decisions['loop_number'] == loop_number]
        if len(decision) > 0:
            return decision.iloc[0].to_dict()
        return None
    
    def export_report(self, output_file='report.html'):
        """
        Export analysis report.
        
        Args:
            output_file (str): Output HTML file
        """
        try:
            import matplotlib.pyplot as plt
            
            # Create visualizations
            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            
            # Heart rate over time
            axes[0, 0].plot(self.features['heart_rate_bpm'])
            axes[0, 0].set_title('Heart Rate Over Time')
            axes[0, 0].set_ylabel('BPM')
            
            # HRV
            axes[0, 1].plot(self.features['hrv_ms'])
            axes[0, 1].set_title('Heart Rate Variability')
            axes[0, 1].set_ylabel('ms')
            
            # Decision distribution
            decision_counts = self.decisions['level'].value_counts()
            axes[1, 0].bar(decision_counts.index, decision_counts.values)
            axes[1, 0].set_title('Decision Distribution')
            axes[1, 0].set_ylabel('Count')
            
            # Confidence over time
            axes[1, 1].plot(self.decisions['confidence'])
            axes[1, 1].set_title('Decision Confidence')
            axes[1, 1].set_ylabel('%')
            
            plt.tight_layout()
            plt.savefig(output_file.replace('.html', '.png'))
            
            print(f"✓ Report exported: {output_file}")
            
        except Exception as e:
            print(f"⚠ Could not export report: {e}")


# Demo
if __name__ == "__main__":
    print("=" * 70)
    print("MODULE 8: DATA LOGGING & REPLAY - TESTING")
    print("=" * 70)
    
    # Create logger
    logger = DataLogger()
    
    # Simulate logging
    print("\n[SIMULATION] Logging 10 iterations...\n")
    
    for i in range(10):
        # Simulate ECG batch
        ecg_batch = pd.DataFrame({
            'timestamp_ms': range(250),
            'adc_value': np.random.randint(1500, 2500, 250),
            'status': [0] * 250
        })
        
        # Simulate features
        features = {
            'timestamp': i * 1000,
            'heart_rate_bpm': 70 + np.random.normal(0, 5),
            'hrv_ms': 50 + np.random.normal(0, 10),
            'signal_quality': {
                'quality_score': 80 + np.random.normal(0, 5),
                'quality_label': 'GOOD',
                'num_peaks': 1
            },
            'hr_stable': True,
            'rhythm_regular': True
        }
        
        # Simulate decision
        decision = {
            'timestamp': datetime.now().isoformat(),
            'level': 'NORMAL',
            'level_numeric': 0,
            'confidence': 85,
            'short_explanation': 'All normal',
            'measurements': {
                'hr': features['heart_rate_bpm'],
                'hrv': features['hrv_ms'],
                'quality': features['signal_quality']['quality_score']
            }
        }
        
        # Simulate RL feedback
        rl_feedback = {
            'state': (1, 1, 1),
            'action': 'MAINTAIN',
            'reward': 5,
            'q_value': 10.5,
            'baseline_hr': 70,
            'sensitivity': 1.0
        }
        
        # Log everything
        logger.log_ecg_data(ecg_batch, i)
        logger.log_features(features, i)
        logger.log_decision(decision, i)
        logger.log_rl_action(rl_feedback, i)
        
        if i % 5 == 0:
            logger.flush()
    
    # Close logger
    logger.close()
    
    # Test replay
    print("\n" + "="*70)
    print("TESTING REPLAY")
    print("="*70)
    
    replay = ReplayManager(logger.session_id)
    summary = replay.get_summary()
    
    print("\nSession Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Module 8 Complete!")
    print("\n🔄 Next: Module 9 - Evaluation Metrics")