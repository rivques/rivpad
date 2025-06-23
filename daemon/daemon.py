import time
import psutil
import serial
import serial.tools.list_ports
from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetUtilizationRates, nvmlDeviceGetMemoryInfo
import threading

# Initialize NVIDIA Management Library
nvmlInit()
gpu_handle = nvmlDeviceGetHandleByIndex(0)  # Assuming a single GPU

# Automatically detect the serial port with VID 0x1209 and PID 0x0001
ports = serial.tools.list_ports.comports()
selected_port = None
for port in ports:
    if port.vid == 0x1209 and port.pid == 0x0001:
        selected_port = port.device

print(f"Using serial port: {selected_port}")  # Log the selected serial port

# Initialize serial communication
serial_port = serial.Serial(selected_port, baudrate=9600, timeout=1)

def get_system_utilization():
    """Gather system utilization metrics."""
    # CPU average utilization
    cpu_av = psutil.cpu_percent(interval=1)

    # CPU peak utilization
    cpu_pk = max(psutil.cpu_percent(percpu=True))

    # RAM utilization
    ram = psutil.virtual_memory().percent

    # Disk utilization
    disk = psutil.disk_usage('/').percent

    # Network utilization (approximation based on bytes sent/received)
    net_io_start = psutil.net_io_counters()
    time.sleep(1)  # Measure over 1 second
    net_io_end = psutil.net_io_counters()
    net = ((net_io_end.bytes_sent + net_io_end.bytes_recv) - (net_io_start.bytes_sent + net_io_start.bytes_recv)) / (1024 * 1024)  # MB/s

    # GPU utilization
    gpu_util = nvmlDeviceGetUtilizationRates(gpu_handle).gpu

    # VRAM utilization
    vram_info = nvmlDeviceGetMemoryInfo(gpu_handle)
    vram = (vram_info.used / vram_info.total) * 100

    return [
        int(cpu_av),
        int(cpu_pk),
        int(ram),
        int(disk),
        int(net),
        int(gpu_util),
        int(vram)
    ]


def main():
    global serial_port
    while True:
        try:
            # Check if the serial port is open
            if not serial_port.is_open:
                print("Serial port disconnected. Attempting to reconnect...")
                serial_port.close()  # Ensure it's closed before reconnecting
                ports = serial.tools.list_ports.comports()
                selected_port = None
                for port in ports:
                    if port.vid == 0x1209 and port.pid == 0x0001:
                        selected_port = port.device
                        

                if selected_port:
                    serial_port = serial.Serial(selected_port, baudrate=9600, timeout=1)
                    print(f"Reconnected to serial port: {selected_port}")
                else:
                    print("No valid serial port found. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue

            # Get utilization metrics
            utilization = get_system_utilization()

            # Format as comma-separated string
            utilization_str = ','.join(map(str, utilization)) + '\n'

            # Send over serial
            buf = utilization_str.encode('utf-8')
            bytes_sent = serial_port.write(buf)

            # Debug output
            print(f"Sent ({bytes_sent}): {utilization_str.strip()}")

            time.sleep(1)  # Add a delay to reduce CPU usage

        except serial.SerialException as e:
            print(f"Serial error: {e}. Attempting to reconnect...")
            serial_port.close()
            time.sleep(5)  # Wait before retrying

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)  # Add a delay to avoid rapid error loops

if __name__ == "__main__":
    main()
