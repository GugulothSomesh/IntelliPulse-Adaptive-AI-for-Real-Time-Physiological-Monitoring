"""
MAIN SYSTEM INTEGRATION - CORRECTED VERSION

Improved output formatting and real-time statistics

Usage:
    python main.py --mode <mode> --duration <seconds>

Modes:
    - demo: Quick 30-second demonstration
    - training: Extended training session
    - evaluation: Performance evaluation

Example:
    python main.py --mode demo --duration 30
"""

import argparse
import time
import sys
import os
from datetime import datetime
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Import all modules
from fpga_interface.fpga_stream import FPGAInterface
from signal_processing.features import SignalProcessor
from rl_engine.q_learning import AdaptiveRLAgent
from decision_engine.explainable_ai import ExplainableDecisionEngine
from utils.adaptive_controller import AdaptiveController
from utils.logger import DataLogger


class HealthMonitoringSystem:
    """
    Complete FPGA-based adaptive health monitoring system with improved UI.
    """
    
    def __init__(self, mode='demo'):
        """Initialize complete system."""
        self.mode = mode
        
        print("\n" + "=" * 80)
        print("  🫀 FPGA-BASED ADAPTIVE PHYSIOLOGICAL MONITORING SYSTEM")
        print("     with Reinforcement Learning and Explainable AI")
        print("=" * 80)
        print()
        
        # Initialize components
        self._initialize_components()
        
        # Initialize logger
        self.logger = DataLogger()
        
        # Statistics tracking
        self.stats = {
            'normal_count': 0,
            'warning_count': 0,
            'alert_count': 0,
            'critical_count': 0,
            'avg_hr': [],
            'avg_hrv': [],
            'avg_quality': []
        }
        
        print("\n✅ System initialization complete!")
        print()
    
    def _initialize_components(self):
        """Initialize all system components"""
        print("🔧 Initializing system components...")
        
        # FPGA Interface
        print("\n[1/5] FPGA Interface")
        self.fpga = FPGAInterface(
            source_type='dummy',
            sampling_rate=250,
            base_heart_rate=70
        )
        
        # Signal Processor
        print("\n[2/5] Signal Processor")
        self.processor = SignalProcessor(sampling_rate=250)
        
        # RL Agent
        print("\n[3/5] Reinforcement Learning Agent")
        self.rl_agent = AdaptiveRLAgent(
            learning_rate=0.1,
            discount_factor=0.95,
            epsilon=0.2
        )
        
        # Decision Engine
        print("\n[4/5] Explainable AI Decision Engine")
        self.decision_engine = ExplainableDecisionEngine()
        
        # Adaptive Controller
        print("\n[5/5] Closed-Loop Adaptive Controller")
        self.controller = AdaptiveController(
            self.processor,
            self.rl_agent,
            self.decision_engine
        )
    
    def run(self, duration_seconds=30):
        """Run the complete system."""
        print(f"\n{'='*80}")
        print(f"  🚀 STARTING {self.mode.upper()} MODE - Duration: {duration_seconds}s")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        iteration = 0
        
        try:
            while (time.time() - start_time) < duration_seconds:
                iteration += 1
                
                # Read data from FPGA
                ecg_batch = self.fpga.read_data(duration=1.0)
                
                if ecg_batch is None:
                    print("⚠ No data available")
                    break
                
                # Execute control loop
                results = self.controller.control_step(ecg_batch)
                
                # Log everything
                self.logger.log_ecg_data(ecg_batch, iteration)
                self.logger.log_features(results['features'], iteration)
                self.logger.log_decision(results['decision'], iteration)
                self.logger.log_rl_action(results['rl_feedback'], iteration)
                
                # Update statistics
                self._update_stats(results)
                
                # Display progress
                if iteration % 5 == 0:
                    self._display_progress(iteration, results)
                
                # Flush logs periodically
                if iteration % 10 == 0:
                    self.logger.flush()
                
                time.sleep(0.1)  # Small delay
        
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
        
        finally:
            self._shutdown()
    
    def _update_stats(self, results):
        """Update running statistics."""
        decision = results['decision']
        features = results['features']
        
        # Count decision levels
        level = decision['level']
        if level == 'NORMAL':
            self.stats['normal_count'] += 1
        elif level == 'WARNING':
            self.stats['warning_count'] += 1
        elif level == 'ALERT':
            self.stats['alert_count'] += 1
        elif level == 'CRITICAL':
            self.stats['critical_count'] += 1
        
        # Track metrics
        self.stats['avg_hr'].append(features['heart_rate_bpm'])
        self.stats['avg_hrv'].append(features['hrv_ms'])
        self.stats['avg_quality'].append(features['signal_quality']['quality_score'])
        
        # Keep last 100
        for key in ['avg_hr', 'avg_hrv', 'avg_quality']:
            if len(self.stats[key]) > 100:
                self.stats[key].pop(0)
    
    def _display_progress(self, iteration, results):
        """Display progress update with improved formatting."""
        decision = results['decision']
        features = results['features']
        rl_info = results['rl_feedback']
        
        print(f"\n{'─'*80}")
        print(f"⏱  Iteration {iteration}")
        print(f"{'─'*80}")
        
        # Key metrics with color-coding
        hr = features['heart_rate_bpm']
        hrv = features['hrv_ms']
        quality = features['signal_quality']['quality_score']
        
        print(f"❤️  Heart Rate:  {hr:6.1f} BPM")
        print(f"📊 HRV:         {hrv:6.1f} ms")
        print(f"🎯 Quality:     {quality:5.0f}/100 ({features['signal_quality']['quality_label']})")
        print(f"🔍 Peaks Found: {features['signal_quality']['num_peaks']}")
        
        # Decision with symbol
        decision_symbol = {
            'NORMAL': '✅',
            'WARNING': '⚠️',
            'ALERT': '🚨',
            'CRITICAL': '🚨🚨'
        }
        symbol = decision_symbol.get(decision['level'], '?')
        
        print(f"\n{symbol} Decision: {decision['level']} (Confidence: {decision['confidence']:.0f}%)")
        print(f"   {decision['short_explanation']}")
        
        # RL Info
        if rl_info['action'] != "MAINTAIN":
            print(f"\n🧠 RL Action: {rl_info['action']} (Reward: {rl_info['reward']:.1f})")
        
        # Learning progress every 10 iterations
        if iteration % 10 == 0:
            progress = self.rl_agent.get_learning_progress()
            print(f"\n📈 Learning Progress:")
            print(f"   Accuracy: {progress['accuracy']:.1f}%")
            print(f"   Precision: {progress['precision']:.1f}%")
            print(f"   False Positive Rate: {progress['false_positive_rate']:.1f}%")
            print(f"   Adaptations: {progress['adaptations']}")
            print(f"   Baseline HR: {rl_info['baseline_hr']:.1f} BPM")
            print(f"   Sensitivity: {rl_info['sensitivity']:.2f}x")
    
    def _shutdown(self):
        """Shutdown system gracefully"""
        print(f"\n{'='*80}")
        print("  🛑 SHUTTING DOWN SYSTEM")
        print(f"{'='*80}\n")
        
        # Close FPGA interface
        self.fpga.close()
        
        # Close logger
        self.logger.close()
        
        # Display final statistics
        self._display_final_stats()
        
        print("\n✅ System shutdown complete")
    
    def _display_final_stats(self):
        """Display final statistics"""
        print("\n📊 FINAL STATISTICS")
        print("=" * 80)
        
        # System status
        status = self.controller.get_system_status()
        print("\nSystem Performance:")
        print(f"  Total Iterations: {status['loop_iterations']}")
        print(f"  Learning Accuracy: {status['learning_accuracy']:.1f}%")
        print(f"  Learning Precision: {self.rl_agent.get_learning_progress()['precision']:.1f}%")
        print(f"  Adaptations Made: {status['adaptations_made']}")
        print(f"  False Positive Rate: {status['false_positive_rate']:.1f}%")
        
        # Decision distribution
        total_decisions = (self.stats['normal_count'] + self.stats['warning_count'] + 
                          self.stats['alert_count'] + self.stats['critical_count'])
        
        if total_decisions > 0:
            print("\nDecision Distribution:")
            print(f"  ✅ NORMAL:   {self.stats['normal_count']:3d} ({self.stats['normal_count']/total_decisions*100:5.1f}%)")
            print(f"  ⚠️  WARNING:  {self.stats['warning_count']:3d} ({self.stats['warning_count']/total_decisions*100:5.1f}%)")
            print(f"  🚨 ALERT:    {self.stats['alert_count']:3d} ({self.stats['alert_count']/total_decisions*100:5.1f}%)")
            print(f"  🚨🚨 CRITICAL: {self.stats['critical_count']:3d} ({self.stats['critical_count']/total_decisions*100:5.1f}%)")
        
        # Average metrics
        if self.stats['avg_hr']:
            import numpy as np
            print("\nAverage Metrics:")
            print(f"  Heart Rate: {np.mean(self.stats['avg_hr']):.1f} BPM")
            print(f"  HRV:        {np.mean(self.stats['avg_hrv']):.1f} ms")
            print(f"  Quality:    {np.mean(self.stats['avg_quality']):.1f}/100")
        
        # Personalization
        print("\nPersonalized Profile:")
        print(f"  Your Baseline HR: {status['current_baseline_hr']:.1f} BPM")
        print(f"  Alert Sensitivity: {status['current_sensitivity']:.2f}x")
        
        # Display comprehensive report
        print("\n" + self.controller.generate_status_report())


