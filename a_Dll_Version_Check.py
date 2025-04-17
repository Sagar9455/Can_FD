import pefile

def check_dll_architecture(dll_path):
    try:
        pe = pefile.PE(dll_path)
        
        # Check the architecture of the DLL
        if pe.FILE_HEADER.Machine == 0x8664:  # 64-bit (AMD64)
            print(f"{dll_path} is a 64-bit DLL")
        elif pe.FILE_HEADER.Machine == 0x14c:  # 32-bit (x86)
            print(f"{dll_path} is a 32-bit DLL")
        else:
            print(f"{dll_path} has an unknown architecture")
    
    except Exception as e:
        print(f"Error reading DLL: {e}")

# Example usage
dll_path = r"E:\GenerateDLL\DLL_Generate_Math_Func\math_operations.dll"  # Replace with your DLL path
check_dll_architecture(dll_path)
