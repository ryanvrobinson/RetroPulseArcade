"""
State interface and base class for menu and minigame implementations.
"""
class State:
    def __init__(self, game_context):
        self.game = game_context

    def enter(self, **kwargs):
        pass

    def exit(self):
        pass

    def handle_input(self, input_handler):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass