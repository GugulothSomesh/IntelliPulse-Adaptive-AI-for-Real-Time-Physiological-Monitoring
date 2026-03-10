"""
MODULE 5: Explainable AI Decision Layer

This module makes intelligent decisions AND explains them in plain English.

🎯 Why Explainability Matters:
- Users trust decisions they understand
- Doctors need reasons, not just alerts
- Debugging becomes easy
- Meets medical AI transparency requirements

Every decision includes:
1. Decision (NORMAL / WARNING / ALERT)
2. Confidence score (0-100%)
3. Human-readable explanation
4. Contributing factors
"""

import numpy as np
from datetime import datetime
from enum import Enum


class AlertLevel(Enum):
    """Alert severity levels"""
    NORMAL = 0
    WARNING = 1
    ALERT = 2
    CRITICAL = 3


class ExplainableDecisionEngine:
    """
    AI Decision Engine with full explainability.
    
    Makes decisions based on:
    - Current measurements
    - User's personal baseline (from RL)
    - Signal quality
    - Temporal trends
    
    Every decision is backed by clear reasoning.
    """
    
    def __init__(self, rl_agent=None):
        """
        Initialize decision engine.
        
        Args:
            rl_agent: Reinforcement learning agent (provides adaptive thresholds)
        """
        self.rl_agent = rl_agent
        self.decision_history = []
        
        # Default thresholds (will be adapted by RL)
        self.thresholds = {
            'hr_min': 50,
            'hr_max': 100,
            'hr_critical_min': 40,
            'hr_critical_max': 130,
            'hrv_min': 20,
            'hrv_critical': 10,
            'quality_min': 40
        }
        
        print("🤖 Explainable AI Decision Engine Initialized")
    
    def _evaluate_heart_rate(self, features):
        """
        Evaluate heart rate and generate explanation.
        
        Args:
            features (dict): Signal features
            
        Returns:
            dict: HR evaluation results
        """
        hr = features['heart_rate_bpm']
        
        # Get personalized baseline from RL agent
        if self.rl_agent:
            baseline = self.rl_agent.user_profile['baseline_hr']
            hr_std = self.rl_agent.user_profile['hr_std']
            sensitivity = self.rl_agent.user_profile['sensitivity']
        else:
            baseline = 70
            hr_std = 10
            sensitivity = 1.0
        
        # Adaptive thresholds based on baseline
        hr_min = baseline - (2 * hr_std * sensitivity)
        hr_max = baseline + (2 * hr_std * sensitivity)
        
        # Evaluate
        if hr < self.thresholds['hr_critical_min']:
            level = AlertLevel.CRITICAL
            reason = f"Critically low heart rate ({hr:.0f} BPM)"
            concern = "severe_bradycardia"
        elif hr > self.thresholds['hr_critical_max']:
            level = AlertLevel.CRITICAL
            reason = f"Critically high heart rate ({hr:.0f} BPM)"
            concern = "severe_tachycardia"
        elif hr < hr_min:
            level = AlertLevel.WARNING
            reason = f"Heart rate below your baseline ({hr:.0f} vs {baseline:.0f} BPM)"
            concern = "mild_bradycardia"
        elif hr > hr_max:
            level = AlertLevel.WARNING
            reason = f"Heart rate above your baseline ({hr:.0f} vs {baseline:.0f} BPM)"
            concern = "mild_tachycardia"
        else:
            level = AlertLevel.NORMAL
            reason = f"Heart rate within normal range ({hr:.0f} BPM)"
            concern = None
        
        return {
            'level': level,
            'reason': reason,
            'concern': concern,
            'value': hr,
            'baseline': baseline,
            'deviation': abs(hr - baseline)
        }
    
    def _evaluate_hrv(self, features):
        """
        Evaluate heart rate variability.
        
        Low HRV indicates:
        - Stress
        - Fatigue
        - Poor recovery
        - Potential health issues
        
        Args:
            features (dict): Signal features
            
        Returns:
            dict: HRV evaluation results
        """
        hrv = features['hrv_ms']
        
        # Get baseline from RL
        if self.rl_agent:
            baseline_hrv = self.rl_agent.user_profile['baseline_hrv']
        else:
            baseline_hrv = 50
        
        # Evaluate
        if hrv < self.thresholds['hrv_critical']:
            level = AlertLevel.CRITICAL
            reason = f"Extremely low HRV ({hrv:.1f} ms) - severe stress or fatigue"
            concern = "critical_stress"
        elif hrv < self.thresholds['hrv_min']:
            level = AlertLevel.WARNING
            reason = f"Low HRV ({hrv:.1f} ms) - elevated stress or fatigue"
            concern = "elevated_stress"
        elif hrv < baseline_hrv * 0.7:
            level = AlertLevel.WARNING
            reason = f"HRV below your baseline ({hrv:.1f} vs {baseline_hrv:.1f} ms)"
            concern = "reduced_variability"
        else:
            level = AlertLevel.NORMAL
            reason = f"HRV within healthy range ({hrv:.1f} ms)"
            concern = None
        
        return {
            'level': level,
            'reason': reason,
            'concern': concern,
            'value': hrv,
            'baseline': baseline_hrv
        }
    
    def _evaluate_signal_quality(self, features):
        """
        Evaluate signal quality and reliability.
        
        Args:
            features (dict): Signal features
            
        Returns:
            dict: Quality evaluation
        """
        quality = features['signal_quality']
        score = quality['quality_score']
        
        if score < self.thresholds['quality_min']:
            level = AlertLevel.WARNING
            reason = f"Poor signal quality ({score:.0f}/100) - measurements may be unreliable"
            recommendation = "Check sensor connection"
        elif score < 70:
            level = AlertLevel.WARNING
            reason = f"Fair signal quality ({score:.0f}/100)"
            recommendation = "Results are acceptable but could be improved"
        else:
            level = AlertLevel.NORMAL
            reason = f"Good signal quality ({score:.0f}/100)"
            recommendation = None
        
        return {
            'level': level,
            'reason': reason,
            'recommendation': recommendation,
            'score': score,
            'label': quality['quality_label']
        }
    
    def _evaluate_stability(self, features):
        """
        Evaluate heart rate stability.
        
        Args:
            features (dict): Signal features
            
        Returns:
            dict: Stability evaluation
        """
        stable = features.get('hr_stable', False)
        regular = features.get('rhythm_regular', False)
        
        if not regular:
            level = AlertLevel.WARNING
            reason = "Irregular heart rhythm detected"
            concern = "arrhythmia"
        elif not stable:
            level = AlertLevel.WARNING
            reason = "Heart rate showing high variability"
            concern = "unstable_rhythm"
        else:
            level = AlertLevel.NORMAL
            reason = "Heart rate is stable and regular"
            concern = None
        
        return {
            'level': level,
            'reason': reason,
            'concern': concern,
            'stable': stable,
            'regular': regular
        }
    
    def _calculate_confidence(self, evaluations):
        """
        Calculate decision confidence based on signal quality and consistency.
        
        Args:
            evaluations (dict): All evaluation results
            
        Returns:
            float: Confidence score (0-100)
        """
        quality_score = evaluations['quality']['score']
        
        # Base confidence on signal quality
        confidence = quality_score
        
        # Reduce confidence if conflicting signals
        alert_levels = [
            evaluations['heart_rate']['level'].value,
            evaluations['hrv']['level'].value,
            evaluations['stability']['level'].value
        ]
        
        if len(set(alert_levels)) > 2:
            confidence *= 0.8  # Conflicting signals
        
        return min(100, max(0, confidence))
    
    def _generate_explanation(self, evaluations, final_decision, confidence):
        """
        Generate human-readable explanation.
        
        Args:
            evaluations (dict): All evaluation results
            final_decision (AlertLevel): Final decision
            confidence (float): Confidence score
            
        Returns:
            str: Detailed explanation
        """
        explanation_parts = []
        
        # Decision summary
        explanation_parts.append(f"DECISION: {final_decision.name}")
        explanation_parts.append(f"CONFIDENCE: {confidence:.0f}%")
        explanation_parts.append("")
        explanation_parts.append("REASONS:")
        
        # Add all relevant reasons
        for category, eval_result in evaluations.items():
            if eval_result['level'] != AlertLevel.NORMAL or final_decision == AlertLevel.NORMAL:
                explanation_parts.append(f"  • {eval_result['reason']}")
        
        # Add recommendations if any
        recommendations = []
        if evaluations['quality'].get('recommendation'):
            recommendations.append(evaluations['quality']['recommendation'])
        
        if recommendations:
            explanation_parts.append("")
            explanation_parts.append("RECOMMENDATIONS:")
            for rec in recommendations:
                explanation_parts.append(f"  • {rec}")
        
        return "\n".join(explanation_parts)
    
    def _generate_short_explanation(self, evaluations, final_decision):
        """
        Generate concise one-line explanation.
        
        Args:
            evaluations (dict): All evaluation results
            final_decision (AlertLevel): Final decision
            
        Returns:
            str: Short explanation
        """
        if final_decision == AlertLevel.NORMAL:
            return "All measurements within normal range"
        
        concerns = []
        if evaluations['heart_rate']['concern']:
            concerns.append(evaluations['heart_rate']['concern'].replace('_', ' '))
        if evaluations['hrv']['concern']:
            concerns.append(evaluations['hrv']['concern'].replace('_', ' '))
        if evaluations['stability']['concern']:
            concerns.append(evaluations['stability']['concern'].replace('_', ' '))
        
        return ", ".join(concerns) if concerns else "Anomaly detected"
    
    def make_decision(self, features):
        """
        Make complete decision with full explainability.
        
        This is the main method called by the system.
        
        Args:
            features (dict): Extracted signal features
            
        Returns:
            dict: Complete decision with explanation
        """
        # Evaluate all aspects
        evaluations = {
            'heart_rate': self._evaluate_heart_rate(features),
            'hrv': self._evaluate_hrv(features),
            'quality': self._evaluate_signal_quality(features),
            'stability': self._evaluate_stability(features)
        }
        
        # Determine final alert level (highest severity wins)
        alert_levels = [eval['level'] for eval in evaluations.values()]
        final_decision = max(alert_levels, key=lambda x: x.value)
        
        # Calculate confidence
        confidence = self._calculate_confidence(evaluations)
        
        # Generate explanations
        full_explanation = self._generate_explanation(evaluations, final_decision, confidence)
        short_explanation = self._generate_short_explanation(evaluations, final_decision)
        
        # Create decision object
        decision = {
            'timestamp': datetime.now().isoformat(),
            'level': final_decision.name,
            'level_numeric': final_decision.value,
            'confidence': confidence,
            'explanation': full_explanation,
            'short_explanation': short_explanation,
            'evaluations': evaluations,
            'measurements': {
                'hr': features['heart_rate_bpm'],
                'hrv': features['hrv_ms'],
                'quality': features['signal_quality']['quality_score']
            }
        }
        
        # Store in history
        self.decision_history.append(decision)
        
        # Keep last 1000 decisions
        if len(self.decision_history) > 1000:
            self.decision_history.pop(0)
        
        return decision
    
    def get_decision_summary(self, decision):
        """
        Get formatted summary for display.
        
        Args:
            decision (dict): Decision object
            
        Returns:
            str: Formatted summary
        """
        symbols = {
            'NORMAL': '✓',
            'WARNING': '⚠',
            'ALERT': '⚠',
            'CRITICAL': '🚨'
        }
        
        symbol = symbols.get(decision['level'], '?')
        
        summary = f"""
╔═══════════════════════════════════════════════════════════════╗
║  {symbol} {decision['level']:^10s} - CONFIDENCE: {decision['confidence']:5.0f}%              ║
╠═══════════════════════════════════════════════════════════════╣
║  {decision['short_explanation']:<60s} ║
╠═══════════════════════════════════════════════════════════════╣
║  Heart Rate: {decision['measurements']['hr']:6.1f} BPM                                    ║
║  HRV:        {decision['measurements']['hrv']:6.1f} ms                                     ║
║  Quality:    {decision['measurements']['quality']:6.1f}/100                                    ║
╚═══════════════════════════════════════════════════════════════╝
"""
        return summary
    
    def get_statistics(self):
        """
        Get decision statistics.
        
        Returns:
            dict: Statistics
        """
        if not self.decision_history:
            return {
                'total_decisions': 0,
                'normal_rate': 0,
                'warning_rate': 0,
                'alert_rate': 0,
                'avg_confidence': 0
            }
        
        total = len(self.decision_history)
        normal = sum(1 for d in self.decision_history if d['level'] == 'NORMAL')
        warning = sum(1 for d in self.decision_history if d['level'] == 'WARNING')
        alert = sum(1 for d in self.decision_history if d['level'] in ['ALERT', 'CRITICAL'])
        avg_conf = np.mean([d['confidence'] for d in self.decision_history])
        
        return {
            'total_decisions': total,
            'normal_rate': (normal / total) * 100,
            'warning_rate': (warning / total) * 100,
            'alert_rate': (alert / total) * 100,
            'avg_confidence': avg_conf
        }