def run_demo():
    """Run quick demonstration"""
    print("\n🎬 Starting 30-second demonstration...")
    print("   Watch the system learn and adapt in real-time!")
    system = HealthMonitoringSystem(mode='demo')
    system.run(duration_seconds=30)


def run_training(duration=300):
    """Run extended training session"""
    print("\n🎓 Starting training session...")
    print(f"   Duration: {duration} seconds ({duration//60} minutes)")
    system = HealthMonitoringSystem(mode='training')
    system.run(duration_seconds=duration)


def run_evaluation(duration=60):
    """Run comprehensive evaluation"""
    print("\n📊 Starting evaluation...")
    system = HealthMonitoringSystem(mode='evaluation')
    system.run(duration_seconds=duration)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='FPGA-Based Adaptive Health Monitoring System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode demo
  python main.py --mode training --duration 300
  python main.py --mode evaluation --duration 60

For web dashboard:
  streamlit run dashboard/app.py
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['demo', 'training', 'evaluation', 'dashboard'],
        default='demo',
        help='Operating mode (default: demo)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=30,
        help='Duration in seconds (default: 30)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'demo':
        run_demo()
    elif args.mode == 'training':
        run_training(args.duration)
    elif args.mode == 'evaluation':
        run_evaluation(args.duration)
    elif args.mode == 'dashboard':
        print("\n🌐 Starting web dashboard...")
        print("   Run: streamlit run dashboard/app.py")
        print("   Or use --mode demo for command-line interface")


if __name__ == "__main__":
    # First, generate sample data if needed
    if not os.path.exists('data/dummy_ecg.csv'):
        print("📊 Generating sample ECG data...")
        from data.ecg_simulator import ECGSimulator
        sim = ECGSimulator()
        sim.save_sample_data()
        print()
    
    main()