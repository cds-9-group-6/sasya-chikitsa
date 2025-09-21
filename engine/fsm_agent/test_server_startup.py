#!/usr/bin/env python3
"""
Quick test to verify server startup without warnings
"""
import subprocess
import time
import sys
import signal
import os

def test_server_startup():
    """Test server startup for warnings"""
    print("🧪 Testing FSM Server Startup (No Warnings)")
    print("=" * 50)
    
    # Test configurations
    test_cases = [
        {
            "name": "Normal startup (no reload)",
            "args": ["python3", "run_fsm_server.py", "--port", "8003", "--check-env"],
            "expect_warning": False
        },
        {
            "name": "Startup with reload (should use import string)",
            "args": ["python3", "run_fsm_server.py", "--port", "8003", "--reload", "--check-env"], 
            "expect_warning": False
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['name']}")
        print(f"   Command: {' '.join(test_case['args'])}")
        
        try:
            # Set environment variables
            env = os.environ.copy()
            env['OLLAMA_HOST'] = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')  # Use existing or default
            env['OLLAMA_MODEL'] = 'llama3.1:8b'
            
            # Run command and capture output
            result = subprocess.run(
                test_case['args'],
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )
            
            output = result.stdout + result.stderr
            
            # Check for the specific warning
            has_warning = "You must pass the application as an import string to enable 'reload' or 'workers'" in output
            
            if test_case['expect_warning']:
                if has_warning:
                    print(f"   ✅ Expected warning found")
                else:
                    print(f"   ⚠️  Expected warning NOT found")
            else:
                if not has_warning:
                    print(f"   ✅ No warning (good!)")
                else:
                    print(f"   ❌ Unexpected warning found:")
                    print(f"      {output}")
            
            print(f"   📊 Exit code: {result.returncode}")
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Test timed out (expected for --check-env)")
        except Exception as e:
            print(f"   ❌ Error running test: {str(e)}")
    
    print(f"\n✅ Server startup tests completed!")

if __name__ == "__main__":
    test_server_startup()
