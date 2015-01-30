# -*- mode: python -*-
import os
a = Analysis(['sshpt.py'],
             pathex=['./sshpt'],
             hiddenimports=['Crypto.Cipher.ARC4','Crypto.Hash.SHA256','Crypto.Random','Crypto.PublicKey.RSA','Crypto.Signature.PKCS1_v1_5', 'pkg_resources'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
# To revmoe the warning: no pyconfig
for d in a.datas:
  if 'pyconfig' in d[0]:
    a.datas.remove(d)
    break 
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='sshpt.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True,
          icon='icon/sshpt.ico',)

app = BUNDLE(exe,
            name=os.path.join('dist', 'sshpt.exe.app'))
