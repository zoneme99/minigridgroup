from minigrid.core.world_object import Goal
# (!) Box_Token to destinguise it from Gymnasium Box
from minigrid.core.world_object import Box as Box_Token 

class Flag(Goal):
    def __init__(self, color):
        super().__init__()
        self.color = color

class Base(Box_Token):
    def can_overlap(self):
        return True
