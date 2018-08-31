# -*- mode: python -*-
import os
import platform
block_cipher = None

a = Analysis(['sshpt/__main__.py'],
             pathex=['./sshpt'],
             hookspath=None,
             hiddenimports=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='sshpt',
          debug=False,
          strip=False,
          upx=False,
          console=True,
          #icon='icon/sshpt.ico'
          )