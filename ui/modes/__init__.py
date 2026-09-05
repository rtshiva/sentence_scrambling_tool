from ui.modes.base_controller import BaseRoundController
from ui.modes.jigsaw_controller import JigsawRoundController
from ui.modes.blanks_controller import BlanksRoundController
from ui.modes.listening_controller import ListeningRoundController
from ui.modes.voice_controller import VoiceRoundController
from ui.modes.writing_controller import WritingRoundController
from ui.modes.speed_run_controller import SpeedRunRoundController

__all__ = [
    'BaseRoundController',
    'JigsawRoundController',
    'BlanksRoundController',
    'ListeningRoundController',
    'VoiceRoundController',
    'WritingRoundController',
    'SpeedRunRoundController',
    'create_round_controller'
]

def create_round_controller(mode_name: str, app) -> BaseRoundController:
    """Factory creating the corresponding round controller for a given mode name."""
    if mode_name == 'fill_blanks':
        return BlanksRoundController(app)
    elif mode_name == 'listening':
        return ListeningRoundController(app)
    elif mode_name == 'voice_mastery':
        return VoiceRoundController(app)
    elif mode_name == 'writing':
        return WritingRoundController(app)
    elif mode_name == 'speed_run':
        return SpeedRunRoundController(app)
    else:
        return JigsawRoundController(app)
