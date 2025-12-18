
# Copyright (c) 2025 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2025-12-18T12:28:33
# Last Updated: 2025-12-18T12:28:33
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
Quick performance test runner for supreme-octo-succotash
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description):
    """Run command and return success status"""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print("✅ SUCCESS")
            return True, result.stdout
        else:
            print("❌ FAILED")
            print(f"STDERR: {result.stderr}")
            return False, result.stderr

    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT (5 minutes)")
        return False, "Timeout"
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False, str(e)


def check_server():
    """Check if server is running"""
    print("\n🏥 Checking server health...")

    try:
        import requests
        response = requests.get("http://localhost:5000/health", timeout=10)

        if response.status_code == 200:
            print("✅ Server is healthy")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at http://localhost:5000")
        print("💡 Start the server first: python main_clean.py")
        return False
    except Exception as e:
        print(f"💥 Health check failed: {e}")
        return False


def main():
    """Main test runner"""
    print("🚀 SUPREME-OCTO-SUCCOTASH PERFORMANCE TEST SUITE")
    print("=" * 60)

    # Check server
    if not check_server():
        print("\n❌ Server is not available. Aborting tests.")
        sys.exit(1)

    # Test results
    results = {}

    # 1. Run import tests
    print("\n" + "="*50)
    print("📦 PHASE 1: Import Tests")
    print("="*50)

    success, output = run_command([sys.executable, "test_imports.py"], "Testing imports and app initialization")
    results['imports'] = success

    if not success:
        print("\n❌ Import tests failed. Check application configuration.")
        sys.exit(1)

    # 2. Run business logic tests
    print("\n" + "="*50)
    print("💼 PHASE 2: Business Logic Tests")
    print("="*50)

    success, output = run_command([sys.executable, "test_business_logic.py"], "Testing business logic and pagination")
    results['business_logic'] = success

    # 3. Run remaining endpoints tests
    print("\n" + "="*50)
    print("🔗 PHASE 3: API Endpoint Tests")
    print("="*50)

    success, output = run_command([sys.executable, "test_remaining_endpoints.py"], "Testing all API endpoints")
    results['endpoints'] = success

    # 4. Run pool monitoring
    print("\n" + "="*50)
    print("🏊 PHASE 4: Connection Pool Monitoring")
    print("="*50)

    success, output = run_command([sys.executable, "test_pool_monitor.py"], "Testing database connection pool")
    results['pool_monitor'] = success

    # 5. Run basic load test
    print("\n" + "="*50)
    print("⚡ PHASE 5: Basic Load Test")
    print("="*50)

    success, output = run_command([sys.executable, "load_test_with_profiling.py"], "Running load test with profiling")
    results['load_test'] = success

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUITE SUMMARY")
    print("="*60)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(".1f")
    print("\n📋 Detailed Results:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        test_display = test_name.replace('_', ' ').title()
        print(f"  {status}: {test_display}")

    # Recommendations
    print("\n" + "="*60)
    print("🎯 RECOMMENDATIONS")
    print("="*60)

    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your application is ready for production")
        print("💡 Consider running stress_test_analyzer.py for advanced analysis")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

        failed_tests = [name for name, passed in results.items() if not passed]
        if 'imports' in failed_tests:
            print("❌ Fix import/configuration issues first")
        if 'business_logic' in failed_tests:
            print("❌ Fix business logic issues")
        if 'endpoints' in failed_tests:
            print("❌ Fix API endpoint issues")
        if 'pool_monitor' in failed_tests:
            print("❌ Check database connection issues")
        if 'load_test' in failed_tests:
            print("❌ Investigate performance issues")

    # Performance tips
    print("\n" + "="*60)
    print("🚀 NEXT STEPS")
    print("="*60)

    if passed_tests >= 3:
        print("1. 📈 Run advanced stress testing:")
        print("   python stress_test_analyzer.py")
        print()
        print("2. 🔍 Analyze performance bottlenecks:")
        print("   python analyze_profile.py")
        print()
        print("3. 📊 Check profiling data:")
        print("   Look for .pstat files in PyCharm snapshots")

    print("\n4. 📖 Read performance guide:")
    print("   LOAD_TESTING_README.md")

    print("\n5. 🔧 Optimize based on results:")
    print("   - Database query optimization")
    print("   - Caching implementation")
    print("   - Connection pool tuning")

    print("\n" + "="*60)
    print("✨ Performance testing completed!")
    print("="*60)


if __name__ == "__main__":
    main()
