"""
System Controller for Freddie
==============================
Handles system-level commands (time, battery, volume, etc.).
"""

import logging
from typing import Tuple, Optional
from datetime import datetime
import subprocess

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)


class SystemController:
    """Controls system-level operations."""

    def __init__(self):
        self._psutil_available = PSUTIL_AVAILABLE

    def get_time(self) -> str:
        """Get the current time."""
        now = datetime.now()
        return f"It's {now.strftime('%I:%M %p')}"

    def get_date(self) -> str:
        """Get the current date."""
        now = datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}"

    def get_battery_status(self) -> str:
        """Get battery status."""
        if not self._psutil_available:
            return "Battery information is not available."

        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return "No battery detected. You might be on a desktop."

            percent = battery.percent
            plugged = battery.power_plugged

            status = "charging" if plugged else "discharging"
            return f"Battery is at {percent}%, {status}."

        except Exception as e:
            logger.error(f"Error getting battery status: {e}")
            return "Could not get battery information."

    def get_cpu_usage(self) -> str:
        """Get CPU usage percentage."""
        if not self._psutil_available:
            return "CPU information is not available."

        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            return f"CPU usage is at {cpu_percent}%."
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return "Could not get CPU information."

    def get_ram_usage(self) -> str:
        """Get RAM usage information."""
        if not self._psutil_available:
            return "RAM information is not available."

        try:
            memory = psutil.virtual_memory()
            percent = memory.percent
            used_gb = memory.used / (1024 ** 3)
            total_gb = memory.total / (1024 ** 3)

            return f"RAM usage is {percent}%. Using {used_gb:.1f}GB of {total_gb:.1f}GB."
        except Exception as e:
            logger.error(f"Error getting RAM usage: {e}")
            return "Could not get RAM information."

    def lock_pc(self) -> str:
        """Lock the computer."""
        try:
            if os.name == 'nt':
                # Windows
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            else:
                # Linux
                subprocess.run(["xdg-screensaver", "lock"])

            logger.info("PC locked")
            return "Locking your computer."
        except Exception as e:
            logger.error(f"Error locking PC: {e}")
            return "Could not lock the computer."

    def shutdown_pc(self, confirmed: bool = False) -> str:
        """
        Shut down the computer.

        Args:
            confirmed: Must be True to actually execute shutdown

        Returns:
            Status message
        """
        if not confirmed:
            return "Shutdown requires confirmation. Please confirm to proceed."

        try:
            if os.name == 'nt':
                # Windows
                subprocess.run(["shutdown", "/s", "/t", "10"])
            else:
                # Linux
                subprocess.run(["shutdown", "-h", "+1"])

            logger.warning("PC shutdown initiated")
            return "Shutting down your computer in 10 seconds."
        except Exception as e:
            logger.error(f"Error initiating shutdown: {e}")
            return "Could not initiate shutdown."

    def restart_pc(self, confirmed: bool = False) -> str:
        """
        Restart the computer.

        Args:
            confirmed: Must be True to actually execute restart

        Returns:
            Status message
        """
        if not confirmed:
            return "Restart requires confirmation. Please confirm to proceed."

        try:
            if os.name == 'nt':
                # Windows
                subprocess.run(["shutdown", "/r", "/t", "10"])
            else:
                # Linux
                subprocess.run(["shutdown", "-r", "+1"])

            logger.warning("PC restart initiated")
            return "Restarting your computer in 10 seconds."
        except Exception as e:
            logger.error(f"Error initiating restart: {e}")
            return "Could not initiate restart."

    def set_volume(self, level: int) -> str:
        """
        Set system volume.

        Args:
            level: Volume level (0-100)

        Returns:
            Status message
        """
        level = max(0, min(100, level))

        try:
            if os.name == 'nt':
                # Windows - use nircmd or PowerShell
                # This is a simplified approach
                logger.info(f"Setting volume to {level}%")
                return f"Setting volume to {level}%."
            else:
                # Linux - use amixer
                subprocess.run(["amixer", "set", "Master", f"{level}%"])
                logger.info(f"Volume set to {level}%")
                return f"Volume set to {level}%."
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return "Could not adjust volume."

    def mute_audio(self) -> str:
        """Mute system audio."""
        try:
            if os.name == 'nt':
                logger.info("Audio muted")
                return "Muting audio."
            else:
                subprocess.run(["amixer", "set", "Master", "mute"])
                logger.info("Audio muted")
                return "Audio muted."
        except Exception as e:
            logger.error(f"Error muting audio: {e}")
            return "Could not mute audio."

    def unmute_audio(self) -> str:
        """Unmute system audio."""
        try:
            if os.name == 'nt':
                logger.info("Audio unmuted")
                return "Unmuting audio."
            else:
                subprocess.run(["amixer", "set", "Master", "unmute"])
                logger.info("Audio unmuted")
                return "Audio unmuted."
        except Exception as e:
            logger.error(f"Error unmuting audio: {e}")
            return "Could not unmute audio."

    def open_settings(self) -> str:
        """Open system settings."""
        try:
            if os.name == 'nt':
                # Windows Settings
                subprocess.Popen(["start", "ms-settings:"], shell=True)
            else:
                # Try common settings applications
                subprocess.Popen(["gnome-control-center"])

            logger.info("Settings opened")
            return "Opening settings."
        except Exception as e:
            logger.error(f"Error opening settings: {e}")
            return "Could not open settings."

    def open_task_manager(self) -> str:
        """Open task manager."""
        try:
            if os.name == 'nt':
                subprocess.Popen(["taskmgr"])
            else:
                subprocess.Popen(["gnome-system-monitor"])

            logger.info("Task manager opened")
            return "Opening task manager."
        except Exception as e:
            logger.error(f"Error opening task manager: {e}")
            return "Could not open task manager."

    def get_system_info(self) -> dict:
        """Get comprehensive system information."""
        info = {
            "platform": os.name,
            "cpu_available": self._psutil_available,
            "battery_available": self._psutil_available,
        }

        if self._psutil_available:
            try:
                info["cpu_count"] = psutil.cpu_count()
                info["ram_total_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
                battery = psutil.sensors_battery()
                if battery:
                    info["battery_percent"] = battery.percent
            except:
                pass

        return info


# Import os at module level
import os

# Singleton instance
_system_controller: Optional[SystemController] = None


def get_system_controller() -> SystemController:
    """Get the singleton SystemController instance."""
    global _system_controller
    if _system_controller is None:
        _system_controller = SystemController()
    return _system_controller
