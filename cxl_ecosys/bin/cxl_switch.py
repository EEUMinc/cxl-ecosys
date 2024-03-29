"""
 Copyright (c) 2024, Eeum, Inc.

 This software is licensed under the terms of the Revised BSD License.
 See LICENSE for details.
"""

import asyncio
import click
from cxl_ecosys.util.logger import logger
from cxl_ecosys.apps.cxl_switch import CxlSwitch
from cxl_ecosys.cxl.environment import parse_cxl_environment, CxlEnvironment


# Switch command group
@click.group(name="switch")
def switch_group():
    """Command group for CXL Switch."""
    pass


@switch_group.command(name="start")
@click.argument("config_file", type=click.Path(exists=True))
def start(config_file):
    """Run the CXL Switch with the given configuration file."""
    logger.info("Starting CXL Switch with configuration file: %s", config_file)
    logger.create_log_file(
        "logs/cxl_switch.log",
        loglevel="DEBUG",
        show_timestamp=True,
        show_loglevel=True,
        show_linenumber=False,
    )

    try:
        environment: CxlEnvironment = parse_cxl_environment(config_file)
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        return

    switch = CxlSwitch(environment.switch_config, environment.single_logical_device_configs)
    asyncio.run(switch.run())
