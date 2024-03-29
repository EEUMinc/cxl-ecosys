"""
 Copyright (c) 2024, Eeum, Inc.

 This software is licensed under the terms of the Revised BSD License.
 See LICENSE for details.
"""

from typing import Optional, TypedDict

from cxl_ecosys.util.unaligned_bit_structure import ShareableByteArray
from cxl_ecosys.pci.component.pci import PciComponent
from cxl_ecosys.cxl.config_space.cfg import CxlConfigSpace
from cxl_ecosys.cxl.config_space.doe.doe import CxlDoeExtendedCapabilityOptions
from cxl_ecosys.pci.config_space import PciExpressDeviceConfigSpaceOptions
from cxl_ecosys.cxl.config_space.dvsec import DvsecConfigSpaceOptions, CXL_DEVICE_TYPE


class CxlDeviceConfigSpace(CxlConfigSpace):
    def __init__(
        self,
        options: PciExpressDeviceConfigSpaceOptions,
        data: Optional[ShareableByteArray] = None,
        parent_name: Optional[str] = None,
    ):
        self._pci_component = options["pci_component"]
        self._doe_options = options["doe"]
        self._dvsec_options = options["dvsec"]
        super().__init__(CXL_DEVICE_TYPE.LD, data, parent_name)


class CxlType3SldConfigSpaceOptions(TypedDict):
    pci_component: PciComponent
    dvsec: DvsecConfigSpaceOptions
    doe: CxlDoeExtendedCapabilityOptions


class CxlType3SldConfigSpace(CxlDeviceConfigSpace):
    def __init__(
        self,
        options: CxlType3SldConfigSpaceOptions,
        data: Optional[ShareableByteArray] = None,
        parent_name: Optional[str] = None,
    ):
        super().__init__(options, data, parent_name)
