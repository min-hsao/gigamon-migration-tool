#!/usr/bin/env python3
"""
Gigamon HC2 Migration Tool (AI-Enhanced)
=========================================
Analyzes GigaVUE-HC2 configuration files and uses AI to generate
optimal migration recommendations with detailed Bill of Materials.

Features:
- AI-powered configuration analysis
- Multiple platform recommendations (TA25E, TA200, HC1-Plus, HC3)
- Accurate SKU-based Bill of Materials
- ASCII diagrams and CSV exports

Usage:
    python migrate_hc2_ai.py <config_file> [options]
    
Options:
    --ai-provider [claude|openai]  AI provider (default: claude)
    --output-dir DIR               Output directory
    --price-list FILE              Optional Excel price list
    --verbose                      Verbose output

Author: Skippy (OpenClaw)
Version: 2.0.0
"""

import re
import sys
import os
import json
import argparse
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict

# Import product database
try:
    from gigamon_products import (
        PLATFORMS, MODULES, LICENSES, TRANSCEIVERS, ACCESSORIES,
        get_platform_options, get_modules_for_platform, get_license_for_platform
    )
except ImportError:
    print("Error: gigamon_products.py not found. Run from the same directory.")
    sys.exit(1)


@dataclass
class ConfigAnalysis:
    """Parsed configuration analysis."""
    hostname: str = ""
    hw_type: str = ""
    software_version: str = ""
    slots: Dict[str, str] = field(default_factory=dict)
    
    # Port counts
    inline_network_ports: int = 0
    inline_tool_ports: int = 0
    network_ports: int = 0
    tool_ports: int = 0
    total_ports: int = 0
    
    # Feature flags
    has_gigasmart: bool = False
    has_1g_copper: bool = False
    has_inline: bool = False
    has_tap_module: bool = False
    
    # Detailed info
    inline_networks: List[Dict] = field(default_factory=list)
    inline_tools: List[Dict] = field(default_factory=list)
    gsops: List[str] = field(default_factory=list)
    maps: List[str] = field(default_factory=list)
    
    # Raw data for AI analysis
    raw_config: str = ""


@dataclass
class BOMItem:
    """Bill of Materials line item."""
    sku: str
    description: str
    quantity: int
    category: str
    notes: str = ""
    unit_price: float = 0.0
    
    @property
    def total_price(self) -> float:
        return self.unit_price * self.quantity


@dataclass
class MigrationRecommendation:
    """Complete migration recommendation."""
    source_device: str
    target_platform: str
    target_sku: str
    confidence: str  # high, medium, low
    rationale: str
    bom: List[BOMItem] = field(default_factory=list)
    port_mapping: Dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    alternatives: List[Dict] = field(default_factory=list)


