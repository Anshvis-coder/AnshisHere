#!/usr/bin/env python3
"""
Simple Command-Line Calculator
Supports: addition, subtraction, multiplication, division
"""

def add(x, y):
    """Add two numbers"""
    return x + y

def subtract(x, y):
    """Subtract y from x"""
    return x - y

def multiply(x, y):
    """Multiply two numbers"""
    return x * y

def divide(x, y):
    """Divide x by y"""
    if y == 0:
        raise ValueError("Cannot divide by zero!")
    return x / y

def main():
    print("=" * 40)
    print("       Simple Python Calculator")
    print("=" * 40)
    print("\nOperations:")
    print("  1. Add (+)")
    print("  2. Subtract (-)")
    print("  3. Multiply (*)")
    print("  4. Divide (/)")
    print("  5. Exit")
    print("=" * 40)

    while True:
        choice = input("\nEnter choice (1-5): ")

        if choice == '5':
            print("Thank you for using the calculator. Goodbye!")
            break

        if choice not in ['1', '2', '3', '4']:
            print("Invalid choice! Please enter a number between 1 and 5.")
            continue

        try:
            num1 = float(input("Enter first number: "))
            num2 = float(input("Enter second number: "))
        except ValueError:
            print("Invalid input! Please enter valid numbers.")
            continue

        if choice == '1':
            result = add(num1, num2)
            operator = '+'
        elif choice == '2':
            result = subtract(num1, num2)
            operator = '-'
        elif choice == '3':
            result = multiply(num1, num2)
            operator = '*'
        elif choice == '4':
            try:
                result = divide(num1, num2)
                operator = '/'
            except ValueError as e:
                print(f"Error: {e}")
                continue

        print(f"\nResult: {num1} {operator} {num2} = {result}")

if __name__ == "__main__":
    main()
