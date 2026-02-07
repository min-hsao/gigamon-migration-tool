#!/usr/bin/env python3
"""
Gigamon HC2 Migration Tool
==========================
Analyzes a GigaVUE-HC2 "show diag" configuration file and recommends
replacement hardware with port mapping, ASCII diagram, and Bill of Materials.

Usage:
    python migrate_hc2.py <show_diag_file.log> [--output-dir <dir>]

Author: Skippy (OpenClaw)
Version: 1.0.0
"""

import re
import sys
import os
import json
import argparse
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


@dataclass
class Port:
    """Represents a configured port."""
    slot: str
    port_id: str
    full_id: str
    port_type: str  # 'inline-network', 'inline-tool', 'network', 'tool'
    alias: str = ""
    side: str = ""  # 'A' or 'B' for inline
    pair_alias: str = ""
    maps: List[str] = field(default_factory=list)
    is_spare: bool = False
    speed: str = "10G"  # 10G, 1G, 40G, 100G
    media: str = "SFP+"  # SFP+, QSFP, RJ45


@dataclass
class InlineNetwork:
    """Represents an inline network pair."""
    alias: str
    net_a_port: str
    net_b_port: str
    maps: List[str] = field(default_factory=list)


@dataclass
class InlineTool:
    """Represents an inline tool pair."""
    alias: str
    side_a_port: str
    side_b_port: str
    maps: List[str] = field(default_factory=list)
    is_spare: bool = False
    tool_group: str = ""


@dataclass 
class ChassisInfo:
    """Information about the source chassis."""
    hostname: str = ""
    hw_type: str = ""
    software_version: str = ""
    slots: Dict[str, str] = field(default_factory=dict)
    ip_address: str = ""


@dataclass
class MigrationAnalysis:
    """Complete analysis of the migration."""
    chassis: ChassisInfo
    inline_networks: List[InlineNetwork]
    inline_tools: List[InlineTool]
    network_ports: List[Port]
    tool_ports: List[Port]
    has_gigasmart: bool = False
    gsops: List[str] = field(default_factory=list)
    total_ports: int = 0
    has_1g_ports: bool = False
    has_tap_module: bool = False
    recommended_platform: str = ""
    recommended_modules: List[str] = field(default_factory=list)


