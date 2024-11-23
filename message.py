class Message:
    def __init__(self, role, content):
        self.content = content
        self.role = role
    
    def __str__(self):
        return f"{self.role} -> {self.content}"
    