class ConfigParser:
    """Parse GigaVUE configuration files."""
    
    def __init__(self, content: str):
        self.content = content
        self.lines = content.split('\n')
        
    def parse(self) -> ConfigAnalysis:
        """Parse configuration and return analysis."""
        analysis = ConfigAnalysis(raw_config=self.content)
        
        # Basic info
        analysis.hostname = self._extract_hostname()
        analysis.hw_type = self._extract_hw_type()
        analysis.software_version = self._extract_version()
        analysis.slots = self._extract_slots()
        
        # Count ports
        analysis.inline_networks = self._parse_inline_networks()
        analysis.inline_tools = self._parse_inline_tools()
        analysis.network_ports = self._count_network_ports()
        analysis.tool_ports = self._count_tool_ports()
        
        analysis.inline_network_ports = len(analysis.inline_networks) * 2
        analysis.inline_tool_ports = len(analysis.inline_tools) * 2
        analysis.total_ports = (
            analysis.inline_network_ports +
            analysis.inline_tool_ports +
            analysis.network_ports +
            analysis.tool_ports
        )
        
        # Features
        analysis.has_gigasmart = self._check_gigasmart()
        analysis.has_1g_copper = self._check_1g_copper()
        analysis.has_inline = len(analysis.inline_networks) > 0
        analysis.has_tap_module = 'TAP-HC' in self.content
        analysis.gsops = self._parse_gsops()
        
        return analysis
    
    def _extract_hostname(self) -> str:
        match = re.search(r'[Hh]ostname[:\s]+(\S+)', self.content)
        return match.group(1) if match else "unknown"
    
    def _extract_hw_type(self) -> str:
        match = re.search(r'HW [Tt]ype\s*:\s*(CHS-HC\d+\S*)', self.content)
        return match.group(1) if match else "HC2"
    
    def _extract_version(self) -> str:
        match = re.search(r'Software Version:\s*GigaVUE-OS\s+(\S+)', self.content)
        return match.group(1) if match else ""
    
    def _extract_slots(self) -> Dict[str, str]:
        slots = {}
        pattern = re.compile(r'^(\d+|cc\d+)\s+yes\s+\S+\s+(\S+)', re.MULTILINE)
        for match in pattern.finditer(self.content):
            slots[match.group(1)] = match.group(2)
        return slots
    
    def _parse_inline_networks(self) -> List[Dict]:
        networks = []
        # Look for inline-network configurations
        pattern = re.compile(
            r'inline-network\s+alias\s+(\S+)',
            re.IGNORECASE
        )
        for match in pattern.finditer(self.content):
            networks.append({"alias": match.group(1)})
        return networks
    
    def _parse_inline_tools(self) -> List[Dict]:
        tools = []
        pattern = re.compile(
            r'inline-tool\s+alias\s+(\S+)',
            re.IGNORECASE
        )
        for match in pattern.finditer(self.content):
            tools.append({"alias": match.group(1)})
        return tools
    
    def _count_network_ports(self) -> int:
        pattern = re.compile(r'port\s+\d+/\d+/\S+\s+type\s+network', re.IGNORECASE)
        return len(pattern.findall(self.content))
    
    def _count_tool_ports(self) -> int:
        pattern = re.compile(r'port\s+\d+/\d+/\S+\s+type\s+tool', re.IGNORECASE)
        return len(pattern.findall(self.content))
    
    def _check_gigasmart(self) -> bool:
        if 'No gsgroups configured' in self.content:
            return False
        if 'No gsops configured' in self.content:
            return False
        return bool(re.search(r'gsop\s+alias\s+\S+', self.content, re.IGNORECASE))
    
    def _check_1g_copper(self) -> bool:
        return bool(re.search(r'\d+/\d+/g\d+', self.content, re.IGNORECASE))
    
    def _parse_gsops(self) -> List[str]:
        gsops = []
        pattern = re.compile(r'gsop\s+alias\s+(\S+)', re.IGNORECASE)
        for match in pattern.finditer(self.content):
            gsops.append(match.group(1))
        return gsops


