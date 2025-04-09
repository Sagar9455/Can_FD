import ctypes
import platform
import os

# Check if Python architecture matches the .so
arch = platform.architecture()[0]
print(f"Python architecture: {arch}")

# Set the path to the .so file (make sure it's correct)
so_path = r"E:\GenerateDLL\SO_Generate_Math_Func\math_operations.so"  # Change this to the actual path to your .so file

# Ensure that the .so file and Python architecture match (64-bit or 32-bit)
if arch == '64bit':
    print("Loading a 64-bit .so file...")
    try:
        # Load the 64-bit .so file
        so = ctypes.CDLL(so_path)
        
        # Define argument types and return types for the functions
        so.add.argtypes = [ctypes.c_int, ctypes.c_int]
        so.add.restype = ctypes.c_int

        so.subtract.argtypes = [ctypes.c_int, ctypes.c_int]
        so.subtract.restype = ctypes.c_int

        # Call the functions
        result_add = so.add(5, 3)
        result_subtract = so.subtract(5, 3)

        # Print the results
        print(f"Addition result: {result_add}")
        print(f"Subtraction result: {result_subtract}")

    except Exception as e:
        print(f"Failed to load the .so file or call functions: {e}")

elif arch == '32bit':
    print("Loading a 32-bit .so file...")
    try:
        # Load the 32-bit .so file
        so = ctypes.CDLL(so_path)
        
        # Define argument types and return types for the functions
        so.add.argtypes = [ctypes.c_int, ctypes.c_int]
        so.add.restype = ctypes.c_int

        so.subtract.argtypes = [ctypes.c_int, ctypes.c_int]
        so.subtract.restype = ctypes.c_int

        # Call the functions
        result_add = so.add(5, 3)
        result_subtract = so.subtract(5, 3)

        # Print the results
        print(f"Addition result: {result_add}")
        print(f"Subtraction result: {result_subtract}")

    except Exception as e:
        print(f"Failed to load the .so file or call functions: {e}")

else:
    print("Unknown architecture")
