# -*- mode: python -*-
a = Analysis(['sshpt.py'],
             pathex=['G:\\git.haginara.net\\sshpt'],
             hiddenimports=['Crypto.Cipher.ARC4','Crypto.Hash.SHA256','Crypto.Random','Crypto.PublicKey.RSA','Crypto.Signature.PKCS1_v1_5', 'pkg_resources'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          exclude_binaries=True,
          name='sshpt.exe',
          debug=False,
          strip=None,
          upx=False,
          console=True )