class AIAnalyzer:
    """AI-powered configuration analysis."""
    
    def __init__(self, provider: str = "claude", api_key: str = None):
        self.provider = provider
        self.api_key = api_key or self._get_api_key()
        
    def _get_api_key(self) -> str:
        """Get API key from environment."""
        if self.provider == "claude":
            return os.environ.get("ANTHROPIC_API_KEY", "")
        else:
            return os.environ.get("OPENAI_API_KEY", "")
    
    def analyze(self, analysis: ConfigAnalysis) -> Dict[str, Any]:
        """Use AI to analyze configuration and recommend migration."""
        
        # Build prompt
        prompt = self._build_analysis_prompt(analysis)
        
        # Call AI API
        if self.api_key:
            try:
                if self.provider == "claude":
                    return self._call_claude(prompt)
                else:
                    return self._call_openai(prompt)
            except Exception as e:
                print(f"AI analysis failed: {e}")
                print("Falling back to rule-based analysis...")
        
        # Fallback to rule-based analysis
        return self._rule_based_analysis(analysis)
    
    def _build_analysis_prompt(self, analysis: ConfigAnalysis) -> str:
        """Build the AI analysis prompt."""
        return f"""Analyze this Gigamon GigaVUE-HC2 configuration and recommend the best replacement hardware.

## Source Device
- Hostname: {analysis.hostname}
- Hardware: {analysis.hw_type}
- Software: {analysis.software_version}
- Slots: {json.dumps(analysis.slots)}

## Port Summary
- Inline Network Ports: {analysis.inline_network_ports}
- Inline Tool Ports: {analysis.inline_tool_ports}
- OOB Network Ports: {analysis.network_ports}
- OOB Tool Ports: {analysis.tool_ports}
- Total Ports: {analysis.total_ports}

## Features
- Has GigaSMART: {analysis.has_gigasmart}
- Has 1G Copper Ports: {analysis.has_1g_copper}
- Has Inline Networks: {analysis.has_inline}
- Has TAP Module: {analysis.has_tap_module}
- GigaSMART Operations: {analysis.gsops}

## Available Replacement Platforms
1. GigaVUE-TA25E: 48x SFP28 + 8x QSFP28, 1U, no GigaSMART, IBP license for inline
2. GigaVUE-TA200: 64x SFP28 + 8x QSFP28, 1U, no GigaSMART, higher density
3. GigaVUE-HC1-Plus: 8x QSFP28 + 16x SFP28 + 1 module slot, supports GigaSMART and 1G TAPs
4. GigaVUE-HC3: 4 module slots, full GigaSMART support, most flexible

Recommend the best platform considering:
1. Cost efficiency (TA series is cheaper than HC series)
2. Port requirements (don't over-provision)
3. Feature requirements (GigaSMART, 1G copper)
4. Form factor (1U preferred for simple deployments)

Return a JSON response with:
{{
    "recommended_platform": "platform_key",
    "confidence": "high|medium|low",
    "rationale": "explanation",
    "modules_needed": ["list of module SKUs if applicable"],
    "licenses_needed": ["list of license SKUs"],
    "warnings": ["any concerns or notes"],
    "alternatives": [{{"platform": "key", "reason": "why this is an option"}}]
}}
"""
    
    def _call_claude(self, prompt: str) -> Dict:
        """Call Claude API."""
        import requests
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        
        if response.status_code == 200:
            content = response.json()["content"][0]["text"]
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        
        raise Exception(f"Claude API error: {response.status_code}")
    
    def _call_openai(self, prompt: str) -> Dict:
        """Call OpenAI API."""
        import requests
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
        )
        
        if response.status_code == 200:
            return json.loads(response.json()["choices"][0]["message"]["content"])
        
        raise Exception(f"OpenAI API error: {response.status_code}")
    
    def _rule_based_analysis(self, analysis: ConfigAnalysis) -> Dict:
        """Fallback rule-based analysis when AI is unavailable."""
        total = analysis.total_ports
        
        # Decision tree
        if analysis.has_gigasmart:
            if total <= 32:
                platform = "HC1-Plus"
                licenses = ["LIC-HC1P-GS"]
            else:
                platform = "HC3"
                licenses = ["LIC-HC3-GS"]
        elif total <= 48:
            platform = "TA25E"
            licenses = ["LIC-TA25E-IBP"] if analysis.has_inline else []
        elif total <= 72:
            platform = "TA200"
            licenses = ["LIC-TA200-IBP"] if analysis.has_inline else []
        else:
            platform = "HC3"
            licenses = ["LIC-HC3-IBP"] if analysis.has_inline else []
        
        warnings = []
        if analysis.has_1g_copper and platform in ["TA25E", "TA200"]:
            warnings.append("1G copper ports require media converters or external TAPs")
        
        alternatives = []
        if platform == "TA25E" and analysis.has_1g_copper:
            alternatives.append({
                "platform": "HC1-Plus",
                "reason": "Native 1G copper TAP support via module"
            })
        
        return {
            "recommended_platform": platform,
            "confidence": "high" if not analysis.has_gigasmart and total <= 48 else "medium",
            "rationale": f"Based on {total} total ports, {'GigaSMART required' if analysis.has_gigasmart else 'no GigaSMART needed'}",
            "modules_needed": [],
            "licenses_needed": licenses,
            "warnings": warnings,
            "alternatives": alternatives
        }


