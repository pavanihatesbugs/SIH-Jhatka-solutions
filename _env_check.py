import sys
print("executable", sys.executable)
print("version", sys.version)
mods = ["cv2", "numpy", "PIL", "pymupdf"]
for name in mods:
    try:
        m = __import__(name)
        ver = getattr(m, "__version__", getattr(m, "version", "OK"))
        print(name, "OK", ver)
    except Exception as e:
        print(name, "FAIL", e)
