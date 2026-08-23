# Sentence Scrambling Tool 🧩

A simple, interactive Python desktop application designed to help children and students learn languages and memorize answers by assembling scrambled sentence chunks. 

Perfect for bridging the gap between single-word flashcards and full-sentence recall!

## ✨ Features
* **Adaptive Learning Queue:** Uses a session-based mastery algorithm. Questions you get wrong or use hints on are automatically shuffled back into the deck until you answer them flawlessly.
* **Gamification:** Features engaging pastel-colored UI blocks, star ratings based on hint usage, and satisfying cross-platform sound effects (works natively on Windows & macOS).
* **Built-in Lesson Editor:** Easily create or modify your own lessons. Includes an **Auto-Split** tool where you can paste a full sentence and instantly generate puzzle chunks.
* **Instant Translation Reveal:** Displays the meaning of the sentence the moment you assemble it correctly.
* **Universal Language Support:** Safely handles Unicode characters and delimiters, making it perfect for Hindi (Devanagari), Japanese, English, and more.

## 🚀 Getting Started

### Prerequisites
Make sure you have Python 3 installed. The application uses modern UI themes via `sv_ttk`.

### Installation
1. Clone the repository:
```bash
git clone https://github.com/rtshiva/sentence_scrambling_tool.git
cd sentence_scrambling_tool
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python jigsaw.py
```

## 📂 Customizing Lessons
By default, the app will look for a `sentences.txt` file. You can load any custom `.txt` file using the **"Load File"** button, or build one from scratch using the **"Edit Lesson"** window directly inside the app.
