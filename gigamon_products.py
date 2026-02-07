"""
Gigamon Product Database
========================
Hardware specifications and SKUs for migration recommendations.
Update this file when new products are released or prices change.
"""

# Platform specifications
PLATFORMS = {
    # TA Series - Fixed port appliances
    "TA25": {
        "name": "GigaVUE-TA25",
        "sku": "GVS-TA025",
        "form_factor": "1U",
        "description": "48x 1G/10G SFP+ ports",
        "base_ports": {"sfp_plus": 48},
        "qsfp_ports": 0,
        "max_ports": 48,
        "supports_inline": True,
        "supports_gigasmart": False,
        "supports_1g_copper": False,
        "end_of_sale": False,
        "notes": "Entry-level visibility node"
    },
    "TA25E": {
        "name": "GigaVUE-TA25E",
        "sku": "GVS-TA25E",
        "form_factor": "1U",
        "description": "48x 10G/25G SFP28 + 8x 100G QSFP28 ports",
        "base_ports": {"sfp28": 48, "qsfp28": 8},
        "qsfp_ports": 8,
        "max_ports": 56,
        "supports_inline": True,
        "supports_gigasmart": False,
        "supports_1g_copper": False,
        "end_of_sale": False,
        "notes": "Most popular for HC2 replacement"
    },
    "TA100": {
        "name": "GigaVUE-TA100",
        "sku": "GVS-TA100",
        "form_factor": "1U",
        "description": "32x 100G QSFP28 ports",
        "base_ports": {"qsfp28": 32},
        "qsfp_ports": 32,
        "max_ports": 32,
        "supports_inline": True,
        "supports_gigasmart": False,
        "supports_1g_copper": False,
        "end_of_sale": False,
        "notes": "High-density 100G aggregation"
    },
    "TA200": {
        "name": "GigaVUE-TA200",
        "sku": "GVS-TA200",
        "form_factor": "1U",
        "description": "64x 10G/25G SFP28 + 8x 40G/100G QSFP28 ports",
        "base_ports": {"sfp28": 64, "qsfp28": 8},
        "qsfp_ports": 8,
        "max_ports": 72,
        "supports_inline": True,
        "supports_gigasmart": False,
        "supports_1g_copper": False,
        "end_of_sale": False,
        "notes": "High-density 10G/25G aggregation"
    },
    "TA200E": {
        "name": "GigaVUE-TA200E",
        "sku": "GVS-TA200E",
        "form_factor": "1U",
        "description": "48x 10G/25G SFP28 + 8x 100G/400G QSFP-DD ports",
        "base_ports": {"sfp28": 48, "qsfp_dd": 8},
        "qsfp_ports": 8,
        "max_ports": 56,
        "supports_inline": True,
        "supports_gigasmart": False,
        "supports_1g_copper": False,
        "end_of_sale": False,
        "notes": "400G capable visibility node"
    },
    "TA400": {
        "name": "GigaVUE-TA400",
        "sku": "GVS-TA400",
        "form_factor": "1U",
        "description": "32x 40G/100G/400G QSFP-DD ports",
        "base_ports": {"qsfp_dd": 32},
        "qsfp_ports": 32,
        "max_ports": 32,
        "supports_inline": True,
        "supports_gigasmart": False,
        "supports_1g_copper": False,
        "end_of_sale": False,
        "notes": "400G high-speed visibility"
    },
    
    # HC Series - Modular chassis
    "HC1": {
        "name": "GigaVUE-HC1",
        "sku": "GVS-HC100",
        "form_factor": "1U",
        "description": "Modular 1U chassis with 1 expansion slot",
        "base_ports": {"sfp_plus": 12, "qsfp_plus": 4},
        "module_slots": 1,
        "max_ports": 60,
        "supports_inline": True,
        "supports_gigasmart": True,
        "supports_1g_copper": True,
        "end_of_sale": True,
        "notes": "Legacy - consider HC1-Plus"
    },
    "HC1-Plus": {
        "name": "GigaVUE-HC1-Plus",
        "sku": "GVS-HC1P",
        "form_factor": "1U",
        "description": "8x 100G QSFP28 + 16x 25G SFP28 + 1 expansion slot",
        "base_ports": {"qsfp28": 8, "sfp28": 16},
        "module_slots": 1,
        "max_ports": 48,
        "supports_inline": True,
        "supports_gigasmart": True,
        "supports_1g_copper": True,
        "end_of_sale": False,
        "notes": "Best for small sites needing GigaSMART or 1G TAPs"
    },
    "HC2": {
        "name": "GigaVUE-HC2",
        "sku": "GVS-HC200",
        "form_factor": "3U",
        "description": "Modular 3U chassis with 4 module slots",
        "base_ports": {},
        "module_slots": 4,
        "max_ports": 96,
        "supports_inline": True,
        "supports_gigasmart": True,
        "supports_1g_copper": True,
        "end_of_sale": True,
        "notes": "End of Sale - migrate to HC3 or TA series"
    },
    "HC3": {
        "name": "GigaVUE-HC3",
        "sku": "GVS-HC300",
        "form_factor": "3U",
        "description": "Modular 3U chassis with 4 module slots",
        "base_ports": {},
        "module_slots": 4,
        "max_ports": 128,
        "supports_inline": True,
        "supports_gigasmart": True,
        "supports_1g_copper": True,
        "end_of_sale": False,
        "notes": "Current flagship modular platform"
    },
}

