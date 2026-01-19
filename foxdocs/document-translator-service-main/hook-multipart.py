# PyInstaller hook for python-multipart package
from PyInstaller.utils.hooks import collect_all

# Collect everything from multipart module
datas, binaries, hiddenimports = collect_all('multipart')

# Explicitly add all submodules
hiddenimports += [
    'multipart',
    'multipart.multipart',
]

