"""
 Copyright (c) 2024, Eeum, Inc.

 This software is licensed under the terms of the Revised BSD License.
 See LICENSE for details.
"""

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum, IntEnum, auto
from typing import Optional, List

from cxl_ecosys.cxl.config_space.doe.cdat import CDAT_ENTRY
from cxl_ecosys.cxl.features.mailbox import CxlMailbox
from cxl_ecosys.cxl.features.event_manager import EventManager
from cxl_ecosys.cxl.features.log_manager import LogManager
from cxl_ecosys.cxl.component.hdm_decoder import HdmDecoderManagerBase
from cxl_ecosys.util.component import LabeledComponent


class CXL_COMPONENT_TYPE(Enum):
    P = auto()
    D1 = auto()
    D2 = auto()
    LD = auto()
    FMLD = auto()
    UP1 = auto()
    DP1 = auto()
    R = auto()
    RC = auto()
    USP = auto()
    DSP = auto()


class PORT_TYPE(Enum):
    USP = auto()
    DSP = auto()


@dataclass
class PortConfig:
    type: PORT_TYPE


class CxlComponent(LabeledComponent):
    def get_primary_mailbox(self) -> Optional[CxlMailbox]:
        return None

    def get_secondary_mailbox(self) -> Optional[CxlMailbox]:
        return None

    def get_hdm_decoder_manager(self) -> Optional[HdmDecoderManagerBase]:
        return None

    def get_cdat_entries(self) -> List[CDAT_ENTRY]:
        return []

    @abstractmethod
    def get_component_type(self) -> CXL_COMPONENT_TYPE:
        """This must be implemented in the child class"""


class CXL_DEVICE_CAPABILITY_TYPE(IntEnum):
    INFER_PCI_CLASS_CODE = 0
    MEMORY_DEVICE = 1
    SWITCH_MAILBOX_CCI = 2


class CxlDeviceComponent(CxlComponent):
    @abstractmethod
    def get_capability_type(self) -> CXL_DEVICE_CAPABILITY_TYPE:
        """This must be implemented in the child class"""

    @abstractmethod
    def get_event_manager(self) -> EventManager:
        """This must be implemented in the child class"""

    @abstractmethod
    def get_log_manager(self) -> LogManager:
        """This must be implemented in the child class"""
