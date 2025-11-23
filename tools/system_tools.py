import psutil
import time
from langchain.tools import tool
import threading


@tool
def get_system_status():
    """
    Cross-platform system status tool.

    Automatically chooses:
    - Linux/macOS → GiB (base-2)
    - Windows → GB (base-10)
    """
    import platform
    # Try GPU
    try:
        import pynvml
        pynvml.nvmlInit()
        GPU_AVAILABLE = True
    except Exception:
        GPU_AVAILABLE = False

    os_name = platform.system().lower()

    # OS-based unit logic
    if os_name == "windows":
        # Windows typically uses base-10 GB in UI/Disk
        divisor = 1e9  # GB
        unit = "GB"
    else:
        # Linux/macOS use GiB everywhere (free, top, df, psutil)
        divisor = 1024 ** 3  # GiB
        unit = "GiB"

    # Collect stats
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    status = {
        "os": os_name,
        "units": unit,

        "cpu_percent": round(cpu, 2),

        "ram_percent": round(ram.percent, 2),
        "ram_used": f"{ram.used / divisor:.2f} {unit}",
        "ram_total": f"{ram.total / divisor:.2f} {unit}",

        "disk_percent": round(disk.percent, 2),
        "disk_used": f"{disk.used / divisor:.2f} {unit}",
        "disk_total": f"{disk.total / divisor:.2f} {unit}",

        "net_sent_mb": f"{net.bytes_sent / (1024**2):.2f} MB",
        "net_recv_mb": f"{net.bytes_recv / (1024**2):.2f} MB",

        "gpu_available": GPU_AVAILABLE
    }

    # GPU support
    if GPU_AVAILABLE:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)

            # GPU memory is always reported in bytes → convert to MB (base-2)
            status.update({
                "gpu_util_percent": gpu_util.gpu,
                "gpu_mem_used": f"{mem.used / (1024**2):.2f} MB",
                "gpu_mem_total": f"{mem.total / (1024**2):.2f} MB",
                "gpu_mem_percent": round((mem.used / mem.total) * 100, 2)
            })

        except Exception as e:
            status["gpu_error"] = f"GPU query failed: {str(e)}"

    return status

system_tools = [get_system_status]