import ctypes
import platform

# Check if Python architecture matches the DLL
arch = platform.architecture()[0]
print(f"Python architecture: {arch}")

# Set the DLL path (make sure it's correct)
dll_path = r"E:\GenerateDLL\DLL_Generate_Math_Func\math_operations.dll"

# Ensure that the DLL and Python architecture match (64-bit or 32-bit)
if arch == '64bit':
    print("Loading a 64-bit DLL...")
    try:
        # Load the 64-bit DLL
        dll = ctypes.CDLL(dll_path)
        
        # Define argument types and return types for the functions
        dll.add.argtypes = [ctypes.c_int, ctypes.c_int]
        dll.add.restype = ctypes.c_int

        dll.subtract.argtypes = [ctypes.c_int, ctypes.c_int]
        dll.subtract.restype = ctypes.c_int

        # Call the functions
        result_add = dll.add(5, 3)
        result_subtract = dll.subtract(5, 3)

        # Print the results
        print(f"Addition result: {result_add}")
        print(f"Subtraction result: {result_subtract}")

    except Exception as e:
        print(f"Failed to load the DLL or call functions: {e}")

elif arch == '32bit':
    print("Loading a 32-bit DLL...")
    try:
        # Load the 32-bit DLL
        dll = ctypes.CDLL(dll_path)
        
        # Define argument types and return types for the functions
        dll.add.argtypes = [ctypes.c_int, ctypes.c_int]
        dll.add.restype = ctypes.c_int

        dll.subtract.argtypes = [ctypes.c_int, ctypes.c_int]
        dll.subtract.restype = ctypes.c_int

        # Call the functions
        result_add = dll.add(5, 3)
        result_subtract = dll.subtract(5, 3)

        # Print the results
        print(f"Addition result: {result_add}")
        print(f"Subtraction result: {result_subtract}")

    except Exception as e:
        print(f"Failed to load the DLL or call functions: {e}")

else:
    print("Unknown architecture")
