"""
 Copyright (c) 2024, Eeum, Inc.

 This software is licensed under the terms of the Revised BSD License.
 See LICENSE for details.
"""

import re

from cxl_ecosys.util.logger import logger
from cxl_ecosys.cxl.component.cxl_component import CXL_COMPONENT_TYPE
from cxl_ecosys.cxl.device.port_device import CxlPortDevice
from cxl_ecosys.cxl.config_space.doe.doe import CxlDoeExtendedCapabilityOptions
from cxl_ecosys.cxl.config_space.dvsec import (
    DvsecConfigSpaceOptions,
    DvsecRegisterLocatorOptions,
    CXL_DEVICE_TYPE,
)
from cxl_ecosys.cxl.config_space.port import (
    CxlUpstreamPortConfigSpace,
    CxlUpstreamPortConfigSpaceOptions,
)
from cxl_ecosys.cxl.mmio import CombinedMmioRegister, CombinedMmioRegiterOptions
from cxl_ecosys.cxl.component.cxl_connection import CxlConnection
from cxl_ecosys.cxl.component.cxl_bridge_component import (
    CxlUpstreamPortComponent,
    HDM_DECODER_COUNT,
)
from cxl_ecosys.cxl.component.virtual_switch.routing_table import RoutingTable
from cxl_ecosys.cxl.component.cxl_mem_manager import CxlMemManager
from cxl_ecosys.pci.component.pci import (
    PciBridgeComponent,
    PCI_BRIDGE_TYPE,
    PciComponentIdentity,
    EEUM_VID,
    SW_USP_DID,
    PCI_CLASS,
    PCI_BRIDGE_SUBCLASS,
    PCI_DEVICE_PORT_TYPE,
)
from cxl_ecosys.pci.component.mmio_manager import MmioManager, BarEntry
from cxl_ecosys.pci.component.config_space_manager import (
    ConfigSpaceManager,
    PCI_DEVICE_TYPE,
)


class UpstreamPortDevice(CxlPortDevice):
    def __init__(self, transport_connection: CxlConnection, port_index: int):
        super().__init__(transport_connection, port_index)
        self._downstream_connection = CxlConnection()
        self._decoder_count = HDM_DECODER_COUNT.DECODER_32

        label = f"USP{self._port_index}"
        self._label = label

        # NOTE: Create USP Component
        self._cxl_component = CxlUpstreamPortComponent(
            decoder_count=self._decoder_count, label=label
        )

        self._mmio_manager = MmioManager(
            self._transport_connection.mmio_fifo,
            self._downstream_connection.mmio_fifo,
            label=label,
        )

        pci_identity = PciComponentIdentity(
            vendor_id=EEUM_VID,
            device_id=SW_USP_DID,
            base_class_code=PCI_CLASS.BRIDGE,
            sub_class_coce=PCI_BRIDGE_SUBCLASS.PCI_BRIDGE,
            programming_interface=0x00,
            device_port_type=PCI_DEVICE_PORT_TYPE.UPSTREAM_PORT_OF_PCI_EXPRESS_SWITCH,
        )

        self._pci_bridge_component = PciBridgeComponent(
            identity=pci_identity,
            type=PCI_BRIDGE_TYPE.UPSTREAM_PORT,
            mmio_manager=self._mmio_manager,
        )

        self._config_space_manager = ConfigSpaceManager(
            self._transport_connection.cfg_fifo,
            self._downstream_connection.cfg_fifo,
            label=label,
            device_type=PCI_DEVICE_TYPE.UPSTREAM_BRIDGE,
        )

        self._cxl_mem_manager = CxlMemManager(
            self._transport_connection.cxl_mem_fifo,
            self._downstream_connection.cxl_mem_fifo,
            label=label,
        )

        # NOTE: Create MMIO Register
        mmio_options = CombinedMmioRegiterOptions(cxl_component=self._cxl_component)
        mmio_register = CombinedMmioRegister(options=mmio_options)
        self._mmio_manager.set_bar_entries([BarEntry(mmio_register)])

        # NOTE: Create Config Space Register
        doe_options = CxlDoeExtendedCapabilityOptions(cdat_entries=[])
        pci_registers_options = CxlUpstreamPortConfigSpaceOptions(
            pci_bridge_component=self._pci_bridge_component,
            dvsec=DvsecConfigSpaceOptions(
                device_type=CXL_DEVICE_TYPE.USP,
                register_locator=DvsecRegisterLocatorOptions(
                    registers=mmio_register.get_dvsec_register_offsets()
                ),
            ),
            doe=doe_options,
        )
        pci_registers = CxlUpstreamPortConfigSpace(options=pci_registers_options)
        self._config_space_manager.set_register(pci_registers)

    def get_reg_vals(self):
        return self._config_space_manager.get_register()

    def get_downstream_connection(self) -> CxlConnection:
        return self._downstream_connection

    def set_routing_table(self, routing_table: RoutingTable):
        logger.debug(f"[UpstreamPort{self.get_port_index()}] Setting routing table")
        self._pci_bridge_component.set_routing_table(routing_table)
        self._cxl_component.set_routing_table(routing_table)

    def get_device_type(self) -> CXL_COMPONENT_TYPE:
        return CXL_COMPONENT_TYPE.USP

    def get_hdm_decoder_count(self) -> int:
        name = HDM_DECODER_COUNT(self._decoder_count).name
        return int(re.search(r"\d+", name).group())
