def decorator(function):
    def wrapper(self):
        print("hello")
        function(self)
    return wrapper

class Account:
    def __init__(self):
        self.user = None
    @decorator
    def simple(self):
        print('justin')

# Example usage:
account_instance = Account()
account_instance.simple()  # This line remains the same
