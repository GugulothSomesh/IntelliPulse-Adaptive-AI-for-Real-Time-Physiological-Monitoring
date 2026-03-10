"""
MODULE 4: Reinforcement Learning Engine (Q-Learning)

This is the BRAIN of the adaptive system.

🎯 What is Reinforcement Learning?
RL is learning through trial and error with rewards/penalties.
Like training a dog: good behavior → treat, bad behavior → no treat.

🎯 Why Q-Learning?
Q-Learning learns the "quality" (Q-value) of taking actions in different states.
It's simple, interpretable, and perfect for this application.

🎯 How it adapts to YOU:
- Learns your normal heart rate range
- Adjusts alert thresholds automatically
- Reduces false alarms over time
- Gets smarter with every heartbeat

Components:
1. STATE: Current physiological condition
2. ACTION: Threshold adjustments
3. REWARD: Feedback on decision quality
4. POLICY: Learned decision strategy
"""

import numpy as np
import pandas as pd
import json
import os
from collections import defaultdict


class AdaptiveRLAgent:
    """
    Reinforcement Learning Agent for personalized health monitoring.
    
    This agent learns:
    - Your baseline heart rate
    - Your normal variability patterns
    - When to alert vs when to stay quiet
    - How to minimize false positives
    """
    
    def __init__(self, learning_rate=0.1, discount_factor=0.95, epsilon=0.2):
        """
        Initialize RL agent.
        
        Args:
            learning_rate (float): How fast to learn (0-1)
                                   High = adapt quickly, Low = stable learning
            discount_factor (float): How much to value future rewards (0-1)
                                     High = long-term thinking
            epsilon (float): Exploration rate (0-1)
                            High = try new things, Low = stick to what works
        """
        # Q-Learning parameters
        self.alpha = learning_rate       # α: learning rate
        self.gamma = discount_factor     # γ: discount factor
        self.epsilon = epsilon           # ε: exploration rate
        
        # Q-Table: stores learned values for (state, action) pairs
        # Q(s,a) = expected total reward for taking action a in state s
        self.q_table = defaultdict(lambda: np.zeros(5))
        
        # User profile (personalized baselines)
        self.user_profile = {
            'baseline_hr': 70.0,        # Will adapt to user
            'baseline_hrv': 50.0,       # Will adapt to user
            'hr_std': 10.0,             # Normal variation
            'alert_threshold_hr': 100,   # Current threshold (will adapt)
            'alert_threshold_hrv': 30,   # Low HRV threshold
            'sensitivity': 1.0          # Alert sensitivity (1.0 = normal)
        }
        
        # Learning statistics
        self.stats = {
            'episodes': 0,
            'total_reward': 0,
            'false_positives': 0,
            'true_positives': 0,
            'true_negatives': 0,
            'false_negatives': 0,
            'adaptations_made': 0
        }
        
        # History for baseline learning
        self.hr_history = []
        self.hrv_history = []
        
        print("🧠 Reinforcement Learning Agent Initialized")
        print(f"   Learning Rate: {self.alpha}")
        print(f"   Discount Factor: {self.gamma}")
        print(f"   Exploration Rate: {self.epsilon}")
    
    def _discretize_state(self, features):
        """
        Convert continuous features to discrete state.
        
        State representation:
        - HR Zone: LOW (0), NORMAL (1), ELEVATED (2), HIGH (3)
        - HRV Zone: LOW (0), NORMAL (1), HIGH (2)
        - Quality: POOR (0), GOOD (1)
        
        Args:
            features (dict): Signal features
            
        Returns:
            tuple: Discrete state representation
        """
        hr = features['heart_rate_bpm']
        hrv = features['hrv_ms']
        quality = features['signal_quality']['quality_score']
        
        # Discretize HR (relative to baseline)
        baseline = self.user_profile['baseline_hr']
        hr_std = self.user_profile['hr_std']
        
        if hr < baseline - hr_std:
            hr_zone = 0  # LOW
        elif hr < baseline + hr_std:
            hr_zone = 1  # NORMAL
        elif hr < baseline + 2 * hr_std:
            hr_zone = 2  # ELEVATED
        else:
            hr_zone = 3  # HIGH
        
        # Discretize HRV
        hrv_baseline = self.user_profile['baseline_hrv']
        if hrv < hrv_baseline * 0.7:
            hrv_zone = 0  # LOW (stressed)
        elif hrv < hrv_baseline * 1.3:
            hrv_zone = 1  # NORMAL
        else:
            hrv_zone = 2  # HIGH (relaxed)
        
        # Quality
        quality_zone = 1 if quality > 60 else 0
        
        state = (hr_zone, hrv_zone, quality_zone)
        return state
    
    def _get_actions(self):
        """
        Define possible actions.
        
        Actions:
        0: DECREASE sensitivity (less alerts)
        1: KEEP current settings
        2: INCREASE sensitivity (more alerts)
        3: ADJUST baseline up
        4: ADJUST baseline down
        
        Returns:
            dict: Action descriptions
        """
        return {
            0: "DECREASE_SENSITIVITY",
            1: "MAINTAIN",
            2: "INCREASE_SENSITIVITY",
            3: "BASELINE_UP",
            4: "BASELINE_DOWN"
        }
    
    def select_action(self, state):
        """
        Select action using ε-greedy policy.
        
        Exploration vs Exploitation:
        - With probability ε: explore (random action)
        - With probability 1-ε: exploit (best known action)
        
        Args:
            state (tuple): Current state
            
        Returns:
            int: Selected action
        """
        # ε-greedy action selection
        if np.random.random() < self.epsilon:
            # Explore: random action
            action = np.random.randint(0, 5)
        else:
            # Exploit: best action based on Q-values
            action = np.argmax(self.q_table[state])
        
        return action
    
    def _execute_action(self, action):
        """
        Execute the selected action (modify thresholds).
        
        Args:
            action (int): Action to execute
        """
        actions_map = self._get_actions()
        
        if action == 0:  # DECREASE sensitivity
            self.user_profile['sensitivity'] = max(0.5, self.user_profile['sensitivity'] - 0.1)
            self.stats['adaptations_made'] += 1
            
        elif action == 2:  # INCREASE sensitivity
            self.user_profile['sensitivity'] = min(2.0, self.user_profile['sensitivity'] + 0.1)
            self.stats['adaptations_made'] += 1
            
        elif action == 3:  # BASELINE up
            self.user_profile['baseline_hr'] += 2
            self.stats['adaptations_made'] += 1
            
        elif action == 4:  # BASELINE down
            self.user_profile['baseline_hr'] -= 2
            self.stats['adaptations_made'] += 1
    
    def _calculate_reward(self, features, decision, user_feedback=None):
        """
        Calculate reward for the decision made.
        
        Reward structure:
        +10: Correct alert (true positive)
        +5:  Correct normal (true negative)
        -10: False alert (false positive) - PENALTY
        -15: Missed alert (false negative) - BIGGER PENALTY
        +2:  Good signal quality maintained
        
        Args:
            features (dict): Current features
            decision (str): Decision made (NORMAL/WARNING/ALERT)
            user_feedback (str): User's actual state (if known)
            
        Returns:
            float: Reward value
        """
        reward = 0
        
        hr = features['heart_rate_bpm']
        hrv = features['hrv_ms']
        quality = features['signal_quality']['quality_score']
        
        # Ground truth (in real system, this comes from user feedback or medical validation)
        # For now, we simulate it based on thresholds
        actual_alert_needed = (hr > 110 or hr < 50 or hrv < 25)
        
        # Reward based on decision accuracy
        if decision == "ALERT" or decision == "WARNING":
            if actual_alert_needed:
                reward += 10  # True positive
                self.stats['true_positives'] += 1
            else:
                reward -= 10  # False positive (PENALTY)
                self.stats['false_positives'] += 1
        else:  # NORMAL
            if not actual_alert_needed:
                reward += 5   # True negative
                self.stats['true_negatives'] += 1
            else:
                reward -= 15  # False negative (BIGGER PENALTY)
                self.stats['false_negatives'] += 1
        
        # Bonus for good signal quality
        if quality > 80:
            reward += 2
        
        # Penalty for poor quality decisions
        if quality < 40 and decision != "NORMAL":
            reward -= 3
        
        self.stats['total_reward'] += reward
        return reward
    
    def update_baseline(self, features):
        """
        Update user baseline using exponential moving average.
        
        This allows the system to adapt to long-term changes in user's
        physiological state (e.g., improved fitness).
        
        Args:
            features (dict): Current features
        """
        hr = features['heart_rate_bpm']
        hrv = features['hrv_ms']
        
        # Store in history
        self.hr_history.append(hr)
        self.hrv_history.append(hrv)
        
        # Keep last 500 measurements
        if len(self.hr_history) > 500:
            self.hr_history.pop(0)
            self.hrv_history.pop(0)
        
        # Update baseline (slow adaptation)
        if len(self.hr_history) > 10:
            # Exponential moving average
            alpha_baseline = 0.05  # Slow adaptation
            self.user_profile['baseline_hr'] = (
                alpha_baseline * hr + 
                (1 - alpha_baseline) * self.user_profile['baseline_hr']
            )
            self.user_profile['baseline_hrv'] = (
                alpha_baseline * hrv + 
                (1 - alpha_baseline) * self.user_profile['baseline_hrv']
            )
            
            # Update standard deviation
            if len(self.hr_history) > 30:
                self.user_profile['hr_std'] = np.std(self.hr_history[-30:])
    
    def learn(self, state, action, reward, next_state):
        """
        Q-Learning update rule.
        
        Q(s,a) ← Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
        
        This updates our knowledge about the value of taking action a in state s.
        
        Args:
            state (tuple): Previous state
            action (int): Action taken
            reward (float): Reward received
            next_state (tuple): New state after action
        """
        # Current Q-value
        current_q = self.q_table[state][action]
        
        # Best next Q-value
        max_next_q = np.max(self.q_table[next_state])
        
        # Q-Learning update
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        
        # Update Q-table
        self.q_table[state][action] = new_q
        
        self.stats['episodes'] += 1
    
    def step(self, features, decision):
        """
        Complete RL step: observe → act → learn.
        
        This is the main method called each time new data arrives.
        
        Args:
            features (dict): Current signal features
            decision (str): Decision made by explainable AI
            
        Returns:
            dict: RL step information
        """
        # Get current state
        state = self._discretize_state(features)
        
        # Select action
        action = self.select_action(state)
        
        # Execute action
        self._execute_action(action)
        
        # Calculate reward
        reward = self._calculate_reward(features, decision)
        
        # Update baseline (slow adaptation)
        self.update_baseline(features)
        
        # Get next state (after action)
        next_state = self._discretize_state(features)
        
        # Learn from experience
        self.learn(state, action, reward, next_state)
        
        # Return info
        return {
            'state': state,
            'action': self._get_actions()[action],
            'reward': reward,
            'q_value': self.q_table[state][action],
            'baseline_hr': self.user_profile['baseline_hr'],
            'sensitivity': self.user_profile['sensitivity']
        }
    
    def get_learning_progress(self):
        """
        Get learning progress metrics.
        
        Returns:
            dict: Progress statistics
        """
        total_decisions = (self.stats['true_positives'] + self.stats['true_negatives'] +
                          self.stats['false_positives'] + self.stats['false_negatives'])
        
        if total_decisions > 0:
            accuracy = ((self.stats['true_positives'] + self.stats['true_negatives']) / 
                       total_decisions * 100)
            precision = (self.stats['true_positives'] / 
                        (self.stats['true_positives'] + self.stats['false_positives'])
                        if (self.stats['true_positives'] + self.stats['false_positives']) > 0 else 0)
        else:
            accuracy = 0
            precision = 0
        
        return {
            'episodes': self.stats['episodes'],
            'accuracy': accuracy,
            'precision': precision * 100,
            'false_positive_rate': (self.stats['false_positives'] / total_decisions * 100 
                                   if total_decisions > 0 else 0),
            'avg_reward': (self.stats['total_reward'] / self.stats['episodes'] 
                          if self.stats['episodes'] > 0 else 0),
            'adaptations': self.stats['adaptations_made'],
            'q_table_size': len(self.q_table)
        }
    
    def save_model(self, filename='rl_engine/trained_model.json'):
        """Save learned Q-table and user profile."""
        model_data = {
            'q_table': {str(k): v.tolist() for k, v in self.q_table.items()},
            'user_profile': self.user_profile,
            'stats': self.stats
        }
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        print(f"✓ Model saved: {filename}")
    
    def load_model(self, filename='rl_engine/trained_model.json'):
        """Load trained Q-table and user profile."""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                model_data = json.load(f)
            
            self.q_table = defaultdict(lambda: np.zeros(5))
            for k, v in model_data['q_table'].items():
                self.q_table[eval(k)] = np.array(v)
            
            self.user_profile = model_data['user_profile']
            self.stats = model_data['stats']
            
            print(f"✓ Model loaded: {filename}")
        else:
            print(f"⚠ Model file not found: {filename}")


