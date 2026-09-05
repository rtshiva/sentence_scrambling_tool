# 🧩 Sentence Jigsaw (Sentence Scrambling Tool)

An interactive, pedagogical Python desktop application designed to help children and students master sentence construction, grammar, and pronunciation across languages (Hindi, Japanese, English, and more) by assembling scrambled phrase chunks.

Built with **Apple Human Interface Guidelines (HIG)** aesthetics, modern flat pill containers, 3-zone visual drag-and-drop mechanics, spaced repetition memory algorithms, and neural text-to-speech audio.

---

## ✨ Key Features

### 🎮 4 Distinct Learning Modes
1. **🎯 2-Stage Progressive Mastery Mode**:
   - Uses an active session learning queue with spaced repetition. Mistakes and hint-assisted attempts are automatically requeued.
   - Progresses from **4-words-per-block** down to granular **2-words-per-block** for deep structural recall.
2. **⚡ Speed Run / Timed Challenge**:
   - Race against the clock (1–5 min) with dynamic point multipliers and fire streaks (`🔥 Streak x3`).
3. **🧩 Fill in the Blanks**:
   - Masks select slots in the sentence (1 blank, 2 blanks, or auto 30%) with amber slot placeholders (`____`).
4. **🎧 Listening Comprehension Mode**:
   - Conceals the question text; students listen to the neural speech audio and reconstruct the sentence purely by ear.
5. **🎙️ Voice Coach Mastery Mode**:
   - Instead of assembling jigsaw puzzle tiles, the student reads or listens to the sentence and speaks their complete answer aloud into the microphone.
   - Evaluated by local Ollama AI models (Gemma 4 / Qwen 3.5 / Ornith 9B) with the exact same spaced-repetition mastery mechanics: accurate answers ($\ge 80\%$) advance the queue, while inaccurate answers are gently explained and re-queued for practice.

---

### 🎨 Apple HIG Modern Interface & 3-Zone Drag-and-Drop
- **Two-Tier Header**: Top tier for student profiles, mode switches, and level filters; second tier for progress bars and utility shortcuts.
- **Docked Action Bar**: Bottom control bar (`💡 Hint`, `⟲ Undo`, `🗑 Clear`, `Skip ⏭`, `Next ➔`) remains permanently visible and accessible regardless of monitor scaling or sentence length.
- **3-Zone Interactive Drag & Drop**:
  - **Between Blocks Insertion**: Dragging over the edge between two blocks highlights *both* neighbor boxes in **Sky Blue (`#0284c7`)**, seamlessly inserting the block between them.
  - **Direct Swap / Replace**: Dragging over the center of a block highlights that single box in **Amber (`#eab308`)**, swapping positions or replacing the selected chunk.
- **Translucent Glass Ghost (`DragGhost`)**: High-performance translucent pill preview window that tracks cursor movement during drag operations.
- **Pill Badging & Direct Click Removal**: Flat 1px border chips with instant single-click removal back to the pool.

---

### 🔊 Neural Speech, Voice Recording & AI Coach
- **Natural Multilingual TTS**: Uses Microsoft Edge Neural Text-to-Speech (`Swara` for Hindi, `Nanami` for Japanese, `Neerja` for English) with adjustable playback rates (0.50x to 1.25x).
- **Voice Recorder & Playback**: Students can record their own pronunciation and compare side-by-side with the teacher's neural audio.
- **🤖 AI Voice Coach (Powered by Ollama)**: Evaluates the student's spoken voice answer using local models like **Gemma 4 (`gemma4:12b`, `gemma4:26b`)**, **Qwen 3.5 (`qwen3.5:9b`)**, or **Ornith (`ornith-1.5:9b`)**. It calculates semantic accuracy and provides encouraging, gentle feedback pointing out missing or substituted words.
- **Dictionary Cache & Instant Translation**: Automatically fetches, caches, and translates full sentences and words offline with auto-collapsing disclosure callouts.

---

### 📊 Progress Tracking & Profiles
- **Multi-Student Profile Isolation**: Switch between student profiles with isolated memory stores, settings, and progress logs.
- **Visual Learning Dashboard**: Displays total mastery percentage, accuracy radar, streak counts, and smart mode recommendations.
- **Printable HTML Worksheet Generator**: Generates formatted, ready-to-print homework worksheets with answer keys.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `1` – `9`, `0` | Select phrases 1 through 10 |
| `A` – `Z` | Select extended phrases (11+) |
| `Ctrl + H` | 💡 Give Hint |
| `Ctrl + L` | 🔊 Hear Teacher Pronunciation |
| `Ctrl + A` | 🔊 Hear Current Assembled Answer |
| `Ctrl + R` | 🎙️ Start / Stop Voice Recording |
| `Ctrl + P` | ▶️ Play Back Student Recording |
| `Ctrl + S` | ⏭ Skip Sentence |
| `Backspace` | ⟲ Undo Last Block |
| `Escape` | 🗑 Clear Answer & Reshuffle Blocks |
| `Return` / `Enter` | ➔ Advance to Next Question |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ installed
- Audio output device (speakers or headphones)

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/rtshiva/sentence_scrambling_tool.git
cd sentence_scrambling_tool

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the application
python jigsaw.py
```

### Running the Autonomous Visual Demo Bot
```bash
python bot.py
```

---

## 🧪 Testing & Validation
The project includes a comprehensive test suite covering game engines, SM-2 memory intervals, UI event routing, TTS rate bounds, and profile persistence:
```bash
python -m unittest discover tests -v
```

---

## 📂 Lesson Format
Create custom lessons in simple plain text files or using the built-in **✏️ Edit Lesson** GUI:
```text
# Title: Everyday Conversations
Level: 1
Q: नमस्ते, आप कैसे हैं? | A: नमस्ते, / आप / कैसे हैं? | M: Hello, how are you?
Q: यह एक बहुत सुंदर बगीचा है। | A: यह एक / बहुत सुंदर / बगीचा है। | M: This is a very beautiful garden.
```
