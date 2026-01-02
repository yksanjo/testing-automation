"""
Testing Automation Script

This script provides tools for automating testing workflows.
Features include:
- Running test suites with various configurations
- Generating test reports
- Code coverage analysis
- Performance testing
"""

import os
import sys
import subprocess
import json
import argparse
import time
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET


class TestRunner:
    """
    A class to handle running tests and generating reports.
    """
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.test_results_dir = self.project_root / "test_results"
        self.test_results_dir.mkdir(exist_ok=True)
    
    def run_pytest(self, test_path: str = "tests/", output_format: str = "json", 
                   coverage: bool = False, extra_args: List[str] = None) -> Dict[str, Any]:
        """
        Run pytest on the specified path.
        
        Args:
            test_path: Path to run tests on
            output_format: Format for output (json, xml, text)
            coverage: Whether to include coverage analysis
            extra_args: Additional arguments to pass to pytest
            
        Returns:
            Dictionary containing test results
        """
        cmd = [sys.executable, "-m", "pytest", str(test_path)]
        
        # Add output format
        if output_format == "json":
            json_path = self.test_results_dir / "pytest_report.json"
            cmd.extend(["--json-report", f"--json-report-file={json_path}"])
        elif output_format == "xml":
            xml_path = self.test_results_dir / "pytest_report.xml"
            cmd.extend(["--junitxml", str(xml_path)])
        
        # Add coverage if requested
        if coverage:
            cmd.extend(["--cov=.", "--cov-report=html:{}".format(self.test_results_dir / "coverage_html")])
            cmd.extend(["--cov-report=xml:{}".format(self.test_results_dir / "coverage.xml")])
        
        # Add extra arguments
        if extra_args:
            cmd.extend(extra_args)
        
        # Add verbose output
        cmd.append("-v")
        
        print(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            # Process results based on output format
            if output_format == "json":
                json_path = self.test_results_dir / "pytest_report.json"
                if json_path.exists():
                    with open(json_path, 'r') as f:
                        report_data = json.load(f)
                else:
                    report_data = {"error": "JSON report not generated"}
            elif output_format == "xml":
                xml_path = self.test_results_dir / "pytest_report.xml"
                if xml_path.exists():
                    report_data = self._parse_junit_xml(xml_path)
                else:
                    report_data = {"error": "XML report not generated"}
            else:
                report_data = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            
            return {
                "command": " ".join(cmd),
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "report_data": report_data
            }
            
        except Exception as e:
            return {
                "command": " ".join(cmd),
                "error": str(e),
                "report_data": {}
            }
    
    def _parse_junit_xml(self, xml_path: Path) -> Dict[str, Any]:
        """
        Parse JUnit XML report and extract key information.
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Extract test suite information
            testsuite = root
            if root.tag == 'testsuites':
                # Multiple test suites
                testsuites_info = []
                for suite in root:
                    testsuites_info.append({
                        "name": suite.get("name", ""),
                        "tests": int(suite.get("tests", 0)),
                        "failures": int(suite.get("failures", 0)),
                        "errors": int(suite.get("errors", 0)),
                        "skipped": int(suite.get("skipped", 0)),
                        "time": float(suite.get("time", 0))
                    })
                return {"testsuites": testsuites_info}
            else:
                # Single test suite
                return {
                    "name": testsuite.get("name", ""),
                    "tests": int(testsuite.get("tests", 0)),
                    "failures": int(testsuite.get("failures", 0)),
                    "errors": int(testsuite.get("errors", 0)),
                    "skipped": int(testsuite.get("skipped", 0)),
                    "time": float(testsuite.get("time", 0))
                }
        except Exception as e:
            return {"error": f"Could not parse XML: {str(e)}"}
    
    def run_unittest(self, test_path: str = "tests/", output_format: str = "text") -> Dict[str, Any]:
        """
        Run unittest on the specified path.
        
        Args:
            test_path: Path containing test modules
            output_format: Format for output (text, xml)
            
        Returns:
            Dictionary containing test results
        """
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", test_path, "-v"]
        
        if output_format == "xml":
            # Install and use xmlrunner if available
            try:
                import xmlrunner
                # For xmlrunner, we need to run differently
                cmd = [sys.executable, "-c", f'''
import unittest
import xmlrunner
import sys
import os
sys.path.insert(0, "{self.project_root}")
loader = unittest.TestLoader()
start_dir = "{test_path}"
suite = loader.discover(start_dir, pattern="test*.py")
runner = xmlrunner.XMLTestRunner(output="{self.test_results_dir}/unittest_xml")
result = runner.run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
''']
            except ImportError:
                print("xmlrunner not available, running without XML output")
                output_format = "text"
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            return {
                "command": " ".join(cmd),
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            return {
                "command": " ".join(cmd),
                "error": str(e)
            }
    
    def generate_test_report(self, results: Dict[str, Any], report_type: str = "summary") -> str:
        """
        Generate a human-readable test report.
        
        Args:
            results: Results from test run
            report_type: Type of report to generate (summary, detailed)
            
        Returns:
            Formatted report as string
        """
        if "error" in results:
            return f"Error running tests: {results['error']}"
        
        report = []
        report.append("Test Execution Report")
        report.append("=" * 50)
        report.append(f"Command: {results['command']}")
        report.append(f"Return Code: {results['returncode']}")
        
        if results['returncode'] == 0:
            report.append("Status: PASSED")
        else:
            report.append("Status: FAILED")
        
        report.append("")
        
        # Add specific report data based on test runner
        if "report_data" in results:
            report_data = results["report_data"]
            
            if "error" in report_data:
                report.append(f"Report Error: {report_data['error']}")
            elif "testsuites" in report_data:
                # Multiple test suites
                for suite in report_data["testsuites"]:
                    report.append(f"Test Suite: {suite['name']}")
                    report.append(f"  Tests: {suite['tests']}")
                    report.append(f"  Failures: {suite['failures']}")
                    report.append(f"  Errors: {suite['errors']}")
                    report.append(f"  Skipped: {suite['skipped']}")
                    report.append(f"  Time: {suite['time']:.2f}s")
                    report.append("")
            elif "tests" in report_data:
                # Single test suite
                report.append(f"Tests: {report_data['tests']}")
                report.append(f"Failures: {report_data['failures']}")
                report.append(f"Errors: {report_data['errors']}")
                report.append(f"Skipped: {report_data['skipped']}")
                report.append(f"Time: {report_data['time']:.2f}s")
            else:
                # Generic report
                report.append("Detailed report data:")
                for key, value in report_data.items():
                    report.append(f"  {key}: {value}")
        
        report.append("")
        report.append("Standard Output:")
        report.append("-" * 20)
        report.append(results.get('stdout', ''))
        
        if results.get('stderr'):
            report.append("")
            report.append("Standard Error:")
            report.append("-" * 20)
            report.append(results['stderr'])
        
        return "\n".join(report)
    
    def run_performance_tests(self, script_path: str, iterations: int = 10) -> Dict[str, Any]:
        """
        Run performance tests using a Python script.
        
        Args:
            script_path: Path to the performance test script
            iterations: Number of iterations to run
            
        Returns:
            Dictionary containing performance results
        """
        script_path = Path(script_path)
        if not script_path.exists():
            return {"error": f"Performance test script {script_path} does not exist"}
        
        times = []
        for i in range(iterations):
            start_time = time.time()
            try:
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )
                end_time = time.time()
                
                if result.returncode == 0:
                    times.append(end_time - start_time)
                else:
                    return {
                        "error": f"Performance test failed on iteration {i+1}",
                        "stderr": result.stderr
                    }
            except Exception as e:
                return {"error": f"Performance test failed on iteration {i+1}: {str(e)}"}
        
        if not times:
            return {"error": "No successful iterations"}
        
        return {
            "iterations": iterations,
            "times": times,
            "min_time": min(times),
            "max_time": max(times),
            "avg_time": sum(times) / len(times),
            "total_time": sum(times)
        }


class TestAutomation:
    """
    Main class for test automation.
    """
    
    def __init__(self, project_root: str = "."):
        self.runner = TestRunner(project_root)
    
    def run_tests(self, test_framework: str = "pytest", test_path: str = "tests/", 
                  output_format: str = "json", coverage: bool = False, 
                  extra_args: List[str] = None) -> Dict[str, Any]:
        """
        Run tests using the specified framework.
        
        Args:
            test_framework: Testing framework to use (pytest, unittest)
            test_path: Path to run tests on
            output_format: Output format (json, xml, text)
            coverage: Whether to include coverage analysis
            extra_args: Additional arguments to pass to the test runner
            
        Returns:
            Dictionary containing test results
        """
        if test_framework == "pytest":
            return self.runner.run_pytest(test_path, output_format, coverage, extra_args)
        elif test_framework == "unittest":
            return self.runner.run_unittest(test_path, output_format)
        else:
            return {"error": f"Unsupported test framework: {test_framework}"}
    
    def create_test_summary(self, results: Dict[str, Any]) -> str:
        """
        Create a summary of test results.
        
        Args:
            results: Results from test run
            
        Returns:
            Summary as string
        """
        if "error" in results:
            return f"Error: {results['error']}"
        
        if results['returncode'] == 0:
            status = "PASSED"
        else:
            status = "FAILED"
        
        summary = [
            "Test Summary",
            "=" * 50,
            f"Status: {status}",
            f"Return Code: {results['returncode']}"
        ]
        
        if "report_data" in results:
            report_data = results["report_data"]
            if "tests" in report_data:
                summary.extend([
                    f"Tests Run: {report_data['tests']}",
                    f"Failures: {report_data['failures']}",
                    f"Errors: {report_data['errors']}",
                    f"Skipped: {report_data['skipped']}",
                    f"Execution Time: {report_data['time']:.2f}s"
                ])
        
        return "\n".join(summary)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all tests in the project using default settings.
        
        Returns:
            Dictionary containing all test results
        """
        results = {}
        
        # Try to run pytest tests
        if (self.runner.project_root / "pytest.ini").exists() or \
           (self.runner.project_root / "pyproject.toml").exists() or \
           any(self.runner.project_root.glob("**/test_*.py")) or \
           any(self.runner.project_root.glob("**/*_test.py")):
            print("Running pytest tests...")
            results["pytest"] = self.runner.run_pytest(coverage=True)
        
        # Try to run unittest tests
        if any(self.runner.project_root.glob("**/test*.py")):
            print("Running unittest tests...")
            results["unittest"] = self.runner.run_unittest()
        
        return results


def main():
    """
    Main function to demonstrate the TestAutomation capabilities.
    """
    parser = argparse.ArgumentParser(description='Testing Automation Tool')
    parser.add_argument('command', choices=['run', 'summary', 'perf'], 
                       help='Command to execute')
    parser.add_argument('--framework', choices=['pytest', 'unittest'], default='pytest',
                       help='Testing framework to use (default: pytest)')
    parser.add_argument('--path', default='tests/', help='Path to tests (default: tests/)')
    parser.add_argument('--format', choices=['json', 'xml', 'text'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--coverage', action='store_true', help='Include coverage analysis')
    parser.add_argument('--perf-script', help='Performance test script path (for perf command)')
    parser.add_argument('--iterations', type=int, default=10, help='Number of performance test iterations')
    
    args = parser.parse_args()
    
    automation = TestAutomation()
    
    if args.command == 'run':
        results = automation.run_tests(
            test_framework=args.framework,
            test_path=args.path,
            output_format=args.format,
            coverage=args.coverage
        )
        
        report = automation.runner.generate_test_report(results)
        print(report)
        
        # Save detailed report
        report_path = automation.runner.test_results_dir / f"test_report_{args.framework}.{args.format}"
        if args.format == "json" and "report_data" in results:
            with open(report_path, 'w') as f:
                json.dump(results["report_data"], f, indent=2)
        print(f"\nDetailed report saved to: {report_path}")
    
    elif args.command == 'summary':
        results = automation.run_tests(
            test_framework=args.framework,
            test_path=args.path,
            output_format=args.format
        )
        
        summary = automation.create_test_summary(results)
        print(summary)
    
    elif args.command == 'perf':
        if not args.perf_script:
            print("Error: --perf-script is required for performance tests")
            return
        
        results = automation.runner.run_performance_tests(args.perf_script, args.iterations)
        
        if "error" in results:
            print(f"Performance test error: {results['error']}")
        else:
            print("Performance Test Results:")
            print(f"  Iterations: {results['iterations']}")
            print(f"  Min Time: {results['min_time']:.4f}s")
            print(f"  Max Time: {results['max_time']:.4f}s")
            print(f"  Avg Time: {results['avg_time']:.4f}s")
            print(f"  Total Time: {results['total_time']:.4f}s")


if __name__ == "__main__":
    main()