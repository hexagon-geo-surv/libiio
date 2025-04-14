#!/bin/bash
set -x
uname -a
sudo apt update
sudo apt install -y gcc-10
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 100
echo "$PWD"
mkdir build && cd build
cmake .. -Werror=dev -DCOMPILE_WARNING_AS_ERROR=ON -DWITH_SERIAL_BACKEND=ON -DWITH_EXAMPLES=ON -DPYTHON_BINDINGS=ON -DCPP_BINDINGS=ON -DENABLE_PACKAGING=ON -DCPACK_SYSTEM_NAME="${ARTIFACTNAME}"
make
make package
make required2tar
