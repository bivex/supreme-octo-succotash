try:
    import uvloop
    print("uvloop available")
except ImportError:
    print("uvloop not installed")