# Demo
if __name__ == "__main__":
    print("=" * 70)
    print("MODULE 5: EXPLAINABLE AI DECISION ENGINE - TESTING")
    print("=" * 70)
    
    # Create decision engine
    engine = ExplainableDecisionEngine()
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'Normal Rest',
            'features': {
                'heart_rate_bpm': 72,
                'hrv_ms': 55,
                'signal_quality': {'quality_score': 85, 'quality_label': 'GOOD'},
                'hr_stable': True,
                'rhythm_regular': True
            }
        },
        {
            'name': 'Elevated (Exercise)',
            'features': {
                'heart_rate_bpm': 115,
                'hrv_ms': 25,
                'signal_quality': {'quality_score': 78, 'quality_label': 'GOOD'},
                'hr_stable': True,
                'rhythm_regular': True
            }
        },
        {
            'name': 'High Stress',
            'features': {
                'heart_rate_bpm': 95,
                'hrv_ms': 15,
                'signal_quality': {'quality_score': 82, 'quality_label': 'GOOD'},
                'hr_stable': False,
                'rhythm_regular': True
            }
        },
        {
            'name': 'Poor Signal Quality',
            'features': {
                'heart_rate_bpm': 70,
                'hrv_ms': 50,
                'signal_quality': {'quality_score': 35, 'quality_label': 'POOR'},
                'hr_stable': True,
                'rhythm_regular': True
            }
        }
    ]
    
    print("\n[TESTING] Various scenarios...\n")
    
    for scenario in test_scenarios:
        print(f"\n{'='*70}")
        print(f"SCENARIO: {scenario['name']}")
        print(f"{'='*70}")
        
        decision = engine.make_decision(scenario['features'])
        print(engine.get_decision_summary(decision))
        print("\nFull Explanation:")
        print(decision['explanation'])
    
    # Statistics
    print("\n" + "="*70)
    print("DECISION STATISTICS")
    print("="*70)
    stats = engine.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value:.2f}")
    
    print("\n✅ Module 5 Complete!")
    print("\n🔄 Next: Module 6 - Closed-Loop Adaptive System")