import hashlib

def hash_password(password):
    """Hash a password using MD5."""
    return hashlib.md5(password.encode()).hexdigest()

def load_hashed_passwords(file_path):
    """Load hashed passwords from a file."""
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def check_password(input_password, hashed_passwords):
    """Check if the input password matches any hashed passwords."""
    input_hash = hash_password(input_password)
    return input_hash in hashed_passwords

def main():
    # Path to the file containing hashed passwords
    passwords_file_path = 'passwords.txt'

    # Load hashed passwords from file
    hashed_passwords = load_hashed_passwords(passwords_file_path)

    # Input password to check
    input_password = input("Enter the password: ")

    # Check if the password matches
    if check_password(input_password, hashed_passwords):
        print("Password match found.")
    else:
        print("Password does not match.")

if __name__ == "__main__":
    main()
