#!/usr/bin/env python3
"""
Interactive Integration Setup Script.

Guides users through setting up API keys for Conviva, NewRelic, and Atlassian.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print styled header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 79}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 79}{Colors.END}\n")


def print_success(text: str):
    """Print success message."""
    print(f"   {Colors.GREEN}✓{Colors.END} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"   {Colors.YELLOW}⚠{Colors.END} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"   {Colors.RED}✗{Colors.END} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"   {Colors.BLUE}ℹ{Colors.END} {text}")


def get_input(prompt: str, default: Optional[str] = None, required: bool = True) -> str:
    """Get user input with optional default."""
    if default:
        prompt = f"{prompt} [{Colors.CYAN}{default}{Colors.END}]: "
    else:
        prompt = f"{prompt}: "
    
    while True:
        value = input(f"   {prompt}").strip()
        
        if not value and default:
            return default
        
        if not value and required:
            print_error("This field is required. Please enter a value.")
            continue
        
        return value


def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Get yes/no input from user."""
    default_str = "Y/n" if default else "y/N"
    prompt = f"{prompt} [{Colors.CYAN}{default_str}{Colors.END}]: "
    
    while True:
        value = input(f"   {prompt}").strip().lower()
        
        if not value:
            return default
        
        if value in ('y', 'yes'):
            return True
        elif value in ('n', 'no'):
            return False
        else:
            print_error("Please enter 'y' or 'n'")


def test_conviva_connection(customer_key: str, api_key: str) -> bool:
    """Test Conviva API connection."""
    try:
        from mcp.integrations import ConvivaClient
        
        # Temporarily set env vars
        os.environ['CONVIVA_CUSTOMER_KEY'] = customer_key
        os.environ['CONVIVA_API_KEY'] = api_key
        
        client = ConvivaClient()
        result = client.get_qoe_metrics()
        
        if 'error' not in result:
            print_success("Conviva connection successful!")
            return True
        else:
            print_error(f"Conviva connection failed: {result.get('error')}")
            return False
    except Exception as e:
        print_error(f"Conviva connection failed: {str(e)}")
        return False


def test_newrelic_connection(api_key: str, account_id: str) -> bool:
    """Test NewRelic API connection."""
    try:
        from mcp.integrations import NewRelicClient
        
        # Temporarily set env vars
        os.environ['NEWRELIC_API_KEY'] = api_key
        os.environ['NEWRELIC_ACCOUNT_ID'] = account_id
        
        client = NewRelicClient()
        result = client.get_apm_metrics()
        
        if 'error' not in result:
            print_success("NewRelic connection successful!")
            return True
        else:
            print_error(f"NewRelic connection failed: {result.get('error')}")
            return False
    except Exception as e:
        print_error(f"NewRelic connection failed: {str(e)}")
        return False


def test_jira_connection(url: str, email: str, token: str) -> bool:
    """Test JIRA API connection."""
    try:
        from mcp.integrations import JIRAConnector
        
        # Temporarily set env vars
        os.environ['JIRA_API_URL'] = url
        os.environ['JIRA_API_EMAIL'] = email
        os.environ['JIRA_API_TOKEN'] = token
        
        connector = JIRAConnector()
        # Try to fetch issues (will use mock if connection fails)
        issues = connector.get_issues()
        
        if issues and not connector.use_mock_data:
            print_success("JIRA connection successful!")
            return True
        else:
            print_warning("JIRA connection failed, will use mock data")
            return False
    except Exception as e:
        print_error(f"JIRA connection failed: {str(e)}")
        return False


def setup_conviva() -> Dict[str, str]:
    """Setup Conviva integration."""
    print_header("CONVIVA INTEGRATION SETUP")
    
    print_info("Conviva provides real-time Quality of Experience (QoE) metrics.")
    print_info("You'll need: Customer Key and API Key")
    print_info("Get them from: https://pulse.conviva.com → Settings → API Keys\n")
    
    if not get_yes_no("Do you want to set up Conviva?", default=False):
        return {"CONVIVA_ENABLED": "false"}
    
    config = {}
    config["CONVIVA_ENABLED"] = "true"
    config["CONVIVA_API_URL"] = get_input(
        "Conviva API URL",
        default="https://api.conviva.com/insights/2.4",
        required=False
    )
    config["CONVIVA_CUSTOMER_KEY"] = get_input(
        "Customer Key (e.g., c3.your_company)",
        required=True
    )
    config["CONVIVA_API_KEY"] = get_input(
        "API Key",
        required=True
    )
    
    print("\n   Testing connection...")
    test_conviva_connection(config["CONVIVA_CUSTOMER_KEY"], config["CONVIVA_API_KEY"])
    
    return config


