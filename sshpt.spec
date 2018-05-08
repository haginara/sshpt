# -*- mode: python -*-
import os
import platform
a = Analysis(['sshpt/__main__.py'],
             pathex=['./sshpt'],
             hiddenimports=['Crypto.Cipher.ARC4','Crypto.Hash.SHA256','Crypto.Random','Crypto.PublicKey.RSA','Crypto.Signature.PKCS1_v1_5', 'pkg_resources'],
             hookspath=None,
             runtime_hooks=None)

if platform.system().find("Windows")>= 0:
    a.datas = [i for i in a.datas if i[0].find('Include') < 0]

pyz = PYZ(a.pure)
#a.datas = filter(lambda d: 'pyconfig' not in d[0], a.datas)
exe = EXE(pyz,
          a.scripts,
          a.binaries + [('msvcr100.dll', os.environ['WINDIR'] + '\system32\msvcr100.dll', 'BINARY')],
          a.zipfiles,
          a.datas,
          name='sshpt.exe',
          debug=False,
          strip=None,
          upx=False,
          console=True,
          #icon='icon/sshpt.ico'
          )

app = BUNDLE(exe, name=os.path.join('dist', 'sshpt.exe.app'))
