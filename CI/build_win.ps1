$COMPILER=$Env:COMPILER
$src_dir=$pwd

echo "Running cmake for $COMPILER on 64 bit..."
mkdir build-x64
cp .\libiio.iss.cmakein .\build-x64
cd build-x64

cmake -G "$COMPILER" -DCMAKE_SYSTEM_PREFIX_PATH="C:" -DENABLE_IPV6=OFF -DWITH_USB_BACKEND=ON -DWITH_SERIAL_BACKEND=ON -DPYTHON_BINDINGS=ON -DCSHARP_BINDINGS:BOOL=ON -DLIBXML2_LIBRARIES="C:\\libs\\64\\libxml2.lib" -DLIBUSB_LIBRARIES="C:\\libs\\64\\libusb-1.0.lib" -DLIBSERIALPORT_LIBRARIES="C:\\libs\\64\\libserialport.dll.a" -DLIBUSB_INCLUDE_DIR="C:\\include\\libusb-1.0" -DLIBXML2_INCLUDE_DIR="C:\\include\\libxml2" ..
cmake --build . --config Release
cp .\libiio.iss $env:BUILD_ARTIFACTSTAGINGDIRECTORY

cd ../bindings/python
python.exe setup.py.cmakein sdist
Get-ChildItem dist\pylibiio-*.tar.gz | Rename-Item -NewName "libiio-py39-amd64.tar.gz"
mv .\dist\*.gz .
rm .\dist\*.gz
