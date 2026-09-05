from core.game_engine import GameEngine
from ui.modes.jigsaw_controller import JigsawRoundController

class SpeedRunRoundController(JigsawRoundController):
    """Encapsulates Timed Challenge / Speed Run gameplay mechanics (timer countdown + streak multiplier)."""

    @property
    def mode_name(self) -> str:
        return 'speed_run'

    def check_answer(self):
        app = self.app
        is_correct = (app.user_selected_chunks == app.original_chunks)
        super().check_answer()
        if is_correct:
            app.speed_run_streak += 1
            app.speed_run_total_solved += 1
            points = GameEngine.calculate_speed_run_points(app.speed_run_streak)
            app.speed_run_score += points
            app.score_label.config(text=f'+{points} pts! 🔥 Streak {app.speed_run_streak}')
        else:
            app.speed_run_streak = 0