class BOMGenerator:
    """Generate Bill of Materials."""
    
    def __init__(self, analysis: ConfigAnalysis, ai_recommendation: Dict):
        self.analysis = analysis
        self.recommendation = ai_recommendation
        
    def generate(self) -> List[BOMItem]:
        """Generate complete BOM."""
        bom = []
        
        platform_key = self.recommendation["recommended_platform"]
        platform = PLATFORMS.get(platform_key, PLATFORMS.get("TA25E"))
        
        # 1. Platform/Chassis
        bom.append(BOMItem(
            sku=platform["sku"],
            description=platform["name"],
            quantity=1,
            category="Chassis",
            notes=platform["description"]
        ))
        
        # 2. Modules (for modular platforms)
        if platform_key in ["HC3", "HC1-Plus"]:
            bom.extend(self._get_modules(platform_key))
        
        # 3. Licenses
        for lic_sku in self.recommendation.get("licenses_needed", []):
            for key, lic in LICENSES.items():
                if lic["sku"] == lic_sku or key == lic_sku:
                    bom.append(BOMItem(
                        sku=lic["sku"],
                        description=lic["name"],
                        quantity=1,
                        category="License",
                        notes=lic["description"]
                    ))
                    break
            else:
                # Handle IBP licenses by platform
                if "IBP" in lic_sku or platform_key in lic_sku:
                    ibp_lic = get_license_for_platform(platform_key, "inline bypass")
                    if ibp_lic:
                        bom.append(BOMItem(
                            sku=ibp_lic["sku"],
                            description=ibp_lic["name"],
                            quantity=1,
                            category="License",
                            notes=ibp_lic["description"]
                        ))
        
        # 4. Transceivers
        bom.extend(self._get_transceivers(platform_key))
        
        # 5. Power Supplies (redundant)
        for key, acc in ACCESSORIES.items():
            if "PWR" in key and platform_key in acc.get("compatible_platforms", []):
                bom.append(BOMItem(
                    sku=acc["sku"],
                    description=acc["description"],
                    quantity=2,
                    category="Power Supply",
                    notes="Redundant pair"
                ))
                break
        
        return bom
    
    def _get_modules(self, platform_key: str) -> List[BOMItem]:
        """Get required modules for modular platforms."""
        items = []
        total = self.analysis.total_ports
        
        if platform_key == "HC3":
            # Calculate modules needed
            if self.analysis.has_inline:
                items.append(BOMItem(
                    sku="BPS-HC3-C25F2G",
                    description="Inline Bypass Module",
                    quantity=1,
                    category="Module",
                    notes="Required for inline bypass protection"
                ))
                remaining = total - 8  # Bypass module handles some ports
            else:
                remaining = total
            
            # Add port modules
            if remaining > 0:
                modules_needed = (remaining + 15) // 16
                items.append(BOMItem(
                    sku="SMT-HC3-C16",
                    description="16-port Multi-rate Module",
                    quantity=modules_needed,
                    category="Module",
                    notes="10G/25G/40G/100G capable"
                ))
            
            # TAP module if 1G copper needed
            if self.analysis.has_1g_copper:
                items.append(BOMItem(
                    sku="TAP-HC3-G100C0",
                    description="1G Copper TAP Module",
                    quantity=1,
                    category="Module",
                    notes="For 1G copper connectivity"
                ))
        
        elif platform_key == "HC1-Plus":
            if self.analysis.has_1g_copper:
                items.append(BOMItem(
                    sku="TAP-HC1-G100C0",
                    description="1G Copper TAP Module",
                    quantity=1,
                    category="Module",
                    notes="For 1G copper connectivity"
                ))
        
        return items
    
    def _get_transceivers(self, platform_key: str) -> List[BOMItem]:
        """Calculate transceiver requirements."""
        items = []
        
        # Estimate based on port count (assume 10G SFP+ as default)
        sfp_count = min(self.analysis.total_ports, 48)
        
        if sfp_count > 0:
            items.append(BOMItem(
                sku="SFP-531",
                description="10G SFP+ SR Transceiver",
                quantity=sfp_count,
                category="Transceiver",
                notes="Adjust quantity based on actual fiber reach needs"
            ))
        
        # Add QSFP if platform has them
        platform = PLATFORMS.get(platform_key, {})
        qsfp_count = platform.get("qsfp_ports", 0)
        if qsfp_count > 0:
            items.append(BOMItem(
                sku="QSF-507",
                description="100G QSFP28 SR4 Transceiver",
                quantity=min(qsfp_count, 4),  # Assume not all QSFP ports used
                category="Transceiver",
                notes="Optional - for 100G uplinks"
            ))
        
        return items