def setup_newrelic() -> Dict[str, str]:
    """Setup NewRelic integration."""
    print_header("NEWRELIC INTEGRATION SETUP")
    
    print_info("NewRelic provides Application Performance Monitoring (APM).")
    print_info("You'll need: User API Key and Account ID")
    print_info("Get them from: https://one.newrelic.com → Account Settings → API Keys\n")
    
    if not get_yes_no("Do you want to set up NewRelic?", default=False):
        return {"NEWRELIC_ENABLED": "false"}
    
    config = {}
    config["NEWRELIC_ENABLED"] = "true"
    config["NEWRELIC_API_URL"] = get_input(
        "NewRelic API URL",
        default="https://api.newrelic.com/graphql",
        required=False
    )
    config["NEWRELIC_API_KEY"] = get_input(
        "User API Key (starts with NRAK-)",
        required=True
    )
    config["NEWRELIC_ACCOUNT_ID"] = get_input(
        "Account ID",
        required=True
    )
    
    print("\n   Testing connection...")
    test_newrelic_connection(config["NEWRELIC_API_KEY"], config["NEWRELIC_ACCOUNT_ID"])
    
    return config


def setup_jira() -> Dict[str, str]:
    """Setup JIRA integration."""
    print_header("JIRA INTEGRATION SETUP")
    
    print_info("JIRA provides production issue tracking and management.")
    print_info("You'll need: Site URL, Email, and API Token")
    print_info("Get token from: https://id.atlassian.com/manage-profile/security/api-tokens\n")
    
    if not get_yes_no("Do you want to set up JIRA?", default=True):
        return {"JIRA_ENABLED": "false"}
    
    config = {}
    config["JIRA_ENABLED"] = "true"
    config["JIRA_FORCE_LIVE"] = "true"
    config["JIRA_API_URL"] = get_input(
        "Atlassian Site URL (e.g., https://yourcompany.atlassian.net)",
        required=True
    )
    config["JIRA_API_EMAIL"] = get_input(
        "Your Atlassian email",
        required=True
    )
    config["JIRA_API_TOKEN"] = get_input(
        "API Token",
        required=True
    )
    config["JIRA_PROJECT_KEY"] = get_input(
        "JIRA Project Key",
        default="PROD",
        required=False
    )
    
    print("\n   Testing connection...")
    test_jira_connection(
        config["JIRA_API_URL"],
        config["JIRA_API_EMAIL"],
        config["JIRA_API_TOKEN"]
    )
    
    return config


def setup_confluence() -> Dict[str, str]:
    """Setup Confluence integration."""
    print_header("CONFLUENCE INTEGRATION SETUP")
    
    print_info("Confluence provides operational runbooks and documentation.")
    print_info("Uses the same Atlassian credentials as JIRA.\n")
    
    if not get_yes_no("Do you want to set up Confluence?", default=True):
        return {"CONFLUENCE_ENABLED": "false"}
    
    config = {}
    config["CONFLUENCE_ENABLED"] = "true"
    config["CONFLUENCE_API_URL"] = get_input(
        "Atlassian Site URL (same as JIRA)",
        required=True
    )
    config["CONFLUENCE_USERNAME"] = get_input(
        "Your Atlassian email (same as JIRA)",
        required=True
    )
    config["CONFLUENCE_API_TOKEN"] = get_input(
        "API Token (same as JIRA)",
        required=True
    )
    config["CONFLUENCE_SPACE_KEY"] = get_input(
        "Confluence Space Key",
        default="OPS",
        required=False
    )
    
    print_success("Confluence configured!")
    
    return config