class HC2Parser:
    """Parses GigaVUE-HC2 show diag output."""
    
    def __init__(self, content: str):
        self.content = content
        self.lines = content.split('\n')
        
    def parse(self) -> MigrationAnalysis:
        """Parse the configuration and return analysis."""
        analysis = MigrationAnalysis(
            chassis=self._parse_chassis_info(),
            inline_networks=self._parse_inline_networks(),
            inline_tools=self._parse_inline_tools(),
            network_ports=self._parse_network_ports(),
            tool_ports=self._parse_tool_ports(),
            has_gigasmart=self._check_gigasmart(),
            gsops=self._parse_gsops(),
        )
        
        # Calculate totals
        analysis.total_ports = (
            len(analysis.inline_networks) * 2 +
            len(analysis.inline_tools) * 2 +
            len(analysis.network_ports) +
            len(analysis.tool_ports)
        )
        
        # Check for 1G ports (TAP module)
        analysis.has_1g_ports = self._has_1g_ports()
        analysis.has_tap_module = 'TAP-HC0' in self.content or 'TAP-HC' in self.content
        
        # Generate recommendations
        analysis.recommended_platform, analysis.recommended_modules = self._recommend_hardware(analysis)
        
        return analysis
    
    def _parse_chassis_info(self) -> ChassisInfo:
        """Extract chassis information."""
        info = ChassisInfo()
        
        # Hostname
        match = re.search(r'[Hh]ostname[:\s]+(\S+)', self.content)
        if match:
            info.hostname = match.group(1)
        
        # Hardware type
        match = re.search(r'HW [Tt]ype\s*:\s*(CHS-HC\d+\S*)', self.content)
        if match:
            info.hw_type = match.group(1)
        
        # Software version
        match = re.search(r'Software Version:\s*GigaVUE-OS\s+(\S+)', self.content)
        if match:
            info.software_version = match.group(1)
        
        # Parse slot information
        slot_pattern = re.compile(r'^(\d+|cc\d+)\s+yes\s+\S+\s+(\S+)', re.MULTILINE)
        for match in slot_pattern.finditer(self.content):
            info.slots[match.group(1)] = match.group(2)
        
        return info
    
    def _parse_inline_networks(self) -> List[InlineNetwork]:
        """Extract inline network configurations."""
        networks = []
        
        # Look for inline-network definitions
        pattern = re.compile(
            r'inline-network\s+alias\s+(\S+).*?'
            r'net[_-]?a\s+(\d+/\d+/\S+).*?'
            r'net[_-]?b\s+(\d+/\d+/\S+)',
            re.DOTALL | re.IGNORECASE
        )
        
        for match in pattern.finditer(self.content):
            networks.append(InlineNetwork(
                alias=match.group(1),
                net_a_port=match.group(2),
                net_b_port=match.group(3)
            ))
        
        # Alternative parsing: look for port configurations
        if not networks:
            # Try to find from port alias patterns
            net_pattern = re.compile(r'(\d+/\d+/\S+).*?inline-network.*?alias\s+(\S+)', re.IGNORECASE)
            port_pairs = defaultdict(dict)
            
            for line in self.lines:
                if 'inline-network' in line.lower():
                    # Extract port and alias information
                    port_match = re.search(r'(\d+/\d+/\S+)', line)
                    alias_match = re.search(r'alias\s+(\S+)', line)
                    side_match = re.search(r'(net-?[ab]|side-?[ab])', line.lower())
                    
                    if port_match and alias_match:
                        alias = alias_match.group(1)
                        port = port_match.group(1)
                        side = 'a' if side_match and 'a' in side_match.group(1) else 'b'
                        
                        if side == 'a':
                            port_pairs[alias]['net_a'] = port
                        else:
                            port_pairs[alias]['net_b'] = port
            
            for alias, ports in port_pairs.items():
                if 'net_a' in ports and 'net_b' in ports:
                    networks.append(InlineNetwork(
                        alias=alias,
                        net_a_port=ports['net_a'],
                        net_b_port=ports['net_b']
                    ))
        
        return networks
    
    def _parse_inline_tools(self) -> List[InlineTool]:
        """Extract inline tool configurations."""
        tools = []
        seen_aliases = set()
        
        # Look for inline-tool definitions in config section
        pattern = re.compile(
            r'inline-tool\s+alias\s+(\S+).*?'
            r'side[_-]?a\s+(\d+/\d+/\S+).*?'
            r'side[_-]?b\s+(\d+/\d+/\S+)',
            re.DOTALL | re.IGNORECASE
        )
        
        for match in pattern.finditer(self.content):
            alias = match.group(1)
            if alias not in seen_aliases:
                tools.append(InlineTool(
                    alias=alias,
                    side_a_port=match.group(2),
                    side_b_port=match.group(3)
                ))
                seen_aliases.add(alias)
        
        # Check for spare tools (tools in groups but not in active maps)
        for tool in tools:
            # Simple heuristic: if alias contains "spare" or "-B" suffix and low map count
            if 'spare' in tool.alias.lower() or tool.alias.endswith('-B'):
                tool.is_spare = True
        
        return tools
    
    def _parse_network_ports(self) -> List[Port]:
        """Extract out-of-band network ports."""
        ports = []
        
        # Look for network port configurations
        pattern = re.compile(r'port\s+(\d+/\d+/\S+)\s+type\s+network', re.IGNORECASE)
        
        for match in pattern.finditer(self.content):
            port_id = match.group(1)
            alias = self._find_port_alias(port_id)
            
            ports.append(Port(
                slot=port_id.split('/')[0],
                port_id=port_id,
                full_id=port_id,
                port_type='network',
                alias=alias,
                speed=self._get_port_speed(port_id),
                media=self._get_port_media(port_id)
            ))
        
        return ports
    
    def _parse_tool_ports(self) -> List[Port]:
        """Extract out-of-band tool ports."""
        ports = []
        
        # Look for tool port configurations
        pattern = re.compile(r'port\s+(\d+/\d+/\S+)\s+type\s+tool', re.IGNORECASE)
        
        for match in pattern.finditer(self.content):
            port_id = match.group(1)
            alias = self._find_port_alias(port_id)
            
            ports.append(Port(
                slot=port_id.split('/')[0],
                port_id=port_id,
                full_id=port_id,
                port_type='tool',
                alias=alias,
                speed=self._get_port_speed(port_id),
                media=self._get_port_media(port_id)
            ))
        
        return ports
    
    def _find_port_alias(self, port_id: str) -> str:
        """Find the alias for a given port."""
        pattern = re.compile(rf'{re.escape(port_id)}.*?alias\s+(\S+)', re.IGNORECASE)
        match = pattern.search(self.content)
        if match:
            return match.group(1)
        
        # Try reverse: alias ... port
        pattern = re.compile(rf'alias\s+(\S+).*?{re.escape(port_id)}', re.IGNORECASE)
        match = pattern.search(self.content)
        if match:
            return match.group(1)
        
        return ""
    
    def _get_port_speed(self, port_id: str) -> str:
        """Determine port speed from port ID."""
        if '/g' in port_id.lower():
            return "1G"
        elif '/q' in port_id.lower():
            return "40G"
        elif '/c' in port_id.lower():
            return "100G"
        else:
            return "10G"
    
    def _get_port_media(self, port_id: str) -> str:
        """Determine port media type."""
        if '/g' in port_id.lower():
            # Check if it's copper
            if 'TAP' in self.content and 'C0' in self.content:
                return "RJ45"
            return "SFP"
        elif '/q' in port_id.lower():
            return "QSFP+"
        elif '/c' in port_id.lower():
            return "QSFP28"
        else:
            return "SFP+"
    
    def _check_gigasmart(self) -> bool:
        """Check if GigaSMART is configured."""
        if 'No gsgroups configured' in self.content:
            return False
        if 'No gsops configured' in self.content:
            return False
        
        # Check for active gsops
        gsop_pattern = re.compile(r'gsop\s+alias\s+\S+', re.IGNORECASE)
        return bool(gsop_pattern.search(self.content))
    
    def _parse_gsops(self) -> List[str]:
        """Extract GigaSMART operations if any."""
        gsops = []
        pattern = re.compile(r'gsop\s+alias\s+(\S+)', re.IGNORECASE)
        
        for match in pattern.finditer(self.content):
            gsops.append(match.group(1))
        
        return gsops
    
    def _has_1g_ports(self) -> bool:
        """Check if there are 1G ports configured."""
        return bool(re.search(r'\d+/\d+/g\d+', self.content, re.IGNORECASE))
    
    def _recommend_hardware(self, analysis: MigrationAnalysis) -> Tuple[str, List[str]]:
        """Recommend replacement hardware based on analysis."""
        total_ports = analysis.total_ports
        modules = []
        
        # Decision logic
        if analysis.has_gigasmart:
            # Needs GigaSMART - must use HC3 or HC1-Plus
            if total_ports <= 32:
                platform = "GigaVUE-HC1-Plus"
                modules = ["Base: 8x100G + 16x25G built-in", "GigaSMART license required"]
            else:
                platform = "GigaVUE-HC3"
                modules = [
                    "SMT-HC3-C16 (16x 10G/25G/100G)",
                    "GigaSMART module (if advanced features needed)",
                    "Additional modules as needed"
                ]
        elif total_ports <= 48:
            # TA25E is preferred for simplicity and cost
            platform = "GigaVUE-TA25E"
            modules = [
                "Base: 48x SFP28 (10G/25G) + 8x QSFP28 (100G)",
                "IBP License (for inline bypass protection)"
            ]
            
            if analysis.has_1g_ports or analysis.has_tap_module:
                modules.append("⚠️  1G copper ports require: media converters OR external 1G TAPs")
                modules.append("")
                modules.append("─── ALTERNATIVE OPTION ───")
                modules.append("GigaVUE-HC1-Plus (if native 1G TAP needed):")
                modules.append("  • Base: 8x100G + 16x25G built-in")
                modules.append("  • TAP-HC1-G100C0 (1G copper TAP module)")
                modules.append("  • IBP License")
        
        else:
            # Large deployment - HC3
            platform = "GigaVUE-HC3"
            modules = [
                "SMT-HC3-C16 (16x multi-rate 10G/25G/40G/100G)",
                "BPS-HC3-C25F2G (Inline bypass module)",
            ]
            
            if analysis.has_1g_ports:
                modules.append("TAP-HC3-G100C0 (1G copper TAP)")
            
            # Calculate how many modules needed
            ports_per_module = 16
            modules_needed = (total_ports + ports_per_module - 1) // ports_per_module
            if modules_needed > 1:
                modules.append(f"Note: {modules_needed} port modules may be needed")
        
        return platform, modules


