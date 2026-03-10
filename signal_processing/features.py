"""
MODULE 3: Real-Time Signal Processing & Feature Extraction

CORRECTED VERSION - Robust peak detection and error handling

This module processes raw ECG data and extracts meaningful features for AI decision-making.

Features Extracted:
1. Heart Rate (BPM)
2. Heart Rate Variability (HRV)
3. Signal Quality
4. Peak Characteristics
"""

import numpy as np
import pandas as pd
from scipy import signal
from collections import deque
import warnings


class SignalProcessor:
    """
    Real-time ECG signal processor with robust error handling.
    
    Processes raw ADC values and extracts health-relevant features.
    Designed for real-time operation with minimal latency.
    """
    
    def __init__(self, sampling_rate=250):
        """
        Initialize signal processor.
        
        Args:
            sampling_rate (int): Sampling frequency in Hz
        """
        self.sampling_rate = sampling_rate
        self.history_buffer = deque(maxlen=sampling_rate * 10)  # 10 seconds history
        self.peak_history = deque(maxlen=50)  # Last 50 detected peaks
        self.hr_history = deque(maxlen=20)  # Last 20 HR values
        
        # Design filters
        self._design_filters()
        
        # Tracking for stability
        self.last_hr = 70.0
        self.last_hrv = 50.0
        
        print(f"✓ Signal Processor initialized (SR={sampling_rate} Hz)")
    
    def _design_filters(self):
        """
        Design digital filters for ECG processing.
        
        Filters used:
        1. Bandpass filter (0.5-40 Hz) - removes baseline and high-freq noise
        2. Notch filter (50 Hz) - removes powerline interference
        """
        # Bandpass filter (0.5 to 40 Hz)
        nyquist = self.sampling_rate / 2
        low = 0.5 / nyquist
        high = 40 / nyquist
        
        # Ensure valid frequency range
        low = max(0.001, min(0.99, low))
        high = max(0.001, min(0.99, high))
        
        self.b_bandpass, self.a_bandpass = signal.butter(
            3, [low, high], btype='band'
        )
        
        # Notch filter at 50 Hz (powerline)
        f0 = 50.0  # Frequency to remove
        Q = 30.0   # Quality factor
        self.b_notch, self.a_notch = signal.iirnotch(f0, Q, self.sampling_rate)
        
        print(f"  ✓ Filters designed: Bandpass (0.5-40 Hz), Notch (50 Hz)")
    
    def filter_signal(self, ecg_data):
        """
        Apply digital filters to clean ECG signal.
        
        Args:
            ecg_data (numpy.array): Raw ADC values
            
        Returns:
            numpy.array: Filtered signal
        """
        if len(ecg_data) < 10:
            # Not enough data, return zeros
            return np.zeros_like(ecg_data)
        
        try:
            # Convert ADC values to voltage-like signal (normalized)
            normalized = (ecg_data - 2048) / 2048.0
            
            # Apply bandpass filter
            filtered = signal.filtfilt(self.b_bandpass, self.a_bandpass, normalized)
            
            # Apply notch filter
            filtered = signal.filtfilt(self.b_notch, self.a_notch, filtered)
            
            return filtered
            
        except Exception as e:
            print(f"⚠ Filter error: {e}")
            return np.zeros_like(ecg_data)
    
    def detect_peaks(self, filtered_signal):
        """
        Detect R-peaks in ECG (heartbeats) with robust error handling.
        
        Uses adaptive threshold method:
        1. Find local maxima
        2. Apply threshold based on signal statistics
        3. Enforce minimum distance between peaks
        
        Args:
            filtered_signal (numpy.array): Filtered ECG
            
        Returns:
            numpy.array: Indices of detected peaks
        """
        if len(filtered_signal) < 10:
            return np.array([])
        
        try:
            # Calculate adaptive threshold
            signal_abs = np.abs(filtered_signal)
            signal_mean = np.mean(signal_abs)
            signal_std = np.std(signal_abs)
            signal_max = np.max(signal_abs)
            
            # Robust threshold calculation
            if signal_std > 0:
                threshold = signal_mean + 0.3 * signal_std
            else:
                threshold = signal_max * 0.5
            
            # Ensure minimum threshold
            threshold = max(threshold, 0.1)
            
            # Minimum distance between peaks (in samples)
            # At HR=200 BPM, interval = 0.3 sec = 75 samples @ 250 Hz
            # At HR=40 BPM, interval = 1.5 sec = 375 samples @ 250 Hz
            min_distance = int(0.25 * self.sampling_rate)  # 0.25 sec = 62 samples
            
            # Find peaks using scipy with relaxed parameters
            peaks, properties = signal.find_peaks(
                signal_abs,
                height=threshold,
                distance=min_distance,
                prominence=threshold * 0.3
            )
            
            # If no peaks found, try with lower threshold
            if len(peaks) == 0:
                threshold = signal_max * 0.3
                peaks, properties = signal.find_peaks(
                    signal_abs,
                    height=threshold,
                    distance=min_distance
                )
            
            return peaks
            
        except Exception as e:
            print(f"⚠ Peak detection error: {e}")
            return np.array([])
    
    def calculate_heart_rate(self, peaks):
        """
        Calculate instantaneous heart rate from peak intervals.
        
        Args:
            peaks (numpy.array): Peak indices
            
        Returns:
            float: Heart rate in BPM
        """
        if len(peaks) < 2:
            # Not enough peaks, return last known HR
            return self.last_hr
        
        try:
            # Calculate intervals between consecutive peaks
            intervals = np.diff(peaks) / self.sampling_rate  # Convert to seconds
            
            # Filter out invalid intervals (too short or too long)
            valid_intervals = intervals[(intervals > 0.3) & (intervals < 2.0)]
            
            if len(valid_intervals) == 0:
                return self.last_hr
            
            # Calculate BPM from median interval (robust to outliers)
            median_interval = np.median(valid_intervals)
            heart_rate = 60.0 / median_interval
            
            # Sanity check: HR should be between 30 and 220 BPM
            heart_rate = np.clip(heart_rate, 30, 220)
            
            # Update last known HR
            self.last_hr = heart_rate
            self.hr_history.append(heart_rate)
            
            return heart_rate
            
        except Exception as e:
            print(f"⚠ HR calculation error: {e}")
            return self.last_hr
    
    def calculate_hrv(self, peaks):
        """
        Calculate Heart Rate Variability (HRV).
        
        HRV measures variation in time between heartbeats.
        We use SDNN: Standard Deviation of NN intervals
        
        Args:
            peaks (numpy.array): Peak indices
            
        Returns:
            float: HRV in milliseconds
        """
        if len(peaks) < 3:
            # Not enough peaks
            return self.last_hrv
        
        try:
            # Calculate RR intervals in milliseconds
            rr_intervals = np.diff(peaks) / self.sampling_rate * 1000
            
            # Filter out invalid intervals
            valid_rr = rr_intervals[(rr_intervals > 300) & (rr_intervals < 2000)]
            
            if len(valid_rr) < 2:
                return self.last_hrv
            
            # SDNN: Standard deviation of RR intervals
            hrv = np.std(valid_rr)
            
            # Sanity check: HRV typically 20-100 ms for normal conditions
            hrv = np.clip(hrv, 5, 200)
            
            # Update last known HRV
            self.last_hrv = hrv
            
            return hrv
            
        except Exception as e:
            print(f"⚠ HRV calculation error: {e}")
            return self.last_hrv
    
    def assess_signal_quality(self, filtered_signal, peaks):
        """
        Assess ECG signal quality.
        
        Quality indicators:
        1. SNR (Signal-to-Noise Ratio)
        2. Number of detected peaks
        3. Regularity of peaks
        
        Args:
            filtered_signal (numpy.array): Filtered ECG
            peaks (numpy.array): Detected peaks
            
        Returns:
            dict: Quality metrics
        """
        try:
            # Calculate SNR
            if len(peaks) > 0 and len(filtered_signal) > 0:
                peak_values = np.abs(filtered_signal[peaks])
                signal_power = np.mean(peak_values ** 2) if len(peak_values) > 0 else 0
                noise_power = np.var(filtered_signal)
                
                if noise_power > 0 and signal_power > 0:
                    snr = 10 * np.log10(signal_power / noise_power)
                else:
                    snr = 0
            else:
                snr = 0
            
            # Peak regularity (coefficient of variation of RR intervals)
            if len(peaks) > 2:
                rr_intervals = np.diff(peaks)
                valid_rr = rr_intervals[(rr_intervals > 0.25 * self.sampling_rate) & 
                                       (rr_intervals < 2.0 * self.sampling_rate)]
                
                if len(valid_rr) > 1 and np.mean(valid_rr) > 0:
                    regularity = np.std(valid_rr) / np.mean(valid_rr)
                else:
                    regularity = 1.0
            else:
                regularity = 1.0
            
            # Expected peaks per second (should be around 1-2 for normal HR)
            duration_sec = len(filtered_signal) / self.sampling_rate
            expected_peaks = int(duration_sec * 1.2)  # Assume ~72 BPM baseline
            peak_ratio = len(peaks) / max(1, expected_peaks)
            
            # Quality score (0-100)
            # Based on: SNR, peak count, regularity
            snr_score = min(100, max(0, (snr + 10) * 5))  # SNR contribution
            peak_score = min(100, peak_ratio * 80)  # Peak count contribution
            regularity_score = max(0, 100 - regularity * 100)  # Regularity contribution
            
            quality_score = (snr_score * 0.4 + peak_score * 0.4 + regularity_score * 0.2)
            
            # Quality category
            if quality_score > 80:
                quality_label = "EXCELLENT"
            elif quality_score > 60:
                quality_label = "GOOD"
            elif quality_score > 40:
                quality_label = "FAIR"
            else:
                quality_label = "POOR"
            
            return {
                'snr_db': snr,
                'regularity': regularity,
                'quality_score': quality_score,
                'quality_label': quality_label,
                'num_peaks': len(peaks)
            }
            
        except Exception as e:
            print(f"⚠ Quality assessment error: {e}")
            return {
                'snr_db': 0,
                'regularity': 1.0,
                'quality_score': 30,
                'quality_label': 'POOR',
                'num_peaks': 0
            }
    
    def process_batch(self, ecg_batch):
        """
        Process one batch of ECG data and extract all features.
        
        This is the main method called by the RL engine.
        
        Args:
            ecg_batch (pandas.DataFrame): Raw FPGA data
            
        Returns:
            dict: Extracted features
        """
        try:
            # Extract ADC values
            adc_values = ecg_batch['adc_value'].values
            
            # Add to history buffer
            self.history_buffer.extend(adc_values)
            
            # Filter signal
            filtered = self.filter_signal(adc_values)
            
            # Detect peaks
            peaks = self.detect_peaks(filtered)
            
            # Store peaks for history
            if len(peaks) > 0:
                self.peak_history.extend(peaks)
            
            # Calculate features
            hr = self.calculate_heart_rate(peaks)
            hrv = self.calculate_hrv(peaks)
            quality = self.assess_signal_quality(filtered, peaks)
            
            features = {
                # Primary metrics
                'heart_rate_bpm': hr,
                'hrv_ms': hrv,
                
                # Signal quality
                'signal_quality': quality,
                
                # Raw data
                'filtered_signal': filtered,
                'peak_indices': peaks,
                'raw_signal': adc_values,
                
                # Timing
                'timestamp': ecg_batch['timestamp_ms'].iloc[-1] if len(ecg_batch) > 0 else 0,
                'num_samples': len(adc_values)
            }
            
            # Add derived features
            features['hr_stable'] = self._check_hr_stability()
            features['rhythm_regular'] = quality['regularity'] < 0.2
            
            return features
            
        except Exception as e:
            print(f"⚠ Processing error: {e}")
            # Return safe default values
            return {
                'heart_rate_bpm': self.last_hr,
                'hrv_ms': self.last_hrv,
                'signal_quality': {
                    'snr_db': 0,
                    'regularity': 1.0,
                    'quality_score': 30,
                    'quality_label': 'POOR',
                    'num_peaks': 0
                },
                'filtered_signal': np.zeros(250),
                'peak_indices': np.array([]),
                'raw_signal': np.zeros(250),
                'timestamp': 0,
                'num_samples': 250,
                'hr_stable': False,
                'rhythm_regular': False
            }
    
    def _check_hr_stability(self):
        """
        Check if heart rate has been stable over recent history.
        
        Returns:
            bool: True if HR is stable
        """
        if len(self.hr_history) < 3:
            return True  # Assume stable if not enough data
        
        try:
            recent_hr = list(self.hr_history)[-10:]
            hr_std = np.std(recent_hr)
            
            # Stable if variation less than 10 BPM
            return hr_std < 10.0
            
        except:
            return True
    
    def get_summary(self, features):
        """
        Generate human-readable summary of extracted features.
        
        Args:
            features (dict): Extracted features
            
        Returns:
            str: Summary text
        """
        hr = features['heart_rate_bpm']
        hrv = features['hrv_ms']
        quality = features['signal_quality']
        
        summary = f"""
┌─────────────────────────────────────────┐
│         SIGNAL ANALYSIS SUMMARY         │
├─────────────────────────────────────────┤
│ Heart Rate:    {hr:6.1f} BPM            │
│ HRV (SDNN):    {hrv:6.1f} ms            │
│ Signal Quality: {quality['quality_label']:8s}        │
│ Quality Score:  {quality['quality_score']:5.1f}/100          │
│ Peaks Detected: {quality['num_peaks']:3d}                │
│ HR Stable:     {'YES' if features['hr_stable'] else 'NO ':3s}               │
│ Rhythm:        {'Regular' if features['rhythm_regular'] else 'Irregular':9s}        │
└─────────────────────────────────────────┘
"""
        return summary


