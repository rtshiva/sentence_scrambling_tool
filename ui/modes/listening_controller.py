from core.models import QuestionItem
from ui.modes.jigsaw_controller import JigsawRoundController

class ListeningRoundController(JigsawRoundController):
    """Encapsulates Listening Comprehension gameplay mechanics (veiled text + audio prompt)."""

    @property
    def mode_name(self) -> str:
        return 'listening'

    def setup_round(self, question_item: QuestionItem):
        super().setup_round(question_item)
        app = self.app
        app.question_label.config(
            text='🎧 [ Click "Teacher (L)" to hear the sentence ]',
            foreground='#2980b9'
        )
        if hasattr(app, '_listening_after_id') and app._listening_after_id:
            try:
                app.root.after_cancel(app._listening_after_id)
            except Exception:
                pass
        app._listening_after_id = app.root.after(300, app.speak_current_question)

    def check_answer(self):
        app = self.app
        is_correct = (app.user_selected_chunks == app.original_chunks)
        if is_correct:
            data = app.model.get_current_question()
            if data:
                app.question_label.config(text=data.question, foreground='#1e8449')
        super().check_answer()

    def teardown(self):
        app = self.app
        if hasattr(app, '_listening_after_id') and app._listening_after_id:
            try:
                app.root.after_cancel(app._listening_after_id)
            except Exception:
                pass
            app._listening_after_id = None
