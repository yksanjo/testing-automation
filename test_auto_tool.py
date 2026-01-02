#!/usr/bin/env python3
"""
Command-line interface for the Testing Automation Tool.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from testing_automation.test_automation import TestAutomation


def main():
    """
    Main CLI function for the testing automation tool.
    """
    if len(sys.argv) < 2:
        print("Usage: test_auto_tool.py <command> [options]")
        print("Commands:")
        print("  run      - Run tests")
        print("  summary  - Run tests and show summary")
        print("  perf     - Run performance tests")
        print("")
        print("Options:")
        print("  --framework FRAMEWORK  - Test framework (pytest, unittest) [default: pytest]")
        print("  --path PATH            - Path to tests [default: tests/]")
        print("  --format FORMAT        - Output format (json, xml, text) [default: json]")
        print("  --coverage             - Include coverage analysis")
        print("  --perf-script PATH     - Performance test script path (for perf command)")
        print("  --iterations N         - Number of performance test iterations [default: 10]")
        return

    command = sys.argv[1]
    automation = TestAutomation()
    
    # Parse common options
    framework = "pytest"
    path = "tests/"
    output_format = "json"
    coverage = False
    perf_script = None
    iterations = 10
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--framework" and i + 1 < len(sys.argv):
            framework = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--path" and i + 1 < len(sys.argv):
            path = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--format" and i + 1 < len(sys.argv):
            output_format = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--coverage":
            coverage = True
            i += 1
        elif sys.argv[i] == "--perf-script" and i + 1 < len(sys.argv):
            perf_script = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--iterations" and i + 1 < len(sys.argv):
            try:
                iterations = int(sys.argv[i + 1])
                i += 2
            except ValueError:
                print(f"Error: Invalid number of iterations: {sys.argv[i + 1]}")
                return
        else:
            print(f"Unknown option: {sys.argv[i]}")
            return
    
    if command == "run":
        results = automation.run_tests(
            test_framework=framework,
            test_path=path,
            output_format=output_format,
            coverage=coverage
        )
        
        report = automation.runner.generate_test_report(results)
        print(report)
        
        # Save detailed report
        report_path = automation.runner.test_results_dir / f"test_report_{framework}.{output_format}"
        if output_format == "json" and "report_data" in results:
            import json
            with open(report_path, 'w') as f:
                json.dump(results["report_data"], f, indent=2)
        print(f"\nDetailed report saved to: {report_path}")
    
    elif command == "summary":
        results = automation.run_tests(
            test_framework=framework,
            test_path=path,
            output_format=output_format
        )
        
        summary = automation.create_test_summary(results)
        print(summary)
    
    elif command == "perf":
        if not perf_script:
            print("Error: --perf-script is required for performance tests")
            return
        
        results = automation.runner.run_performance_tests(perf_script, iterations)
        
        if "error" in results:
            print(f"Performance test error: {results['error']}")
        else:
            print("Performance Test Results:")
            print(f"  Iterations: {results['iterations']}")
            print(f"  Min Time: {results['min_time']:.4f}s")
            print(f"  Max Time: {results['max_time']:.4f}s")
            print(f"  Avg Time: {results['avg_time']:.4f}s")
            print(f"  Total Time: {results['total_time']:.4f}s")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()