# Demo and test
if __name__ == "__main__":
    print("=" * 70)
    print("MODULE 3: SIGNAL PROCESSING & FEATURE EXTRACTION - TESTING")
    print("=" * 70)
    
    # Import FPGA interface
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from fpga_interface.fpga_stream import FPGAInterface
    
    # Initialize
    print("\n[STEP 1] Initialize FPGA Interface and Signal Processor")
    fpga = FPGAInterface(source_type='dummy', sampling_rate=250, base_heart_rate=70)
    processor = SignalProcessor(sampling_rate=250)
    
    # Process 10 seconds of data
    print("\n[STEP 2] Process real-time data stream")
    print("-" * 70)
    
    # Suppress numpy warnings for cleaner output
    warnings.filterwarnings('ignore')
    
    for i in range(10):
        # Read data from FPGA
        ecg_batch = fpga.read_data(duration=1.0)
        
        if ecg_batch is not None:
            # Process and extract features
            features = processor.process_batch(ecg_batch)
            
            # Display results
            print(f"\n⏱ Second {i+1}/10:")
            print(processor.get_summary(features))
    
    fpga.close()
    
    print("\n✅ Module 3 Complete!")
    print("\n📊 Features Ready for RL Engine:")
    print("  ✓ Heart Rate (BPM)")
    print("  ✓ Heart Rate Variability (HRV)")
    print("  ✓ Signal Quality Metrics")
    print("  ✓ Stability Indicators")
    print("\n🔄 Next: Module 4 - Reinforcement Learning Engine")