# Line cards / Modules
MODULES = {
    # HC3 Modules
    "SMT-HC3-C16": {
        "name": "SMT-HC3-C16",
        "sku": "SMT-HC3-C16",
        "description": "16-port 10G/25G/40G/100G multi-rate module",
        "ports": {"multi_rate": 16},
        "compatible_platforms": ["HC3"],
        "supports_inline": True,
        "notes": "Flexible multi-rate ports"
    },
    "SMT-HC3-C08Q08": {
        "name": "SMT-HC3-C08Q08",
        "sku": "SMT-HC3-C08Q08",
        "description": "8x 100G QSFP28 + 8x 25G SFP28 module",
        "ports": {"qsfp28": 8, "sfp28": 8},
        "compatible_platforms": ["HC3"],
        "supports_inline": True,
        "notes": "Mixed 100G/25G density"
    },
    "BPS-HC3-C25F2G": {
        "name": "BPS-HC3-C25F2G",
        "sku": "BPS-HC3-C25F2G",
        "description": "Inline bypass module with 25G/10G/1G fiber ports",
        "ports": {"bypass_pairs": 4},
        "compatible_platforms": ["HC3"],
        "supports_inline": True,
        "is_bypass_module": True,
        "notes": "Native inline bypass protection"
    },
    "TAP-HC3-G100C0": {
        "name": "TAP-HC3-G100C0",
        "sku": "TAP-HC3-G100C0",
        "description": "1G copper TAP module",
        "ports": {"rj45_1g": 24},
        "compatible_platforms": ["HC3"],
        "supports_inline": False,
        "is_tap_module": True,
        "notes": "1G copper TAP connectivity"
    },
    "PRT-HC3-X24": {
        "name": "PRT-HC3-X24",
        "sku": "PRT-HC3-X24",
        "description": "24-port 10G SFP+ module",
        "ports": {"sfp_plus": 24},
        "compatible_platforms": ["HC3"],
        "supports_inline": True,
        "notes": "High-density 10G ports"
    },
    "PRT-HC3-C08Q16": {
        "name": "PRT-HC3-C08Q16",
        "sku": "PRT-HC3-C08Q16",
        "description": "8x 100G QSFP28 + 16x 25G SFP28 module",
        "ports": {"qsfp28": 8, "sfp28": 16},
        "compatible_platforms": ["HC3"],
        "supports_inline": True,
        "notes": "High-density mixed module"
    },
    
    # HC1-Plus Modules
    "TAP-HC1-G100C0": {
        "name": "TAP-HC1-G100C0",
        "sku": "TAP-HC1-G100C0",
        "description": "1G copper TAP module for HC1-Plus",
        "ports": {"rj45_1g": 12},
        "compatible_platforms": ["HC1-Plus", "HC1"],
        "supports_inline": False,
        "is_tap_module": True,
        "notes": "1G copper TAP for HC1 series"
    },
    "BPS-HC1-D25A8G": {
        "name": "BPS-HC1-D25A8G",
        "sku": "BPS-HC1-D25A8G",
        "description": "Bypass module for HC1-Plus",
        "ports": {"bypass_pairs": 4},
        "compatible_platforms": ["HC1-Plus"],
        "supports_inline": True,
        "is_bypass_module": True,
        "notes": "Inline bypass for HC1-Plus"
    },
    
    # Legacy HC2 Modules (for reference)
    "SMT-HC0-X16": {
        "name": "SMT-HC0-X16",
        "sku": "SMT-HC0-X16",
        "description": "16-port 10G SFP+ module (HC2)",
        "ports": {"sfp_plus": 16},
        "compatible_platforms": ["HC2"],
        "supports_inline": True,
        "notes": "Legacy HC2 module"
    },
    "TAP-HC0-G100C0": {
        "name": "TAP-HC0-G100C0",
        "sku": "TAP-HC0-G100C0",
        "description": "1G copper TAP module (HC2)",
        "ports": {"rj45_1g": 24},
        "compatible_platforms": ["HC2"],
        "supports_inline": False,
        "is_tap_module": True,
        "notes": "Legacy HC2 TAP module"
    },
    "PRT-HC0-X24": {
        "name": "PRT-HC0-X24",
        "sku": "PRT-HC0-X24",
        "description": "24-port 10G SFP+ module (HC2)",
        "ports": {"sfp_plus": 24},
        "compatible_platforms": ["HC2"],
        "supports_inline": True,
        "notes": "Legacy HC2 high-density module"
    },
}

