def calculate_fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib_sequence = [0, 1]
    for i in range(2, n):
        fib_sequence.append(fib_sequence[i-1] + fib_sequence[i-2])
    
    return fib_sequence


class MathUtils:
    def __init__(self, precision=2):
        self.precision = precision
    
    def round_number(self, value):
        return round(value, self.precision)
    
    def calculate_average(self, numbers):
        if not numbers:
            return 0
        return sum(numbers) / len(numbers)


def process_data(data, transform_func=None):
    result = []
    
    # Process each item in the data
    for item in data:
        # Apply transformation if provided
        if transform_func:
            item = transform_func(item)
        
        # Add processed item to results
        result.append(item)
    
    return result 

def calculate_kek(n):
    if n <= 0:
        return []
    else:
        return [0]