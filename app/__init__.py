#   AUTO_MAA:A MAA Multi Account Management and Automation Tool
#   Copyright © 2024-2025 DLmaster361

#   This file is part of AUTO_MAA.

#   AUTO_MAA is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   AUTO_MAA is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with AUTO_MAA. If not, see <https://www.gnu.org/licenses/>.

#   Contact: DLmaster_361@163.com

"""
AUTO_MAA
AUTO_MAA主程序包
v4.4
作者：DLmaster_361
"""

__version__ = "4.2.0"
__author__ = "DLmaster361 <DLmaster_361@163.com>"
__license__ = "GPL-3.0 license"

from .core import QueueConfig, MaaConfig, MaaUserConfig, Task, TaskManager, MainTimer
from .models import MaaManager
from .services import Notify, Crypto, System
from .ui import AUTO_MAA

__all__ = [
    "QueueConfig",
    "MaaConfig",
    "MaaUserConfig",
    "Task",
    "TaskManager",
    "MainTimer",
    "MaaManager",
    "Notify",
    "Crypto",
    "System",
    "AUTO_MAA",
]