# Licenses
LICENSES = {
    "IBP-TA25E": {
        "name": "Inline Bypass Protection License - TA25E",
        "sku": "LIC-TA25E-IBP",
        "description": "Enables inline bypass protection on TA25E",
        "compatible_platforms": ["TA25E"],
        "required_for": "inline bypass"
    },
    "IBP-TA200": {
        "name": "Inline Bypass Protection License - TA200",
        "sku": "LIC-TA200-IBP",
        "description": "Enables inline bypass protection on TA200",
        "compatible_platforms": ["TA200", "TA200E"],
        "required_for": "inline bypass"
    },
    "IBP-HC1P": {
        "name": "Inline Bypass Protection License - HC1-Plus",
        "sku": "LIC-HC1P-IBP",
        "description": "Enables inline bypass protection on HC1-Plus",
        "compatible_platforms": ["HC1-Plus"],
        "required_for": "inline bypass"
    },
    "IBP-HC3": {
        "name": "Inline Bypass Protection License - HC3",
        "sku": "LIC-HC3-IBP",
        "description": "Enables inline bypass protection on HC3",
        "compatible_platforms": ["HC3"],
        "required_for": "inline bypass"
    },
    "GS-HC1P": {
        "name": "GigaSMART License - HC1-Plus",
        "sku": "LIC-HC1P-GS",
        "description": "Enables GigaSMART features on HC1-Plus",
        "compatible_platforms": ["HC1-Plus"],
        "required_for": "gigasmart"
    },
    "GS-HC3": {
        "name": "GigaSMART License - HC3",
        "sku": "LIC-HC3-GS",
        "description": "Enables GigaSMART features on HC3",
        "compatible_platforms": ["HC3"],
        "required_for": "gigasmart"
    },
    "CLUSTERING": {
        "name": "Clustering License",
        "sku": "LIC-CLUSTER",
        "description": "Enables fabric clustering",
        "compatible_platforms": ["TA25E", "TA200", "HC1-Plus", "HC3"],
        "required_for": "clustering"
    },
}

# Transceivers
TRANSCEIVERS = {
    "SFP-501": {
        "sku": "SFP-501",
        "description": "1G SFP SX Transceiver",
        "speed": "1G",
        "type": "fiber",
        "reach": "SR"
    },
    "SFP-502": {
        "sku": "SFP-502",
        "description": "1G SFP LX Transceiver",
        "speed": "1G",
        "type": "fiber",
        "reach": "LR"
    },
    "SFP-531": {
        "sku": "SFP-531",
        "description": "10G SFP+ SR Transceiver",
        "speed": "10G",
        "type": "fiber",
        "reach": "SR"
    },
    "SFP-532": {
        "sku": "SFP-532",
        "description": "10G SFP+ LR Transceiver",
        "speed": "10G",
        "type": "fiber",
        "reach": "LR"
    },
    "SFP-533": {
        "sku": "SFP-533",
        "description": "10G SFP+ DAC 3m",
        "speed": "10G",
        "type": "dac",
        "reach": "3m"
    },
    "SFP-551": {
        "sku": "SFP-551",
        "description": "25G SFP28 SR Transceiver",
        "speed": "25G",
        "type": "fiber",
        "reach": "SR"
    },
    "SFP-552": {
        "sku": "SFP-552",
        "description": "25G SFP28 LR Transceiver",
        "speed": "25G",
        "type": "fiber",
        "reach": "LR"
    },
    "QSF-502": {
        "sku": "QSF-502",
        "description": "40G QSFP+ SR4 Transceiver",
        "speed": "40G",
        "type": "fiber",
        "reach": "SR"
    },
    "QSF-507": {
        "sku": "QSF-507",
        "description": "100G QSFP28 SR4 Transceiver",
        "speed": "100G",
        "type": "fiber",
        "reach": "SR"
    },
    "QSF-508": {
        "sku": "QSF-508",
        "description": "100G QSFP28 LR4 Transceiver",
        "speed": "100G",
        "type": "fiber",
        "reach": "LR"
    },
}

