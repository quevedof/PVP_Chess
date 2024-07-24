class Move():
    def __init__(self, initial, final):
        # initial and final are squares
        self.initial = initial
        self.final = final

    # tell python how to compare moves
    def __eq__(self, other):
        return self.initial == other.initial and self.final == other.final