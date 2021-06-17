# -*- coding: utf-8 -*-
# -*- mode: python -*-
# VRMをPMXに変換するツール 64bit版

block_cipher = None


a = Analysis(['src\\executor.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=['pkg_resources', 'wx._adv', 'wx._html', 'bezier', 'quaternion'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['mkl','libopenblas', 'tkinter', 'win32comgenpy', 'traitlets', 'PIL', 'IPython', 'pydoc', 'lib2to3', 'pygments', 'matplotlib'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
a.datas += [('.\\src\\Vrm2PmxExporter.ico','.\\src\\Vrm2PmxExporter.ico', 'Data')]
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Vrm2PmxExporter_1.03_β07_64bit',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon='.\\src\\Vrm2PmxExporter.ico')

