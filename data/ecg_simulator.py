"""
MODULE 1: ECG Digital Twin - Realistic Physiological Signal Generator

This module creates realistic ECG-like signals that mimic real FPGA sensor output.
Perfect for testing before connecting actual hardware.

Key Features:
- Generates heart rate with natural variability
- Adds realistic noise
- Simulates different physiological states
- Output format matches FPGA UART/SPI stream
"""

import numpy as np
import pandas as pd
from datetime import datetime
import time


class ECGSimulator:
    """
    Digital Twin for ECG signal generation.
    
    This simulates what an FPGA would send after:
    1. Reading analog ECG sensor
    2. ADC conversion (12-bit)
    3. Digital filtering
    4. UART/SPI transmission
    """
    
    def __init__(self, sampling_rate=250, base_heart_rate=70):
        """
        Initialize ECG simulator.
        
        Args:
            sampling_rate (int): Samples per second (Hz). FPGA typical: 250-1000 Hz
            base_heart_rate (int): Normal resting heart rate (BPM)
        """
        self.sampling_rate = sampling_rate
        self.base_hr = base_heart_rate
        self.current_hr = base_heart_rate
        self.time_elapsed = 0
        self.state = "NORMAL"  # NORMAL, EXERCISE, STRESS, ANOMALY
        
        print(f"✓ ECG Simulator initialized")
        print(f"  Sampling Rate: {sampling_rate} Hz")
        print(f"  Base Heart Rate: {base_heart_rate} BPM")
        
    def _generate_ecg_wave(self, duration=1.0):
        """
        Generate one second of ECG signal using simplified cardiac cycle.
        
        ECG Wave Components:
        - P wave: Atrial contraction
        - QRS complex: Ventricular contraction (main peak)
        - T wave: Ventricular recovery
        
        Args:
            duration (float): Duration in seconds
            
        Returns:
            numpy.array: ECG signal samples
        """
        num_samples = int(duration * self.sampling_rate)
        t = np.linspace(0, duration, num_samples)
        
        # Calculate beats in this duration
        hr = self.current_hr + np.random.normal(0, 2)  # Natural HR variability
        beats_per_second = hr / 60.0
        
        signal = np.zeros(num_samples)
        
        # Generate each heartbeat
        beat_interval = 1.0 / beats_per_second
        num_beats = int(duration / beat_interval) + 1
        
        for beat in range(num_beats):
            beat_time = beat * beat_interval
            
            # QRS complex (main spike) - simplified Gaussian
            qrs_center = beat_time
            qrs_width = 0.05  # 50ms duration
            qrs = 1.0 * np.exp(-((t - qrs_center) ** 2) / (2 * qrs_width ** 2))
            
            # P wave (smaller, before QRS)
            p_center = beat_time - 0.15
            p_width = 0.08
            p_wave = 0.25 * np.exp(-((t - p_center) ** 2) / (2 * p_width ** 2))
            
            # T wave (after QRS)
            t_center = beat_time + 0.20
            t_width = 0.10
            t_wave = 0.35 * np.exp(-((t - t_center) ** 2) / (2 * t_width ** 2))
            
            signal += qrs + p_wave + t_wave
        
        return signal
    
    def _add_realistic_noise(self, signal):
        """
        Add realistic noise sources:
        1. Baseline wander (breathing, movement)
        2. Muscle noise (EMG)
        3. Powerline interference (50/60 Hz)
        4. ADC quantization noise
        
        Args:
            signal (numpy.array): Clean ECG signal
            
        Returns:
            numpy.array: Noisy signal
        """
        num_samples = len(signal)
        t = np.linspace(0, len(signal) / self.sampling_rate, num_samples)
        
        # 1. Baseline wander (slow drift, 0.15-0.3 Hz)
        baseline_wander = 0.05 * np.sin(2 * np.pi * 0.2 * t)
        
        # 2. Muscle noise (high frequency, random)
        muscle_noise = np.random.normal(0, 0.02, num_samples)
        
        # 3. Powerline interference (50 Hz or 60 Hz)
        powerline = 0.01 * np.sin(2 * np.pi * 50 * t)
        
        # 4. ADC quantization (12-bit ADC simulation)
        adc_resolution = 4096  # 12-bit
        signal_quantized = np.round(signal * adc_resolution) / adc_resolution
        
        # Combine all noise sources
        noisy_signal = signal_quantized + baseline_wander + muscle_noise + powerline
        
        return noisy_signal
    
    def _convert_to_fpga_format(self, signal):
        """
        Convert signal to FPGA output format.
        
        FPGA Output Format (typical):
        - 12-bit ADC values (0-4095)
        - Timestamp (milliseconds)
        - Status byte
        
        Args:
            signal (numpy.array): Normalized signal (-1 to 1)
            
        Returns:
            pandas.DataFrame: FPGA-formatted data
        """
        # Scale to 12-bit ADC range (0-4095)
        # Center at 2048, scale to use ±1500 range
        adc_values = 2048 + (signal * 1500)
        adc_values = np.clip(adc_values, 0, 4095).astype(np.uint16)
        
        # Generate timestamps (milliseconds)
        num_samples = len(signal)
        timestamps = self.time_elapsed + np.arange(num_samples) * (1000.0 / self.sampling_rate)
        
        # Status byte (0 = normal, 1 = lead-off, 2 = saturation)
        status = np.zeros(num_samples, dtype=np.uint8)
        
        # Create DataFrame (like FPGA UART packet structure)
        data = pd.DataFrame({
            'timestamp_ms': timestamps.astype(np.uint32),
            'adc_value': adc_values,
            'status': status,
            'heart_rate_bpm': self.current_hr,
            'state': self.state
        })
        
        self.time_elapsed = timestamps[-1] + (1000.0 / self.sampling_rate)
        
        return data
    
    def generate_stream(self, duration=1.0, state="NORMAL"):
        """
        Generate one batch of ECG data (like FPGA sending 1 second of data).
        
        Args:
            duration (float): Duration in seconds
            state (str): Physiological state (NORMAL, EXERCISE, STRESS, ANOMALY)
            
        Returns:
            pandas.DataFrame: FPGA-formatted ECG data
        """
        self.state = state
        
        # Adjust heart rate based on state
        state_hr_map = {
            "NORMAL": self.base_hr,
            "EXERCISE": self.base_hr + 40,
            "STRESS": self.base_hr + 25,
            "ANOMALY": self.base_hr + np.random.randint(-20, 50)
        }
        self.current_hr = state_hr_map.get(state, self.base_hr)
        
        # Generate clean ECG
        clean_signal = self._generate_ecg_wave(duration)
        
        # Add realistic noise
        noisy_signal = self._add_realistic_noise(clean_signal)
        
        # Convert to FPGA format
        fpga_data = self._convert_to_fpga_format(noisy_signal)
        
        return fpga_data
    
    def save_sample_data(self, filename='data/dummy_ecg.csv', duration=60):
        """
        Generate and save sample ECG data for testing.
        
        Args:
            filename (str): Output CSV file path
            duration (int): Total duration in seconds
        """
        print(f"\n📊 Generating {duration} seconds of sample ECG data...")
        
        all_data = []
        states = ["NORMAL"] * 30 + ["EXERCISE"] * 15 + ["STRESS"] * 10 + ["NORMAL"] * 5
        
        for i in range(duration):
            state = states[i] if i < len(states) else "NORMAL"
            data = self.generate_stream(duration=1.0, state=state)
            all_data.append(data)
            
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{duration} seconds")
        
        # Combine all data
        full_data = pd.concat(all_data, ignore_index=True)
        full_data.to_csv(filename, index=False)
        
        print(f"✓ Sample data saved: {filename}")
        print(f"  Total samples: {len(full_data)}")
        print(f"  File size: {len(full_data) * 4 / 1024:.2f} KB")
        print(f"\n📋 Data format matches FPGA UART output:")
        print(full_data.head(10))


# Demo usage
if __name__ == "__main__":
    print("=" * 70)
    print("MODULE 1: ECG DIGITAL TWIN - PHYSIOLOGICAL SIGNAL GENERATOR")
    print("=" * 70)
    
    # Create simulator
    ecg_sim = ECGSimulator(sampling_rate=250, base_heart_rate=70)
    
    # Generate and save sample data
    ecg_sim.save_sample_data(filename='data/dummy_ecg.csv', duration=60)
    
    print("\n✅ Module 1 Complete!")
    print("\n🔄 Next: This data will feed into the FPGA Interface (Module 2)")
    print("   Later: Replace with real FPGA UART/SPI data - no code changes needed!")