# Power supplies and accessories
ACCESSORIES = {
    "PWR-AC-TA25": {
        "sku": "PWR-AC-TA25",
        "description": "AC Power Supply for TA25/TA25E",
        "compatible_platforms": ["TA25", "TA25E"]
    },
    "PWR-AC-TA200": {
        "sku": "PWR-AC-TA200",
        "description": "AC Power Supply for TA200",
        "compatible_platforms": ["TA200", "TA200E"]
    },
    "PWR-AC-HC1P": {
        "sku": "PWR-AC-HC1P",
        "description": "AC Power Supply for HC1-Plus",
        "compatible_platforms": ["HC1-Plus"]
    },
    "PWR-AC-HC3": {
        "sku": "PWR-AC-HC3",
        "description": "AC Power Supply for HC3",
        "compatible_platforms": ["HC3"]
    },
    "FAN-HC3": {
        "sku": "FAN-HC3",
        "description": "Fan Tray for HC3",
        "compatible_platforms": ["HC3"]
    },
}


def get_platform_options(port_count: int, needs_gigasmart: bool, needs_1g_copper: bool,
                         needs_inline: bool = True) -> list:
    """
    Returns a list of suitable platforms based on requirements.
    """
    options = []
    
    for key, platform in PLATFORMS.items():
        # Skip end-of-sale unless specifically allowed
        if platform.get("end_of_sale", False):
            continue
            
        # Check port capacity
        if platform["max_ports"] < port_count:
            continue
            
        # Check GigaSMART requirement
        if needs_gigasmart and not platform["supports_gigasmart"]:
            continue
            
        # Check 1G copper requirement
        if needs_1g_copper and not platform["supports_1g_copper"]:
            # TA series can use media converters
            pass
            
        # Check inline requirement
        if needs_inline and not platform["supports_inline"]:
            continue
            
        options.append({
            "key": key,
            "platform": platform,
            "score": _calculate_platform_score(platform, port_count, needs_gigasmart, needs_1g_copper)
        })
    
    # Sort by score (higher is better)
    options.sort(key=lambda x: x["score"], reverse=True)
    return options


def _calculate_platform_score(platform: dict, port_count: int, needs_gigasmart: bool, 
                               needs_1g_copper: bool) -> int:
    """Calculate a suitability score for platform ranking."""
    score = 100
    
    # Prefer 1U form factors (cost/space efficiency)
    if platform["form_factor"] == "1U":
        score += 20
    
    # Penalize over-provisioning
    excess_ports = platform["max_ports"] - port_count
    if excess_ports > 30:
        score -= 10
    
    # Prefer non-modular if GigaSMART not needed (simpler)
    if not needs_gigasmart and platform["module_slots"] if "module_slots" in platform else 0 == 0:
        score += 15
    
    # Prefer native 1G support if needed
    if needs_1g_copper and platform["supports_1g_copper"]:
        score += 10
    
    return score


def get_modules_for_platform(platform_key: str) -> list:
    """Get compatible modules for a platform."""
    return [
        (key, mod) for key, mod in MODULES.items()
        if platform_key in mod.get("compatible_platforms", [])
    ]


def get_license_for_platform(platform_key: str, license_type: str) -> dict:
    """Get the appropriate license for a platform and type."""
    for key, lic in LICENSES.items():
        if platform_key in lic.get("compatible_platforms", []):
            if license_type in lic.get("required_for", ""):
                return lic
    return None
