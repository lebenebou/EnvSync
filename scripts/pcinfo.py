import platform
import socket
import psutil

class PcInfo:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.system_info = self._get_system_info()
        self.cpu_info = self._get_cpu_info()
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
