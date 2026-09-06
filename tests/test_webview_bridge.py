import unittest
import os
import shutil
import tempfile
from core.profile_manager import ProfileManager
from core.deck_manager import DeckManager
from core.memory import MemoryManager
from ui.web_bridge import WebBridgeAPI

class TestWebBridgeAPI(unittest.TestCase):
    def setUp(self):
        self.temp_file = os.path.join(tempfile.gettempdir(), f"test_bridge_profiles_{os.getpid()}.json")
        for suffix in ("", ".bak", ".tmp"):
            p = self.temp_file + suffix
            if os.path.exists(p):
                try: os.remove(p)
                except Exception: pass
        ProfileManager.set_filepath(self.temp_file)
        self.api = WebBridgeAPI()

    def tearDown(self):
        for suffix in ("", ".bak", ".tmp"):
            p = self.temp_file + suffix
            if os.path.exists(p):
                try: os.remove(p)
                except Exception: pass

    def test_get_state_and_profile_switching(self):
        state = self.api.get_state()
        self.assertIn('active_profile', state)
        self.assertIn('decks', state)
        self.assertIn('exam_metrics', state)
        self.assertIn('mission_queue', state)

        # Add and switch profile
        new_state = self.api.create_profile('NewLearner')
        self.assertEqual(new_state['active_profile'], 'NewLearner')
        self.assertIn('NewLearner', new_state['profiles'])

        switched_state = self.api.switch_profile('Default')
        self.assertEqual(switched_state['active_profile'], 'Default')

    def test_deck_crud_operations(self):
        deck_data = {
            'title': 'Test Science Deck',
            'subject': 'Science',
            'description': 'Test deck description',
            'cards': [
                {'question': 'What do plants need?', 'chunks': ['Plants', 'need', 'light'], 'ladder_stage': 1}
            ],
            'tags': ['test']
        }
        saved = self.api.save_deck(deck_data)
        self.assertIsNotNone(saved)
        self.assertEqual(saved['title'], 'Test Science Deck')
        deck_id = saved['id']

        decks = self.api.get_decks()
        self.assertTrue(any(d['id'] == deck_id for d in decks))

        deleted = self.api.delete_deck(deck_id)
        self.assertTrue(deleted)
        decks_after = self.api.get_decks()
        self.assertFalse(any(d['id'] == deck_id for d in decks_after))

    def test_spelling_evaluation(self):
        res = self.api.evaluate_spelling('The quick brown fox', 'The quik brown fox')
        self.assertFalse(res['flawless'])
        self.assertTrue(any(t['status'] == 'typo' for t in res['tokens']))

        flawless_res = self.api.evaluate_spelling('The quick brown fox', 'The quick brown fox')
        self.assertTrue(flawless_res['flawless'])
        self.assertEqual(flawless_res['overall_score'], 100)

    def test_mission_step_evaluation(self):
        res = self.api.evaluate_mission_step(1, flawless=True, score=100)
        self.assertTrue(res['passed'])
        self.assertEqual(res['next_stage'], 2)

    def test_exam_scoping_and_chapters_bridge(self):
        deck_data = {
            'title': 'History Class 4',
            'subject': 'Social Studies',
            'cards': [
                {'question': 'Ashoka ruled Maurya.', 'chunks': ['Ashoka', 'ruled Maurya.'], 'lesson_name': 'Chapter 1: Ashoka', 'ladder_stage': 6},
                {'question': 'Iron Pillar is in Delhi.', 'chunks': ['Iron Pillar', 'is in Delhi.'], 'lesson_name': 'Chapter 2: Monuments', 'ladder_stage': 2}
            ]
        }
        saved_deck = self.api.save_deck(deck_data)
        d_id = saved_deck['id']

        # Test get_deck_chapters
        chaps = self.api.get_deck_chapters(d_id)
        self.assertEqual(len(chaps), 2)

        # Test get_all_decks_with_chapters
        all_hier = self.api.get_all_decks_with_chapters()
        self.assertTrue(any(d['id'] == d_id for d in all_hier))

        # Save exam goal with selected scope
        saved_exam = self.api.save_exam_goal(
            name="History Mid-Term",
            target_date_str="2026-09-30",
            target_cards=1,
            deck_ids=[d_id],
            selected_scope={d_id: ["Chapter 1: Ashoka"]}
        )
        self.assertEqual(saved_exam['exam_name'], "History Mid-Term")
        self.assertEqual(saved_exam['total_cards'], 1)
        self.assertEqual(len(saved_exam['chapters_breakdown']), 1)
        self.assertEqual(saved_exam['chapters_breakdown'][0]['chapter_name'], "Chapter 1: Ashoka")
        self.assertEqual(saved_exam['chapters_breakdown'][0]['status'], "⭐ Mastered")

        # Test get_exam_details
        details = self.api.get_exam_details(saved_exam['id'])
        self.assertEqual(details['id'], saved_exam['id'])
        self.assertEqual(details['exam_name'], "History Mid-Term")

    def test_multi_exam_switching_and_deletion_bridge(self):
        deck = self.api.save_deck({
            'title': 'Maths Deck',
            'cards': [
                {'question': '2+2=4', 'chunks': ['2+2', '=4'], 'lesson_name': 'Addition', 'ladder_stage': 6}
            ]
        })
        d_id = deck['id']

        # 1. Create Exam 1
        exam1 = self.api.save_exam_goal(
            name="Quarterly Exam",
            target_date_str="2026-10-01",
            target_cards=1,
            deck_ids=[d_id],
            selected_scope={d_id: ["Addition"]}
        )
        e1_id = exam1['id']

        # 2. Create Exam 2 - automatically active
        exam2 = self.api.save_exam_goal(
            name="Final Assessment",
            target_date_str="2026-11-01",
            target_cards=1,
            deck_ids=[d_id],
            selected_scope={d_id: ["Addition"]}
        )
        e2_id = exam2['id']

        metrics = self.api.get_exam_metrics()
        self.assertEqual(metrics['selected_exam_id'], e2_id)
        self.assertEqual(metrics['exam_title'], "Final Assessment")
        self.assertEqual(len(metrics['all_exams']), 2)

        # 3. Switch back to Exam 1
        switch_res = self.api.switch_exam(e1_id)
        self.assertTrue(switch_res['success'])
        metrics_after_switch = self.api.get_exam_metrics()
        self.assertEqual(metrics_after_switch['selected_exam_id'], e1_id)
        self.assertEqual(metrics_after_switch['exam_title'], "Quarterly Exam")

        # 4. Delete active Exam 1 -> falls back to Exam 2
        del1_res = self.api.delete_exam(e1_id)
        self.assertTrue(del1_res['success'])
        metrics_after_del1 = self.api.get_exam_metrics()
        self.assertEqual(metrics_after_del1['selected_exam_id'], e2_id)
        self.assertEqual(metrics_after_del1['exam_title'], "Final Assessment")
        self.assertEqual(len(metrics_after_del1['all_exams']), 1)

        # 5. Delete Exam 2 -> no exams remain
        del2_res = self.api.delete_exam(e2_id)
        self.assertTrue(del2_res['success'])
        metrics_after_del2 = self.api.get_exam_metrics()
        self.assertIsNone(metrics_after_del2['selected_exam_id'])
        self.assertEqual(len(metrics_after_del2['all_exams']), 0)

    def test_chapter_addition_and_removal_bridge(self):
        deck = self.api.save_deck({
            'title': 'Geography Deck',
            'cards': [
                {'question': 'G1', 'chunks': ['A'], 'lesson_name': 'Rivers', 'ladder_stage': 6},
                {'question': 'G2', 'chunks': ['B'], 'lesson_name': 'Mountains', 'ladder_stage': 6},
            ]
        })
        d_id = deck['id']

        # Create exam with only Rivers
        exam = self.api.save_exam_goal(
            name="Geo Exam",
            target_date_str="2026-10-15",
            target_cards=1,
            deck_ids=[d_id],
            selected_scope={d_id: ["Rivers"]}
        )
        exam_id = exam['id']
        self.assertEqual(exam['total_cards'], 1)

        # Add Mountains to exam
        updated_exam = self.api.save_exam_goal(
            name="Geo Exam",
            target_date_str="2026-10-15",
            target_cards=2,
            deck_ids=[d_id],
            selected_scope={d_id: ["Rivers", "Mountains"]},
            exam_id=exam_id
        )
        self.assertEqual(updated_exam['id'], exam_id)
        self.assertEqual(updated_exam['total_cards'], 2)
        ch_names = [c['chapter_name'] for c in updated_exam['chapters_breakdown']]
        self.assertIn("Rivers", ch_names)
        self.assertIn("Mountains", ch_names)

        # Remove Rivers, leaving only Mountains
        updated_exam2 = self.api.save_exam_goal(
            name="Geo Exam",
            target_date_str="2026-10-15",
            target_cards=1,
            deck_ids=[d_id],
            selected_scope={d_id: ["Mountains"]},
            exam_id=exam_id
        )
        self.assertEqual(updated_exam2['total_cards'], 1)
        self.assertEqual(updated_exam2['chapters_breakdown'][0]['chapter_name'], "Mountains")

    def test_speak_text_and_gameplay_launch_validation(self):
        # Empty text should return False immediately
        self.assertFalse(self.api.speak_text(""))
        self.assertFalse(self.api.speak_text("   "))

        # Launching gameplay with non-existent deck or empty cards returns False
        self.assertFalse(self.api.launch_gameplay(deck_id="non_existent_deck_id"))

        # Launching exam mission with non-existent exam returns False
        self.assertFalse(self.api.launch_exam_mission(exam_id="non_existent_exam_id"))

        # Gameplay active guard
        self.api._gameplay_active = True
        self.assertFalse(self.api._start_gameplay_thread([]))
        self.api._gameplay_active = False

    def test_in_browser_session_and_submission(self):
        deck_data = {
            'title': 'Hindi Practice',
            'subject': 'Hindi',
            'cards': [
                {
                    'card_id': 'c1',
                    'question': 'पेड़ हमें क्या देते हैं?',
                    'chunks': ['पेड़ हमें', 'छाया और फल', 'देते हैं।'],
                    'lesson_name': 'Chapter 1',
                    'ladder_stage': 1
                }
            ]
        }
        saved = self.api.save_deck(deck_data)
        d_id = saved['id']

        # 1. Fetch active session cards directly
        cards = self.api.get_active_session_cards(deck_id=d_id, chapter_name='Chapter 1')
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]['card_id'], 'c1')
        self.assertEqual(cards[0]['ladder_stage'], 1)

        # 2. Submit card result
        res = self.api.submit_card_result(
            deck_id=d_id,
            card_id='c1',
            ladder_stage=1,
            passed=True,
            score=100,
            flawless=True
        )
        self.assertTrue(res['passed'])
        self.assertEqual(res['next_stage'], 2)

        # Check updated card stage in deck
        updated_deck = self.api.get_deck_details(d_id)
        c1 = next(c for c in updated_deck['cards'] if c['card_id'] == 'c1')
        self.assertEqual(c1['ladder_stage'], 2)

    def test_parent_create_custom_lesson_and_card_editing(self):
        raw_text = """=== Ch-9 नए विचार ===
प्रश्न (क) राजा ने क्या आदेश दिया? ||| राजा ने ||| सभी को ||| सभा में ||| उपस्थित होने का ||| आदेश दिया। ||| // The king ordered everyone to attend the assembly."""
        deck = self.api.create_custom_lesson("Ch-9 नए विचार", "Hindi", raw_text)
        self.assertIsNotNone(deck)
        d_id = deck['id']
        cards = deck.get('cards', [])
        self.assertEqual(len(cards), 1)
        c_id = cards[0]['card_id']

        # Edit card chunks
        updated = self.api.update_card(
            deck_id=d_id,
            card_id=c_id,
            question="प्रश्न (क) राजा ने क्या आज्ञा दी?",
            chunks=["राजा ने", "सभी को", "सभा में", "बुलाया।"],
            meaning="The king summoned everyone."
        )
        self.assertTrue(updated)
        details = self.api.get_deck_details(d_id)
        card_mod = next(c for c in details['cards'] if c['card_id'] == c_id)
        self.assertEqual(card_mod['question'], "प्रश्न (क) राजा ने क्या आज्ञा दी?")
        self.assertEqual(len(card_mod['chunks']), 4)

        # Delete card
        del_ok = self.api.delete_card(d_id, c_id)
        self.assertTrue(del_ok)
        details2 = self.api.get_deck_details(d_id)
        self.assertEqual(len(details2['cards']), 0)

    def test_multi_subject_metrics(self):
        d1 = self.api.save_deck({
            'title': 'Hindi Ch 1',
            'subject': 'Hindi',
            'cards': [{'question': 'Q1', 'chunks': ['A', 'B'], 'ladder_stage': 6}]
        })
        d2 = self.api.save_deck({
            'title': 'Science Ch 1',
            'subject': 'Science',
            'cards': [{'question': 'Q2', 'chunks': ['C', 'D'], 'ladder_stage': 1}]
        })

        metrics = self.api.get_multi_subject_metrics()
        subjects = {s['subject']: s for s in metrics['subjects']}
        self.assertIn('Hindi', subjects)
        self.assertIn('Science', subjects)
        self.assertEqual(subjects['Hindi']['readiness_percent'], 100)
        self.assertEqual(subjects['Science']['readiness_percent'], 0)

    def test_multi_subject_exam_session_retrieval(self):
        # UC-2: Mixed Hindi & Science Exam Scoping
        hindi_deck = self.api.save_deck({
            'title': 'Grade 7 Hindi Deck',
            'subject': 'Hindi',
            'cards': [
                {'card_id': 'h1', 'question': 'HQ1', 'chunks': ['A', 'B'], 'lesson_name': 'Ch-1 माँ, कह एक कहानी', 'ladder_stage': 1},
                {'card_id': 'h2', 'question': 'HQ2', 'chunks': ['C', 'D'], 'lesson_name': 'Ch - 3 फूल और काँटा', 'ladder_stage': 1}
            ]
        })
        science_deck = self.api.save_deck({
            'title': 'Grade 7 Science Deck',
            'subject': 'Science',
            'cards': [
                {'card_id': 's1', 'question': 'SQ1', 'chunks': ['E', 'F'], 'lesson_name': 'Photosynthesis', 'ladder_stage': 1}
            ]
        })

        h_id = hindi_deck['id']
        s_id = science_deck['id']

        # Save exam goal spanning both decks and specific chapters
        exam = self.api.save_exam_goal(
            name="Hindi & Science Mid-Term",
            target_date_str="2026-09-30",
            target_cards=3,
            deck_ids=[h_id, s_id],
            selected_scope={
                h_id: ['Ch-1 माँ, कह एक कहानी', 'Ch - 3 फूल और काँटा'],
                s_id: ['Photosynthesis']
            }
        )
        exam_id = exam['id']

        # Retrieve active exam session cards
        session_cards = self.api.get_active_session_cards(exam_id=exam_id)
        self.assertEqual(len(session_cards), 3)
        card_ids = {c['card_id'] for c in session_cards}
        self.assertEqual(card_ids, {'h1', 'h2', 's1'})

    def test_sm2_successive_ladder_advancement(self):
        # UC-10: Progressive ladder stages 1 through 6
        deck = self.api.save_deck({
            'title': 'Progression Test Deck',
            'subject': 'Hindi',
            'cards': [
                {'card_id': 'prog_c1', 'question': 'Q', 'chunks': ['A', 'B'], 'ladder_stage': 1}
            ]
        })
        d_id = deck['id']

        current_stage = 1
        for expected_next in range(2, 7):
            res = self.api.submit_card_result(
                deck_id=d_id,
                card_id='prog_c1',
                ladder_stage=current_stage,
                passed=True,
                score=100,
                flawless=True
            )
            self.assertTrue(res['passed'])
            self.assertEqual(res['next_stage'], expected_next)
            current_stage = expected_next

        # Check final card stage in deck
        final_deck = self.api.get_deck_details(d_id)
        final_card = next(c for c in final_deck['cards'] if c['card_id'] == 'prog_c1')
        self.assertEqual(final_card['ladder_stage'], 6)

    def test_parent_lesson_parsing_with_comments_and_headers(self):
        # UC-8: Parent bulk text import with headers and meaning comments
        raw_text = """=== Ch-1 माँ, कह एक कहानी ===
प्रश्न: राहुल ने किससे कहानी सुनाने का आग्रह किया? ||| राहुल ने ||| अपनी माँ से ||| कहानी सुनाने का ||| आग्रह किया। ||| // Rahul requested his mother to narrate a story."""
        deck = self.api.create_custom_lesson("Ch-1 माँ, कह एक कहानी", "Hindi", raw_text)
        self.assertIsNotNone(deck)
        cards = deck.get('cards', [])
        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertEqual(card['question'], "प्रश्न: राहुल ने किससे कहानी सुनाने का आग्रह किया?")
        self.assertEqual(len(card['chunks']), 4)
        self.assertEqual(card['meaning'], "Rahul requested his mother to narrate a story.")
        self.assertFalse(any("//" in ch for ch in card['chunks']))

    def test_chunk_translations_bridge(self):
        # Test lookup of single chunk and batch prefetching
        res_single = self.api.get_chunk_translation("दयालु")
        self.assertTrue(bool(res_single))
        self.assertIn("merciful", res_single.lower())

        batch_res = self.api.get_chunk_translations(["दयालु", "nonexistent_xyz_123"])
        self.assertIn("दयालु", batch_res)
        self.assertTrue(bool(batch_res["दयालु"]))

    def test_play_sound_bridge(self):
        # Verify play_sound handles click, success, error, hint, complete
        self.assertTrue(self.api.play_sound('click'))
        self.assertTrue(self.api.play_sound('success'))
        self.assertTrue(self.api.play_sound('error'))
        self.assertTrue(self.api.play_sound('hint'))
        self.assertTrue(self.api.play_sound('complete'))

        # Verify mute setting disables sound
        ProfileManager.save_settings({'sound_enabled': False})
        self.assertFalse(self.api.play_sound('click'))
        ProfileManager.save_settings({'sound_enabled': True})
        self.assertTrue(self.api.play_sound('click'))

    def test_save_settings_and_reset_memory(self):
        # Test save_settings
        new_s = {
            'theme': 'space',
            'sound_enabled': False,
            'tts_speed_rate': '-50%',
            'fill_blanks_count_mode': '3',
            'speed_run_duration_seconds': 300,
            'font_size': 'xlarge',
            'jigsaw_words_per_block': '3',
            'ai_coach_enabled': True,
            'ollama_model': 'gemma4:26b',
            'ollama_url': 'http://127.0.0.1:11434'
        }
        res = self.api.save_settings(new_s)
        self.assertIn('settings', res)
        saved = res['settings']
        self.assertEqual(saved['theme'], 'space')
        self.assertEqual(saved['font_size'], 'xlarge')
        self.assertEqual(saved['jigsaw_words_per_block'], '3')
        self.assertFalse(saved['sound_enabled'])
        self.assertEqual(saved['tts_speed_rate'], '-50%')
        self.assertEqual(saved['fill_blanks_count_mode'], '3')
        self.assertEqual(saved['speed_run_duration_seconds'], 300)
        self.assertEqual(saved['ollama_model'], 'gemma4:26b')

        # Test reset_active_memory
        self.assertTrue(self.api.reset_active_memory())
        self.assertEqual(ProfileManager.get_active_memory(), {})

    def test_profile_deletion(self):
        self.api.create_profile("ProfileToDelete")
        state = self.api.get_state()
        self.assertIn("ProfileToDelete", state['profiles'])

        # Switch back to Default so we can delete ProfileToDelete
        self.api.switch_profile("Default")
        del_res = self.api.delete_profile("ProfileToDelete")
        self.assertNotIn("ProfileToDelete", del_res['profiles'])

    def test_ollama_connection_bridge(self):
        # Test connection endpoint returns structured dict
        res = self.api.test_ollama_connection("http://127.0.0.1:11434")
        self.assertIn('connected', res)
        self.assertIn('models', res)
        self.assertIn('url', res)

    def test_generate_printable_worksheet(self):
        deck_data = {
            'title': 'Test Worksheet Deck',
            'subject': 'Hindi',
            'cards': [
                {
                    'card_id': 'ws_c1',
                    'question': 'प्रश्न: पक्षी कहाँ उड़ते हैं?',
                    'chunks': ['पक्षी', 'नीले', 'आकाश में', 'उड़ते हैं।'],
                    'meaning': 'Birds fly in blue sky.',
                    'lesson_name': 'Ch-1 Nature'
                }
            ]
        }
        saved_deck = self.api.save_deck(deck_data)
        d_id = saved_deck['id']

        html = self.api.generate_printable_worksheet(d_id, 'Ch-1 Nature')
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Test Worksheet Deck', html)
        self.assertIn('Ch-1 Nature', html)
        self.assertIn('प्रश्न: पक्षी कहाँ उड़ते हैं?', html)
        self.assertIn('number-box', html)
        self.assertIn('chunk-box', html)

    def test_submit_card_result_timing_and_improvement(self):
        # 1. Create a test deck with a card
        deck_data = {
            'title': 'Test Timing Deck',
            'subject': 'Hindi',
            'cards': [
                {
                    'card_id': 'time_card_1',
                    'question': 'प्रश्न: सूर्य किस दिशा से उगता है?',
                    'chunks': ['सूर्य', 'पूर्व', 'दिशा से', 'उगता है।'],
                    'ladder_stage': 1,
                    'stage_history': []
                }
            ]
        }
        saved_deck = self.api.save_deck(deck_data)
        d_id = saved_deck['id']
        c_id = 'time_card_1'

        # 2. Attempt 1: First attempt (baseline) - 15.0 seconds
        res1 = self.api.submit_card_result(
            deck_id=d_id,
            card_id=c_id,
            ladder_stage=1,
            passed=True,
            score=100,
            flawless=True,
            duration_seconds=15.0
        )
        self.assertIn('timing', res1)
        t1 = res1['timing']
        self.assertEqual(t1['duration_seconds'], 15.0)
        self.assertIsNone(t1['previous_duration_seconds'])
        self.assertTrue(t1['is_new_best'])
        self.assertEqual(t1['best_duration_seconds'], 15.0)

        # Verify SM-2 Spaced repetition memory records attempt duration
        mem = ProfileManager.get_active_memory()
        card_mem_key = MemoryManager.get_sentence_key('प्रश्न: सूर्य किस दिशा से उगता है?', ['सूर्य', 'पूर्व', 'दिशा से', 'उगता है।'])
        self.assertIn(card_mem_key, mem)
        self.assertEqual(mem[card_mem_key]['last_duration_seconds'], 15.0)
        self.assertEqual(mem[card_mem_key]['best_duration_seconds'], 15.0)

        # 3. Attempt 2: Faster attempt at same stage - 9.5 seconds (5.5s improvement)
        res2 = self.api.submit_card_result(
            deck_id=d_id,
            card_id=c_id,
            ladder_stage=1,
            passed=True,
            score=100,
            flawless=True,
            duration_seconds=9.5
        )
        t2 = res2['timing']
        self.assertEqual(t2['duration_seconds'], 9.5)
        self.assertEqual(t2['previous_duration_seconds'], 15.0)
        self.assertEqual(t2['diff_seconds'], 5.5)
        self.assertTrue(t2['improved'])
        self.assertTrue(t2['is_new_best'])
        self.assertEqual(t2['best_duration_seconds'], 9.5)

        # Memory updated with new best
        mem = ProfileManager.get_active_memory()
        self.assertEqual(mem[card_mem_key]['last_duration_seconds'], 9.5)
        self.assertEqual(mem[card_mem_key]['best_duration_seconds'], 9.5)

        # 4. Attempt 3: Slower attempt at same stage - 12.0 seconds
        res3 = self.api.submit_card_result(
            deck_id=d_id,
            card_id=c_id,
            ladder_stage=1,
            passed=True,
            score=100,
            flawless=True,
            duration_seconds=12.0
        )
        t3 = res3['timing']
        self.assertEqual(t3['duration_seconds'], 12.0)
        self.assertEqual(t3['previous_duration_seconds'], 9.5)
        self.assertEqual(t3['diff_seconds'], -2.5)
        self.assertFalse(t3['improved'])
        self.assertFalse(t3['is_new_best'])
        self.assertEqual(t3['best_duration_seconds'], 9.5)

        # Memory preserves best duration while updating last duration
        mem = ProfileManager.get_active_memory()
        self.assertEqual(mem[card_mem_key]['last_duration_seconds'], 12.0)
        self.assertEqual(mem[card_mem_key]['best_duration_seconds'], 9.5)

        # 5. Verify DeckManager persisted all 3 attempt durations into card stage_history
        deck = DeckManager.get_deck(d_id)
        card = deck['cards'][0]
        history = card.get('stage_history', [])
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]['duration_seconds'], 15.0)
        self.assertEqual(history[1]['duration_seconds'], 9.5)
        self.assertEqual(history[2]['duration_seconds'], 12.0)

    def test_speak_text_speed_rate_and_settings(self):
        from unittest.mock import patch
        import time

        # Test empty or whitespace string returns False
        self.assertFalse(self.api.speak_text(""))
        self.assertFalse(self.api.speak_text("   "))

        with patch('core.tts_engine.TTSManager.speak') as mock_speak:
            # 1. Explicit rate provided: should override settings
            res = self.api.speak_text("Hello World", lang="en", rate="-50%")
            self.assertTrue(res)
            time.sleep(0.05)
            mock_speak.assert_called_with("Hello World", rate_str="-50%", override_voice="auto", lang="en")

        with patch('core.tts_engine.TTSManager.speak') as mock_speak:
            # 2. No explicit rate provided: should fall back to active profile settings
            ProfileManager.save_settings({'tts_speed_rate': '-25%'})
            res = self.api.speak_text("Bonjour", lang="fr")
            self.assertTrue(res)
            time.sleep(0.05)
            mock_speak.assert_called_with("Bonjour", rate_str="-25%", override_voice="auto", lang="fr")

        with patch('core.tts_engine.TTSManager.speak') as mock_speak:
            # 3. Default rate if none in settings and none provided: +0%
            ProfileManager.save_settings({'tts_speed_rate': '+0%'})
            res = self.api.speak_text("Namaste", lang="hi")
            self.assertTrue(res)
            time.sleep(0.05)
            mock_speak.assert_called_with("Namaste", rate_str="+0%", override_voice="auto", lang="hi")

    def test_submit_card_result_retry_does_not_advance_next_stage(self):
        """Verifies that retrying an already completed stage does not advance or mark the next stage as completed."""
        deck_data = {
            'title': 'Retry Test Deck',
            'subject': 'Hindi',
            'cards': [
                {
                    'card_id': 'retry_c1',
                    'question': 'पेड़ हमें क्या देते हैं?',
                    'chunks': ['पेड़', 'हमें', 'फल और फूल', 'देते हैं।'],
                    'ladder_stage': 1,
                    'stage_history': []
                }
            ]
        }
        saved_deck = self.api.save_deck(deck_data)
        d_id = saved_deck['id']
        c_id = 'retry_c1'

        # 1. Attempt 1: First pass at Stage 1 (Blanks)
        res1 = self.api.submit_card_result(
            deck_id=d_id,
            card_id=c_id,
            ladder_stage=1,
            passed=True,
            duration_seconds=12.0
        )
        self.assertTrue(res1['passed'])
        self.assertTrue(res1['stage_advanced'])
        self.assertEqual(res1['next_stage'], 2)
        deck = DeckManager.get_deck(d_id)
        self.assertEqual(deck['cards'][0]['ladder_stage'], 2)

        # 2. Attempt 2: Retrying Stage 1 after successful completion
        # Must record attempt and timing but NOT advance to Stage 3 or mark Stage 2 as completed
        res2 = self.api.submit_card_result(
            deck_id=d_id,
            card_id=c_id,
            ladder_stage=1,
            passed=True,
            duration_seconds=9.0
        )
        self.assertTrue(res2['passed'])
        self.assertFalse(res2['stage_advanced'])
        self.assertEqual(res2['next_stage'], 2)  # Remains Stage 2
        deck = DeckManager.get_deck(d_id)
        self.assertEqual(deck['cards'][0]['ladder_stage'], 2)  # Card in deck remains Stage 2

        # 3. Attempt 3: Advance to Stage 2 (Jigsaw)
        res3 = self.api.submit_card_result(
            deck_id=d_id,
            card_id=c_id,
            ladder_stage=2,
            passed=True,
            duration_seconds=15.0
        )
        self.assertTrue(res3['passed'])
        self.assertTrue(res3['stage_advanced'])
        self.assertEqual(res3['next_stage'], 3)
        deck = DeckManager.get_deck(d_id)
        self.assertEqual(deck['cards'][0]['ladder_stage'], 3)

        # 4. Attempt 4: Retrying Stage 2 after completion
        res4 = self.api.submit_card_result(
            deck_id=d_id,
            card_id=c_id,
            ladder_stage=2,
            passed=True,
            duration_seconds=11.5
        )
        self.assertTrue(res4['passed'])
        self.assertFalse(res4['stage_advanced'])
        self.assertEqual(res4['next_stage'], 3)  # Remains Stage 3
        deck = DeckManager.get_deck(d_id)
        self.assertEqual(deck['cards'][0]['ladder_stage'], 3)

        # 5. Attempt 5: Practicing Stage 1 on a card that has already reached Stage 3
        res5 = self.api.submit_card_result(
            deck_id=d_id,
            card_id=c_id,
            ladder_stage=1,
            passed=True,
            duration_seconds=7.0
        )
        self.assertTrue(res5['passed'])
        self.assertFalse(res5['stage_advanced'])
        self.assertEqual(res5['next_stage'], 3)  # Neither downgrades nor jumps to Stage 4
        deck = DeckManager.get_deck(d_id)
        self.assertEqual(deck['cards'][0]['ladder_stage'], 3)

        # 6. Verify all 5 attempts are recorded in stage_history with correct attempted stages
        history = deck['cards'][0]['stage_history']
        self.assertEqual(len(history), 5)
        self.assertEqual(history[0]['stage'], 1)
        self.assertEqual(history[1]['stage'], 1)
        self.assertEqual(history[2]['stage'], 2)
        self.assertEqual(history[3]['stage'], 2)
        self.assertEqual(history[4]['stage'], 1)

    def test_reset_card_stage_and_reset_chapter_stages(self):
        """Verifies explicitly resetting a single card or an entire chapter's learning stage."""
        deck_data = {
            'title': 'Reset Capability Deck',
            'subject': 'Science',
            'cards': [
                {
                    'card_id': 'reset_c1',
                    'lesson_name': 'Photosynthesis',
                    'question': 'Q1',
                    'chunks': ['Plants', 'make', 'food'],
                    'ladder_stage': 4,
                    'stage_history': [{'stage': 1, 'duration_seconds': 10.0}]
                },
                {
                    'card_id': 'reset_c2',
                    'lesson_name': 'Photosynthesis',
                    'question': 'Q2',
                    'chunks': ['Leaves', 'absorb', 'light'],
                    'ladder_stage': 5,
                    'stage_history': [{'stage': 1, 'duration_seconds': 12.0}]
                },
                {
                    'card_id': 'reset_c3',
                    'lesson_name': 'Respiration',
                    'question': 'Q3',
                    'chunks': ['Cells', 'need', 'oxygen'],
                    'ladder_stage': 3,
                    'stage_history': []
                }
            ]
        }
        saved_deck = self.api.save_deck(deck_data)
        d_id = saved_deck['id']

        # 1. Reset single card to Stage 1 (preserving history)
        res_card = self.api.reset_card_stage(d_id, 'reset_c1', target_stage=1, clear_history=False)
        self.assertTrue(res_card['success'])
        self.assertEqual(res_card['new_stage'], 1)
        
        deck = DeckManager.get_deck(d_id)
        card1 = next(c for c in deck['cards'] if c['card_id'] == 'reset_c1')
        self.assertEqual(card1['ladder_stage'], 1)
        self.assertTrue(len(card1['stage_history']) >= 1)

        # 2. Reset single card to Stage 2 with clear_history=True
        res_card2 = self.api.reset_card_stage(d_id, 'reset_c2', target_stage=2, clear_history=True)
        self.assertTrue(res_card2['success'])
        self.assertEqual(res_card2['new_stage'], 2)
        
        deck = DeckManager.get_deck(d_id)
        card2 = next(c for c in deck['cards'] if c['card_id'] == 'reset_c2')
        self.assertEqual(card2['ladder_stage'], 2)
        self.assertEqual(len(card2['stage_history']), 0)

        # 3. Reset entire chapter 'Photosynthesis' back to Stage 1
        res_chap = self.api.reset_chapter_stages(d_id, 'Photosynthesis', target_stage=1, clear_history=False)
        self.assertTrue(res_chap['success'])
        self.assertEqual(res_chap['updated_count'], 2)
        self.assertEqual(res_chap['target_stage'], 1)

        deck = DeckManager.get_deck(d_id)
        c1 = next(c for c in deck['cards'] if c['card_id'] == 'reset_c1')
        c2 = next(c for c in deck['cards'] if c['card_id'] == 'reset_c2')
        c3 = next(c for c in deck['cards'] if c['card_id'] == 'reset_c3')
        self.assertEqual(c1['ladder_stage'], 1)
        self.assertEqual(c2['ladder_stage'], 1)
        # Respiration chapter card was untouched
        self.assertEqual(c3['ladder_stage'], 3)

    def test_jigsaw_words_per_block_settings(self):
        """Verifies jigsaw words per block options ('auto', '2', '3', '4') are properly validated and stored."""
        from core.models import DEFAULT_SETTINGS
        self.assertIn('jigsaw_words_per_block', DEFAULT_SETTINGS)
        self.assertEqual(DEFAULT_SETTINGS['jigsaw_words_per_block'], 'auto')

        for val in ['2', '3', '4', 'auto']:
            res = self.api.save_settings({'jigsaw_words_per_block': val})
            self.assertEqual(res['settings']['jigsaw_words_per_block'], val)

        state = self.api.get_state()
        self.assertEqual(state['settings']['jigsaw_words_per_block'], 'auto')

    def test_submit_card_result_hint_excluded_from_best_timing_and_advancement(self):
        """Verifies hint-assisted jigsaw attempts are excluded from Personal Best and do not advance stage."""
        deck_data = {
            'title': 'Jigsaw Hint Tests',
            'subject': 'Hindi',
            'cards': [
                {
                    'card_id': 'hint_card_1',
                    'question': 'सूरज किधर उगता है?',
                    'chunks': ['सूरज', 'पूर्व दिशा में', 'उगता है।'],
                    'lesson_name': 'Disha Chapter',
                    'ladder_stage': 2,
                    'stage_history': []
                }
            ]
        }
        saved = self.api.save_deck(deck_data)
        d_id = saved['id']

        # Attempt 1: Solved very fast (2.0s) BUT using a hint
        res_hint = self.api.submit_card_result(
            deck_id=d_id,
            card_id='hint_card_1',
            ladder_stage=2,
            passed=True,
            score=100,
            flawless=True,
            duration_seconds=2.0,
            hint_used=True,
            hints_used=1
        )
        self.assertFalse(res_hint['passed'], "Hint-assisted Jigsaw attempt must not count as passed")
        self.assertFalse(res_hint['stage_advanced'], "Hint-assisted attempt must not advance stage")
        self.assertEqual(res_hint['next_stage'], 2, "Card should remain at Stage 2 for unassisted retry")
        timing_hint = res_hint['timing']
        self.assertFalse(timing_hint['is_new_best'], "Hint attempt must NEVER be flagged as new personal best")
        self.assertIsNone(timing_hint['best_duration_seconds'], "Best duration should be None if only hint attempts exist")

        # Attempt 2: Solved cleanly without hints in 8.5s
        res_clean = self.api.submit_card_result(
            deck_id=d_id,
            card_id='hint_card_1',
            ladder_stage=2,
            passed=True,
            score=100,
            flawless=True,
            duration_seconds=8.5,
            hint_used=False,
            hints_used=0
        )
        self.assertTrue(res_clean['passed'], "Clean Jigsaw attempt must pass")
        self.assertTrue(res_clean['stage_advanced'], "Clean Jigsaw attempt must advance stage")
        self.assertEqual(res_clean['next_stage'], 3, "Clean Jigsaw pass should graduate to Stage 3")
        timing_clean = res_clean['timing']
        self.assertTrue(timing_clean['is_new_best'], "Clean attempt should become the first real Personal Best")
        self.assertEqual(timing_clean['best_duration_seconds'], 8.5, "Personal Best should reflect clean 8.5s")

        # Attempt 3: Retry Stage 2 with hints in 1.5s
        res_hint2 = self.api.submit_card_result(
            deck_id=d_id,
            card_id='hint_card_1',
            ladder_stage=2,
            passed=True,
            score=100,
            flawless=True,
            duration_seconds=1.5,
            hint_used=True,
            hints_used=2
        )
        timing_hint2 = res_hint2['timing']
        self.assertFalse(timing_hint2['is_new_best'], "1.5s with hint must NOT become personal best")
        self.assertEqual(timing_hint2['best_duration_seconds'], 8.5, "Personal Best should remain the clean 8.5s")








