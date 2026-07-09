import re
import pandas as pd

def _format_single_phone_number(match):
    """
    A helper function for re.sub that formats a single matched phone number.
    """
    # Get the matched string and remove all non-digit characters
    digits = re.sub(r'\D', '', match.group(0))

    # Handle standard 10-digit US numbers
    if len(digits) == 10:
        return f"1({digits[0:3]}){digits[3:6]}-{digits[6:10]}"
    
    # Handle 11-digit numbers that already start with '1'
    if len(digits) == 11 and digits.startswith('1'):
        return f"1({digits[1:4]}){digits[4:7]}-{digits[7:11]}"
        
    # If it's not a format we recognize, return the original match
    return match.group(0)

def format_phone_numbers_in_cell(cell_value):
    """
    Finds all phone-like numbers in a string and formats them consistently.
    Handles multiple numbers in a single cell.
    """
    # Ensure the input is a string, handle None or NaN
    if cell_value is None or pd.isna(cell_value):
        return ""
    
    cell_str = str(cell_value)

    # A robust regex to find phone numbers (10 or 11 digits with optional formatting)
    # This will find things like 1234567890, 123-456-7890, (123) 456-7890, etc.
    phone_regex = re.compile(
        r'(\b(\+?1?[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b)'
    )
    
    # Use the regex's sub() method with our helper function to replace all matches
    return phone_regex.sub(_format_single_phone_number, cell_str)

# Example usage (for testing)
if __name__ == '__main__':
    import pandas as pd
    test_string1 = "Call me at 3365145915 or (919) 223-0874"
    test_string2 = "Main: 216-402-9971, emergency contact is 6183675061."
    test_string3 = "Invalid number 12345, real one is 18005551234" # 11-digit number
    
    print(f"Original: '{test_string1}'\nFormatted: '{format_phone_numbers_in_cell(test_string1)}'\n")
    print(f"Original: '{test_string2}'\nFormatted: '{format_phone_numbers_in_cell(test_string2)}'\n")
    print(f"Original: '{test_string3}'\nFormatted: '{format_phone_numbers_in_cell(test_string3)}'\n")