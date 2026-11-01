
import platform
import socket
import psutil
import subprocess
import shutil
import re


class PcInfo:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.system_info = self._get_system_info()
        self.cpu_info = self._get_cpu_info()
        self.gpu_info = self._get_gpu_info()
        self.memory_info = self._get_memory_info()
        self.storage_info = self._get_storage_info()
        self.network_info = self._get_network_info()

    @staticmethod
    def to_gb(value):
        return round(value / (1024 ** 3), 2)

    @staticmethod
    def section(title):
        print(f"\n{'=' * 15} {title} {'=' * 15}")

    @staticmethod
    def print_info(info):
        for key, value in info.items():
            print(f"{key:<20}: {value}")

    @staticmethod
    def _run_command(command, timeout=5):
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return None

    def _get_system_info(self):
        return {
            "Hostname": self.hostname,
            "OS": platform.system(),
            "OS Version": platform.release(),
            "Architecture": platform.machine(),
            "Platform": platform.platform(),
            "Python Version": platform.python_version(),
        }

    def _get_cpu_info(self):
        return {
            "Processor": platform.processor() or "Unknown",
            "Physical Cores": psutil.cpu_count(logical=False),
            "Logical Cores": psutil.cpu_count(logical=True),
        }

    def _get_gpu_info(self):
        gpus = []

        # NVIDIA: nvidia-smi works on both Windows and Linux.
        if shutil.which("nvidia-smi"):
            output = self._run_command([
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits"
            ])

            if output:
                for line in output.splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3:
                        gpus.append({
                            "Name": parts[0],
                            "Vendor": "NVIDIA",
                            "VRAM": f"{parts[1]} MB",
                            "Driver": parts[2],
                        })

        # Windows: use PowerShell CIM for NVIDIA, AMD and Intel.
        if platform.system() == "Windows":
            if not gpus:
                output = self._run_command([
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | "
                    "Select-Object Name, AdapterRAM, DriverVersion | "
                    "ConvertTo-Csv -NoTypeInformation"
                ])

                if output:
                    lines = output.splitlines()[1:]

                    for line in lines:
                        parts = [
                            p.strip().strip('"')
                            for p in line.split(",")
                        ]

                        if len(parts) >= 3:
                            name, vram, driver = parts[:3]

                            try:
                                vram = self.to_gb(int(vram))
                                vram = f"{vram} GB"
                            except (ValueError, TypeError):
                                vram = "Unknown"

                            gpus.append({
                                "Name": name,
                                "Vendor": self._detect_vendor(name),
                                "VRAM": vram,
                                "Driver": driver or "Unknown",
                            })

        # Linux: use lspci for NVIDIA, AMD and Intel.
        elif platform.system() == "Linux":
            if not gpus and shutil.which("lspci"):
                output = self._run_command(["lspci", "-mm"])

                if output:
                    for line in output.splitlines():
                        if "VGA compatible controller" in line or \
                           "3D controller" in line or \
                           "Display controller" in line:

                            match = re.search(r'"([^"]+)"\s*$', line)
                            name = match.group(1) if match else line

                            gpus.append({
                                "Name": name,
                                "Vendor": self._detect_vendor(name),
                                "VRAM": "Unknown",
                                "Driver": "Unknown",
                            })

        if not gpus:
            return [{
                "Name": "No GPU detected",
                "Vendor": "Unknown",
                "VRAM": "Unknown",
                "Driver": "Unknown",
            }]

        return gpus

    @staticmethod
    def _detect_vendor(name):
        name = name.lower()

        if "nvidia" in name or "geforce" in name or "rtx" in name:
            return "NVIDIA"
        elif "amd" in name or "radeon" in name:
            return "AMD"
        elif "intel" in name or "iris" in name or "uhd" in name:
            return "Intel"

        return "Unknown"

    def _get_memory_info(self):
        ram = psutil.virtual_memory()
        return {
            "Total RAM": f"{self.to_gb(ram.total)} GB",
        }

    def _get_storage_info(self):
        storage = []

        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                storage.append({
                    "Device": partition.device,
                    "Mount Point": partition.mountpoint,
                    "Filesystem": partition.fstype,
                    "Total Capacity": f"{self.to_gb(usage.total)} GB",
                })
            except (PermissionError, OSError):
                continue

        return storage

    def _get_network_info(self):
        interfaces = psutil.net_if_addrs()
        network = {}

        for name, addresses in interfaces.items():
            ips = [
                addr.address
                for addr in addresses
                if addr.family in (socket.AF_INET, socket.AF_INET6)
            ]

            if ips:
                network[name] = ", ".join(ips)

        return network

    def display(self):
        sections = [
            ("SYSTEM", self.system_info),
            ("CPU", self.cpu_info),
            ("MEMORY", self.memory_info),
        ]

        for title, data in sections:
            self.section(title)
            self.print_info(data)

        self.section("GPU")

        for index, gpu in enumerate(self.gpu_info, 1):
            print(f"\nGPU #{index}")
            self.print_info(gpu)

        self.section("STORAGE")

        for index, disk in enumerate(self.storage_info, 1):
            print(f"\nDisk #{index}")
            self.print_info(disk)

        self.section("NETWORK INTERFACES")
        self.print_info(self.network_info)
        print()


if __name__ == "__main__":
    pc = PcInfo()
    pc.display()