import wmi
import platform

def get_hardware_profile():
    profile = {
        "cpu": "Desconocido",
        "cpu_brand": "unknown",
        "gpu": "Desconocido",
        "gpu_brand": "unknown",
        "ram_gb": 0,
        "cores": 0,
    }

    try:
        c = wmi.WMI()

        cpu = c.Win32_Processor()[0]
        profile["cpu"] = cpu.Name.strip()
        profile["cores"] = cpu.NumberOfCores

        name_lower = profile["cpu"].lower()
        if "amd" in name_lower or "ryzen" in name_lower:
            profile["cpu_brand"] = "amd"
        elif "intel" in name_lower:
            profile["cpu_brand"] = "intel"

        for gpu in c.Win32_VideoController():
            name = gpu.Name.strip()
            name_lower = name.lower()
            if "nvidia" in name_lower or "rtx" in name_lower or "gtx" in name_lower:
                profile["gpu"] = name
                profile["gpu_brand"] = "nvidia"
                break
            elif "amd" in name_lower or "radeon" in name_lower:
                profile["gpu"] = name
                profile["gpu_brand"] = "amd"
                break

        ram = c.Win32_ComputerSystem()[0]
        profile["ram_gb"] = round(int(ram.TotalPhysicalMemory) / (1024 ** 3))

    except Exception:
        pass

    return profile