class ReportGenerator:
    """Generates migration reports."""
    
    def __init__(self, analysis: MigrationAnalysis):
        self.analysis = analysis
    
    def generate_ascii_diagram(self) -> str:
        """Generate ASCII diagram of the new configuration."""
        a = self.analysis
        platform = a.recommended_platform
        
        # Calculate port assignments
        port_num = 1
        inline_net_ports = []
        inline_tool_active_ports = []
        inline_tool_spare_ports = []
        oob_net_ports = []
        oob_tool_ports = []
        
        # Assign ports
        for net in a.inline_networks:
            inline_net_ports.append((port_num, port_num + 1, net.alias))
            port_num += 2
        
        active_tools = [t for t in a.inline_tools if not t.is_spare]
        spare_tools = [t for t in a.inline_tools if t.is_spare]
        
        for tool in active_tools:
            inline_tool_active_ports.append((port_num, port_num + 1, tool.alias))
            port_num += 2
        
        for tool in spare_tools:
            inline_tool_spare_ports.append((port_num, port_num + 1, tool.alias))
            port_num += 2
        
        for p in a.network_ports:
            oob_net_ports.append((port_num, p.alias or f"Net-{port_num}"))
            port_num += 1
        
        for p in a.tool_ports:
            oob_tool_ports.append((port_num, p.alias or f"Tool-{port_num}"))
            port_num += 1
        
        # Build diagram
        width = 100
        lines = []
        
        lines.append("=" * width)
        lines.append(f"  {platform} Migration from {a.chassis.hostname} ({a.chassis.hw_type})".center(width))
        lines.append("=" * width)
        lines.append("")
        
        # Main chassis box
        lines.append("┌" + "─" * (width - 2) + "┐")
        lines.append("│" + f"  {platform}".ljust(width - 3) + "│")
        lines.append("│" + f"  Migrated from: {a.chassis.hostname}".ljust(width - 3) + "│")
        lines.append("├" + "─" * (width - 2) + "┤")
        
        # Inline Networks section
        if inline_net_ports:
            lines.append("│" + "  INLINE NETWORKS".ljust(width - 3) + "│")
            lines.append("│" + "  " + "─" * 40 + " ".ljust(width - 45) + "│")
            
            port_line = "│  "
            for start, end, alias in inline_net_ports:
                port_line += f"[P{start}-P{end}: {alias[:15]}]  "
            port_line = port_line.ljust(width - 2) + "│"
            lines.append(port_line)
            lines.append("│" + " " * (width - 3) + "│")
        
        # Inline Tools Active section
        if inline_tool_active_ports:
            lines.append("│" + "  INLINE TOOLS (Active)".ljust(width - 3) + "│")
            lines.append("│" + "  " + "─" * 40 + " ".ljust(width - 45) + "│")
            
            # Split into rows of 4
            for i in range(0, len(inline_tool_active_ports), 4):
                port_line = "│  "
                for start, end, alias in inline_tool_active_ports[i:i+4]:
                    short_alias = alias[:12] if len(alias) > 12 else alias
                    port_line += f"[P{start}-P{end}: {short_alias}]  "
                port_line = port_line.ljust(width - 2) + "│"
                lines.append(port_line)
            lines.append("│" + " " * (width - 3) + "│")
        
        # Inline Tools Spare section
        if inline_tool_spare_ports:
            lines.append("│" + "  INLINE TOOLS (Spare)".ljust(width - 3) + "│")
            lines.append("│" + "  " + "─" * 40 + " ".ljust(width - 45) + "│")
            
            for i in range(0, len(inline_tool_spare_ports), 4):
                port_line = "│  "
                for start, end, alias in inline_tool_spare_ports[i:i+4]:
                    short_alias = alias[:12] if len(alias) > 12 else alias
                    port_line += f"[P{start}-P{end}: {short_alias}]  "
                port_line = port_line.ljust(width - 2) + "│"
                lines.append(port_line)
            lines.append("│" + " " * (width - 3) + "│")
        
        # OOB Network section
        if oob_net_ports:
            lines.append("│" + "  OUT-OF-BAND NETWORK PORTS".ljust(width - 3) + "│")
            lines.append("│" + "  " + "─" * 40 + " ".ljust(width - 45) + "│")
            
            for i in range(0, len(oob_net_ports), 5):
                port_line = "│  "
                for pnum, alias in oob_net_ports[i:i+5]:
                    short_alias = alias[:10] if len(alias) > 10 else alias
                    port_line += f"[P{pnum}: {short_alias}]  "
                port_line = port_line.ljust(width - 2) + "│"
                lines.append(port_line)
            lines.append("│" + " " * (width - 3) + "│")
        
        # OOB Tool section
        if oob_tool_ports:
            lines.append("│" + "  OUT-OF-BAND TOOL PORTS".ljust(width - 3) + "│")
            lines.append("│" + "  " + "─" * 40 + " ".ljust(width - 45) + "│")
            
            for i in range(0, len(oob_tool_ports), 5):
                port_line = "│  "
                for pnum, alias in oob_tool_ports[i:i+5]:
                    short_alias = alias[:10] if len(alias) > 10 else alias
                    port_line += f"[P{pnum}: {short_alias}]  "
                port_line = port_line.ljust(width - 2) + "│"
                lines.append(port_line)
            lines.append("│" + " " * (width - 3) + "│")
        
        # Spare ports
        spare_start = port_num
        if platform == "GigaVUE-TA25E":
            spare_end = 48
            qsfp_ports = "Q1-Q8 (100G QSFP28)"
        elif platform == "GigaVUE-HC1-Plus":
            spare_end = 24
            qsfp_ports = "8x 100G QSFP28 built-in"
        else:
            spare_end = 64
            qsfp_ports = "QSFP28 ports per module config"
        
        if spare_start <= spare_end:
            lines.append("│" + f"  SPARE PORTS: P{spare_start}-P{spare_end} | {qsfp_ports}".ljust(width - 3) + "│")
        
        lines.append("└" + "─" * (width - 2) + "┘")
        
        # Summary section
        lines.append("")
        lines.append("=" * width)
        lines.append("  PORT SUMMARY".center(width))
        lines.append("=" * width)
        lines.append("")
        lines.append(f"  {'Category':<30} {'Count':<10} {'Ports':<20}")
        lines.append(f"  {'-' * 30} {'-' * 10} {'-' * 20}")
        lines.append(f"  {'Inline Networks':<30} {len(a.inline_networks) * 2:<10} {'pairs: ' + str(len(a.inline_networks)):<20}")
        lines.append(f"  {'Inline Tools (Active)':<30} {len(active_tools) * 2:<10} {'pairs: ' + str(len(active_tools)):<20}")
        lines.append(f"  {'Inline Tools (Spare)':<30} {len(spare_tools) * 2:<10} {'pairs: ' + str(len(spare_tools)):<20}")
        lines.append(f"  {'OOB Network Ports':<30} {len(a.network_ports):<10} {'':<20}")
        lines.append(f"  {'OOB Tool Ports':<30} {len(a.tool_ports):<10} {'':<20}")
        lines.append(f"  {'-' * 30} {'-' * 10} {'-' * 20}")
        lines.append(f"  {'TOTAL CONFIGURED':<30} {a.total_ports:<10} {'':<20}")
        lines.append("")
        
        # Notes
        if a.has_1g_ports:
            lines.append("  ⚠️  NOTE: Original config has 1G ports - may need media converters")
        if a.has_gigasmart:
            lines.append("  ⚠️  NOTE: GigaSMART is configured - ensure licensing on new platform")
        if not a.has_gigasmart:
            lines.append("  ✅  No GigaSMART configured - no additional licensing needed")
        
        lines.append("")
        lines.append("=" * width)
        
        return "\n".join(lines)
    
    def generate_bom(self) -> str:
        """Generate Bill of Materials."""
        a = self.analysis
        lines = []
        
        lines.append("=" * 80)
        lines.append("  BILL OF MATERIALS".center(80))
        lines.append(f"  Migration from {a.chassis.hostname} ({a.chassis.hw_type})".center(80))
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        lines.append("=" * 80)
        lines.append("")
        
        lines.append(f"  {'Item':<5} {'Part Number':<25} {'Description':<40} {'Qty':<5}")
        lines.append(f"  {'-' * 5} {'-' * 25} {'-' * 40} {'-' * 5}")
        
        item = 1
        
        # Platform
        if a.recommended_platform == "GigaVUE-TA25E":
            lines.append(f"  {item:<5} {'GVS-TA25E':<25} {'GigaVUE-TA25E Chassis':<40} {'1':<5}")
            item += 1
            lines.append(f"  {item:<5} {'GVS-TA25E-IBP':<25} {'Inline Bypass Protection License':<40} {'1':<5}")
            item += 1
            
            # SFP+ transceivers (estimate based on port count)
            sfp_count = min(a.total_ports, 48)
            lines.append(f"  {item:<5} {'SFP-532':<25} {'10G SFP+ SR Transceiver':<40} {sfp_count:<5}")
            item += 1
            
        elif a.recommended_platform == "GigaVUE-HC1-Plus":
            lines.append(f"  {item:<5} {'GVS-HC1P':<25} {'GigaVUE-HC1-Plus Chassis':<40} {'1':<5}")
            item += 1
            lines.append(f"  {item:<5} {'GVS-HC1P-IBP':<25} {'Inline Bypass Protection License':<40} {'1':<5}")
            item += 1
            
            if a.has_1g_ports:
                lines.append(f"  {item:<5} {'TAP-HC1-G100C0':<25} {'1G Copper TAP Module':<40} {'1':<5}")
                item += 1
            
        else:  # HC3
            lines.append(f"  {item:<5} {'GVS-HC300':<25} {'GigaVUE-HC3 Chassis':<40} {'1':<5}")
            item += 1
            
            # Calculate modules needed
            ports_needed = a.total_ports
            modules_needed = (ports_needed + 15) // 16
            
            lines.append(f"  {item:<5} {'SMT-HC3-C16':<25} {'16-port 10G/25G/100G Module':<40} {modules_needed:<5}")
            item += 1
            
            if a.inline_networks:
                lines.append(f"  {item:<5} {'BPS-HC3-C25F2G':<25} {'Inline Bypass Module':<40} {'1':<5}")
                item += 1
            
            if a.has_1g_ports:
                lines.append(f"  {item:<5} {'TAP-HC3-G100C0':<25} {'1G Copper TAP Module':<40} {'1':<5}")
                item += 1
        
        # Common items
        lines.append(f"  {item:<5} {'PWR-AC-TA25E/HC1/HC3':<25} {'AC Power Supply (Redundant)':<40} {'2':<5}")
        item += 1
        
        lines.append("")
        lines.append("=" * 80)
        lines.append("  NOTES:")
        lines.append("  - Part numbers are representative; verify with Gigamon for exact SKUs")
        lines.append("  - Transceiver quantities may vary based on actual deployment needs")
        lines.append("  - Consider spare transceivers (10-20% additional)")
        if a.has_1g_ports:
            lines.append("  - 1G copper connectivity may require media converters if TAP module not used")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def generate_csv(self) -> str:
        """Generate CSV port mapping."""
        a = self.analysis
        lines = []
        
        lines.append("New Port,Type,Category,Alias,Original Port,Side,Notes")
        
        port_num = 1
        
        # Inline networks
        for net in a.inline_networks:
            lines.append(f"{port_num},SFP28,Inline Network,{net.alias}-Net-A,{net.net_a_port},A,Inline pair")
            port_num += 1
            lines.append(f"{port_num},SFP28,Inline Network,{net.alias}-Net-B,{net.net_b_port},B,Inline pair")
            port_num += 1
        
        # Inline tools
        for tool in a.inline_tools:
            status = "Spare" if tool.is_spare else "Active"
            lines.append(f"{port_num},SFP28,Inline Tool ({status}),{tool.alias}-Side-A,{tool.side_a_port},A,")
            port_num += 1
            lines.append(f"{port_num},SFP28,Inline Tool ({status}),{tool.alias}-Side-B,{tool.side_b_port},B,")
            port_num += 1
        
        # OOB Network
        for p in a.network_ports:
            lines.append(f"{port_num},SFP28,OOB Network,{p.alias},{p.full_id},-,{p.speed} {p.media}")
            port_num += 1
        
        # OOB Tool
        for p in a.tool_ports:
            lines.append(f"{port_num},SFP28,OOB Tool,{p.alias},{p.full_id},-,{p.speed} {p.media}")
            port_num += 1
        
        return "\n".join(lines)
    
    def generate_json(self) -> str:
        """Generate JSON report."""
        a = self.analysis
        
        report = {
            "source": {
                "hostname": a.chassis.hostname,
                "hw_type": a.chassis.hw_type,
                "software_version": a.chassis.software_version,
                "slots": a.chassis.slots
            },
            "recommendation": {
                "platform": a.recommended_platform,
                "modules": a.recommended_modules
            },
            "summary": {
                "total_ports": a.total_ports,
                "inline_networks": len(a.inline_networks),
                "inline_tools_active": len([t for t in a.inline_tools if not t.is_spare]),
                "inline_tools_spare": len([t for t in a.inline_tools if t.is_spare]),
                "oob_network_ports": len(a.network_ports),
                "oob_tool_ports": len(a.tool_ports),
                "has_gigasmart": a.has_gigasmart,
                "has_1g_ports": a.has_1g_ports
            },
            "port_mapping": {
                "inline_networks": [
                    {"alias": n.alias, "net_a": n.net_a_port, "net_b": n.net_b_port}
                    for n in a.inline_networks
                ],
                "inline_tools": [
                    {"alias": t.alias, "side_a": t.side_a_port, "side_b": t.side_b_port, "spare": t.is_spare}
                    for t in a.inline_tools
                ],
                "network_ports": [
                    {"alias": p.alias, "port": p.full_id, "speed": p.speed}
                    for p in a.network_ports
                ],
                "tool_ports": [
                    {"alias": p.alias, "port": p.full_id, "speed": p.speed}
                    for p in a.tool_ports
                ]
            },
            "generated": datetime.now().isoformat()
        }
        
        return json.dumps(report, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze GigaVUE-HC2 config and recommend migration to modern hardware"
    )
    parser.add_argument("input_file", help="Path to show diag output file")
    parser.add_argument("--output-dir", "-o", default=".", help="Output directory for reports")
    parser.add_argument("--format", "-f", choices=["all", "ascii", "csv", "json", "bom"], 
                       default="all", help="Output format(s)")
    
    args = parser.parse_args()
    
    # Read input file
    if not os.path.exists(args.input_file):
        print(f"Error: File not found: {args.input_file}")
        sys.exit(1)
    
    with open(args.input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Parse configuration
    print(f"Analyzing: {args.input_file}")
    parser_obj = HC2Parser(content)
    analysis = parser_obj.parse()
    
    # Generate reports
    generator = ReportGenerator(analysis)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Base filename
    base_name = os.path.splitext(os.path.basename(args.input_file))[0]
    
    outputs = []
    
    if args.format in ["all", "ascii"]:
        ascii_file = os.path.join(args.output_dir, f"{base_name}_migration_diagram.txt")
        with open(ascii_file, 'w') as f:
            f.write(generator.generate_ascii_diagram())
        outputs.append(ascii_file)
        print(f"Generated: {ascii_file}")
    
    if args.format in ["all", "csv"]:
        csv_file = os.path.join(args.output_dir, f"{base_name}_port_mapping.csv")
        with open(csv_file, 'w') as f:
            f.write(generator.generate_csv())
        outputs.append(csv_file)
        print(f"Generated: {csv_file}")
    
    if args.format in ["all", "bom"]:
        bom_file = os.path.join(args.output_dir, f"{base_name}_bill_of_materials.txt")
        with open(bom_file, 'w') as f:
            f.write(generator.generate_bom())
        outputs.append(bom_file)
        print(f"Generated: {bom_file}")
    
    if args.format in ["all", "json"]:
        json_file = os.path.join(args.output_dir, f"{base_name}_migration.json")
        with open(json_file, 'w') as f:
            f.write(generator.generate_json())
        outputs.append(json_file)
        print(f"Generated: {json_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Source Device: {analysis.chassis.hostname} ({analysis.chassis.hw_type})")
    print(f"Recommended Platform: {analysis.recommended_platform}")
    print(f"Total Ports to Migrate: {analysis.total_ports}")
    print(f"GigaSMART Required: {'Yes' if analysis.has_gigasmart else 'No'}")
    print(f"1G Ports Present: {'Yes' if analysis.has_1g_ports else 'No'}")
    print("\nRecommended Modules/Licenses:")
    for mod in analysis.recommended_modules:
        print(f"  • {mod}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
