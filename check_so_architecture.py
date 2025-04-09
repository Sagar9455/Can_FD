import struct

def check_so_architecture(so_file):
    try:
        with open(so_file, "rb") as f:
            # Read the ELF header (first 4 bytes are magic number, then e_ident[4] is the class)
            e_ident = f.read(16)

            if len(e_ident) < 16:
                print("Not a valid ELF file.")
                return
            
            # Check the magic number (ELF files should start with 0x7f followed by "ELF")
            if e_ident[0] != 0x7f or e_ident[1:4] != b"ELF":
                print("Not an ELF file.")
                return
            
            # e_ident[4] holds the class: 1 = 32-bit, 2 = 64-bit
            elf_class = e_ident[4]

            if elf_class == 1:
                print(f"The file {so_file} is a 32-bit shared object.")
            elif elf_class == 2:
                print(f"The file {so_file} is a 64-bit shared object.")
            else:
                print(f"Unknown architecture in {so_file}.")
                
    except FileNotFoundError:
        print(f"The file {so_file} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    so_file = "math_operations.so"  # Replace with the path to your .so file
    check_so_architecture(so_file)
