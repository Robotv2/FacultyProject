class Course:
    def __init__(self, id: str, credits: int):
        self.id = id
        self.credits = credits

    def __repr__(self):
        return f"Course(id={self.id}, credits={self.credits})"


class Faculty:
    def __init__(self, id: str, preferences: dict):
        self.id = id
        self.preferences = preferences

    def __repr__(self):
        return f"Faculty(id={self.id}, preferences={self.preferences})"
