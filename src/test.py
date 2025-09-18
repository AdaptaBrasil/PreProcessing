from typing import List, Tuple, Optional
from decimal import Decimal, InvalidOperation
def generate_continuous_intervals(min_value: float, max_value: float, n_terms: int) -> List[Tuple[float, float]]:
    """
    Generate n continuous intervals from min_value to max_value.
    
    Each interval follows the pattern where the next minimum value is 
    the previous maximum value plus 0.01, ensuring continuity.
    
    Args:
        min_value: Starting minimum value for the first interval
        max_value: Ending maximum value for the last interval  
        n_terms: Number of intervals to generate
        
    Returns:
        List of tuples containing (min, max) for each interval
        
    Raises:
        ValueError: If n_terms <= 0 or min_value >= max_value
    """
    if n_terms <= 0:
        raise ValueError("Number of terms must be greater than 0")
    
    if min_value >= max_value:
        raise ValueError("Minimum value must be less than maximum value")
    
    # Calculate the total range and interval size
    total_range = max_value - min_value
    interval_size = total_range / n_terms
    
    intervals: List[Tuple[float, float]] = []
    current_min = min_value
    
    for i in range(n_terms):
        if i == n_terms - 1:  # Last interval
            current_max = max_value
        else:
            current_max = round(current_min + interval_size, 2)
        
        intervals.append((current_min, current_max))
        
        # Next minimum is current maximum + 0.01 (continuous pattern)
        current_min = round(current_max + 0.01, 2)
    
    return intervals

def validate_continuous_intervals(intervals: List[Tuple[float, float]]) -> Tuple[bool, List[str]]:
    """
    Validate if a list of intervals is continuous.
    
    Checks that each interval follows the pattern where the next minimum 
    value is the previous maximum value plus 0.01, ensuring continuity
    as expected by the existing validation logic.
    
    Args:
        intervals: List of tuples containing (min, max) for each interval
        
    Returns:
        Tuple containing (is_valid, error_messages)
        - is_valid: Boolean indicating if all intervals are continuous
        - error_messages: List of validation error messages
        
    Raises:
        ValueError: If intervals list is empty or contains invalid data
    """
    if not intervals:
        raise ValueError("Intervals list cannot be empty")
    
    errors: List[str] = []
    
    # Sort intervals by minimum value to ensure proper order
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    
    prev_max_val: Optional[float] = None
    
    for i, (min_val, max_val) in enumerate(sorted_intervals):
        # Validate min < max for each interval
        if min_val >= max_val:
            errors.append(
                f"Interval {i + 1}: Minimum value ({min_val}) must be less than maximum value ({max_val})"
            )
        
        # Check continuity with previous interval
        if prev_max_val is not None:
            try:
                # Using Decimal for precision (same as existing validation)
                expected_min = prev_max_val + 0.01
                if Decimal(str(min_val)) - Decimal(str(prev_max_val)) != Decimal("0.01"):
                    errors.append(
                        f"Interval {i + 1}: Not continuous. Minimum value {min_val} should be {expected_min} to follow previous maximum value"
                    )
            except InvalidOperation:
                errors.append(f"Interval {i + 1}: Invalid numeric values for continuity validation")
        
        prev_max_val = max_val
    
    is_valid = len(errors) == 0
    return is_valid, errors

# Example usage:
intervals = generate_continuous_intervals(0.0, 1.0, 5)
# Altera o primeiro e o último intervalo para testar a validação
intervals[0] = (0.0, 0.19)  # Should be (0.0, 0.2)
intervals[-1] = (0.81, 1.0)  # Should be (0.81, 1.0
for idx, (min_val, max_val) in enumerate(intervals):
    print(f"Interval {idx + 1}: Min = {min_val}, Max = {max_val}")
    
    
print("\nValidation Results:")
is_valid, error_messages = validate_continuous_intervals(intervals)
if is_valid:
    print("All intervals are continuous and valid.")
else:
    print("Validation errors found:")
    for error in error_messages:
        print(error)
# Bibliotecas de visualização