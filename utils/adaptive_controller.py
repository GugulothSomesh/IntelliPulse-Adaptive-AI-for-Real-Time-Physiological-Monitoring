"""
MODULE 6: Closed-Loop Adaptive System

This module implements a true feedback control loop:

    ┌─────────────────────────────────────────┐
    │  OBSERVE → DECIDE → ACT → MEASURE → LEARN │
    └─────────────────────────────────────────┘

Unlike traditional systems with fixed rules, this system:
- Observes physiological state
- Makes intelligent decisions
- Takes actions (adjust thresholds/sensitivity)
- Measures outcomes
- Learns from results
- Adapts for better future performance

This creates a self-improving system that gets smarter over time.
"""

import numpy as np
import pandas as pd
from datetime import datetime
import time


class AdaptiveController:
    """
    Closed-loop adaptive controller.
    
    Implements the complete feedback loop integrating:
    - Signal processing
    - RL agent
    - Decision engine
    - Adaptation mechanism
    """
    
    def __init__(self, signal_processor, rl_agent, decision_engine):
        """
        Initialize adaptive controller.
        
        Args:
            signal_processor: Signal processing module
            rl_agent: Reinforcement learning agent
            decision_engine: Explainable AI decision engine
        """
        self.processor = signal_processor
        self.rl_agent = rl_agent
        self.decision_engine = decision_engine
        
        # Connect RL agent to decision engine
        self.decision_engine.rl_agent = rl_agent
        
        # Control loop state
        self.loop_count = 0
        self.running = False
        
        # Performance tracking
        self.performance_metrics = {
            'alert_reduction': [],
            'decision_stability': [],
            'learning_speed': [],
            'adaptation_effectiveness': []
        }
        
        # Adaptation history
        self.adaptation_log = []
        
        print("🔄 Closed-Loop Adaptive Controller Initialized")
        print("   Components connected: Processor ↔ RL ↔ Decision Engine")
    
    def control_step(self, ecg_batch):
        """
        Execute one complete control loop iteration.
        
        Control Loop Steps:
        1. OBSERVE: Process sensor data
        2. DECIDE: Make intelligent decision
        3. ACT: Adjust system parameters
        4. MEASURE: Evaluate decision quality
        5. LEARN: Update RL policy
        
        Args:
            ecg_batch (pd.DataFrame): Raw ECG data from FPGA
            
        Returns:
            dict: Complete loop results
        """
        self.loop_count += 1
        loop_start = time.time()
        
        # ═══════════════════════════════════════════════════
        # STEP 1: OBSERVE - Process Signal
        # ═══════════════════════════════════════════════════
        features = self.processor.process_batch(ecg_batch)
        
        # ═══════════════════════════════════════════════════
        # STEP 2: DECIDE - Make Explainable Decision
        # ═══════════════════════════════════════════════════
        decision = self.decision_engine.make_decision(features)
        
        # ═══════════════════════════════════════════════════
        # STEP 3 & 4: ACT & MEASURE - RL Learning Step
        # ═══════════════════════════════════════════════════
        rl_feedback = self.rl_agent.step(features, decision['level'])
        
        # ═══════════════════════════════════════════════════
        # STEP 5: LEARN - Record Adaptation
        # ═══════════════════════════════════════════════════
        if rl_feedback['action'] != "MAINTAIN":
            self._record_adaptation(features, decision, rl_feedback)
        
        # ═══════════════════════════════════════════════════
        # Performance Evaluation
        # ═══════════════════════════════════════════════════
        self._update_performance_metrics(decision, rl_feedback)
        
        loop_time = time.time() - loop_start
        
        # Return complete results
        return {
            'loop_number': self.loop_count,
            'features': features,
            'decision': decision,
            'rl_feedback': rl_feedback,
            'performance': self._get_current_performance(),
            'loop_time_ms': loop_time * 1000,
            'timestamp': datetime.now()
        }
    
    def _record_adaptation(self, features, decision, rl_feedback):
        """
        Record adaptation event for analysis.
        
        Args:
            features (dict): Signal features
            decision (dict): Decision made
            rl_feedback (dict): RL adaptation info
        """
        adaptation = {
            'timestamp': datetime.now().isoformat(),
            'loop': self.loop_count,
            'action': rl_feedback['action'],
            'reason': self._explain_adaptation(features, decision, rl_feedback),
            'old_baseline': rl_feedback['baseline_hr'],
            'old_sensitivity': rl_feedback['sensitivity'],
            'reward': rl_feedback['reward'],
            'decision_level': decision['level']
        }
        
        self.adaptation_log.append(adaptation)
        
        # Keep last 100 adaptations
        if len(self.adaptation_log) > 100:
            self.adaptation_log.pop(0)
    
    def _explain_adaptation(self, features, decision, rl_feedback):
        """
        Generate human-readable explanation for adaptation.
        
        Args:
            features (dict): Signal features
            decision (dict): Decision made
            rl_feedback (dict): RL feedback
            
        Returns:
            str: Explanation
        """
        action = rl_feedback['action']
        reward = rl_feedback['reward']
        
        if action == "DECREASE_SENSITIVITY":
            return f"Reduced sensitivity to minimize false alerts (reward: {reward:.1f})"
        elif action == "INCREASE_SENSITIVITY":
            return f"Increased sensitivity to catch important events (reward: {reward:.1f})"
        elif action == "BASELINE_UP":
            return f"Adjusted baseline HR upward based on recent trends (reward: {reward:.1f})"
        elif action == "BASELINE_DOWN":
            return f"Adjusted baseline HR downward based on recent trends (reward: {reward:.1f})"
        else:
            return f"Maintained current settings (reward: {reward:.1f})"
    
    def _update_performance_metrics(self, decision, rl_feedback):
        """
        Update performance tracking metrics.
        
        Args:
            decision (dict): Decision made
            rl_feedback (dict): RL feedback
        """
        # Alert reduction (compared to initial naive system)
        rl_progress = self.rl_agent.get_learning_progress()
        if rl_progress['episodes'] > 0:
            false_positive_rate = rl_progress['false_positive_rate']
            self.performance_metrics['alert_reduction'].append(
                max(0, 100 - false_positive_rate)
            )
        
        # Decision stability (confidence trend)
        self.performance_metrics['decision_stability'].append(
            decision['confidence']
        )
        
        # Learning speed (reward trend)
        self.performance_metrics['learning_speed'].append(
            rl_feedback['reward']
        )
        
        # Keep last 100 measurements
        for key in self.performance_metrics:
            if len(self.performance_metrics[key]) > 100:
                self.performance_metrics[key].pop(0)
    
    def _get_current_performance(self):
        """
        Get current performance summary.
        
        Returns:
            dict: Performance metrics
        """
        metrics = {}
        
        for metric_name, values in self.performance_metrics.items():
            if values:
                metrics[metric_name] = {
                    'current': values[-1],
                    'average': np.mean(values),
                    'trend': 'improving' if len(values) > 10 and np.mean(values[-10:]) > np.mean(values[:10]) else 'stable'
                }
            else:
                metrics[metric_name] = {'current': 0, 'average': 0, 'trend': 'unknown'}
        
        return metrics
    
    def get_adaptation_summary(self, last_n=10):
        """
        Get summary of recent adaptations.
        
        Args:
            last_n (int): Number of recent adaptations to show
            
        Returns:
            str: Formatted summary
        """
        if not self.adaptation_log:
            return "No adaptations yet."
        
        recent = self.adaptation_log[-last_n:]
        
        summary = f"\n{'='*70}\n"
        summary += f"RECENT ADAPTATIONS (Last {len(recent)})\n"
        summary += f"{'='*70}\n"
        
        for i, adapt in enumerate(recent, 1):
            summary += f"\n{i}. Loop {adapt['loop']} - {adapt['action']}\n"
            summary += f"   {adapt['reason']}\n"
        
        return summary
    
    def get_system_status(self):
        """
        Get complete system status report.
        
        Returns:
            dict: System status
        """
        rl_progress = self.rl_agent.get_learning_progress()
        decision_stats = self.decision_engine.get_statistics()
        
        return {
            'loop_iterations': self.loop_count,
            'rl_episodes': rl_progress['episodes'],
            'learning_accuracy': rl_progress['accuracy'],
            'adaptations_made': rl_progress['adaptations'],
            'decision_confidence_avg': decision_stats['avg_confidence'],
            'false_positive_rate': rl_progress['false_positive_rate'],
            'current_baseline_hr': self.rl_agent.user_profile['baseline_hr'],
            'current_sensitivity': self.rl_agent.user_profile['sensitivity']
        }
    
    def generate_status_report(self):
        """
        Generate formatted status report.
        
        Returns:
            str: Formatted report
        """
        status = self.get_system_status()
        performance = self._get_current_performance()
        
        report = f"""
╔═══════════════════════════════════════════════════════════════════╗
║              ADAPTIVE SYSTEM STATUS REPORT                        ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Control Loop Iterations: {status['loop_iterations']:<6d}                              ║
║  RL Learning Episodes:    {status['rl_episodes']:<6d}                              ║
║  Adaptations Made:        {status['adaptations_made']:<6d}                              ║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  LEARNING PERFORMANCE                                             ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Decision Accuracy:       {status['learning_accuracy']:5.1f}%                              ║
║  Avg Confidence:          {status['decision_confidence_avg']:5.1f}%                              ║
║  False Positive Rate:     {status['false_positive_rate']:5.1f}%                              ║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  PERSONALIZED SETTINGS                                            ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Your Baseline HR:        {status['current_baseline_hr']:5.1f} BPM                          ║
║  Alert Sensitivity:       {status['current_sensitivity']:5.2f}x                             ║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  PERFORMANCE TRENDS                                               ║
╠═══════════════════════════════════════════════════════════════════╣
"""
        
        for metric, data in performance.items():
            trend_symbol = '↑' if data['trend'] == 'improving' else '→'
            report += f"║  {metric:25s} {trend_symbol} {data['average']:6.1f} (avg)      ║\n"
        
        report += "╚═══════════════════════════════════════════════════════════════════╝\n"
        
        return report


