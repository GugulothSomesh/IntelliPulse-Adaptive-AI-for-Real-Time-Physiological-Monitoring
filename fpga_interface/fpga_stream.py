"""
MODULE 2: FPGA Interface Abstraction

This module provides a unified interface to receive ECG data from multiple sources:
- Dummy data (current)
- Real FPGA via UART (future)
- Real FPGA via SPI (future)
- CSV files (replay mode)

Key Design Principle: Change data source with 1 line of code!
"""

import pandas as pd
import numpy as np
import time
from abc import ABC, abstractmethod
import sys
import os

# Add parent directory to path to import ECG simulator
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.ecg_simulator import ECGSimulator


class DataSource(ABC):
    """
    Abstract base class for all data sources.
    Any data source (dummy, UART, SPI, file) must implement these methods.
    """
    
    @abstractmethod
    def read_stream(self, duration=1.0):
        """Read one batch of data"""
        pass
    
    @abstractmethod
    def is_available(self):
        """Check if data source is ready"""
        pass
    
    @abstractmethod
    def close(self):
        """Cleanup and close connection"""
        pass


class DummyDataSource(DataSource):
    """
    Dummy data source using ECG simulator.
    This mimics FPGA output perfectly.
    """
    
    def __init__(self, sampling_rate=250, base_heart_rate=70):
        self.simulator = ECGSimulator(sampling_rate, base_heart_rate)
        self.running = True
        print("✓ Dummy Data Source initialized (simulating FPGA)")
        
    def read_stream(self, duration=1.0):
        """
        Read simulated FPGA data stream.
        
        Returns:
            pandas.DataFrame: ECG data in FPGA format
        """
        if not self.running:
            return None
        
        # Randomly vary physiological state for realistic simulation
        states = ["NORMAL", "NORMAL", "NORMAL", "EXERCISE", "STRESS"]
        state = np.random.choice(states, p=[0.7, 0.1, 0.1, 0.05, 0.05])
        
        return self.simulator.generate_stream(duration, state)
    
    def is_available(self):
        return self.running
    
    def close(self):
        self.running = False
        print("✓ Dummy data source closed")


class FPGAUARTSource(DataSource):
    """
    Real FPGA data source via UART/Serial.
    
    **FUTURE IMPLEMENTATION**
    When FPGA is ready, uncomment and configure:
    
    import serial
    
    def __init__(self, port='COM3', baudrate=115200):
        self.serial = serial.Serial(port, baudrate, timeout=1)
        
    def read_stream(self, duration=1.0):
        # Read UART packets
        # Parse according to FPGA packet structure
        # Return DataFrame with same format as dummy data
        pass
    """
    
    def __init__(self, port='COM3', baudrate=115200):
        raise NotImplementedError(
            "UART source not yet implemented. Connect FPGA hardware first.\n"
            "For now, use DummyDataSource."
        )
    
    def read_stream(self, duration=1.0):
        pass
    
    def is_available(self):
        return False
    
    def close(self):
        pass


class CSVReplaySource(DataSource):
    """
    Replay data from saved CSV file.
    Useful for:
    - Testing with known data
    - Debugging
    - Demonstrations
    """
    
    def __init__(self, filename, sampling_rate=250):
        self.data = pd.read_csv(filename)
        self.sampling_rate = sampling_rate
        self.current_index = 0
        self.samples_per_read = int(sampling_rate * 1.0)  # 1 second chunks
        print(f"✓ CSV Replay Source initialized: {filename}")
        print(f"  Total samples: {len(self.data)}")
        
    def read_stream(self, duration=1.0):
        """Read next chunk from CSV file"""
        samples_to_read = int(self.sampling_rate * duration)
        
        if self.current_index >= len(self.data):
            return None  # End of file
        
        end_index = min(self.current_index + samples_to_read, len(self.data))
        chunk = self.data.iloc[self.current_index:end_index].copy()
        self.current_index = end_index
        
        return chunk
    
    def is_available(self):
        return self.current_index < len(self.data)
    
    def close(self):
        print("✓ CSV replay source closed")


