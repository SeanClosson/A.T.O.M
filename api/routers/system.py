# api/routers/system.py

from fastapi import APIRouter
import time
import psutil

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "timestamp": time.time()}

@router.get("/version")
def version():
    return {"version": "1.0", "api": "ATOM API"}

def get_temperature_c():
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None

        # Common Linux sensors
        for key in ["coretemp", "cpu_thermal", "k10temp"]:
            if key in temps:
                entries = temps[key]
                if entries and hasattr(entries[0], "current"):
                    return float(entries[0].current)

        # fallback: first entry anywhere
        for entries in temps.values():
            if entries and hasattr(entries[0], "current"):
                return float(entries[0].current)

    except Exception:
        pass

    return None


@router.get("/load")
async def system_load():
    try:
        # CPU load as 0–1
        cpu_percent = psutil.cpu_percent(interval=0.1) / 100.0

        temp = get_temperature_c()

        # If no temperature sensor, fake a stable safe value so UI doesn't break
        if temp is None:
            temp = 50.0

        return {
            "cpuLoad": round(cpu_percent, 3),
            "temperature": round(temp, 2)
        }

    except Exception as e:
        print("SYSTEM LOAD ERROR:", e)
        return {
            "cpuLoad": 0.0,
            "temperature": 0.0,
            "error": str(e)
        }