# Demo
if __name__ == "__main__":
    print("=" * 70)
    print("MODULE 4: REINFORCEMENT LEARNING ENGINE - TESTING")
    print("=" * 70)
    
    # Create agent
    agent = AdaptiveRLAgent(learning_rate=0.1, discount_factor=0.95, epsilon=0.2)
    
    # Simulate learning over time
    print("\n[SIMULATION] Learning over 50 episodes...\n")
    
    for episode in range(50):
        # Simulate features
        features = {
            'heart_rate_bpm': 70 + np.random.normal(0, 10),
            'hrv_ms': 50 + np.random.normal(0, 15),
            'signal_quality': {'quality_score': 80 + np.random.normal(0, 10)}
        }
        
        # Make decision (dummy)
        decision = "NORMAL" if features['heart_rate_bpm'] < 100 else "ALERT"
        
        # RL step
        rl_info = agent.step(features, decision)
        
        if (episode + 1) % 10 == 0:
            progress = agent.get_learning_progress()
            print(f"Episode {episode + 1}:")
            print(f"  Accuracy: {progress['accuracy']:.1f}%")
            print(f"  Avg Reward: {progress['avg_reward']:.2f}")
            print(f"  Baseline HR: {rl_info['baseline_hr']:.1f} BPM")
            print(f"  Adaptations: {progress['adaptations']}")
            print()
    
    # Final progress
    print("=" * 70)
    print("LEARNING COMPLETE")
    print("=" * 70)
    final_progress = agent.get_learning_progress()
    for key, value in final_progress.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Module 4 Complete!")
    print("\n🔄 Next: Module 5 - Explainable AI Decision Layer")