import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import struct

# Configure serial port - CHANGE 'COM3' to your port
# Windows: Check Device Manager for "USB Serial Port (COMx)"
# Linux/Mac: Usually /dev/ttyUSB0 or /dev/ttyUSB1
try:
    ser = serial.Serial('COM3', 115200, timeout=0.1)
    print(f"Connected to {ser.port}")
except Exception as e:
    print(f"Error opening serial port: {e}")
    print("Available ports:")
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"  {port.device}")
    exit()

# Data buffer
data_buffer = deque(maxlen=1000)

fig, ax = plt.subplots(figsize=(12, 6))
line, = ax.plot([], [], 'b-', linewidth=0.8)
ax.set_ylim(0, 4096)  # 12-bit ADC range
ax.set_xlim(0, 1000)
ax.set_title('ECG Signal (Real-time)', fontsize=14)
ax.set_xlabel('Sample')
ax.set_ylabel('ADC Value (0-4095)')
ax.grid(True, alpha=0.3)

def init():
    line.set_data([], [])
    return line,

byte_buffer = bytearray()

def update(frame):
    global byte_buffer
    
    if ser.in_waiting:
        try:
            # Read available bytes
            new_bytes = ser.read(ser.in_waiting)
            byte_buffer.extend(new_bytes)
            
            # Process pairs of bytes (2 bytes = 1 sample)
            while len(byte_buffer) >= 2:
                # Combine two bytes into 12-bit value
                high_byte = byte_buffer[0]
                low_byte = byte_buffer[1]
                value = ((high_byte & 0x0F) << 8) | low_byte
                
                data_buffer.append(value)
                
                # Remove processed bytes
                byte_buffer = byte_buffer[2:]
            
            if len(data_buffer) > 0:
                line.set_data(range(len(data_buffer)), list(data_buffer))
                
        except Exception as e:
            print(f"Error: {e}")
            pass
    
    return line,

ani = FuncAnimation(fig, update, init_func=init, blit=True, interval=20)

print("Starting ECG monitoring... Touch the electrodes to your body.")
print("Press Ctrl+C to stop.")

try:
    plt.show()
except KeyboardInterrupt:
    print("\nStopping...")
    ser.close()