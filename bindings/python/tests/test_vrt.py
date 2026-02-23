import pytest
import iio
import subprocess
import time

@pytest.fixture(scope="module")
def vrt_simulator():
    # Start the C-based simulator in the background
    proc = subprocess.Popen(["../../build/vrt_simulator"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1) # wait for simulator to be ready
    yield proc
    proc.terminate()
    proc.wait()

def test_vrt_context_discovery(vrt_simulator):
    """Test that we can create a VRT context and find the expected device structure."""
    
    ctx = iio.Context("vrt:127.0.0.1")
    
    assert ctx.name == "vrt"
    assert "VITA" in ctx.description or "VRT" in ctx.description
    
    # Check that at least one device was found
    assert len(ctx.devices) > 0
    
    dev = ctx.devices[0]
    # The device ID should match the streamed format from vrt_simulator (0x12345678)
    assert dev.id == "vrt_device_12345678"
    assert dev.name == "vrt_device_12345678"
    
    # Check that channels were successfully populated
    # Vrt simulator sets up 2 generic channels: voltage0 and voltage1
    assert len(dev.channels) == 2
    assert dev.channels[0].id == "voltage0"
    assert dev.channels[1].id == "voltage1"
