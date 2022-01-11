iscc $env:BUILD_ARTIFACTSTAGINGDIRECTORY\Windows-VS-2019-x64\libiio.iss

Get-ChildItem $env:BUILD_ARTIFACTSTAGINGDIRECTORY -Force -Recurse | Remove-Item -Force -Recurse
cp C:\libiio-setup.exe $env:BUILD_ARTIFACTSTAGINGDIRECTORY