# Demo
if __name__ == "__main__":
    print("=" * 70)
    print("MODULE 6: CLOSED-LOOP ADAPTIVE SYSTEM - TESTING")
    print("=" * 70)
    
    # Import required modules
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    
    from fpga_interface.fpga_stream import FPGAInterface
    from signal_processing.features import SignalProcessor
    from rl_engine.q_learning import AdaptiveRLAgent
    from decision_engine.explainable_ai import ExplainableDecisionEngine
    
    # Initialize all components
    print("\n[INITIALIZATION] Setting up complete adaptive system...")
    fpga = FPGAInterface(source_type='dummy', sampling_rate=250)
    processor = SignalProcessor(sampling_rate=250)
    rl_agent = AdaptiveRLAgent(learning_rate=0.1, discount_factor=0.95, epsilon=0.2)
    decision_engine = ExplainableDecisionEngine()
    
    # Create controller
    controller = AdaptiveController(processor, rl_agent, decision_engine)
    
    print("\n[RUNNING] Closed-loop system for 20 iterations...\n")
    
    for i in range(20):
        # Get data from FPGA
        ecg_batch = fpga.read_data(duration=1.0)
        
        if ecg_batch is not None:
            # Execute control loop
            results = controller.control_step(ecg_batch)
            
            # Display results every 5 iterations
            if (i + 1) % 5 == 0:
                print(f"\n{'='*70}")
                print(f"ITERATION {i + 1}")
                print(f"{'='*70}")
                print(decision_engine.get_decision_summary(results['decision']))
                print(f"\nRL Action: {results['rl_feedback']['action']}")
                print(f"Reward: {results['rl_feedback']['reward']:.2f}")
                print(f"Loop Time: {results['loop_time_ms']:.2f} ms")
        
        time.sleep(0.1)
    
    # Final status report
    print("\n" + controller.generate_status_report())
    print(controller.get_adaptation_summary(last_n=5))
    
    fpga.close()
    
    print("\n✅ Module 6 Complete!")
    print("\n🔄 Next: Module 7 - Real-Time Dashboard (Beautiful GUI)")