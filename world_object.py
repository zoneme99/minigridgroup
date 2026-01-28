from minigrid.core.world_object import Goal
from minigrid.core.world_object import Box as Box_Token


class Flag(Goal):
    def __init__(self, color):
        super().__init__()
        self.color = color

    # ADD THIS METHOD:
    def can_overlap(self):
        return True


class Base(Box_Token):
    def can_overlap(self):
        return True
