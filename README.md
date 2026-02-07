# Gigamon HC2 Migration Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A command-line tool that analyzes GigaVUE-HC2 configuration files and generates migration recommendations for modern Gigamon hardware platforms (TA25E, HC1-Plus, HC3).

## Features

- 📊 **Automatic Hardware Recommendation** - Analyzes port usage, GigaSMART, and 1G requirements
- 🗺️ **Port Mapping** - Maps existing ports to new platform with CSV export
- 📐 **ASCII Diagrams** - Visual representation of the new configuration
- 📋 **Bill of Materials** - Hardware list with part numbers for quoting
- 🔄 **JSON Export** - Machine-readable output for automation

## Installation

```bash
git clone https://github.com/min-hsao/gigamon-migration-tool.git
cd gigamon-migration-tool
```

No external dependencies required - uses Python 3.8+ standard library only.

## Quick Start

```bash
# Generate all reports
python3 migrate_hc2.py /path/to/show_diag.log

# Specify output directory
python3 migrate_hc2.py /path/to/show_diag.log --output-dir ./reports

# Generate specific format only
python3 migrate_hc2.py /path/to/show_diag.log --format ascii
python3 migrate_hc2.py /path/to/show_diag.log --format bom
python3 migrate_hc2.py /path/to/show_diag.log --format csv
python3 migrate_hc2.py /path/to/show_diag.log --format json
```

## How to Capture HC2 Configuration

On your GigaVUE-HC2, run these commands and save the output to a file:

```
enable
show version
show chassis
show card all
show diag
show running-config
show inline-network all
show inline-tool all
show port alias all
show map all
show gsop all
show gsgroup all
```

Save all output to a text file (e.g., `my-hc2-config.log`) and use as input.

## Output Files

| File | Description | Use Case |
|------|-------------|----------|
| `*_migration_diagram.txt` | ASCII diagram of new configuration | Documentation, quick reference |
| `*_port_mapping.csv` | Port-by-port mapping table | Import to Visio, Lucidchart, Excel |
| `*_bill_of_materials.txt` | Hardware BOM with part numbers | Quote requests, procurement |
| `*_migration.json` | Complete migration data | Automation, API integration |

## Platform Recommendation Logic

| Condition | Recommended Platform |
|-----------|---------------------|
| ≤48 ports, no GigaSMART, no 1G | **GigaVUE-TA25E + IBP License** |
| ≤48 ports, no GigaSMART, has 1G | **GigaVUE-TA25E** (with media converters) or **HC1-Plus** |
| Any ports with GigaSMART | **GigaVUE-HC3** or **HC1-Plus** with GS license |
| >48 ports | **GigaVUE-HC3** with multiple modules |

## Example Output

```
============================================================
MIGRATION SUMMARY
============================================================
Source Device: gig-lax-gcs02 (CHS-HC2)
Recommended Platform: GigaVUE-TA25E
Total Ports to Migrate: 40
GigaSMART Required: No
1G Ports Present: Yes

Recommended Modules/Licenses:
  • Base: 48x SFP28 (10G/25G) + 8x QSFP28 (100G)
  • IBP License (for inline bypass protection)
  • ⚠️  1G copper ports require: media converters OR external 1G TAPs
  
  ─── ALTERNATIVE OPTION ───
  • GigaVUE-HC1-Plus (if native 1G TAP needed)
============================================================
```

### Sample ASCII Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│  GigaVUE-TA25E                                                   │
│  Migrated from: gig-lax-gcs02                                    │
├──────────────────────────────────────────────────────────────────┤
│  INLINE NETWORKS                                                 │
│  ──────────────────────────────────────                          │
│  [P1-P2: Cisco9K-A]  [P3-P4: Cisco9K-B]                         │
│                                                                  │
│  INLINE TOOLS (Active)                                           │
│  ──────────────────────────────────────                          │
│  [P5-P6: IPS-A]  [P7-P8: PA-GCS01]  [P9-P10: VMSandvine]        │
│                                                                  │
│  OUT-OF-BAND NETWORK PORTS                                       │
│  ──────────────────────────────────────                          │
│  [P31: SW-SERVICE]  [P32: jun-lax]  [P33: from-gcs01]           │
│                                                                  │
│  SPARE PORTS: P41-P48 | Q1-Q8 (100G QSFP28)                     │
└──────────────────────────────────────────────────────────────────┘
```

### Sample Bill of Materials

```
================================================================================
                                BILL OF MATERIALS                               
================================================================================

  Item  Part Number               Description                              Qty  
  ----- ------------------------- ---------------------------------------- -----
  1     GVS-TA25E                 GigaVUE-TA25E Chassis                    1    
  2     GVS-TA25E-IBP             Inline Bypass Protection License         1    
  3     SFP-532                   10G SFP+ SR Transceiver                  40   
  4     PWR-AC-TA25E              AC Power Supply (Redundant)              2    

================================================================================
```

## Supported Source Platforms

- GigaVUE-HC2 (CHS-HC2)
- GigaVUE-HC2 with various line cards:
  - SMT-HC0-X16 (16x 10G SFP+)
  - TAP-HC0-G100C0 (1G Copper TAP)
  - PRT-HC0-X24 (24x 10G SFP+)

## Target Platforms

- **GigaVUE-TA25E** - 1U, 48x SFP28 + 8x QSFP28, ideal for ≤48 ports
- **GigaVUE-HC1-Plus** - 1U modular, built-in ports + expansion slot
- **GigaVUE-HC3** - 3U modular, for large deployments or GigaSMART

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Roadmap

- [ ] Support for HC1 source devices
- [ ] Support for TA series source devices
- [ ] Draw.io XML export for diagrams
- [ ] Interactive mode for manual adjustments
- [ ] Web interface

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool provides recommendations based on configuration analysis. Always verify recommendations with Gigamon documentation and your account team before making purchasing decisions. Part numbers are representative and should be confirmed with current Gigamon pricing.

## Author

Min-Hsao Chen ([@min-hsao](https://github.com/min-hsao))
