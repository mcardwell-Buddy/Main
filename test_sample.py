# Sample file for testing code analysis

def calculate_sum(numbers):
    """Calculate the sum of a list"""
    result = sum(numbers)
    return result

def main():
    data = [1, 2, 3, 4, 5]
    total = calculate_sum(data)
    print(f"Total: {total}")

if __name__ == "__main__":
    main()

