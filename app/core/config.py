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
AUTO_MAA配置管理
v4.4
作者：DLmaster_361
"""

from loguru import logger
from PySide6.QtCore import Signal
import argparse
import sqlite3
import json
import sys
import shutil
import re
import base64
import calendar
from datetime import datetime, timedelta, date
from collections import defaultdict
from pathlib import Path
from qfluentwidgets import (
    QConfig,
    ConfigItem,
    OptionsConfigItem,
    RangeConfigItem,
    ConfigValidator,
    FolderValidator,
    BoolValidator,
    RangeValidator,
    OptionsValidator,
    exceptionHandler,
)
from urllib.parse import urlparse
from typing import Union, Dict, List

from .network import Network


class FileValidator(ConfigValidator):
    """File validator"""

    def validate(self, value):
        return Path(value).exists()

    def correct(self, value):
        path = Path(value)
        return str(path.absolute()).replace("\\", "/")


class UrlListValidator(ConfigValidator):
    """Url list validator"""

    def validate(self, value):

        try:
            result = urlparse(value)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def correct(self, value: List[str]):

        urls = []

        for url in [_ for _ in value if _ != ""]:
            if url[-1] != "/":
                urls.append(f"{url}/")
            else:
                urls.append(url)

        return list(set([_ for _ in urls if self.validate(_)]))


class LQConfig(QConfig):
    """局域配置类"""

    def __init__(self) -> None:
        super().__init__()

    def toDict(self, serialize=True):
        """convert config items to `dict`"""
        items = {}
        for name in dir(self._cfg):
            item = getattr(self._cfg, name)
            if not isinstance(item, ConfigItem):
                continue

            value = item.serialize() if serialize else item.value
            if not items.get(item.group):
                if not item.name:
                    items[item.group] = value
                else:
                    items[item.group] = {}

            if item.name:
                items[item.group][item.name] = value

        return items

    @exceptionHandler()
    def load(self, file=None, config=None):
        """load config

        Parameters
        ----------
        file: str or Path
            the path of json config file

        config: Config
            config object to be initialized
        """
        if isinstance(config, QConfig):
            self._cfg = config
            self._cfg.themeChanged.connect(self.themeChanged)

        if isinstance(file, (str, Path)):
            self._cfg.file = Path(file)

        try:
            with open(self._cfg.file, encoding="utf-8") as f:
                cfg = json.load(f)
        except:
            cfg = {}

        # map config items'key to item
        items = {}
        for name in dir(self._cfg):
            item = getattr(self._cfg, name)
            if isinstance(item, ConfigItem):
                items[item.key] = item

        # update the value of config item
        for k, v in cfg.items():
            if not isinstance(v, dict) and items.get(k) is not None:
                items[k].deserializeFrom(v)
            elif isinstance(v, dict):
                for key, value in v.items():
                    key = k + "." + key
                    if items.get(key) is not None:
                        items[key].deserializeFrom(value)

        self.theme = self.get(self._cfg.themeMode)


class GlobalConfig(LQConfig):
    """全局配置"""

    def __init__(self) -> None:
        super().__init__()

        self.function_HomeImageMode = OptionsConfigItem(
            "Function",
            "HomeImageMode",
            "默认",
            OptionsValidator(["默认", "自定义", "主题图像"]),
        )
        self.function_HistoryRetentionTime = OptionsConfigItem(
            "Function",
            "HistoryRetentionTime",
            0,
            OptionsValidator([7, 15, 30, 60, 90, 180, 365, 0]),
        )
        self.function_IfAllowSleep = ConfigItem(
            "Function", "IfAllowSleep", False, BoolValidator()
        )
        self.function_IfSilence = ConfigItem(
            "Function", "IfSilence", False, BoolValidator()
        )
        self.function_BossKey = ConfigItem("Function", "BossKey", "")
        self.function_UnattendedMode = ConfigItem(
            "Function", "UnattendedMode", False, BoolValidator()
        )
        self.function_IfAgreeBilibili = ConfigItem(
            "Function", "IfAgreeBilibili", False, BoolValidator()
        )
        self.function_IfSkipMumuSplashAds = ConfigItem(
            "Function", "IfSkipMumuSplashAds", False, BoolValidator()
        )

        self.voice_Enabled = ConfigItem("Voice", "Enabled", False, BoolValidator())
        self.voice_Type = OptionsConfigItem(
            "Voice", "Type", "simple", OptionsValidator(["simple", "noisy"])
        )

        self.start_IfSelfStart = ConfigItem(
            "Start", "IfSelfStart", False, BoolValidator()
        )
        self.start_IfRunDirectly = ConfigItem(
            "Start", "IfRunDirectly", False, BoolValidator()
        )
        self.start_IfMinimizeDirectly = ConfigItem(
            "Start", "IfMinimizeDirectly", False, BoolValidator()
        )

        self.ui_IfShowTray = ConfigItem("UI", "IfShowTray", False, BoolValidator())
        self.ui_IfToTray = ConfigItem("UI", "IfToTray", False, BoolValidator())
        self.ui_size = ConfigItem("UI", "size", "1200x700")
        self.ui_location = ConfigItem("UI", "location", "100x100")
        self.ui_maximized = ConfigItem("UI", "maximized", False, BoolValidator())

        self.notify_SendTaskResultTime = OptionsConfigItem(
            "Notify",
            "SendTaskResultTime",
            "不推送",
            OptionsValidator(["不推送", "任何时刻", "仅失败时"]),
        )
        self.notify_IfSendStatistic = ConfigItem(
            "Notify", "IfSendStatistic", False, BoolValidator()
        )
        self.notify_IfSendSixStar = ConfigItem(
            "Notify", "IfSendSixStar", False, BoolValidator()
        )
        self.notify_IfPushPlyer = ConfigItem(
            "Notify", "IfPushPlyer", False, BoolValidator()
        )
        self.notify_IfSendMail = ConfigItem(
            "Notify", "IfSendMail", False, BoolValidator()
        )
        self.notify_SMTPServerAddress = ConfigItem("Notify", "SMTPServerAddress", "")
        self.notify_AuthorizationCode = ConfigItem("Notify", "AuthorizationCode", "")
        self.notify_FromAddress = ConfigItem("Notify", "FromAddress", "")
        self.notify_ToAddress = ConfigItem("Notify", "ToAddress", "")
        self.notify_IfServerChan = ConfigItem(
            "Notify", "IfServerChan", False, BoolValidator()
        )
        self.notify_ServerChanKey = ConfigItem("Notify", "ServerChanKey", "")
        self.notify_ServerChanChannel = ConfigItem("Notify", "ServerChanChannel", "")
        self.notify_ServerChanTag = ConfigItem("Notify", "ServerChanTag", "")
        self.notify_IfCompanyWebHookBot = ConfigItem(
            "Notify", "IfCompanyWebHookBot", False, BoolValidator()
        )
        self.notify_CompanyWebHookBotUrl = ConfigItem(
            "Notify", "CompanyWebHookBotUrl", ""
        )

        self.update_IfAutoUpdate = ConfigItem(
            "Update", "IfAutoUpdate", False, BoolValidator()
        )
        self.update_UpdateType = OptionsConfigItem(
            "Update", "UpdateType", "stable", OptionsValidator(["stable", "beta"])
        )
        self.update_ThreadNumb = RangeConfigItem(
            "Update", "ThreadNumb", 8, RangeValidator(1, 32)
        )
        self.update_ProxyAddress = ConfigItem("Update", "ProxyAddress", "")
        self.update_ProxyUrlList = ConfigItem(
            "Update", "ProxyUrlList", [], UrlListValidator()
        )
        self.update_MirrorChyanCDK = ConfigItem("Update", "MirrorChyanCDK", "")


class QueueConfig(LQConfig):
    """队列配置"""

    def __init__(self) -> None:
        super().__init__()

        self.queueSet_Name = ConfigItem("QueueSet", "Name", "")
        self.queueSet_Enabled = ConfigItem(
            "QueueSet", "Enabled", False, BoolValidator()
        )
        self.queueSet_AfterAccomplish = OptionsConfigItem(
            "QueueSet",
            "AfterAccomplish",
            "NoAction",
            OptionsValidator(
                ["NoAction", "KillSelf", "Sleep", "Hibernate", "Shutdown"]
            ),
        )

        self.time_TimeEnabled_0 = ConfigItem(
            "Time", "TimeEnabled_0", False, BoolValidator()
        )
        self.time_TimeSet_0 = ConfigItem("Time", "TimeSet_0", "00:00")

        self.time_TimeEnabled_1 = ConfigItem(
            "Time", "TimeEnabled_1", False, BoolValidator()
        )
        self.time_TimeSet_1 = ConfigItem("Time", "TimeSet_1", "00:00")

        self.time_TimeEnabled_2 = ConfigItem(
            "Time", "TimeEnabled_2", False, BoolValidator()
        )
        self.time_TimeSet_2 = ConfigItem("Time", "TimeSet_2", "00:00")

        self.time_TimeEnabled_3 = ConfigItem(
            "Time", "TimeEnabled_3", False, BoolValidator()
        )
        self.time_TimeSet_3 = ConfigItem("Time", "TimeSet_3", "00:00")

        self.time_TimeEnabled_4 = ConfigItem(
            "Time", "TimeEnabled_4", False, BoolValidator()
        )
        self.time_TimeSet_4 = ConfigItem("Time", "TimeSet_4", "00:00")

        self.time_TimeEnabled_5 = ConfigItem(
            "Time", "TimeEnabled_5", False, BoolValidator()
        )
        self.time_TimeSet_5 = ConfigItem("Time", "TimeSet_5", "00:00")

        self.time_TimeEnabled_6 = ConfigItem(
            "Time", "TimeEnabled_6", False, BoolValidator()
        )
        self.time_TimeSet_6 = ConfigItem("Time", "TimeSet_6", "00:00")

        self.time_TimeEnabled_7 = ConfigItem(
            "Time", "TimeEnabled_7", False, BoolValidator()
        )
        self.time_TimeSet_7 = ConfigItem("Time", "TimeSet_7", "00:00")

        self.time_TimeEnabled_8 = ConfigItem(
            "Time", "TimeEnabled_8", False, BoolValidator()
        )
        self.time_TimeSet_8 = ConfigItem("Time", "TimeSet_8", "00:00")

        self.time_TimeEnabled_9 = ConfigItem(
            "Time", "TimeEnabled_9", False, BoolValidator()
        )
        self.time_TimeSet_9 = ConfigItem("Time", "TimeSet_9", "00:00")

        self.queue_Member_1 = OptionsConfigItem("Queue", "Member_1", "禁用")
        self.queue_Member_2 = OptionsConfigItem("Queue", "Member_2", "禁用")
        self.queue_Member_3 = OptionsConfigItem("Queue", "Member_3", "禁用")
        self.queue_Member_4 = OptionsConfigItem("Queue", "Member_4", "禁用")
        self.queue_Member_5 = OptionsConfigItem("Queue", "Member_5", "禁用")
        self.queue_Member_6 = OptionsConfigItem("Queue", "Member_6", "禁用")
        self.queue_Member_7 = OptionsConfigItem("Queue", "Member_7", "禁用")
        self.queue_Member_8 = OptionsConfigItem("Queue", "Member_8", "禁用")
        self.queue_Member_9 = OptionsConfigItem("Queue", "Member_9", "禁用")
        self.queue_Member_10 = OptionsConfigItem("Queue", "Member_10", "禁用")

        self.Data_LastProxyTime = ConfigItem(
            "Data", "LastProxyTime", "2000-01-01 00:00:00"
        )
        self.Data_LastProxyHistory = ConfigItem(
            "Data", "LastProxyHistory", "暂无历史运行记录"
        )


class MaaConfig(LQConfig):
    """MAA配置"""

    def __init__(self) -> None:
        super().__init__()

        self.MaaSet_Name = ConfigItem("MaaSet", "Name", "")
        self.MaaSet_Path = ConfigItem("MaaSet", "Path", ".", FolderValidator())

        self.RunSet_TaskTransitionMethod = OptionsConfigItem(
            "RunSet",
            "TaskTransitionMethod",
            "ExitEmulator",
            OptionsValidator(["NoAction", "ExitGame", "ExitEmulator"]),
        )
        self.RunSet_ProxyTimesLimit = RangeConfigItem(
            "RunSet", "ProxyTimesLimit", 0, RangeValidator(0, 1024)
        )
        self.RunSet_ADBSearchRange = RangeConfigItem(
            "RunSet", "ADBSearchRange", 0, RangeValidator(0, 3)
        )
        self.RunSet_RunTimesLimit = RangeConfigItem(
            "RunSet", "RunTimesLimit", 3, RangeValidator(1, 1024)
        )
        self.RunSet_AnnihilationTimeLimit = RangeConfigItem(
            "RunSet", "AnnihilationTimeLimit", 40, RangeValidator(1, 1024)
        )
        self.RunSet_RoutineTimeLimit = RangeConfigItem(
            "RunSet", "RoutineTimeLimit", 10, RangeValidator(1, 1024)
        )
        self.RunSet_AnnihilationWeeklyLimit = ConfigItem(
            "RunSet", "AnnihilationWeeklyLimit", False, BoolValidator()
        )
        self.RunSet_AutoUpdateMaa = ConfigItem(
            "RunSet", "AutoUpdateMaa", False, BoolValidator()
        )

    def get_name(self) -> str:
        return self.get(self.MaaSet_Name)


class MaaUserConfig(LQConfig):
    """MAA用户配置"""

    def __init__(self) -> None:
        super().__init__()

        self.Info_Name = ConfigItem("Info", "Name", "新用户")
        self.Info_Id = ConfigItem("Info", "Id", "")
        self.Info_Mode = OptionsConfigItem(
            "Info", "Mode", "简洁", OptionsValidator(["简洁", "详细"])
        )
        self.Info_StageMode = ConfigItem("Info", "StageMode", "固定")
        self.Info_Server = OptionsConfigItem(
            "Info", "Server", "Official", OptionsValidator(["Official", "Bilibili"])
        )
        self.Info_Status = ConfigItem("Info", "Status", True, BoolValidator())
        self.Info_RemainedDay = ConfigItem(
            "Info", "RemainedDay", -1, RangeValidator(-1, 1024)
        )
        self.Info_Annihilation = ConfigItem(
            "Info", "Annihilation", False, BoolValidator()
        )
        self.Info_Routine = ConfigItem("Info", "Routine", False, BoolValidator())
        self.Info_InfrastMode = OptionsConfigItem(
            "Info",
            "InfrastMode",
            "Normal",
            OptionsValidator(["Normal", "Rotation", "Custom"]),
        )
        self.Info_Password = ConfigItem("Info", "Password", "")
        self.Info_Notes = ConfigItem("Info", "Notes", "无")
        self.Info_MedicineNumb = ConfigItem(
            "Info", "MedicineNumb", 0, RangeValidator(0, 1024)
        )
        self.Info_SeriesNumb = OptionsConfigItem(
            "Info",
            "SeriesNumb",
            "0",
            OptionsValidator(["0", "6", "5", "4", "3", "2", "1", "-1"]),
        )
        self.Info_Stage = ConfigItem("Info", "Stage", "-")
        self.Info_Stage_1 = ConfigItem("Info", "Stage_1", "-")
        self.Info_Stage_2 = ConfigItem("Info", "Stage_2", "-")
        self.Info_Stage_3 = ConfigItem("Info", "Stage_3", "-")
        self.Info_Stage_Remain = ConfigItem("Info", "Stage_Remain", "-")
        self.Info_IfSkland = ConfigItem("Info", "IfSkland", False, BoolValidator())
        self.Info_SklandToken = ConfigItem("Info", "SklandToken", "")

        self.Data_LastProxyDate = ConfigItem("Data", "LastProxyDate", "2000-01-01")
        self.Data_LastAnnihilationDate = ConfigItem(
            "Data", "LastAnnihilationDate", "2000-01-01"
        )
        self.Data_LastSklandDate = ConfigItem("Data", "LastSklandDate", "2000-01-01")
        self.Data_ProxyTimes = ConfigItem(
            "Data", "ProxyTimes", 0, RangeValidator(0, 1024)
        )
        self.Data_IfPassCheck = ConfigItem("Data", "IfPassCheck", True, BoolValidator())
        self.Data_CustomInfrastPlanIndex = ConfigItem(
            "Data", "CustomInfrastPlanIndex", "0"
        )

        self.Task_IfWakeUp = ConfigItem("Task", "IfWakeUp", True, BoolValidator())
        self.Task_IfRecruiting = ConfigItem(
            "Task", "IfRecruiting", True, BoolValidator()
        )
        self.Task_IfBase = ConfigItem("Task", "IfBase", True, BoolValidator())
        self.Task_IfCombat = ConfigItem("Task", "IfCombat", True, BoolValidator())
        self.Task_IfMall = ConfigItem("Task", "IfMall", True, BoolValidator())
        self.Task_IfMission = ConfigItem("Task", "IfMission", True, BoolValidator())
        self.Task_IfAutoRoguelike = ConfigItem(
            "Task", "IfAutoRoguelike", False, BoolValidator()
        )
        self.Task_IfReclamation = ConfigItem(
            "Task", "IfReclamation", False, BoolValidator()
        )

        self.Notify_Enabled = ConfigItem("Notify", "Enabled", False, BoolValidator())
        self.Notify_IfSendStatistic = ConfigItem(
            "Notify", "IfSendStatistic", False, BoolValidator()
        )
        self.Notify_IfSendSixStar = ConfigItem(
            "Notify", "IfSendSixStar", False, BoolValidator()
        )
        self.Notify_IfSendMail = ConfigItem(
            "Notify", "IfSendMail", False, BoolValidator()
        )
        self.Notify_ToAddress = ConfigItem("Notify", "ToAddress", "")
        self.Notify_IfServerChan = ConfigItem(
            "Notify", "IfServerChan", False, BoolValidator()
        )
        self.Notify_ServerChanKey = ConfigItem("Notify", "ServerChanKey", "")
        self.Notify_ServerChanChannel = ConfigItem("Notify", "ServerChanChannel", "")
        self.Notify_ServerChanTag = ConfigItem("Notify", "ServerChanTag", "")
        self.Notify_IfCompanyWebHookBot = ConfigItem(
            "Notify", "IfCompanyWebHookBot", False, BoolValidator()
        )
        self.Notify_CompanyWebHookBotUrl = ConfigItem(
            "Notify", "CompanyWebHookBotUrl", ""
        )

    def get_plan_info(self) -> Dict[str, Union[str, int]]:
        """获取当前的计划下信息"""

        if self.get(self.Info_StageMode) == "固定":
            return {
                "MedicineNumb": self.get(self.Info_MedicineNumb),
                "SeriesNumb": self.get(self.Info_SeriesNumb),
                "Stage": self.get(self.Info_Stage),
                "Stage_1": self.get(self.Info_Stage_1),
                "Stage_2": self.get(self.Info_Stage_2),
                "Stage_3": self.get(self.Info_Stage_3),
                "Stage_Remain": self.get(self.Info_Stage_Remain),
            }
        elif "计划" in self.get(self.Info_StageMode):
            plan = Config.plan_dict[self.get(self.Info_StageMode)]["Config"]
            return {
                "MedicineNumb": plan.get(plan.get_current_info("MedicineNumb")),
                "SeriesNumb": plan.get(plan.get_current_info("SeriesNumb")),
                "Stage": plan.get(plan.get_current_info("Stage")),
                "Stage_1": plan.get(plan.get_current_info("Stage_1")),
                "Stage_2": plan.get(plan.get_current_info("Stage_2")),
                "Stage_3": plan.get(plan.get_current_info("Stage_3")),
                "Stage_Remain": plan.get(plan.get_current_info("Stage_Remain")),
            }


class MaaPlanConfig(LQConfig):
    """MAA计划表配置"""

    def __init__(self) -> None:
        super().__init__()

        self.Info_Name = ConfigItem("Info", "Name", "")
        self.Info_Mode = OptionsConfigItem(
            "Info", "Mode", "ALL", OptionsValidator(["ALL", "Weekly"])
        )

        self.config_item_dict: dict[str, Dict[str, ConfigItem]] = {}

        for group in [
            "ALL",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            self.config_item_dict[group] = {}

            self.config_item_dict[group]["MedicineNumb"] = ConfigItem(
                group, "MedicineNumb", 0, RangeValidator(0, 1024)
            )
            self.config_item_dict[group]["SeriesNumb"] = OptionsConfigItem(
                group,
                "SeriesNumb",
                "0",
                OptionsValidator(["0", "6", "5", "4", "3", "2", "1", "-1"]),
            )
            self.config_item_dict[group]["Stage"] = ConfigItem(group, "Stage", "-")
            self.config_item_dict[group]["Stage_1"] = ConfigItem(group, "Stage_1", "-")
            self.config_item_dict[group]["Stage_2"] = ConfigItem(group, "Stage_2", "-")
            self.config_item_dict[group]["Stage_3"] = ConfigItem(group, "Stage_3", "-")
            self.config_item_dict[group]["Stage_Remain"] = ConfigItem(
                group, "Stage_Remain", "-"
            )

            for name in [
                "MedicineNumb",
                "SeriesNumb",
                "Stage",
                "Stage_1",
                "Stage_2",
                "Stage_3",
                "Stage_Remain",
            ]:
                setattr(self, f"{group}_{name}", self.config_item_dict[group][name])

    def get_current_info(self, name: str) -> ConfigItem:
        """获取当前的计划表配置项"""

        if self.get(self.Info_Mode) == "ALL":
            return self.config_item_dict["ALL"][name]
        elif self.get(self.Info_Mode) == "Weekly":
            today = datetime.now().strftime("%A")
            if today in self.config_item_dict:
                return self.config_item_dict[today][name]
            else:
                return self.config_item_dict["ALL"][name]


class GeneralConfig(LQConfig):
    """通用配置"""

    def __init__(self) -> None:
        super().__init__()

        self.Script_Name = ConfigItem("Script", "Name", "")
        self.Script_RootPath = ConfigItem("Script", "RootPath", ".", FolderValidator())
        self.Script_ScriptPath = ConfigItem(
            "Script", "ScriptPath", ".", FileValidator()
        )
        self.Script_Arguments = ConfigItem("Script", "Arguments", "")
        self.Script_IfTrackProcess = ConfigItem(
            "Script", "IfTrackProcess", False, BoolValidator()
        )
        self.Script_ConfigPath = ConfigItem(
            "Script", "ConfigPath", ".", FileValidator()
        )
        self.Script_ConfigPathMode = OptionsConfigItem(
            "Script",
            "ConfigPathMode",
            "所有文件 (*)",
            OptionsValidator(["所有文件 (*)", "文件夹"]),
        )
        self.Script_LogPath = ConfigItem("Script", "LogPath", ".", FileValidator())
        self.Script_LogPathFormat = ConfigItem("Script", "LogPathFormat", "%Y-%m-%d")
        self.Script_LogTimeStart = ConfigItem(
            "Script", "LogTimeStart", 1, RangeValidator(1, 1024)
        )
        self.Script_LogTimeEnd = ConfigItem(
            "Script", "LogTimeEnd", 1, RangeValidator(1, 1024)
        )
        self.Script_LogTimeFormat = ConfigItem(
            "Script", "LogTimeFormat", "%Y-%m-%d %H:%M:%S"
        )
        self.Script_SuccessLog = ConfigItem("Script", "SuccessLog", "")
        self.Script_ErrorLog = ConfigItem("Script", "ErrorLog", "")

        self.Game_Enabled = ConfigItem("Game", "Enabled", False, BoolValidator())
        self.Game_Style = OptionsConfigItem(
            "Game", "Style", "Emulator", OptionsValidator(["Emulator", "Client"])
        )
        self.Game_Path = ConfigItem("Game", "Path", ".", FileValidator())
        self.Game_Arguments = ConfigItem("Game", "Arguments", "")
        self.Game_WaitTime = ConfigItem("Game", "WaitTime", 0, RangeValidator(0, 1024))
        self.Game_IfForceClose = ConfigItem(
            "Game", "IfForceClose", False, BoolValidator()
        )

        self.Run_ProxyTimesLimit = RangeConfigItem(
            "Run", "ProxyTimesLimit", 0, RangeValidator(0, 1024)
        )
        self.Run_RunTimesLimit = RangeConfigItem(
            "Run", "RunTimesLimit", 3, RangeValidator(1, 1024)
        )
        self.Run_RunTimeLimit = RangeConfigItem(
            "Run", "RunTimeLimit", 10, RangeValidator(1, 1024)
        )

    def get_name(self) -> str:
        return self.get(self.Script_Name)


class GeneralSubConfig(LQConfig):
    """通用子配置"""

    def __init__(self) -> None:
        super().__init__()

        self.Info_Name = ConfigItem("Info", "Name", "新配置")
        self.Info_Status = ConfigItem("Info", "Status", True, BoolValidator())
        self.Info_RemainedDay = ConfigItem(
            "Info", "RemainedDay", -1, RangeValidator(-1, 1024)
        )
        self.Info_IfScriptBeforeTask = ConfigItem(
            "Info", "IfScriptBeforeTask", False, BoolValidator()
        )
        self.Info_ScriptBeforeTask = ConfigItem(
            "Info", "ScriptBeforeTask", "", FileValidator()
        )
        self.Info_IfScriptAfterTask = ConfigItem(
            "Info", "IfScriptAfterTask", False, BoolValidator()
        )
        self.Info_ScriptAfterTask = ConfigItem(
            "Info", "ScriptAfterTask", "", FileValidator()
        )
        self.Info_Notes = ConfigItem("Info", "Notes", "无")

        self.Data_LastProxyDate = ConfigItem("Data", "LastProxyDate", "2000-01-01")
        self.Data_ProxyTimes = ConfigItem(
            "Data", "ProxyTimes", 0, RangeValidator(0, 1024)
        )

        self.Notify_Enabled = ConfigItem("Notify", "Enabled", False, BoolValidator())
        self.Notify_IfSendStatistic = ConfigItem(
            "Notify", "IfSendStatistic", False, BoolValidator()
        )
        self.Notify_IfSendMail = ConfigItem(
            "Notify", "IfSendMail", False, BoolValidator()
        )
        self.Notify_ToAddress = ConfigItem("Notify", "ToAddress", "")
        self.Notify_IfServerChan = ConfigItem(
            "Notify", "IfServerChan", False, BoolValidator()
        )
        self.Notify_ServerChanKey = ConfigItem("Notify", "ServerChanKey", "")
        self.Notify_ServerChanChannel = ConfigItem("Notify", "ServerChanChannel", "")
        self.Notify_ServerChanTag = ConfigItem("Notify", "ServerChanTag", "")
        self.Notify_IfCompanyWebHookBot = ConfigItem(
            "Notify", "IfCompanyWebHookBot", False, BoolValidator()
        )
        self.Notify_CompanyWebHookBotUrl = ConfigItem(
            "Notify", "CompanyWebHookBotUrl", ""
        )


class AppConfig(GlobalConfig):

    VERSION = "4.4.0.0"

    stage_refreshed = Signal()
    PASSWORD_refreshed = Signal()
    sub_info_changed = Signal()
    power_sign_changed = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.app_path = Path(sys.argv[0]).resolve().parent  # 获取软件根目录
        self.app_path_sys = Path(sys.argv[0]).resolve()  # 获取软件自身的路径

        self.log_path = self.app_path / "debug/AUTO_MAA.log"
        self.database_path = self.app_path / "data/data.db"
        self.config_path = self.app_path / "config/config.json"
        self.key_path = self.app_path / "data/key"

        self.main_window = None
        self.PASSWORD = ""
        self.running_list = []
        self.silence_list = []
        self.info_bar_list = []
        self.stage_dict = {
            "ALL": {"value": [], "text": []},
            "Monday": {"value": [], "text": []},
            "Tuesday": {"value": [], "text": []},
            "Wednesday": {"value": [], "text": []},
            "Thursday": {"value": [], "text": []},
            "Friday": {"value": [], "text": []},
            "Saturday": {"value": [], "text": []},
            "Sunday": {"value": [], "text": []},
        }
        self.power_sign = "NoAction"
        self.if_ignore_silence = False
        self.if_database_opened = False

        self.search_member()
        self.search_queue()

        parser = argparse.ArgumentParser(
            prog="AUTO_MAA",
            description="A MAA Multi Account Management and Automation Tool",
        )
        parser.add_argument(
            "--mode",
            choices=["gui", "cli"],
            default="gui",
            help="使用UI界面或命令行模式运行程序",
        )
        parser.add_argument(
            "--config",
            nargs="+",
            choices=list(self.member_dict.keys()) + list(self.queue_dict.keys()),
            help="指定需要运行哪些配置项",
        )
        self.args = parser.parse_args()

        self.initialize()

    def initialize(self) -> None:
        """初始化程序配置管理模块"""

        # 检查目录
        (self.app_path / "config").mkdir(parents=True, exist_ok=True)
        (self.app_path / "data").mkdir(parents=True, exist_ok=True)
        (self.app_path / "debug").mkdir(parents=True, exist_ok=True)
        (self.app_path / "history").mkdir(parents=True, exist_ok=True)

        self.load(self.config_path, self)
        self.save()

        self.init_logger()
        self.check_data()
        logger.info("程序初始化完成")

    def init_logger(self) -> None:
        """初始化日志记录器"""

        logger.add(
            sink=self.log_path,
            level="DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            enqueue=True,
            backtrace=True,
            diagnose=True,
            rotation="1 week",
            retention="1 month",
            compression="zip",
        )
        logger.info("")
        logger.info("===================================")
        logger.info("AUTO_MAA 主程序")
        logger.info(f"版本号： v{self.VERSION}")
        logger.info(f"根目录： {self.app_path}")
        logger.info(
            f"运行模式： {'图形化界面' if self.args.mode == 'gui' else '命令行界面'}"
        )
        logger.info("===================================")

        logger.info("日志记录器初始化完成")

    def get_stage(self) -> None:
        """从MAA服务器获取活动关卡信息"""

        network = Network.add_task(
            mode="get",
            url="https://api.maa.plus/MaaAssistantArknights/api/gui/StageActivity.json",
        )
        network.loop.exec()
        network_result = Network.get_result(network)
        if network_result["status_code"] == 200:
            stage_infos: List[Dict[str, Union[str, Dict[str, Union[str, int]]]]] = (
                network_result["response_json"]["Official"]["sideStoryStage"]
            )
        else:
            logger.warning(
                f"无法从MAA服务器获取活动关卡信息:{network_result['error_message']}"
            )
            stage_infos = []

        ss_stage_dict = {"value": [], "text": []}

        for stage_info in stage_infos:

            if (
                datetime.strptime(
                    stage_info["Activity"]["UtcStartTime"], "%Y/%m/%d %H:%M:%S"
                )
                < datetime.now()
                < datetime.strptime(
                    stage_info["Activity"]["UtcExpireTime"], "%Y/%m/%d %H:%M:%S"
                )
            ):
                ss_stage_dict["value"].append(stage_info["Value"])
                ss_stage_dict["text"].append(stage_info["Value"])

        # 生成每日关卡信息
        stage_daily_info = [
            {"value": "-", "text": "当前/上次", "days": [1, 2, 3, 4, 5, 6, 7]},
            {"value": "1-7", "text": "1-7", "days": [1, 2, 3, 4, 5, 6, 7]},
            {"value": "R8-11", "text": "R8-11", "days": [1, 2, 3, 4, 5, 6, 7]},
            {
                "value": "12-17-HARD",
                "text": "12-17-HARD",
                "days": [1, 2, 3, 4, 5, 6, 7],
            },
            {"value": "CE-6", "text": "龙门币-6/5", "days": [2, 4, 6, 7]},
            {"value": "AP-5", "text": "红票-5", "days": [1, 4, 6, 7]},
            {"value": "CA-5", "text": "技能-5", "days": [2, 3, 5, 7]},
            {"value": "LS-6", "text": "经验-6/5", "days": [1, 2, 3, 4, 5, 6, 7]},
            {"value": "SK-5", "text": "碳-5", "days": [1, 3, 5, 6]},
            {"value": "PR-A-1", "text": "奶/盾芯片", "days": [1, 4, 5, 7]},
            {"value": "PR-A-2", "text": "奶/盾芯片组", "days": [1, 4, 5, 7]},
            {"value": "PR-B-1", "text": "术/狙芯片", "days": [1, 2, 5, 6]},
            {"value": "PR-B-2", "text": "术/狙芯片组", "days": [1, 2, 5, 6]},
            {"value": "PR-C-1", "text": "先/辅芯片", "days": [3, 4, 6, 7]},
            {"value": "PR-C-2", "text": "先/辅芯片组", "days": [3, 4, 6, 7]},
            {"value": "PR-D-1", "text": "近/特芯片", "days": [2, 3, 6, 7]},
            {"value": "PR-D-2", "text": "近/特芯片组", "days": [2, 3, 6, 7]},
        ]

        for day in range(0, 8):

            today_stage_dict = {"value": [], "text": []}

            for stage_info in stage_daily_info:

                if day in stage_info["days"] or day == 0:
                    today_stage_dict["value"].append(stage_info["value"])
                    today_stage_dict["text"].append(stage_info["text"])

            self.stage_dict[calendar.day_name[day - 1] if day > 0 else "ALL"] = {
                "value": today_stage_dict["value"] + ss_stage_dict["value"],
                "text": today_stage_dict["text"] + ss_stage_dict["text"],
            }

        self.stage_refreshed.emit()

    def server_date(self) -> date:
        """获取当前的服务器日期"""

        dt = datetime.now()
        if dt.time() < datetime.min.time().replace(hour=4):
            dt = dt - timedelta(days=1)
        return dt.date()

    def check_data(self) -> None:
        """检查用户数据文件并处理数据文件版本更新"""

        # 生成主数据库
        if not self.database_path.exists():
            db = sqlite3.connect(self.database_path)
            cur = db.cursor()
            cur.execute("CREATE TABLE version(v text)")
            cur.execute("INSERT INTO version VALUES(?)", ("v1.7",))
            db.commit()
            cur.close()
            db.close()

        # 数据文件版本更新
        db = sqlite3.connect(self.database_path)
        cur = db.cursor()
        cur.execute("SELECT * FROM version WHERE True")
        version = cur.fetchall()

        if version[0][0] != "v1.7":
            logger.info("数据文件版本更新开始")
            if_streaming = False
            # v1.4-->v1.5
            if version[0][0] == "v1.4" or if_streaming:
                logger.info("数据文件版本更新：v1.4-->v1.5")
                if_streaming = True

                member_dict: Dict[str, Dict[str, Union[str, Path]]] = {}
                if (self.app_path / "config/MaaConfig").exists():
                    for maa_dir in (self.app_path / "config/MaaConfig").iterdir():
                        if maa_dir.is_dir():
                            member_dict[maa_dir.name] = {
                                "Type": "Maa",
                                "Path": maa_dir,
                            }

                member_dict = dict(
                    sorted(member_dict.items(), key=lambda x: int(x[0][3:]))
                )

                for name, config in member_dict.items():
                    if config["Type"] == "Maa":

                        _db = sqlite3.connect(config["Path"] / "user_data.db")
                        _cur = _db.cursor()
                        _cur.execute("SELECT * FROM adminx WHERE True")
                        data = _cur.fetchall()
                        data = [list(row) for row in data]
                        data = sorted(data, key=lambda x: (-len(x[15]), x[16]))
                        _cur.close()
                        _db.close()

                        (config["Path"] / "user_data.db").unlink()

                        (config["Path"] / f"UserData").mkdir(
                            parents=True, exist_ok=True
                        )

                        for i in range(len(data)):

                            info = {
                                "Data": {
                                    "IfPassCheck": True,
                                    "LastAnnihilationDate": "2000-01-01",
                                    "LastProxyDate": data[i][5],
                                    "ProxyTimes": data[i][14],
                                },
                                "Info": {
                                    "Annihilation": bool(data[i][10] == "y"),
                                    "GameId": data[i][6],
                                    "GameIdMode": "固定",
                                    "GameId_1": data[i][7],
                                    "GameId_2": data[i][8],
                                    "Id": data[i][1],
                                    "Infrastructure": bool(data[i][11] == "y"),
                                    "MedicineNumb": 0,
                                    "Mode": (
                                        "简洁" if data[i][15] == "simple" else "详细"
                                    ),
                                    "Name": data[i][0],
                                    "Notes": data[i][13],
                                    "Password": base64.b64encode(data[i][12]).decode(
                                        "utf-8"
                                    ),
                                    "RemainedDay": data[i][3],
                                    "Routine": bool(data[i][9] == "y"),
                                    "Server": data[i][2],
                                    "Status": bool(data[i][4] == "y"),
                                },
                            }

                            (config["Path"] / f"UserData/用户_{i + 1}").mkdir(
                                parents=True, exist_ok=True
                            )
                            with (
                                config["Path"] / f"UserData/用户_{i + 1}/config.json"
                            ).open(mode="w", encoding="utf-8") as f:
                                json.dump(info, f, ensure_ascii=False, indent=4)

                            if (
                                self.app_path
                                / f"config/MaaConfig/{name}/{data[i][15]}/{data[i][16]}/annihilation/gui.json"
                            ).exists():
                                (
                                    config["Path"]
                                    / f"UserData/用户_{i + 1}/Annihilation"
                                ).mkdir(parents=True, exist_ok=True)
                                shutil.move(
                                    self.app_path
                                    / f"config/MaaConfig/{name}/{data[i][15]}/{data[i][16]}/annihilation/gui.json",
                                    config["Path"]
                                    / f"UserData/用户_{i + 1}/Annihilation/gui.json",
                                )
                            if (
                                self.app_path
                                / f"config/MaaConfig/{name}/{data[i][15]}/{data[i][16]}/routine/gui.json"
                            ).exists():
                                (
                                    config["Path"] / f"UserData/用户_{i + 1}/Routine"
                                ).mkdir(parents=True, exist_ok=True)
                                shutil.move(
                                    self.app_path
                                    / f"config/MaaConfig/{name}/{data[i][15]}/{data[i][16]}/routine/gui.json",
                                    config["Path"]
                                    / f"UserData/用户_{i + 1}/Routine/gui.json",
                                )
                            if (
                                self.app_path
                                / f"config/MaaConfig/{name}/{data[i][15]}/{data[i][16]}/infrastructure/infrastructure.json"
                            ).exists():
                                (
                                    config["Path"]
                                    / f"UserData/用户_{i + 1}/Infrastructure"
                                ).mkdir(parents=True, exist_ok=True)
                                shutil.move(
                                    self.app_path
                                    / f"config/MaaConfig/{name}/{data[i][15]}/{data[i][16]}/infrastructure/infrastructure.json",
                                    config["Path"]
                                    / f"UserData/用户_{i + 1}/Infrastructure/infrastructure.json",
                                )

                        if (config["Path"] / f"simple").exists():
                            shutil.rmtree(config["Path"] / f"simple")
                        if (config["Path"] / f"beta").exists():
                            shutil.rmtree(config["Path"] / f"beta")

                cur.execute("DELETE FROM version WHERE v = ?", ("v1.4",))
                cur.execute("INSERT INTO version VALUES(?)", ("v1.5",))
                db.commit()

            # v1.5-->v1.6
            if version[0][0] == "v1.5" or if_streaming:
                logger.info("数据文件版本更新：v1.5-->v1.6")
                if_streaming = True
                cur.execute("DELETE FROM version WHERE v = ?", ("v1.5",))
                cur.execute("INSERT INTO version VALUES(?)", ("v1.6",))
                db.commit()
                # 删除旧的注册表项
                import winreg

                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_READ,
                )

                try:
                    value, _ = winreg.QueryValueEx(key, "AUTO_MAA")
                    winreg.CloseKey(key)
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        winreg.KEY_SET_VALUE,
                        winreg.KEY_ALL_ACCESS
                        | winreg.KEY_WRITE
                        | winreg.KEY_CREATE_SUB_KEY,
                    )
                    winreg.DeleteValue(key, "AUTO_MAA")
                    winreg.CloseKey(key)
                except FileNotFoundError:
                    pass
            # v1.6-->v1.7
            if version[0][0] == "v1.6" or if_streaming:
                logger.info("数据文件版本更新：v1.6-->v1.7")
                if_streaming = True

                if (self.app_path / "config/MaaConfig").exists():

                    for MaaConfig in (self.app_path / "config/MaaConfig").iterdir():
                        if MaaConfig.is_dir():
                            for user in (MaaConfig / "UserData").iterdir():
                                if user.is_dir():
                                    if (user / "config.json").exists():
                                        with (user / "config.json").open(
                                            encoding="utf-8"
                                        ) as f:
                                            user_config = json.load(f)
                                        user_config["Info"]["Stage"] = user_config[
                                            "Info"
                                        ]["GameId"]
                                        user_config["Info"]["StageMode"] = user_config[
                                            "Info"
                                        ]["GameIdMode"]
                                        user_config["Info"]["Stage_1"] = user_config[
                                            "Info"
                                        ]["GameId_1"]
                                        user_config["Info"]["Stage_2"] = user_config[
                                            "Info"
                                        ]["GameId_2"]
                                        user_config["Info"]["Stage_Remain"] = (
                                            user_config["Info"]["GameId_Remain"]
                                        )
                                        with (user / "config.json").open(
                                            "w", encoding="utf-8"
                                        ) as f:
                                            json.dump(
                                                user_config,
                                                f,
                                                ensure_ascii=False,
                                                indent=4,
                                            )

                if (self.app_path / "config/MaaPlanConfig").exists():
                    for MaaPlanConfig in (
                        self.app_path / "config/MaaPlanConfig"
                    ).iterdir():
                        if (
                            MaaPlanConfig.is_dir()
                            and (MaaPlanConfig / "config.json").exists()
                        ):
                            with (MaaPlanConfig / "config.json").open(
                                encoding="utf-8"
                            ) as f:
                                plan_config = json.load(f)

                            for k in self.stage_dict.keys():
                                plan_config[k]["Stage"] = plan_config[k]["GameId"]
                                plan_config[k]["Stage_1"] = plan_config[k]["GameId_1"]
                                plan_config[k]["Stage_2"] = plan_config[k]["GameId_2"]
                                plan_config[k]["Stage_Remain"] = plan_config[k][
                                    "GameId_Remain"
                                ]
                            with (MaaPlanConfig / "config.json").open(
                                "w", encoding="utf-8"
                            ) as f:
                                json.dump(plan_config, f, ensure_ascii=False, indent=4)

                cur.execute("DELETE FROM version WHERE v = ?", ("v1.6",))
                cur.execute("INSERT INTO version VALUES(?)", ("v1.7",))
                db.commit()

            cur.close()
            db.close()
            logger.info("数据文件版本更新完成")

    def search_member(self) -> None:
        """搜索所有脚本实例"""

        self.member_dict: Dict[
            str,
            Dict[
                str,
                Union[
                    str,
                    Path,
                    Union[MaaConfig, GeneralConfig],
                    Dict[str, Dict[str, Union[Path, MaaUserConfig, GeneralSubConfig]]],
                ],
            ],
        ] = {}
        if (self.app_path / "config/MaaConfig").exists():
            for maa_dir in (self.app_path / "config/MaaConfig").iterdir():
                if maa_dir.is_dir():

                    maa_config = MaaConfig()
                    maa_config.load(maa_dir / "config.json", maa_config)
                    maa_config.save()

                    self.member_dict[maa_dir.name] = {
                        "Type": "Maa",
                        "Path": maa_dir,
                        "Config": maa_config,
                        "UserData": None,
                    }
        if (self.app_path / "config/GeneralConfig").exists():
            for general_dir in (self.app_path / "config/GeneralConfig").iterdir():
                if general_dir.is_dir():

                    general_config = GeneralConfig()
                    general_config.load(general_dir / "config.json", general_config)
                    general_config.save()

                    self.member_dict[general_dir.name] = {
                        "Type": "General",
                        "Path": general_dir,
                        "Config": general_config,
                        "SubData": None,
                    }

        self.member_dict = dict(
            sorted(self.member_dict.items(), key=lambda x: int(x[0][3:]))
        )

    def search_maa_user(self, name: str) -> None:

        user_dict: Dict[str, Dict[str, Union[Path, MaaUserConfig]]] = {}
        for user_dir in (Config.member_dict[name]["Path"] / "UserData").iterdir():
            if user_dir.is_dir():

                user_config = MaaUserConfig()
                user_config.load(user_dir / "config.json", user_config)
                user_config.save()

                user_dict[user_dir.stem] = {"Path": user_dir, "Config": user_config}

        self.member_dict[name]["UserData"] = dict(
            sorted(user_dict.items(), key=lambda x: int(x[0][3:]))
        )

    def search_general_sub(self, name: str) -> None:

        user_dict: Dict[str, Dict[str, Union[Path, GeneralSubConfig]]] = {}
        for sub_dir in (Config.member_dict[name]["Path"] / "SubData").iterdir():
            if sub_dir.is_dir():

                sub_config = GeneralSubConfig()
                sub_config.load(sub_dir / "config.json", sub_config)
                sub_config.save()

                user_dict[sub_dir.stem] = {"Path": sub_dir, "Config": sub_config}

        self.member_dict[name]["SubData"] = dict(
            sorted(user_dict.items(), key=lambda x: int(x[0][3:]))
        )

    def search_plan(self) -> None:
        """搜索所有计划表"""

        self.plan_dict: Dict[str, Dict[str, Union[str, Path, MaaPlanConfig]]] = {}
        if (self.app_path / "config/MaaPlanConfig").exists():
            for maa_plan_dir in (self.app_path / "config/MaaPlanConfig").iterdir():
                if maa_plan_dir.is_dir():

                    maa_plan_config = MaaPlanConfig()
                    maa_plan_config.load(maa_plan_dir / "config.json", maa_plan_config)
                    maa_plan_config.save()

                    self.plan_dict[maa_plan_dir.name] = {
                        "Type": "Maa",
                        "Path": maa_plan_dir,
                        "Config": maa_plan_config,
                    }

        self.plan_dict = dict(
            sorted(self.plan_dict.items(), key=lambda x: int(x[0][3:]))
        )

    def search_queue(self):
        """搜索所有调度队列实例"""

        self.queue_dict: Dict[str, Dict[str, Union[Path, QueueConfig]]] = {}

        if (self.app_path / "config/QueueConfig").exists():
            for json_file in (self.app_path / "config/QueueConfig").glob("*.json"):

                queue_config = QueueConfig()
                queue_config.load(json_file, queue_config)
                queue_config.save()

                self.queue_dict[json_file.stem] = {
                    "Path": json_file,
                    "Config": queue_config,
                }

        self.queue_dict = dict(
            sorted(self.queue_dict.items(), key=lambda x: int(x[0][5:]))
        )

    def change_queue(self, old: str, new: str) -> None:
        """修改调度队列配置文件的队列参数"""

        for queue in self.queue_dict.values():

            if queue["Config"].get(queue["Config"].queue_Member_1) == old:
                queue["Config"].set(queue["Config"].queue_Member_1, new)
            if queue["Config"].get(queue["Config"].queue_Member_2) == old:
                queue["Config"].set(queue["Config"].queue_Member_2, new)
            if queue["Config"].get(queue["Config"].queue_Member_3) == old:
                queue["Config"].set(queue["Config"].queue_Member_3, new)
            if queue["Config"].get(queue["Config"].queue_Member_4) == old:
                queue["Config"].set(queue["Config"].queue_Member_4, new)
            if queue["Config"].get(queue["Config"].queue_Member_5) == old:
                queue["Config"].set(queue["Config"].queue_Member_5, new)
            if queue["Config"].get(queue["Config"].queue_Member_6) == old:
                queue["Config"].set(queue["Config"].queue_Member_6, new)
            if queue["Config"].get(queue["Config"].queue_Member_7) == old:
                queue["Config"].set(queue["Config"].queue_Member_7, new)
            if queue["Config"].get(queue["Config"].queue_Member_8) == old:
                queue["Config"].set(queue["Config"].queue_Member_8, new)
            if queue["Config"].get(queue["Config"].queue_Member_9) == old:
                queue["Config"].set(queue["Config"].queue_Member_9, new)
            if queue["Config"].get(queue["Config"].queue_Member_10) == old:
                queue["Config"].set(queue["Config"].queue_Member_10, new)

    def change_plan(self, old: str, new: str) -> None:
        """修改脚本管理所有下属用户的计划表配置参数"""

        for member in self.member_dict.values():

            for user in member["UserData"].values():

                if user["Config"].get(user["Config"].Info_StageMode) == old:
                    user["Config"].set(user["Config"].Info_StageMode, new)

    def change_maa_user_info(
        self, name: str, user_data: Dict[str, Dict[str, Union[str, Path, dict]]]
    ) -> None:
        """代理完成后保存改动的用户信息"""

        for user, info in user_data.items():

            user_config = self.member_dict[name]["UserData"][user]["Config"]

            user_config.set(
                user_config.Info_RemainedDay, info["Config"]["Info"]["RemainedDay"]
            )
            user_config.set(
                user_config.Data_LastProxyDate, info["Config"]["Data"]["LastProxyDate"]
            )
            user_config.set(
                user_config.Data_LastAnnihilationDate,
                info["Config"]["Data"]["LastAnnihilationDate"],
            )
            user_config.set(
                user_config.Data_LastSklandDate,
                info["Config"]["Data"]["LastSklandDate"],
            )
            user_config.set(
                user_config.Data_ProxyTimes, info["Config"]["Data"]["ProxyTimes"]
            )
            user_config.set(
                user_config.Data_IfPassCheck, info["Config"]["Data"]["IfPassCheck"]
            )
            user_config.set(
                user_config.Data_CustomInfrastPlanIndex,
                info["Config"]["Data"]["CustomInfrastPlanIndex"],
            )

        self.sub_info_changed.emit()

    def change_general_sub_info(
        self, name: str, sub_data: Dict[str, Dict[str, Union[str, Path, dict]]]
    ) -> None:
        """代理完成后保存改动的配置信息"""

        for sub, info in sub_data.items():

            sub_config = self.member_dict[name]["SubData"][sub]["Config"]

            sub_config.set(
                sub_config.Info_RemainedDay, info["Config"]["Info"]["RemainedDay"]
            )
            sub_config.set(
                sub_config.Data_LastProxyDate, info["Config"]["Data"]["LastProxyDate"]
            )
            sub_config.set(
                sub_config.Data_ProxyTimes, info["Config"]["Data"]["ProxyTimes"]
            )

        self.sub_info_changed.emit()

    def set_power_sign(self, sign: str) -> None:
        """设置当前电源状态"""

        self.power_sign = sign
        self.power_sign_changed.emit()

    def save_history(self, key: str, content: dict) -> None:
        """保存历史记录"""

        if key in self.queue_dict:
            self.queue_dict[key]["Config"].set(
                self.queue_dict[key]["Config"].Data_LastProxyTime, content["Time"]
            )
            self.queue_dict[key]["Config"].set(
                self.queue_dict[key]["Config"].Data_LastProxyHistory, content["History"]
            )
        else:
            logger.warning(f"保存历史记录时未找到调度队列: {key}")

    def save_maa_log(self, log_path: Path, logs: list, maa_result: str) -> bool:
        """保存MAA日志并生成对应统计数据"""

        data: Dict[str, Union[str, Dict[str, Union[int, dict]]]] = {
            "recruit_statistics": defaultdict(int),
            "drop_statistics": defaultdict(dict),
            "maa_result": maa_result,
        }

        if_six_star = False

        # 公招统计（仅统计招募到的）
        confirmed_recruit = False
        current_star_level = None
        i = 0
        while i < len(logs):
            if "公招识别结果:" in logs[i]:
                current_star_level = None  # 每次识别公招时清空之前的星级
                i += 1
                while i < len(logs) and "Tags" not in logs[i]:  # 读取所有公招标签
                    i += 1

                if i < len(logs) and "Tags" in logs[i]:  # 识别星级
                    star_match = re.search(r"(\d+)\s*★ Tags", logs[i])
                    if star_match:
                        current_star_level = f"{star_match.group(1)}★"
                        if current_star_level == "6★":
                            if_six_star = True

            if "已确认招募" in logs[i]:  # 只有确认招募后才统计
                confirmed_recruit = True

            if confirmed_recruit and current_star_level:
                data["recruit_statistics"][current_star_level] += 1
                confirmed_recruit = False  # 重置，等待下一次公招
                current_star_level = None  # 清空已处理的星级

            i += 1

        # 掉落统计
        # 存储所有关卡的掉落统计
        all_stage_drops = {}

        # 查找所有Fight任务的开始和结束位置
        fight_tasks = []
        for i, line in enumerate(logs):
            if "开始任务: Fight" in line:
                # 查找对应的任务结束位置
                end_index = -1
                for j in range(i + 1, len(logs)):
                    if "完成任务: Fight" in logs[j]:
                        end_index = j
                        break
                    # 如果遇到新的Fight任务开始，则当前任务没有正常结束
                    if j < len(logs) and "开始任务: Fight" in logs[j]:
                        break

                # 如果找到了结束位置，记录这个任务的范围
                if end_index != -1:
                    fight_tasks.append((i, end_index))

        # 处理每个Fight任务
        for start_idx, end_idx in fight_tasks:
            # 提取当前任务的日志
            task_logs = logs[start_idx : end_idx + 1]

            # 查找任务中的最后一次掉落统计
            last_drop_stats = {}
            current_stage = None

            for line in task_logs:
                # 匹配掉落统计行，如"1-7 掉落统计:"
                drop_match = re.search(r"([A-Za-z0-9\-]+) 掉落统计:", line)
                if drop_match:
                    # 发现新的掉落统计，重置当前关卡的掉落数据
                    current_stage = drop_match.group(1)
                    last_drop_stats = {}
                    continue

                # 如果已经找到了关卡，处理掉落物
                if current_stage:
                    item_match: List[str] = re.findall(
                        r"^(?!\[)(\S+?)\s*:\s*([\d,]+)(?:\s*\(\+[\d,]+\))?",
                        line,
                        re.M,
                    )
                    for item, total in item_match:
                        # 解析数值时去掉逗号 （如 2,160 -> 2160）
                        total = int(total.replace(",", ""))

                        # 黑名单
                        if item not in [
                            "当前次数",
                            "理智",
                            "最快截图耗时",
                            "专精等级",
                            "剩余时间",
                        ]:
                            last_drop_stats[item] = total

            # 如果任务中有掉落统计，更新总统计
            if current_stage and last_drop_stats:
                if current_stage not in all_stage_drops:
                    all_stage_drops[current_stage] = {}

                # 累加掉落数据
                for item, count in last_drop_stats.items():
                    all_stage_drops[current_stage].setdefault(item, 0)
                    all_stage_drops[current_stage][item] += count

        # 将累加后的掉落数据保存到结果中
        data["drop_statistics"] = all_stage_drops

        # 保存日志
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as f:
            f.writelines(logs)
        with log_path.with_suffix(".json").open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        logger.info(f"处理完成：{log_path}")

        return if_six_star

    def save_general_log(self, log_path: Path, logs: list, general_result: str) -> None:
        """保存通用日志并生成对应统计数据"""

        data: Dict[str, str] = {"general_result": general_result}

        # 保存日志
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.with_suffix(".log").open("w", encoding="utf-8") as f:
            f.writelines(logs)
        with log_path.with_suffix(".json").open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        logger.info(f"处理完成：{log_path}")

    def merge_statistic_info(self, statistic_path_list: List[Path]) -> dict:
        """合并指定数据统计信息文件"""

        data = {"index": {}}

        for json_file in statistic_path_list:

            with json_file.open("r", encoding="utf-8") as f:
                single_data: Dict[str, Union[str, Dict[str, Union[int, dict]]]] = (
                    json.load(f)
                )

            for key in single_data.keys():

                if key not in data:
                    data[key] = {}

                # 合并公招统计
                if key == "recruit_statistics":

                    for star_level, count in single_data[key].items():
                        if star_level not in data[key]:
                            data[key][star_level] = 0
                        data[key][star_level] += count

                # 合并掉落统计
                elif key == "drop_statistics":

                    for stage, drops in single_data[key].items():
                        if stage not in data[key]:
                            data[key][stage] = {}  # 初始化关卡

                        for item, count in drops.items():

                            if item not in data[key][stage]:
                                data[key][stage][item] = 0
                            data[key][stage][item] += count

                # 录入运行结果
                elif key in ["maa_result", "general_result"]:

                    actual_date = datetime.strptime(
                        f"{json_file.parent.parent.name} {json_file.stem}",
                        "%Y-%m-%d %H-%M-%S",
                    ) + timedelta(
                        days=(
                            1
                            if datetime.strptime(json_file.stem, "%H-%M-%S").time()
                            < datetime.min.time().replace(hour=4)
                            else 0
                        )
                    )

                    if single_data[key] != "Success!":
                        if "error_info" not in data:
                            data["error_info"] = {}
                        data["error_info"][actual_date.strftime("%d日 %H:%M:%S")] = (
                            single_data[key]
                        )

                    data["index"][actual_date] = [
                        actual_date.strftime("%d日 %H:%M:%S"),
                        ("完成" if single_data[key] == "Success!" else "异常"),
                        json_file,
                    ]

        data["index"] = [data["index"][_] for _ in sorted(data["index"])]

        return {k: v for k, v in data.items() if v}

    def search_history(
        self, mode: str, start_date: datetime, end_date: datetime
    ) -> dict:
        """搜索所有历史记录"""

        history_dict = {}

        for date_folder in (Config.app_path / "history").iterdir():
            if not date_folder.is_dir():
                continue  # 只处理日期文件夹

            try:

                date = datetime.strptime(date_folder.name, "%Y-%m-%d")

                if not (start_date <= date <= end_date):
                    continue  # 只统计在范围内的日期

                if mode == "按日合并":
                    date_name = date.strftime("%Y年 %m月 %d日")
                elif mode == "按周合并":
                    year, week, _ = date.isocalendar()
                    date_name = f"{year}年 第{week}周"
                elif mode == "按月合并":
                    date_name = date.strftime("%Y年 %m月")

                if date_name not in history_dict:
                    history_dict[date_name] = {}

                for user_folder in date_folder.iterdir():
                    if not user_folder.is_dir():
                        continue  # 只处理用户文件夹

                    if user_folder.stem not in history_dict[date_name]:
                        history_dict[date_name][user_folder.stem] = list(
                            user_folder.with_suffix("").glob("*.json")
                        )
                    else:
                        history_dict[date_name][user_folder.stem] += list(
                            user_folder.with_suffix("").glob("*.json")
                        )

            except ValueError:
                logger.warning(f"非日期格式的目录: {date_folder}")

        return {
            k: v
            for k, v in sorted(history_dict.items(), key=lambda x: x[0], reverse=True)
        }


Config = AppConfig()
