import iio
import time

def main():
    # Create a VRT context on localhost
    print("Creating VRT context on vrt:127.0.0.1...")
    ctx = iio.Context("vrt:127.0.0.1")
    
    print(f"Context name: {ctx.name}")
    print(f"Context description: {ctx.description}")
    print(f"Number of devices: {len(ctx.devices)}")
    
    for dev in ctx.devices:
        print(f"  Found device: {dev.id} ({dev.name})")
        for ch in dev.channels:
            print(f"    Channel: {ch.id}")

if __name__ == '__main__':
    main()
