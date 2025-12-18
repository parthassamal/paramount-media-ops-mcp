#!/usr/bin/env python3
"""
Test Integration Connections.

Tests connectivity to Conviva, NewRelic, JIRA, and Confluence.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_test_header(service: str):
    """Print test header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'─' * 79}{Colors.END}")
    print(f"{Colors.BOLD}Testing {service} Connection{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'─' * 79}{Colors.END}")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.END} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.END} {text}")


def test_dynatrace(verbose: bool = False) -> bool:
    """Test Dynatrace connection."""
    print_test_header("DYNATRACE")
    
    if not settings.dynatrace_enabled:
        print_warning("Dynatrace is disabled in configuration")
        return False
    
    try:
        from mcp.integrations import DynatraceClient
        import time
        
        start = time.time()
        client = DynatraceClient()
        metrics = client.get_application_metrics()
        elapsed = time.time() - start
        
        if 'error' in metrics:
            print_error(f"Connection failed: {metrics['error']}")
            return False
        
        print_success(f"Connected ({elapsed:.1f}s response time)")
        
        if verbose:
            overall = metrics.get('overall', {})
            apps = metrics.get('applications', [])
            print(f"   Applications: {len(apps)}")
            print(f"   Response Time (avg): {overall.get('response_time_avg_ms', 0):.0f}ms")
            print(f"   Throughput: {overall.get('throughput_rpm', 0):,.0f} rpm")
            print(f"   Error Rate: {overall.get('error_rate', 0)*100:.2f}%")
            print(f"   Apdex Score: {overall.get('apdex_score', 0):.2f}")
        
        return True
    
    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        return False


def test_newrelic(verbose: bool = False) -> bool:
    """Test NewRelic connection."""
    print_test_header("NEWRELIC")
    
    if not settings.newrelic_enabled:
        print_warning("NewRelic is disabled in configuration")
        return False
    
    try:
        from mcp.integrations import NewRelicClient
        import time
        
        start = time.time()
        client = NewRelicClient()
        apm = client.get_apm_metrics()
        elapsed = time.time() - start
        
        if 'error' in apm:
            print_error(f"Connection failed: {apm['error']}")
            return False
        
        print_success(f"Connected ({elapsed:.1f}s response time)")
        
        if verbose:
            overall = apm.get('overall', apm)
            print(f"   Response Time (avg): {overall.get('response_time_avg_ms', 0):.0f}ms")
            print(f"   Response Time (p95): {overall.get('response_time_p95_ms', 0):.0f}ms")
            print(f"   Error Rate: {overall.get('error_rate', 0)*100:.2f}%")
            print(f"   Apdex Score: {overall.get('apdex_score', 0):.2f}")
        
        return True
    
    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        return False


def test_jira(verbose: bool = False) -> bool:
    """Test JIRA connection."""
    print_test_header("JIRA")
    
    if not settings.jira_enabled:
        print_warning("JIRA is disabled in configuration")
        return False
    
    try:
        from mcp.integrations import JIRAConnector
        import time
        
        start = time.time()
        connector = JIRAConnector()
        issues = connector.get_issues(max_results=10)
        elapsed = time.time() - start
        
        if connector.use_mock_data:
            print_warning("Using mock data (no live connection)")
            return False
        
        print_success(f"Connected ({elapsed:.1f}s response time)")
        
        if verbose and issues:
            print(f"   Project: {settings.jira_project_key}")
            print(f"   Issues Retrieved: {len(issues)}")
            
            critical = sum(1 for i in issues if i.get('severity') == 'Critical')
            if critical > 0:
                print(f"   Critical Issues: {critical}")
            
            if issues:
                print(f"   Sample Issue: {issues[0].get('issue_id')} - {issues[0].get('title', 'No title')[:50]}")
        
        return True
    
    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        return False


def test_confluence(verbose: bool = False) -> bool:
    """Test Confluence connection."""
    print_test_header("CONFLUENCE")
    
    if not settings.confluence_enabled:
        print_warning("Confluence is disabled in configuration")
        return False
    
    try:
        from mcp.integrations import AtlassianClient
        import time
        
        start = time.time()
        client = AtlassianClient()
        
        # Try to get spaces
        spaces = client.get_confluence_spaces()
        elapsed = time.time() - start
        
        if 'error' in spaces:
            print_error(f"Connection failed: {spaces['error']}")
            return False
        
        print_success(f"Connected ({elapsed:.1f}s response time)")
        
        if verbose:
            print(f"   Spaces Available: {len(spaces.get('results', []))}")
            if spaces.get('results'):
                space = spaces['results'][0]
                print(f"   Sample Space: {space.get('key')} - {space.get('name')}")
        
        return True
    
    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        return False


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test MCP server integrations")
    parser.add_argument(
        '--service',
        choices=['dynatrace', 'newrelic', 'jira', 'confluence'],
        help='Test specific service'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Test all services'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )
    
    args = parser.parse_args()
    
    # Print header
    print(f"\n{Colors.BOLD}{'═' * 79}{Colors.END}")
    print(f"{Colors.BOLD}  PARAMOUNT+ MCP SERVER - INTEGRATION TESTS{Colors.END}")
    print(f"{Colors.BOLD}{'═' * 79}{Colors.END}")
    
    # Run tests
    results = {}
    
    if args.service:
        # Test specific service
        if args.service == 'dynatrace':
            results['Dynatrace'] = test_dynatrace(args.verbose)
        elif args.service == 'newrelic':
            results['NewRelic'] = test_newrelic(args.verbose)
        elif args.service == 'jira':
            results['JIRA'] = test_jira(args.verbose)
        elif args.service == 'confluence':
            results['Confluence'] = test_confluence(args.verbose)
    
    elif args.all or not args.service:
        # Test all services
        results['Dynatrace'] = test_dynatrace(args.verbose)
        results['NewRelic'] = test_newrelic(args.verbose)
        results['JIRA'] = test_jira(args.verbose)
        results['Confluence'] = test_confluence(args.verbose)
    
    # Print summary
    print(f"\n{Colors.BOLD}{'═' * 79}{Colors.END}")
    print(f"{Colors.BOLD}  TEST SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{'═' * 79}{Colors.END}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for service, result in results.items():
        if result:
            print_success(f"{service}: Connected")
        else:
            print_error(f"{service}: Failed or Disabled")
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} services operational{Colors.END}\n")
    
    # Exit code
    if passed == 0 and total > 0:
        print(f"{Colors.YELLOW}No integrations configured. Using mock mode.{Colors.END}")
        print(f"{Colors.YELLOW}Run 'python scripts/setup_integrations.py' to configure.{Colors.END}\n")
        sys.exit(1)
    elif passed < total:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests cancelled by user.{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