def write_env_file(config: Dict[str, str]):
    """Write configuration to .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    
    # Read existing .env if it exists
    existing_config = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_config[key] = value
    
    # Merge configurations (new config takes precedence)
    existing_config.update(config)
    
    # Write .env file
    with open(env_path, 'w') as f:
        f.write("# Paramount+ Media Operations MCP Server Configuration\n")
        f.write("# Generated by setup_integrations.py\n\n")
        
        # Server settings
        f.write("# Server Configuration\n")
        f.write(f"ENVIRONMENT={existing_config.get('ENVIRONMENT', 'development')}\n")
        f.write(f"MCP_SERVER_HOST={existing_config.get('MCP_SERVER_HOST', '0.0.0.0')}\n")
        f.write(f"MCP_SERVER_PORT={existing_config.get('MCP_SERVER_PORT', '8000')}\n")
        f.write(f"MOCK_MODE={existing_config.get('MOCK_MODE', 'true')}\n\n")
        
        # Conviva
        if config.get("CONVIVA_ENABLED") == "true":
            f.write("# Conviva Configuration\n")
            for key in ["CONVIVA_ENABLED", "CONVIVA_API_URL", "CONVIVA_CUSTOMER_KEY", "CONVIVA_API_KEY"]:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
            f.write("\n")
        
        # NewRelic
        if config.get("NEWRELIC_ENABLED") == "true":
            f.write("# NewRelic Configuration\n")
            for key in ["NEWRELIC_ENABLED", "NEWRELIC_API_URL", "NEWRELIC_API_KEY", "NEWRELIC_ACCOUNT_ID"]:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
            f.write("\n")
        
        # JIRA
        if config.get("JIRA_ENABLED") == "true":
            f.write("# JIRA Configuration\n")
            for key in ["JIRA_ENABLED", "JIRA_FORCE_LIVE", "JIRA_API_URL", "JIRA_API_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
            f.write("\n")
        
        # Confluence
        if config.get("CONFLUENCE_ENABLED") == "true":
            f.write("# Confluence Configuration\n")
            for key in ["CONFLUENCE_ENABLED", "CONFLUENCE_API_URL", "CONFLUENCE_USERNAME", "CONFLUENCE_API_TOKEN", "CONFLUENCE_SPACE_KEY"]:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
            f.write("\n")
    
    print_success(f"Configuration written to {env_path}")


def main():
    """Main setup function."""
    print_header("PARAMOUNT+ MCP SERVER - INTEGRATION SETUP")
    
    print(f"{Colors.BOLD}This script will help you set up integrations with:{Colors.END}")
    print("   • Conviva (Streaming QoE)")
    print("   • NewRelic (Application Performance)")
    print("   • JIRA (Production Issues)")
    print("   • Confluence (Operational Runbooks)")
    print()
    
    # Collect all configurations
    all_config = {}
    
    # Setup each service
    all_config.update(setup_conviva())
    all_config.update(setup_newrelic())
    all_config.update(setup_jira())
    
    # Only setup Confluence if JIRA is enabled
    if all_config.get("JIRA_ENABLED") == "true":
        all_config.update(setup_confluence())
    
    # Write configuration
    print_header("SAVING CONFIGURATION")
    write_env_file(all_config)
    
    # Summary
    print_header("SETUP COMPLETE!")
    
    enabled_services = []
    if all_config.get("CONVIVA_ENABLED") == "true":
        enabled_services.append("Conviva")
    if all_config.get("NEWRELIC_ENABLED") == "true":
        enabled_services.append("NewRelic")
    if all_config.get("JIRA_ENABLED") == "true":
        enabled_services.append("JIRA")
    if all_config.get("CONFLUENCE_ENABLED") == "true":
        enabled_services.append("Confluence")
    
    if enabled_services:
        print_success(f"Configured integrations: {', '.join(enabled_services)}")
    else:
        print_warning("No integrations configured (using mock mode)")
    
    print(f"\n{Colors.BOLD}Next steps:{Colors.END}")
    print("   1. Review your .env file")
    print("   2. Test connections: python scripts/test_integrations.py --all")
    print("   3. Start server: python -m mcp.server")
    print("   4. Run demo: python demo_usage.py")
    
    print(f"\n{Colors.CYAN}{'═' * 79}{Colors.END}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user.{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {str(e)}{Colors.END}")
        sys.exit(1)

