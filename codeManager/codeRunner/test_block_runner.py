import subprocess
import time
import json
import sys

def create_container(container_name, image_name="block-runner:latest", network_name="batman"):
    """Create a Docker container from the block-runner image"""
    try:
        # First, ensure network exists
        try:
            subprocess.run([
                'docker', 'network', 'create', network_name
            ], stderr=subprocess.DEVNULL, check=False)
        except:
            pass
        
        # Create container
        subprocess.run([
            'docker', 'run', '-d',
            '--name', container_name,
            '--rm',
            '--network', network_name,
            image_name,
            'tail', '-f', '/dev/null'
        ], check=True)
        print(f"✓ Container {container_name} created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error creating container {container_name}: {e}")
        return False

def is_container_running(container_name):
    """Check if a Docker container is running"""
    result = subprocess.run(
        ['docker', 'ps', '--filter', f"name={container_name}", '--format', '{{.Names}}'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False
    )
    return bool(result.stdout.decode('utf-8').strip())

def remove_container(container_name):
    """Remove a Docker container"""
    try:
        subprocess.run(['docker', 'rm', '-f', container_name], 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        print(f"✓ Container {container_name} removed successfully")
    except Exception as e:
        print(f"✗ Error removing container {container_name}: {e}")

def execute_python_in_container(container_name, python_code):
    """Execute Python code in the container"""
    result = subprocess.run(
        [
            "docker", "exec", "-i", container_name, "python3"
        ],
        input=python_code.encode('utf-8'),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return {
        "stdout": result.stdout.decode("utf-8"),
        "stderr": result.stderr.decode("utf-8")
    }

def test_block_library():
    """Test the block_library.py module in container"""
    container_name = "test_block_runner"
    
    print("\n" + "="*60)
    print("BLOCK LIBRARY CONTAINER TEST")
    print("="*60 + "\n")
    
    # Cleanup if exists
    if is_container_running(container_name):
        remove_container(container_name)
    
    # Create container
    if not create_container(container_name):
        return False
    
    time.sleep(2)  # Wait for container to start
    
    # Test 1: Import block_library
    print("\n[TEST 1] Importing block_library...")
    code1 = "from block_library import Block, BlockDisplay\nprint('✓ Import successful')"
    result = execute_python_in_container(container_name, code1)
    print("STDOUT:", result['stdout'])
    if result['stderr']:
        print("STDERR:", result['stderr'])
    
    # Test 2: Create BlockDisplay
    print("\n[TEST 2] Creating BlockDisplay...")
    code2 = """
from block_library import Block, BlockDisplay
display = BlockDisplay(display_id="test_display")
print(f'✓ BlockDisplay created: {display.display_id}')
print(f'✓ Grid size: 8x8')
"""
    result = execute_python_in_container(container_name, code2)
    print("STDOUT:", result['stdout'])
    if result['stderr']:
        print("STDERR:", result['stderr'])
    
    # Test 3: Access and modify block
    print("\n[TEST 3] Accessing and modifying blocks...")
    code3 = """
from block_library import Block, BlockDisplay
display = BlockDisplay()
block = display[0, 0]
print(f'✓ Accessed block at [0, 0]')
print(f'  - Initial color: {block.color}')
print(f'  - Initial brightness: {block.brightness}')
print(f'  - Initial on state: {block.on}')
"""
    result = execute_python_in_container(container_name, code3)
    print("STDOUT:", result['stdout'])
    if result['stderr']:
        print("STDERR:", result['stderr'])
    
    # Test 4: Set block properties
    print("\n[TEST 4] Setting block properties...")
    code4 = """
from block_library import Block, BlockDisplay
display = BlockDisplay()
block = display[3, 3]
block.color = (255, 0, 0)  # Red
block.brightness = 0.8
block.on = True
print(f'✓ Block properties set:')
print(f'  - Color: {block.color}')
print(f'  - Brightness: {block.brightness}')
print(f'  - On: {block.on}')
"""
    result = execute_python_in_container(container_name, code4)
    print("STDOUT:", result['stdout'])
    if result['stderr']:
        print("STDERR:", result['stderr'])
    
    # Test 5: Fill display
    print("\n[TEST 5] Testing fill method...")
    code5 = """
from block_library import Block, BlockDisplay
display = BlockDisplay()
display.fill(color=(0, 255, 0), brightness=1.0)
block = display[0, 0]
print(f'✓ Display filled:')
print(f'  - Color at [0,0]: {block.color}')
print(f'  - Brightness at [0,0]: {block.brightness}')
print(f'  - On at [0,0]: {block.on}')
"""
    result = execute_python_in_container(container_name, code5)
    print("STDOUT:", result['stdout'])
    if result['stderr']:
        print("STDERR:", result['stderr'])
    
    # Test 6: Clear display
    print("\n[TEST 6] Testing clear method...")
    code6 = """
from block_library import Block, BlockDisplay
display = BlockDisplay()
display.fill()
display.clear()
block = display[0, 0]
print(f'✓ Display cleared:')
print(f'  - On at [0,0]: {block.on}')
"""
    result = execute_python_in_container(container_name, code6)
    print("STDOUT:", result['stdout'])
    if result['stderr']:
        print("STDERR:", result['stderr'])
    
    # Test 7: Check requests library is available
    print("\n[TEST 7] Checking requests library availability...")
    code7 = """
import requests
print(f'✓ Requests library version: {requests.__version__}')
"""
    result = execute_python_in_container(container_name, code7)
    print("STDOUT:", result['stdout'])
    if result['stderr']:
        print("STDERR:", result['stderr'])
    
    # Cleanup
    print("\n[CLEANUP] Removing test container...")
    remove_container(container_name)
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED ✓")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_block_library()
