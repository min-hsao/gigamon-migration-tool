# Gigamon HC2 Migration Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A command-line tool that analyzes GigaVUE-HC2 configuration files and generates migration recommendations for modern Gigamon hardware platforms with accurate SKU-based Bill of Materials.

## Features

- 🤖 **AI-Powered Analysis** - Uses Claude or GPT for intelligent recommendations
- 📊 **Multiple Platform Support** - TA25, TA25E, TA100, TA200, TA400, HC1-Plus, HC3
- 📋 **Accurate BOM** - Real Gigamon SKUs with quantities
- 🗺️ **Port Mapping** - Maps existing ports to new platform
- 📐 **ASCII Diagrams** - Visual representation for documentation
- 📁 **Multiple Exports** - TXT, CSV, JSON formats

## Two Versions Available

| Script | Description | AI Required |
|--------|-------------|-------------|
| `migrate_hc2.py` | Rule-based analysis | No |
| `migrate_hc2_ai.py` | AI-enhanced analysis | Yes (Claude/OpenAI) |

## Installation

```bash
git clone https://github.com/min-hsao/gigamon-migration-tool.git
cd gigamon-migration-tool
```

For AI-enhanced version, set API key:
```bash
export ANTHROPIC_API_KEY="your-key"  # For Claude
# OR
export OPENAI_API_KEY="your-key"     # For OpenAI
```

## Quick Start

### Basic (Rule-Based)
```bash
python3 migrate_hc2.py /path/to/show_diag.log
```

### AI-Enhanced
```bash
python3 migrate_hc2_ai.py /path/to/show_diag.log --ai-provider claude
python3 migrate_hc2_ai.py /path/to/show_diag.log --ai-provider openai
```

### Options
```bash
python3 migrate_hc2_ai.py config.log \
    --output-dir ./reports \
    --ai-provider claude \
    --verbose
```

## How to Capture HC2 Configuration

On your GigaVUE-HC2, run these commands and save the output:

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

## Output Files

| File | Description |
|------|-------------|
| `*_bom.txt` | Formatted Bill of Materials |
| `*_bom.csv` | CSV for Excel/procurement |
| `*_diagram.txt` | ASCII diagram |
| `*_migration.json` | Full data for automation |

## Sample BOM Output

```
==========================================================================================
                                     BILL OF MATERIALS                                    
                           Migration from gig-lax-gcs02 (CHS-HC2)                         
                                   Target: GigaVUE-TA200                                  
==========================================================================================

  Item  SKU                  Description                              Qty   Notes          
  ----- -------------------- ---------------------------------------- ----- ---------------
  1     GVS-TA200            GigaVUE-TA200                            1     Chassis        
  2     LIC-TA200-IBP        Inline Bypass Protection License         1     For inline     
  3     SFP-531              10G SFP+ SR Transceiver                  48    Adjust as needed
  4     QSF-507              100G QSFP28 SR4 Transceiver              4     Optional uplink
  5     PWR-AC-TA200         AC Power Supply                          2     Redundant pair 

==========================================================================================
```

## Platform Recommendation Logic

| Ports | GigaSMART | 1G Copper | Recommended Platform |
|-------|-----------|-----------|---------------------|
| ≤48 | No | No | **TA25E** |
| ≤48 | No | Yes | **TA25E** + converters or **HC1-Plus** |
| 49-72 | No | Any | **TA200** |
| Any | Yes | No | **HC1-Plus** or **HC3** |
| Any | Yes | Yes | **HC3** with TAP module |
| >72 | Any | Any | **HC3** with modules |

## Supported Platforms

### Source (End of Sale)
- GigaVUE-HC2

### Target (Current)
- GigaVUE-TA25 / TA25E
- GigaVUE-TA100
- GigaVUE-TA200 / TA200E
- GigaVUE-TA400
- GigaVUE-HC1-Plus
- GigaVUE-HC3

## Product Database

The `gigamon_products.py` file contains:
- Platform specifications and SKUs
- Module options for modular platforms
- License SKUs
- Transceiver options
- Power supply SKUs

Update this file when new products are released.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a Pull Request

## License

MIT License - see [LICENSE](LICENSE)

## Disclaimer

- Part numbers are representative and should be verified with Gigamon
- Pricing requires current Gigamon quote
- This tool provides recommendations; always consult Gigamon SE for complex deployments

## Author

Min-Hsao Chen ([@min-hsao](https://github.com/min-hsao))
