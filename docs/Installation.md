# Install pycrypto on Windows
Open command prompt with admin privileges
Run vsvars32.bat from your version of VC

```
set CL=-FI"%VCINSTALLDIR%\INCLUDE\stdint.h"
pip install pycrypto
```