class ReportGenerator:
    """Generate reports and diagrams."""
    
    def __init__(self, analysis: ConfigAnalysis, recommendation: MigrationRecommendation):
        self.analysis = analysis
        self.rec = recommendation
        
    def generate_bom_report(self) -> str:
        """Generate formatted Bill of Materials."""
        lines = []
        lines.append("=" * 90)
        lines.append("  BILL OF MATERIALS".center(90))
        lines.append(f"  Migration from {self.analysis.hostname} ({self.analysis.hw_type})".center(90))
        lines.append(f"  Target: {self.rec.target_platform}".center(90))
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(90))
        lines.append("=" * 90)
        lines.append("")
        
        # Group by category
        categories = defaultdict(list)
        for item in self.rec.bom:
            categories[item.category].append(item)
        
        lines.append(f"  {'Item':<5} {'SKU':<20} {'Description':<40} {'Qty':<5} {'Notes':<15}")
        lines.append(f"  {'-'*5} {'-'*20} {'-'*40} {'-'*5} {'-'*15}")
        
        item_num = 1
        for category in ["Chassis", "Module", "License", "Transceiver", "Power Supply"]:
            if category in categories:
                for item in categories[category]:
                    desc = item.description[:38] + ".." if len(item.description) > 40 else item.description
                    notes = item.notes[:13] + ".." if len(item.notes) > 15 else item.notes
                    lines.append(f"  {item_num:<5} {item.sku:<20} {desc:<40} {item.quantity:<5} {notes:<15}")
                    item_num += 1
        
        lines.append("")
        lines.append("=" * 90)
        
        # Warnings
        if self.rec.warnings:
            lines.append("  WARNINGS:")
            for warning in self.rec.warnings:
                lines.append(f"  ⚠️  {warning}")
            lines.append("")
        
        # Alternatives
        if self.rec.alternatives:
            lines.append("  ALTERNATIVE OPTIONS:")
            for alt in self.rec.alternatives:
                lines.append(f"  • {alt['platform']}: {alt['reason']}")
            lines.append("")
        
        lines.append("  NOTES:")
        lines.append("  - Part numbers should be verified with Gigamon for current availability")
        lines.append("  - Transceiver quantities may vary based on actual deployment")
        lines.append("  - Consider 10-20% spare transceivers")
        lines.append(f"  - Confidence: {self.rec.confidence.upper()}")
        lines.append("=" * 90)
        
        return "\n".join(lines)
    
    def generate_csv(self) -> str:
        """Generate CSV BOM."""
        lines = ["SKU,Description,Quantity,Category,Notes"]
        for item in self.rec.bom:
            desc = item.description.replace(",", ";")
            notes = item.notes.replace(",", ";")
            lines.append(f"{item.sku},{desc},{item.quantity},{item.category},{notes}")
        return "\n".join(lines)
    
    def generate_ascii_diagram(self) -> str:
        """Generate ASCII diagram."""
        platform = PLATFORMS.get(self.rec.target_platform.replace("GigaVUE-", ""), {})
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"  {self.rec.target_platform} - Migration from {self.analysis.hostname}".center(80))
        lines.append("=" * 80)
        lines.append("")
        
        # Platform box
        lines.append("┌" + "─" * 78 + "┐")
        lines.append(f"│  {self.rec.target_platform:<74}  │")
        lines.append(f"│  Form Factor: {platform.get('form_factor', 'N/A'):<62}  │")
        lines.append("├" + "─" * 78 + "┤")
        
        # Port sections
        if self.analysis.inline_network_ports:
            lines.append(f"│  INLINE NETWORKS: {self.analysis.inline_network_ports} ports ({len(self.analysis.inline_networks)} pairs){' '*35}│")
        
        if self.analysis.inline_tool_ports:
            lines.append(f"│  INLINE TOOLS: {self.analysis.inline_tool_ports} ports ({len(self.analysis.inline_tools)} pairs){' '*38}│")
        
        if self.analysis.network_ports:
            lines.append(f"│  OOB NETWORK: {self.analysis.network_ports} ports{' '*52}│")
        
        if self.analysis.tool_ports:
            lines.append(f"│  OOB TOOL: {self.analysis.tool_ports} ports{' '*55}│")
        
        lines.append("├" + "─" * 78 + "┤")
        lines.append(f"│  TOTAL CONFIGURED: {self.analysis.total_ports} ports{' '*47}│")
        
        # Available capacity
        max_ports = platform.get("max_ports", 48)
        spare = max_ports - self.analysis.total_ports
        lines.append(f"│  SPARE CAPACITY: {spare} ports{' '*49}│")
        
        lines.append("└" + "─" * 78 + "┘")
        
        # Summary
        lines.append("")
        lines.append("MIGRATION SUMMARY:")
        lines.append(f"  Confidence: {self.rec.confidence.upper()}")
        lines.append(f"  Rationale: {self.rec.rationale}")
        
        if self.rec.warnings:
            lines.append("")
            lines.append("WARNINGS:")
            for w in self.rec.warnings:
                lines.append(f"  ⚠️  {w}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="AI-enhanced Gigamon HC2 migration tool"
    )
    parser.add_argument("input_file", help="Path to show diag/config file")
    parser.add_argument("--output-dir", "-o", default=".", help="Output directory")
    parser.add_argument("--ai-provider", choices=["claude", "openai"], default="claude",
                       help="AI provider for analysis")
    parser.add_argument("--price-list", help="Optional Excel price list file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Read input file
    if not os.path.exists(args.input_file):
        print(f"Error: File not found: {args.input_file}")
        sys.exit(1)
    
    with open(args.input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    print(f"Analyzing: {args.input_file}")
    
    # Parse configuration
    parser_obj = ConfigParser(content)
    analysis = parser_obj.parse()
    
    if args.verbose:
        print(f"  Hostname: {analysis.hostname}")
        print(f"  Hardware: {analysis.hw_type}")
        print(f"  Total Ports: {analysis.total_ports}")
        print(f"  GigaSMART: {analysis.has_gigasmart}")
        print(f"  1G Copper: {analysis.has_1g_copper}")
    
    # AI Analysis
    print(f"Running AI analysis ({args.ai_provider})...")
    ai = AIAnalyzer(provider=args.ai_provider)
    ai_result = ai.analyze(analysis)
    
    if args.verbose:
        print(f"  Recommended: {ai_result['recommended_platform']}")
        print(f"  Confidence: {ai_result['confidence']}")
    
    # Generate BOM
    print("Generating Bill of Materials...")
    bom_gen = BOMGenerator(analysis, ai_result)
    bom_items = bom_gen.generate()
    
    # Create recommendation object
    platform_key = ai_result["recommended_platform"]
    platform = PLATFORMS.get(platform_key, PLATFORMS.get("TA25E"))
    
    recommendation = MigrationRecommendation(
        source_device=f"{analysis.hostname} ({analysis.hw_type})",
        target_platform=platform["name"],
        target_sku=platform["sku"],
        confidence=ai_result["confidence"],
        rationale=ai_result["rationale"],
        bom=bom_items,
        warnings=ai_result.get("warnings", []),
        alternatives=ai_result.get("alternatives", [])
    )
    
    # Generate reports
    report_gen = ReportGenerator(analysis, recommendation)
    
    os.makedirs(args.output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(args.input_file))[0]
    
    # BOM Text
    bom_file = os.path.join(args.output_dir, f"{base_name}_bom.txt")
    with open(bom_file, 'w') as f:
        f.write(report_gen.generate_bom_report())
    print(f"Generated: {bom_file}")
    
    # BOM CSV
    csv_file = os.path.join(args.output_dir, f"{base_name}_bom.csv")
    with open(csv_file, 'w') as f:
        f.write(report_gen.generate_csv())
    print(f"Generated: {csv_file}")
    
    # ASCII Diagram
    diagram_file = os.path.join(args.output_dir, f"{base_name}_diagram.txt")
    with open(diagram_file, 'w') as f:
        f.write(report_gen.generate_ascii_diagram())
    print(f"Generated: {diagram_file}")
    
    # JSON
    json_file = os.path.join(args.output_dir, f"{base_name}_migration.json")
    with open(json_file, 'w') as f:
        json.dump({
            "source": {
                "hostname": analysis.hostname,
                "hw_type": analysis.hw_type,
                "total_ports": analysis.total_ports,
                "has_gigasmart": analysis.has_gigasmart,
                "has_1g_copper": analysis.has_1g_copper
            },
            "recommendation": {
                "platform": recommendation.target_platform,
                "sku": recommendation.target_sku,
                "confidence": recommendation.confidence,
                "rationale": recommendation.rationale
            },
            "bom": [
                {"sku": item.sku, "description": item.description, 
                 "quantity": item.quantity, "category": item.category}
                for item in recommendation.bom
            ],
            "warnings": recommendation.warnings,
            "alternatives": recommendation.alternatives,
            "generated": datetime.now().isoformat()
        }, f, indent=2)
    print(f"Generated: {json_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Source: {recommendation.source_device}")
    print(f"Target: {recommendation.target_platform} ({recommendation.target_sku})")
    print(f"Total Ports: {analysis.total_ports}")
    print(f"Confidence: {recommendation.confidence.upper()}")
    print(f"Rationale: {recommendation.rationale}")
    
    if recommendation.warnings:
        print("\nWarnings:")
        for w in recommendation.warnings:
            print(f"  ⚠️  {w}")
    
    print("\nBOM Summary:")
    for item in recommendation.bom:
        print(f"  {item.quantity}x {item.sku}: {item.description}")
    
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
