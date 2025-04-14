#!/bin/bash
set -x
uname -a
[ -n "$USR_LIB_ARCHNAME" ] && export LD_LIBRARY_PATH=/usr/lib/$USR_LIB_ARCHNAME
echo "$PWD"
mkdir build && cd build
cmake .. -Werror=dev -DCOMPILE_WARNING_AS_ERROR=ON -DWITH_SERIAL_BACKEND=ON -DWITH_EXAMPLES=ON -DPYTHON_BINDINGS=ON -DCPP_BINDINGS=ON -DENABLE_PACKAGING=ON -DCPACK_SYSTEM_NAME="${ARTIFACTNAME}"
make
make package
make required2tar