class FPGAInterface:
    """
    Main FPGA Interface - The Universal Adapter
    
    This class provides a consistent way to receive data regardless of source.
    
    Usage:
        # For development (dummy data)
        fpga = FPGAInterface(source_type='dummy')
        
        # For real FPGA (future)
        fpga = FPGAInterface(source_type='uart', port='COM3')
        
        # For replay
        fpga = FPGAInterface(source_type='csv', filename='data/dummy_ecg.csv')
    """
    
    def __init__(self, source_type='dummy', **kwargs):
        """
        Initialize FPGA interface with specified data source.
        
        Args:
            source_type (str): 'dummy', 'uart', 'spi', or 'csv'
            **kwargs: Source-specific parameters
        """
        print(f"\n{'='*70}")
        print(f"FPGA INTERFACE INITIALIZATION")
        print(f"{'='*70}")
        
        self.source_type = source_type
        self.source = None
        self.buffer = []
        self.stats = {
            'packets_received': 0,
            'total_samples': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Create appropriate data source
        if source_type == 'dummy':
            sampling_rate = kwargs.get('sampling_rate', 250)
            base_hr = kwargs.get('base_heart_rate', 70)
            self.source = DummyDataSource(sampling_rate, base_hr)
            
        elif source_type == 'csv':
            filename = kwargs.get('filename', 'data/dummy_ecg.csv')
            sampling_rate = kwargs.get('sampling_rate', 250)
            self.source = CSVReplaySource(filename, sampling_rate)
            
        elif source_type == 'uart':
            self.source = FPGAUARTSource(**kwargs)
            
        else:
            raise ValueError(f"Unknown source type: {source_type}")
        
        print(f"✓ Interface ready: {source_type.upper()} mode")
        print(f"{'='*70}\n")
    
    def read_data(self, duration=1.0):
        """
        Read data from FPGA (or simulated FPGA).
        
        Args:
            duration (float): Duration in seconds
            
        Returns:
            pandas.DataFrame: ECG data
        """
        if not self.source.is_available():
            return None
        
        try:
            data = self.source.read_stream(duration)
            
            if data is not None and len(data) > 0:
                self.stats['packets_received'] += 1
                self.stats['total_samples'] += len(data)
                self.buffer.append(data)
                
            return data
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"⚠ Error reading data: {e}")
            return None
    
    def get_stats(self):
        """Get interface statistics"""
        elapsed = time.time() - self.stats['start_time']
        return {
            'packets': self.stats['packets_received'],
            'samples': self.stats['total_samples'],
            'errors': self.stats['errors'],
            'runtime_sec': elapsed,
            'sample_rate': self.stats['total_samples'] / elapsed if elapsed > 0 else 0
        }
    
    def close(self):
        """Close interface and cleanup"""
        if self.source:
            self.source.close()
        
        stats = self.get_stats()
        print(f"\n{'='*70}")
        print(f"FPGA INTERFACE CLOSED")
        print(f"{'='*70}")
        print(f"  Packets received: {stats['packets']}")
        print(f"  Total samples: {stats['samples']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Runtime: {stats['runtime_sec']:.2f} seconds")
        print(f"  Avg sample rate: {stats['sample_rate']:.2f} samples/sec")
        print(f"{'='*70}\n")


# Demo and test
if __name__ == "__main__":
    print("=" * 70)
    print("MODULE 2: FPGA INTERFACE ABSTRACTION - TESTING")
    print("=" * 70)
    
    # Test 1: Dummy data source
    print("\n[TEST 1] Dummy Data Source (simulating FPGA)")
    print("-" * 70)
    fpga = FPGAInterface(source_type='dummy', sampling_rate=250, base_heart_rate=70)
    
    print("\nReading 5 seconds of data...")
    for i in range(5):
        data = fpga.read_data(duration=1.0)
        if data is not None:
            print(f"  Second {i+1}: {len(data)} samples, "
                  f"HR={data['heart_rate_bpm'].iloc[0]:.0f} BPM, "
                  f"State={data['state'].iloc[0]}")
        time.sleep(0.1)  # Small delay for realistic streaming
    
    stats = fpga.get_stats()
    print(f"\n📊 Interface Statistics:")
    print(f"  Total samples: {stats['samples']}")
    print(f"  Sample rate: {stats['sample_rate']:.2f} samples/sec")
    
    fpga.close()
    
    # Test 2: CSV Replay (if file exists)
    print("\n" + "=" * 70)
    print("[TEST 2] CSV Replay Source")
    print("-" * 70)
    
    csv_file = 'data/dummy_ecg.csv'
    if os.path.exists(csv_file):
        fpga_replay = FPGAInterface(source_type='csv', filename=csv_file)
        
        print("\nReading 3 seconds from CSV...")
        for i in range(3):
            data = fpga_replay.read_data(duration=1.0)
            if data is not None:
                print(f"  Second {i+1}: {len(data)} samples")
        
        fpga_replay.close()
    else:
        print(f"⚠ CSV file not found: {csv_file}")
        print("  Run ecg_simulator.py first to generate sample data")
    
    print("\n✅ Module 2 Complete!")
    print("\n🔄 Key Achievement:")
    print("  ✓ Can switch between dummy/real FPGA with 1 line")
    print("  ✓ Same interface for all data sources")
    print("  ✓ Ready for Module 3: Signal Processing")