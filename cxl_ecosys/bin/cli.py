"""
 Copyright (c) 2024, Eeum, Inc.

 This software is licensed under the terms of the Revised BSD License.
 See LICENSE for details.
"""

import click
import os
import sys
import threading
import logging

from cxl_ecosys.util.logger import logger
from cxl_ecosys.bin import fabric_manager
from cxl_ecosys.bin import cxl_switch
from cxl_ecosys.bin import single_logical_device as sld
from cxl_ecosys.bin import host


@click.group()
def cli():
    pass


def validate_component(ctx, param, components):
    valid_components = ["fm", "switch", "host", "host-group", "sld", "sld-group"]
    if "all" in components:
        return ("fm", "switch", "host-group", "sld-group")
    for c in components:
        if not c in valid_components:
            raise click.BadParameter(f"Please select from {list(valid_components)}")
    return components


def validate_log_level(ctx, param, level):
    valid_levels = list(logging.getLevelNamesMapping().keys())
    if level:
        level = level.upper()
        if not level in valid_levels:
            raise click.BadParameter(f"Please select from {valid_levels}")
    return level


@cli.command(name="start")
@click.pass_context
@click.option(
    "-c",
    "--comp",
    multiple=True,
    required=True,
    callback=validate_component,
    help='Components. e.g. "-c fm -c switch ..." ',
)
@click.option("--config-file", help="<Config File> input path.")
@click.option("--log-file", help="<Log File> output path.")
@click.option("--pcap-file", help="<Packet Capture File> output path.")
@click.option("--log-level", callback=validate_log_level, help="Specify log level.")
@click.option("--show-timestamp", is_flag=True, default=False, help="Show timestamp.")
@click.option("--show-loglevel", is_flag=True, default=False, help="Show log level.")
@click.option("--show-linenumber", is_flag=True, default=False, help="Show line number.")
def start(
    ctx,
    comp,
    config_file,
    log_level,
    log_file,
    pcap_file,
    show_timestamp,
    show_loglevel,
    show_linenumber,
):
    """Start components"""

    # config file mandatory
    config_components = ["switch", "sld-group", "host-group"]
    for c in comp:
        if c in config_components and not config_file:
            raise click.BadParameter(f"Must specify <config file> for {config_components}")

    if log_level or show_timestamp or show_loglevel or show_linenumber:
        logger.set_stdout_levels(
            loglevel=log_level if log_level else "INFO",
            show_timestamp=show_timestamp,
            show_loglevel=show_loglevel,
            show_linenumber=show_linenumber,
        )

    if log_file:
        logger.create_log_file(
            f"{log_file}",
            loglevel=log_level if log_level else "INFO",
            show_timestamp=show_timestamp,
            show_loglevel=show_loglevel,
            show_linenumber=show_linenumber,
        )

    threads = []
    if pcap_file:
        from multiprocessing import Process

        pcap_proc = Process(target=start_capture, args=(ctx, pcap_file))
        pcap_proc.start()

    if "fm" in comp:
        t_fm = threading.Thread(target=start_fabric_manager, args=(ctx,))
        threads.append(t_fm)
        t_fm.start()

    if "switch" in comp:
        t_switch = threading.Thread(target=start_switch, args=(ctx, config_file))
        threads.append(t_switch)
        t_switch.start()

    if "sld" in comp:
        t_host = threading.Thread(target=start_sld, args=(ctx,))
        threads.append(t_host)
        t_host.start()
    if "sld-group" in comp:
        t_sgroup = threading.Thread(target=start_sld_group, args=(ctx, config_file))
        threads.append(t_sgroup)
        t_sgroup.start()

    if "host" in comp:
        t_host = threading.Thread(target=start_host, args=(ctx,))
        threads.append(t_host)
        t_host.start()
    elif "host-group" in comp:
        t_hgroup = threading.Thread(target=start_host_group, args=(ctx, config_file))
        threads.append(t_hgroup)
        t_hgroup.start()


# helper functions
def start_capture(ctx, pcap_file):
    def capture(pcap_file):
        from pylibpcap.pcap import Sniff, wpcap
        from pylibpcap.exception import LibpcapError

        logging.info(f"Capturing in pid: {os.getpid()}")
        if os.path.exists(pcap_file):
            os.remove(pcap_file)

        filter_str = (
            "((tcp port 8000) or (tcp port 8100) or (tcp port 8200))"
            + " and (((ip[2:2] - ((ip[0] & 0xf) << 2)) - ((tcp[12] & 0xf0) >> 2)) != 0)"
        )
        try:
            sniffobj = Sniff(iface="lo", count=-1, promisc=1, filters=filter_str)
            for plen, t, buf in sniffobj.capture():
                wpcap(buf, pcap_file)
                logger.hexdump("TRACE", buf)
        except KeyboardInterrupt:
            pass
        except LibpcapError as e:
            logger.error(f"Packet capture error: {e}")
            sys.exit()

        if sniffobj is not None:
            stats = sniffobj.stats()
            logger.debug(stats.capture_cnt, " packets captured")
            logger.debug(stats.ps_recv, " packets received by filter")
            logger.debug(stats.ps_drop, "  packets dropped by kernel")
            logger.debug(stats.ps_ifdrop, "  packets dropped by iface")

    ctx.invoke(capture, pcap_file=pcap_file)


def start_fabric_manager(ctx):
    logger.info(f"Starting fabric manager in thread id: 0x{threading.get_ident():x}")
    ctx.invoke(fabric_manager.start)


def start_switch(ctx, config_file):
    logger.info(f"Starting cxl-switch in thread id: 0x{threading.get_ident():x}")
    ctx.invoke(cxl_switch.start, config_file=config_file)


def start_host(ctx):
    logger.info(f"Starting host in thread id: 0x{threading.get_ident():x}")
    ctx.invoke(host.start)


def start_host_group(ctx, config_file):
    logger.info(f"Starting host_group in thread id: 0x{threading.get_ident():x}")
    ctx.invoke(host.start_group, config_file=config_file)


def start_sld(ctx, config_file):
    logger.info(f"Starting sld_group in thread id: 0x{threading.get_ident():x}")
    ctx.invoke(sld.start, config=config_file)


def start_sld_group(ctx, config_file):
    logger.info(f"Starting sld_group in thread id: 0x{threading.get_ident():x}")
    ctx.invoke(sld.start_group, config=config_file)


@cli.command(name="stop")
def foo():
    """Stop components"""
    pass


if __name__ == "__main__":
    cli()
