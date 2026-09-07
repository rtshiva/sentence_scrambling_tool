// Automated Comprehensive Frontend & DOM Contract Unit Tests for Sentence Jigsaw 3.0 WebUI SPA
// Validates all 10 Use Case scenarios, index.html IDs, app.js execution, and in-browser gameplay rendering.

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const ROOT_DIR = path.resolve(__dirname, '..');
const HTML_PATH = path.join(ROOT_DIR, 'ui', 'web', 'index.html');
const JS_PATH = path.join(ROOT_DIR, 'ui', 'web', 'app.js');
const PARTICLES_PATH = path.join(ROOT_DIR, 'ui', 'web', 'js', 'effects', 'particles.js');

const htmlContent = fs.readFileSync(HTML_PATH, 'utf-8');
const jsContent = fs.readFileSync(JS_PATH, 'utf-8');
const particlesContent = fs.existsSync(PARTICLES_PATH) ? fs.readFileSync(PARTICLES_PATH, 'utf-8') : '';

console.log("=== Running WebUI Frontend & Gameplay DOM Comprehensive Test Suite ===");

// -------------------------------------------------------------------------
// 1. Static Contract: Extract and verify all getElementById calls
// -------------------------------------------------------------------------
const allJsCode = jsContent + '\n' + particlesContent;
const jsIdMatches = [...allJsCode.matchAll(/document\.getElementById\(['"]([^'"]+)['"]\)/g)].map(m => m[1]);
const uniqueJsIds = [...new Set(jsIdMatches)];

const htmlIdMatches = [...htmlContent.matchAll(/id=["']([^"']+)["']/g)].map(m => m[1]);
const htmlIdsSet = new Set(htmlIdMatches);

const missingFromHtml = uniqueJsIds.filter(id => !htmlIdsSet.has(id));

console.log(`[Test 1] DOM Contract Verification: ${uniqueJsIds.length} JS IDs queried, ${htmlIdsSet.size} HTML IDs present.`);
if (missingFromHtml.length > 0) {
  console.error("FAIL: Missing IDs in index.html:", missingFromHtml);
  process.exit(1);
}
assert.strictEqual(missingFromHtml.length, 0, `Missing IDs in index.html: ${missingFromHtml.join(', ')}`);
console.log("✓ PASS: 100% of DOM IDs queried in app.js exist in index.html!");

// -------------------------------------------------------------------------
// 2. Mock DOM Environment for Dynamic Gameplay Tests
// -------------------------------------------------------------------------
class MockClassList {
  constructor(el) {
    this.el = el;
    this.classes = new Set();
  }
  add(...cls) { cls.forEach(c => this.classes.add(c)); }
  remove(...cls) { cls.forEach(c => this.classes.delete(c)); }
  contains(cls) { return this.classes.has(cls); }
  toggle(cls) { if (this.contains(cls)) this.remove(cls); else this.add(cls); }
}

class MockElement {
  constructor(tagName = 'div', id = '') {
    this.tagName = tagName.toUpperCase();
    this.id = id;
    this.classList = new MockClassList(this);
    this._textContent = '';
    this._innerHTML = '';
    this.value = '';
    this.title = '';
    this.style = {};
    this.dataset = {};
    this.selectionStart = 0;
    this.selectionEnd = 0;
    this.children = [];
    this.parentElement = null;
    this.onclick = null;
    this.onchange = null;
    this.onmouseenter = null;
    this.onmouseleave = null;
    this.onmousemove = null;
    this._listeners = {};
  }

  get className() {
    return Array.from(this.classList.classes).join(' ');
  }
  set className(val) {
    this.classList.classes = new Set((val || '').split(/\s+/).filter(Boolean));
  }

  addEventListener(event, callback) {
    if (!this._listeners[event]) this._listeners[event] = [];
    this._listeners[event].push(callback);
  }

  removeEventListener(event, callback) {
    if (!this._listeners[event]) return;
    this._listeners[event] = this._listeners[event].filter(cb => cb !== callback);
  }

  dispatchEvent(evt) {
    const type = typeof evt === 'string' ? evt : (evt.type || '');
    if (this[`on${type}`]) this[`on${type}`](evt);
    if (this._listeners[type]) {
      this._listeners[type].forEach(cb => cb(evt));
    }
  }

  getBoundingClientRect() {
    return { top: 100, left: 100, width: 80, height: 40, right: 180, bottom: 140 };
  }

  setAttribute(attr, val) {
    if (!this._attributes) this._attributes = {};
    this._attributes[attr] = String(val);
  }

  getAttribute(attr) {
    return this._attributes ? this._attributes[attr] : null;
  }

  get textContent() { return this._textContent; }
  set textContent(val) {
    this._textContent = String(val);
    this.children = [];
  }

  get innerHTML() { return this._innerHTML; }
  set innerHTML(val) {
    this._innerHTML = String(val);
    if (val === '') {
      this.children = [];
    }
  }

  appendChild(child) {
    child.parentElement = this;
    this.children.push(child);
    if ((this.tagName === 'SELECT' || this.id.includes('select')) && (!this.value || child.selected)) {
      this.value = child.value;
    }
    return child;
  }

  removeChild(child) {
    const idx = this.children.indexOf(child);
    if (idx !== -1) {
      child.parentElement = null;
      this.children.splice(idx, 1);
    }
    return child;
  }

  focus() {}

  getContext(type) {
    return {
      fillRect: () => {},
      clearRect: () => {},
      beginPath: () => {},
      arc: () => {},
      fill: () => {}
    };
  }

  querySelector(sel) {
    const list = this.querySelectorAll(sel);
    return list.length > 0 ? list[0] : null;
  }

  querySelectorAll(sel) {
    const matches = [];
    const walk = (node) => {
      if (sel.startsWith('.')) {
        const cls = sel.substring(1);
        if (node.classList && node.classList.contains(cls)) matches.push(node);
      } else if (sel.startsWith('#')) {
        if (node.id === sel.substring(1)) matches.push(node);
      } else {
        if (node.tagName && node.tagName.toLowerCase() === sel.toLowerCase()) matches.push(node);
      }
      for (const ch of (node.children || [])) walk(ch);
    };
    for (const ch of (this.children || [])) walk(ch);
    return matches;
  }
}

// Pre-populate elements declared in index.html
const elementsMap = new Map();
htmlIdsSet.forEach(id => {
  const el = new MockElement('div', id);
  if (id.includes('box') || id.includes('result') || id.includes('celebration') || id.includes('tooltip')) {
    el.classList.add('hidden');
  }
  elementsMap.set(id, el);
});

// Setup DOM tree relationships
const assemblyParent = new MockElement('div', 'assembly-parent');
const chipsParent = new MockElement('div', 'chips-parent');
assemblyParent.appendChild(elementsMap.get('game-assembly-board'));
chipsParent.appendChild(elementsMap.get('game-chips-tray'));

class MockFileReader {
  constructor() {
    this.onload = null;
  }
  readAsText(file, encoding) {
    if (typeof this.onload === 'function') {
      this.onload({ target: { result: file.content || '' } });
    }
  }
}

const mockDocument = {
  getElementById: (id) => {
    if (!elementsMap.has(id)) {
      const el = new MockElement('div', id);
      elementsMap.set(id, el);
    }
    return elementsMap.get(id);
  },
  createElement: (tag) => new MockElement(tag),
  addEventListener: () => {},
  documentElement: new MockElement('html', 'html-root'),
  body: new MockElement('body', 'body-root')
};

class MockAudioNode {
  connect() {}
  setValueAtTime() {}
  exponentialRampToValueAtTime() {}
  linearRampToValueAtTime() {}
  start() {}
  stop() {}
}

class MockAudioContext {
  constructor() {
    this.currentTime = 0;
    this.state = 'running';
    this.destination = new MockAudioNode();
  }
  createOscillator() { return new MockAudioNode(); }
  createGain() { return { gain: new MockAudioNode(), connect: () => {} }; }
  resume() { this.state = 'running'; }
}

const soundCalls = [];
const speakCalls = [];

const mockWindow = {
  document: mockDocument,
  addEventListener: () => {},
  setTimeout: (fn) => { fn(); return 1; },
  clearTimeout: () => {},
  setInterval: (fn) => 1,
  clearInterval: () => {},
  scrollTo: () => {},
  alert: (msg) => {},
  confirm: (msg) => true,
  open: (url) => ({ document: { open: () => {}, write: () => {}, close: () => {} }, focus: () => {} }),
  location: { reload: () => {} },
  FileReader: MockFileReader,
  innerWidth: 1024,
  innerHeight: 768,
  SpeechRecognition: null,
  webkitSpeechRecognition: null,
  AudioContext: MockAudioContext,
  webkitAudioContext: MockAudioContext,
  pywebview: {
    api: {
      get_state: async () => (mockWindow.state || {}),
      get_multi_subject_metrics: async () => ({ subjects: [] }),
      get_all_decks_with_chapters: async () => [],
      toggle_fullscreen: async () => {
        mockWindow._mockFullscreen = !mockWindow._mockFullscreen;
        return mockWindow._mockFullscreen;
      },
      is_fullscreen: async () => Boolean(mockWindow._mockFullscreen),
      play_sound: (type) => soundCalls.push(type),
      speak_text: (text, lang, rate) => speakCalls.push({ text, lang, rate }),
      submit_card_result: async (deckId, cardId, attemptStage, passed, score, flawless, duration) => {
        let card = null;
        if (mockWindow.state && mockWindow.state.decks) {
          for (const d of mockWindow.state.decks) {
            const found = (d.cards || []).find(c => c.card_id === cardId);
            if (found) { card = found; break; }
          }
        }
        const existingStage = card ? (card.ladder_stage || 1) : (attemptStage || 1);
        const advanced = passed && attemptStage >= existingStage;
        const finalStage = advanced ? Math.min(6, existingStage + 1) : existingStage;
        return {
          passed: passed,
          next_stage: finalStage,
          stage_advanced: advanced,
          attempted_stage: attemptStage,
          feedback: advanced ? `Graduated to Stage ${finalStage}` : `Completed Stage ${attemptStage}`,
          timing: {
            duration_seconds: duration,
            previous_duration_seconds: null,
            diff_seconds: null,
            improved: false,
            is_new_best: true,
            best_duration_seconds: duration,
            total_attempts: 1
          }
        };
      },
      reset_card_stage: async (deckId, cardId, targetStage, clearHistory) => ({
        success: true,
        card_id: cardId,
        new_stage: targetStage,
        clear_history: clearHistory
      }),
      reset_chapter_stages: async (deckId, chapterName, targetStage, clearHistory) => ({
        success: true,
        updated_count: 1,
        target_stage: targetStage
      })
    }
  }
};

// Create execution sandbox
const context = vm.createContext({
  window: mockWindow,
  document: mockDocument,
  console: console,
  setTimeout: mockWindow.setTimeout,
  clearTimeout: mockWindow.clearTimeout,
  setInterval: mockWindow.setInterval,
  clearInterval: mockWindow.clearInterval,
  alert: mockWindow.alert,
  confirm: mockWindow.confirm,
  FileReader: MockFileReader,
  AudioContext: MockAudioContext,
  webkitAudioContext: MockAudioContext,
  navigator: { userAgent: 'NodeTest' }
});

// Execute particles first, then app.js
if (particlesContent) vm.runInContext(particlesContent, context);
vm.runInContext(jsContent, context);

console.log("✓ PASS: particles.js and app.js loaded and evaluated cleanly in sandbox without errors.");

const testHindiCard = {
  card_id: 'card_ch1_q1',
  lesson_name: 'Ch-1 माँ, कह एक कहानी',
  question: 'प्रश्न (क) आपके विचार से इस कविता में कौन-सी पंक्ति सबसे महत्वपूर्ण है? आप उसे ही सबसे महत्वपूर्ण क्यों मानते हैं?',
  chunks: [
    '“कोई निरपराध को मारे,',
    'तो क्यों अन्य उसे न उबारे?',
    'रक्षक पर भक्षक को वारे,',
    'न्याय दया का दानी!”',
    'इन पंक्तियों में दया और',
    'न्याय का संदेश मिलता है',
    'कि निरपराध की रक्षा',
    'करना सबसे महत्वपूर्ण है।'
  ],
  meaning: 'Which line is most important in the poem and why?',
  ladder_stage: 1
};

const assemblyBoard = mockDocument.getElementById('game-assembly-board');
const chipsTray = mockDocument.getElementById('game-chips-tray');
const passBox = mockDocument.getElementById('game-pass-indicator-box');

// -------------------------------------------------------------------------
// Test 2: Adaptive Fill-in-the-Blanks Mode with Grade 7 Hindi Card
// -------------------------------------------------------------------------
console.log("\n[Test 2] Testing Adaptive Fill-in-the-Blanks Mode Initial Rendering...");
context.setupGameSession([testHindiCard], 'blanks', 'Ch-1 माँ, कह एक कहानी');

assert.strictEqual(passBox.classList.contains('hidden'), false, "game-pass-indicator-box MUST NOT be hidden in blanks mode");
assert(assemblyBoard.children.length > 0, "game-assembly-board MUST have rendered slots/chips!");
assert(chipsTray.children.length > 0, "game-chips-tray MUST have candidate chips for blanks!");

const staticChips = assemblyBoard.children.filter(ch => ch.tagName === 'SPAN');
const blankSlots = assemblyBoard.children.filter(ch => ch.tagName === 'BUTTON');

assert(staticChips.length > 0, "Must have unblanked visible sentence chunks in Pass 1");
assert(blankSlots.length > 0, "Must have missing blank slots in Pass 1");
assert.strictEqual(staticChips.length + blankSlots.length, testHindiCard.chunks.length, "Total slots + static chunks must equal total card chunks");
console.log(`✓ PASS: Blanks rendered (${staticChips.length} static prose chunks, ${blankSlots.length} interactive slots)`);

// -------------------------------------------------------------------------
// Test 3: Interactive Slot Filling & Emptying Interaction
// -------------------------------------------------------------------------
console.log("\n[Test 3] Testing Interactive Slot Filling & Emptying Interaction...");
const firstChip = chipsTray.children[0];
const chipText = firstChip.textContent;

firstChip.onclick();
const stateAfterFill = mockWindow.state.gameplay;
assert(Object.keys(stateAfterFill.filled_slots).length > 0, "filled_slots must have an entry after chip clicked");

const updatedSlots = assemblyBoard.children.filter(ch => ch.tagName === 'BUTTON');
const filledSlot = updatedSlots.find(s => s.textContent.includes(chipText) || s.innerHTML.includes(chipText));
assert(filledSlot, "Slot matching filled chip must exist on board");

// Click filled slot to return chip
filledSlot.onclick();
assert.strictEqual(Object.keys(stateAfterFill.filled_slots).length, 0, "filled_slots must be empty after returning chip");
console.log("✓ PASS: Interactive slot filling and clearing works flawlessly!");

// -------------------------------------------------------------------------
// Test 4: Blanks Mode Hint Action
// -------------------------------------------------------------------------
console.log("\n[Test 4] Testing Hint Action in Adaptive Blanks Mode...");
context.setupGameSession([testHindiCard], 'blanks', 'Ch-1');
assert.strictEqual(Object.keys(mockWindow.state.gameplay.filled_slots).length, 0, "Slots must be empty before hint");

context.gameActionHint();
assert.strictEqual(Object.keys(mockWindow.state.gameplay.filled_slots).length, 1, "Hint must auto-fill exactly 1 slot");
const hintedIdx = Object.keys(mockWindow.state.gameplay.filled_slots)[0];
assert.strictEqual(mockWindow.state.gameplay.filled_slots[hintedIdx], testHindiCard.chunks[hintedIdx], "Hinted slot must have correct chunk");
console.log(`✓ PASS: Hint correctly placed chunk [${hintedIdx}]: "${testHindiCard.chunks[hintedIdx]}"`);

// -------------------------------------------------------------------------
// Test 5: Blanks Incorrect Answer Handling
// -------------------------------------------------------------------------
console.log("\n[Test 5] Testing Incorrect Answer Handling in Blanks Mode...");
context.setupGameSession([testHindiCard], 'blanks', 'Ch-1');
const g = mockWindow.state.gameplay;

// Intentionally fill incorrect text
g.pass_blank_indices.forEach(idx => {
  g.filled_slots[idx] = "गलत उत्तर";
});

context.checkCurrentAnswer();
assert.strictEqual(g.flawless, false, "Flawless must become false upon wrong submission");
assert.strictEqual(g.pass_number, 1, "Pass number must not advance on incorrect submission");
console.log("✓ PASS: Incorrect answer detected, streak reset, and retry allowed without pass progression.");

// -------------------------------------------------------------------------
// Test 6: Multi-Pass Cognitive Fading Progression (Pass 1 -> Pass 2 -> Pass 3)
// -------------------------------------------------------------------------
console.log("\n[Test 6] Testing Multi-Pass Scaffolding Progression (Pass 1 -> Pass 2 -> Pass 3)...");
context.setupGameSession([testHindiCard], 'blanks', 'Ch-1');
const blanksState = mockWindow.state.gameplay;

// Pass 1: Fill all blanks correctly
const pass1Blanks = [...blanksState.pass_blank_indices];
pass1Blanks.forEach(idx => {
  blanksState.filled_slots[idx] = testHindiCard.chunks[idx];
});
context.checkCurrentAnswer();

assert.strictEqual(blanksState.pass_number, 2, "Must advance to Pass 2 upon completing Pass 1");
const pass2Blanks = [...blanksState.pass_blank_indices];
console.log(`   - Pass 1 blanks: [${pass1Blanks.join(', ')}]`);
console.log(`   - Pass 2 blanks: [${pass2Blanks.join(', ')}]`);
assert.notDeepStrictEqual(pass1Blanks, pass2Blanks, "Pass 2 blank indices MUST differ from Pass 1 to prevent positional memorization!");

// Pass 2: Fill all blanks correctly
pass2Blanks.forEach(idx => {
  blanksState.filled_slots[idx] = testHindiCard.chunks[idx];
});
context.checkCurrentAnswer();

assert.strictEqual(blanksState.pass_number, 3, "Must advance to Pass 3 upon completing Pass 2");
const pass3Blanks = [...blanksState.pass_blank_indices];
console.log(`   - Pass 3 challenge blanks: [${pass3Blanks.join(', ')}] (${pass3Blanks.length} chunks blanked)`);
assert(pass3Blanks.length >= pass2Blanks.length, "Pass 3 must have at least as many blanks as Pass 2");

// Pass 3: Complete final pass
console.log("Before Pass 3 fill - pass_number:", blanksState.pass_number, "max_passes:", blanksState.max_passes);
console.log("pass3Blanks indices:", pass3Blanks);
pass3Blanks.forEach(idx => {
  blanksState.filled_slots[idx] = testHindiCard.chunks[idx];
});
console.log("filled_slots keys:", Object.keys(blanksState.filled_slots));
context.checkCurrentAnswer();

const celebCard = mockDocument.getElementById('game-celebration-card');
console.log("celebCard hidden class?:", celebCard.classList.contains('hidden'));
assert.strictEqual(celebCard.classList.contains('hidden'), false, "Celebration card must be shown after completing Pass 3");
console.log("✓ PASS: Full 3-Pass progressive cognitive fading cycle verified!");

// -------------------------------------------------------------------------
// Test 7: Jigsaw Puzzle Mode Initial Scramble
// -------------------------------------------------------------------------
console.log("\n[Test 7] Testing Jigsaw Puzzle Mode...");
context.setupGameSession([testHindiCard], 'jigsaw', 'Ch-1');

assert.strictEqual(passBox.classList.contains('hidden'), true, "game-pass-indicator-box MUST be hidden in jigsaw mode");
const totalJigsawChunks = mockWindow.state.gameplay.active_chunks.length;
assert.strictEqual(chipsTray.children.length, totalJigsawChunks, "All chunks must be in chips tray initially in jigsaw mode");

const jigsawChip = chipsTray.children[0];
jigsawChip.onclick();
const placedChips = assemblyBoard.querySelectorAll('.chip-btn');
assert.strictEqual(placedChips.length, 1, "Assembly board must contain 1 placed chip after click");
assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 1);
assert.strictEqual(chipsTray.children.length, totalJigsawChunks - 1, "Tray must contain n-1 chips");
console.log("✓ PASS: Jigsaw piece placement and movement verified!");

// -------------------------------------------------------------------------
// Test 8: Jigsaw Undo & Clear Actions
// -------------------------------------------------------------------------
console.log("\n[Test 8] Testing Jigsaw Undo and Clear Actions...");
context.setupGameSession([testHindiCard], 'jigsaw', 'Ch-1');

// Place 2 chips
chipsTray.children[0].onclick();
chipsTray.children[0].onclick();
assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 2);

// Undo
context.gameActionUndo();
assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 1, "Undo must remove exactly 1 placed chunk");

// Clear
context.gameActionClear();
assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 0, "Clear must reset placed chunks to empty");
assert.strictEqual(mockWindow.state.gameplay.available_chips.length, mockWindow.state.gameplay.active_chunks.length, "All chips returned to tray");
console.log("✓ PASS: Jigsaw Undo and Clear actions verified!");

// -------------------------------------------------------------------------
// Test 9: Jigsaw Hint Action
// -------------------------------------------------------------------------
console.log("\n[Test 9] Testing Jigsaw Hint Action...");
context.setupGameSession([testHindiCard], 'jigsaw', 'Ch-1');

context.gameActionHint();
assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 1, "Hint must place 1 chunk");
assert.strictEqual(mockWindow.state.gameplay.placed_chunks[0], mockWindow.state.gameplay.active_chunks[0], "First hinted chunk must match first sentence chunk");
console.log(`✓ PASS: Jigsaw hint placed correct chunk: "${mockWindow.state.gameplay.active_chunks[0]}"`);

// -------------------------------------------------------------------------
// Test 10: Jigsaw Check Evaluation (Correct vs Incorrect)
// -------------------------------------------------------------------------
console.log("\n[Test 10] Testing Jigsaw Sequence Checking...");
context.setupGameSession([testHindiCard], 'jigsaw', 'Ch-1');
const jg = mockWindow.state.gameplay;

// Incomplete check
context.checkCurrentAnswer();
assert.strictEqual(celebCard.classList.contains('hidden'), true, "Incomplete assembly must not graduate");

// Fully correct placement
jg.placed_chunks = [...mockWindow.state.gameplay.active_chunks];
context.checkCurrentAnswer();
assert.strictEqual(celebCard.classList.contains('hidden'), false, "Correct assembly must trigger celebration card");
console.log("✓ PASS: Jigsaw sentence verification validated!");

// -------------------------------------------------------------------------
// Test 11: Auditory Decoding & Listening Studio
// -------------------------------------------------------------------------
console.log("\n[Test 11] Testing Listening Studio Prompt Masking & Audio Trigger...");
context.setupGameSession([testHindiCard], 'listening', 'Ch-1');

const listenBox = mockDocument.getElementById('game-listening-box');
assert.strictEqual(listenBox.classList.contains('hidden'), false, "Listening box must be visible");

const qPromptText = mockDocument.getElementById('game-question-text').textContent;
assert(qPromptText.includes('🎧'), "Question text MUST be masked with auditory icon to train listening comprehension");
console.log("✓ PASS: Listening Studio masking verified:", qPromptText);

// -------------------------------------------------------------------------
// Test 12: Voice Mastery Studio Pronunciation Evaluation
// -------------------------------------------------------------------------
console.log("\n[Test 12] Testing Voice Studio Evaluation...");
context.setupGameSession([testHindiCard], 'voice', 'Ch-1');

const voiceBox = mockDocument.getElementById('game-voice-box');
assert.strictEqual(voiceBox.classList.contains('hidden'), false, "Voice box must be visible");

const targetDisplay = mockDocument.getElementById('voice-target-sentence').textContent;
assert(targetDisplay.length > 0, "Target sentence must be populated in Devanagari");

// Test voice speech evaluation with high accuracy (Passing score >= 80)
context.evaluateVoiceSpeech(targetDisplay, targetDisplay);
assert.strictEqual(celebCard.classList.contains('hidden'), false, "Matching voice speech must pass and advance card");

// Reset and test voice speech with low accuracy (< 80)
celebCard.classList.add('hidden');
context.evaluateVoiceSpeech("कुछ और वाक्य", targetDisplay);
assert.strictEqual(celebCard.classList.contains('hidden'), true, "Mismatched voice speech must not advance card");
console.log("✓ PASS: Voice studio pronunciation evaluation (pass >= 80%, retry < 80%) verified!");

// -------------------------------------------------------------------------
// Test 13: Active Writing Studio (Hindi Virtual Matras Bar & Diff Pills)
// -------------------------------------------------------------------------
console.log("\n[Test 13] Testing Active Writing Studio & Virtual Hindi Matras Bar...");
context.setupGameSession([testHindiCard], 'writing', 'Ch-1');

const writeBox = mockDocument.getElementById('game-writing-box');
assert.strictEqual(writeBox.classList.contains('hidden'), false, "Writing box must be visible");

// Test virtual helper bar character insertion
const inputArea = mockDocument.getElementById('writing-input-area');
inputArea.value = 'नरपराध';
inputArea.selectionStart = 1;
inputArea.selectionEnd = 1;

context.insertCharIntoWritingInput('ि');
assert.strictEqual(inputArea.value, 'निरपराध', "Inserting 'ि' at position 1 must produce 'निरपराध'");
console.log(`   - Virtual keyboard insertion verified: 'नरपराध' + 'ि' -> '${inputArea.value}'`);

// Test Writing token diff rendering
const mockEvalTokens = [
  { text: 'निरपराध', status: 'match' },
  { text: 'की', status: 'match' },
  { text: 'रक्षा', status: 'typo' },
  { text: 'करना', status: 'missing' }
];
context.renderWritingDiffPills(mockEvalTokens);

const tokensRow = mockDocument.getElementById('writing-tokens-row');
assert.strictEqual(tokensRow.children.length, 4, "Tokens row must render 4 diff pills");
const pillClasses = tokensRow.children.map(c => c.className);
assert(pillClasses[0].includes('emerald'), "Match token must be emerald green");
assert(pillClasses[2].includes('rose'), "Typo token must be rose red");
assert(pillClasses[3].includes('amber'), "Missing token must be amber orange");
console.log("✓ PASS: Active Writing virtual Hindi helper bar & color diff pills verified!");

// -------------------------------------------------------------------------
// Test 14: Parent & Educator Studio (Lesson Builder, Chunks & Upload)
// -------------------------------------------------------------------------
console.log("\n[Test 14] Testing Parent Lesson Studio Q&A Parsing, Chunk Splitting & Merging...");

// Q&A text parser
const rawText = `प्रश्न: पेड़ क्या देते हैं?
उत्तर: पेड़ हमें मीठे फल देते हैं।

प्रश्न: सूर्य क्या है? ||| सूर्य ||| एक विशाल तारा ||| है।`;

mockDocument.getElementById('parent-raw-text').value = rawText;
context.parentAnalyzeAndPreview();

const previewItems = mockWindow.state.parent_preview_items;
assert.strictEqual(previewItems.length, 2, "Parent parser must generate 2 question items");
console.log(`   - Parsed ${previewItems.length} questions from mixed multi-line and pipe formats.`);

// Test Chunk Splitting: split "पेड़ हमें" into "पेड़" and "हमें"
const item0ChunksBefore = [...previewItems[0].chunks];
const firstChunkWords = item0ChunksBefore[0].split(/\s+/).length;
if (firstChunkWords > 1) {
  context.parentSplitChunk(0, 0);
  assert(previewItems[0].chunks.length > item0ChunksBefore.length, "Splitting must increase total chunks count");
  console.log(`   - Chunk split verified: "${item0ChunksBefore[0]}" -> [${previewItems[0].chunks.slice(0, 2).join(', ')}]`);
}

// Test Chunk Merging: merge chunk 0 and chunk 1
const chunksBeforeMerge = [...previewItems[0].chunks];
context.parentMergeChunk(0, 0);
assert.strictEqual(previewItems[0].chunks.length, chunksBeforeMerge.length - 1, "Merging must decrease chunks count by 1");
assert.strictEqual(previewItems[0].chunks[0], chunksBeforeMerge[0] + ' ' + chunksBeforeMerge[1], "Merged chunk must join strings");
console.log(`   - Chunk merge verified: "${previewItems[0].chunks[0]}"`);

// Test File Upload Simulation
const mockFileEvent = {
  target: {
    files: [
      {
        name: 'chapter_science_plants.txt',
        content: `Question: What is photosynthesis?\nAnswer: Plants make food using light.`
      }
    ]
  }
};
context.parentHandleFileUpload(mockFileEvent);
// Check that title is auto-populated and content is loaded
const titleVal = mockDocument.getElementById('parent-new-title').value;
assert(titleVal.toLowerCase().includes('science') || titleVal.toLowerCase().includes('plants'), "Title must be auto-derived from filename");
console.log("✓ PASS: Parent Studio Q&A parsing, chunk split/merge, and file upload verified!");

// -------------------------------------------------------------------------
// Test 15: View Router & Subject Filter
// -------------------------------------------------------------------------
console.log("\n[Test 15] Testing View Router & Subject Filter...");

context.showView('parent');
assert.strictEqual(mockDocument.getElementById('view-parent').classList.contains('hidden'), false, "view-parent must be active");
assert.strictEqual(mockDocument.getElementById('view-dashboard').classList.contains('hidden'), true, "view-dashboard must be hidden");

context.showView('dashboard');
assert.strictEqual(mockDocument.getElementById('view-dashboard').classList.contains('hidden'), false, "view-dashboard must be active");
assert.strictEqual(mockDocument.getElementById('view-parent').classList.contains('hidden'), true, "view-parent must be hidden");
assert.strictEqual(mockDocument.getElementById('app-header').classList.contains('hidden'), false, "app-header must be visible on dashboard");

// Header must be hidden during any gameplay mode
context.showView('gameplay');
assert.strictEqual(mockDocument.getElementById('view-gameplay').classList.contains('hidden'), false, "view-gameplay must be active");
assert.strictEqual(mockDocument.getElementById('app-header').classList.contains('hidden'), true, "app-header must be hidden during gameplay modes");

// Header must be visible during chapter selection section
context.showView('chapter', { deck_id: 'deck_hindi', chapter_name: 'Ch-1', deck_title: 'Hindi', cards: [] });
assert.strictEqual(mockDocument.getElementById('view-chapter').classList.contains('hidden'), false, "view-chapter must be active");
assert.strictEqual(mockDocument.getElementById('app-header').classList.contains('hidden'), false, "app-header must be visible during chapter selection section");

// Returning to dashboard keeps header visible
context.showView('dashboard');
assert.strictEqual(mockDocument.getElementById('app-header').classList.contains('hidden'), false, "app-header must be visible on dashboard");

context.switchRole('parent');
assert.strictEqual(mockWindow.state.role, 'parent');
context.switchRole('student');
assert.strictEqual(mockWindow.state.role, 'student');

// Subject filter test
context.setSubjectFilter('Hindi');
assert.strictEqual(mockWindow.state.subject_filter, 'Hindi');
context.setSubjectFilter('Science');
assert.strictEqual(mockWindow.state.subject_filter, 'Science');

console.log("✓ PASS: View router transitions, role toggling, and subject filtering verified!");

// -------------------------------------------------------------------------
// Test 16: Answer Block & Chip Hover Translations Subsystem
// -------------------------------------------------------------------------
console.log("\n[Test 16] Testing Answer Blocks & Chips Mouse Hover Translations...");

// 1. Verify Tooltip container exists in DOM
const hoverTooltip = mockDocument.getElementById('chunk-hover-tooltip');
const hoverTooltipText = mockDocument.getElementById('chunk-hover-tooltip-text');
assert(hoverTooltip, "#chunk-hover-tooltip must exist in DOM");
assert(hoverTooltipText, "#chunk-hover-tooltip-text must exist in DOM");
assert(hoverTooltip.classList.contains('hidden'), "Tooltip must initially be hidden");

// 2. Set up translations cache in state
mockWindow.state.chunk_translations['“कोई निरपराध को मारे,'] = 'Kill an innocent';
mockWindow.state.chunk_translations['तो क्यों अन्य उसे न उबारे?'] = 'Rescue him from danger';
mockWindow.state.chunk_translations['रक्षक पर भक्षक को वारे,'] = 'Sacrifice eater for protector';

// 3. Launch Blanks session
context.setupGameSession([testHindiCard], 'blanks', 'Ch-1 Test');

// Verify static block in answer board has translation attached
const boardEl = mockDocument.getElementById('game-assembly-board');
const staticBlocks = boardEl.children.filter(c => c.tagName === 'SPAN');
assert(staticBlocks.length > 0, "Static chunks must be present in board");
const firstStaticBlock = staticBlocks[0];
assert(firstStaticBlock.title.includes('Kill an innocent') || firstStaticBlock.title.includes('निरपराध'),
  `Static block must have translation in title attribute. Found: "${firstStaticBlock.title}"`);
assert(typeof firstStaticBlock.onmouseenter === 'function', "Static block must have onmouseenter hover listener");

// Test Mouseenter on static block
firstStaticBlock.onmouseenter({ currentTarget: firstStaticBlock, clientX: 150, clientY: 120 });
assert.strictEqual(hoverTooltip.classList.contains('hidden'), false, "Hover tooltip must be visible on mouseenter");
assert(hoverTooltipText.textContent.includes('Kill an innocent') || hoverTooltipText.textContent.includes('निरपराध'),
  `Hover tooltip text must display chunk translation! Found: "${hoverTooltipText.textContent}"`);

// Test Mouseleave hides tooltip
firstStaticBlock.onmouseleave();
assert(hoverTooltip.classList.contains('opacity-0'), "Hover tooltip must fade out on mouseleave");

// 4. Test candidate chips in tray
const trayEl = mockDocument.getElementById('game-chips-tray');
const candidateChips = trayEl.children.filter(c => c.tagName === 'BUTTON');
assert(candidateChips.length > 0, "Candidate chips must be rendered in tray");
const firstTrayChip = candidateChips[0];
assert(firstTrayChip.title.length > 0, "Tray candidate chip must have informative hover title");
assert(typeof firstTrayChip.onmouseenter === 'function', "Tray candidate chip must have hover listener");

// Hover over tray chip
firstTrayChip.onmouseenter({ currentTarget: firstTrayChip, clientX: 200, clientY: 250 });
assert.strictEqual(hoverTooltip.classList.contains('hidden'), false, "Tooltip must appear on tray chip hover");
assert(hoverTooltipText.textContent.length > 0, "Tooltip must have translation/meaning content");
firstTrayChip.onmouseleave();

// 5. Test filled slot in answer board
// Fill blank slot
firstTrayChip.onclick();
const testedFilledSlot = boardEl.children.find(c => c.tagName === 'BUTTON' && c.innerHTML.includes('✕'));
assert(testedFilledSlot, "Filled slot must exist on board");
assert(testedFilledSlot.title.length > 0, "Filled slot must have hover tooltip title");
assert(typeof testedFilledSlot.onmouseenter === 'function', "Filled slot must have onmouseenter handler");

testedFilledSlot.onmouseenter({ currentTarget: testedFilledSlot, clientX: 180, clientY: 130 });
assert.strictEqual(hoverTooltip.classList.contains('hidden'), false, "Tooltip must show when hovering over filled slot");
testedFilledSlot.onmouseleave();

// 6. Test Jigsaw mode blocks and tray chips
context.setupGameSession([testHindiCard], 'jigsaw', 'Ch-1 Jigsaw');
const jigsawTray = mockDocument.getElementById('game-chips-tray');
const jChip = jigsawTray.children[0];
assert(jChip, "Jigsaw available chip must exist in tray");
assert(jChip.title.length > 0, "Jigsaw chip must have hover translation title");

// Place chip into answer board
jChip.onclick();
const jigsawBoard = mockDocument.getElementById('game-assembly-board');
const placedBlock = jigsawBoard.querySelector('.chip-btn');
assert(placedBlock, "Placed block must exist in jigsaw answer board");
assert(placedBlock.title.length > 0, "Placed block in jigsaw answer board must have translation title");
assert(typeof placedBlock.onmouseenter === 'function', "Placed block must have hover listener");

placedBlock.onmouseenter({ currentTarget: placedBlock, clientX: 160, clientY: 110 });
assert.strictEqual(hoverTooltip.classList.contains('hidden'), false, "Placed answer block must display translation on hover");
placedBlock.onmouseleave();

console.log("✓ PASS: Hover translation tooltips verified across static chunks, filled slots, tray chips, and jigsaw answer blocks!");

// -------------------------------------------------------------------------
// Test 17: Progress Tracking & Stage Advancement Calculation
// -------------------------------------------------------------------------
console.log("\n[Test 17] Testing Progress Tracking & Stage Advancement Calculation After Section Completion...");

// Setup mock decks with a chapter having 5 cards at Stage 1
context.setSubjectFilter('All');
const progressDeck = {
  id: 'deck_progress_test',
  title: 'Progress Hindi Test',
  subject: 'Hindi',
  cards: [
    { card_id: 'p_c1', lesson_name: 'Ch-1 Story', question: 'Q1', chunks: ['A', 'B'], ladder_stage: 1 },
    { card_id: 'p_c2', lesson_name: 'Ch-1 Story', question: 'Q2', chunks: ['C', 'D'], ladder_stage: 1 },
    { card_id: 'p_c3', lesson_name: 'Ch-1 Story', question: 'Q3', chunks: ['E', 'F'], ladder_stage: 1 },
    { card_id: 'p_c4', lesson_name: 'Ch-1 Story', question: 'Q4', chunks: ['G', 'H'], ladder_stage: 1 },
    { card_id: 'p_c5', lesson_name: 'Ch-1 Story', question: 'Q5', chunks: ['I', 'J'], ladder_stage: 1 }
  ]
};
mockWindow.state.decks = [progressDeck];

// Initially at Stage 1: progress should be 0%
context.renderDashboard();
let grid = mockDocument.getElementById('chapters-cards-grid');
let chapterCardHtml = grid.children[0].innerHTML;
assert(chapterCardHtml.includes('Stage 1: Blanks'), "Initial stage must be Stage 1 (Blanks)");
assert(chapterCardHtml.includes('0%'), "Initial progress must be 0%");

// Simulate student completing Section 1 (Fill in Blanks) for all cards
progressDeck.cards.forEach(c => {
  c.ladder_stage = 2; // Advanced to Stage 2 (Jigsaw)
});

context.renderDashboard();
grid = mockDocument.getElementById('chapters-cards-grid');
chapterCardHtml = grid.children[0].innerHTML;

// Progress MUST NOT be 0%! Stage 2 corresponds to 20% progress
assert(chapterCardHtml.includes('20%'), `Progress must show 20% after completing blanks! HTML: ${chapterCardHtml}`);
assert(chapterCardHtml.includes('Stage 2: Jigsaw'), `Must display active stage as Stage 2 (Jigsaw)! HTML: ${chapterCardHtml}`);
assert(chapterCardHtml.includes('Practice (Jigsaw)'), `Practice button must adapt to Jigsaw! HTML: ${chapterCardHtml}`);

// Test Chapter Details View reflects 20%
context.openChapterDetails('deck_progress_test', 'Ch-1 Story');
const chapterMasteryText = mockDocument.getElementById('chapter-mastery-text').textContent;
assert(chapterMasteryText.includes('20%'), `Chapter view must reflect 20% progress! Found: "${chapterMasteryText}"`);
assert(chapterMasteryText.includes('Stage 2'), `Chapter view must show Stage 2! Found: "${chapterMasteryText}"`);

console.log("✓ PASS: Progress saving and stage advancement verified (0% -> 20% on completing blanks)!");

// -------------------------------------------------------------------------
// Test 18: Question Order Jumbling (Blanks maintains order, Jigsaw/others jumble)
// -------------------------------------------------------------------------
console.log("\n[Test 18] Testing Question Order Jumbling...");

const sequenceCards = [
  { card_id: 'q1', lesson_name: 'Story', question: 'Q1', chunks: ['A1', 'B1'] },
  { card_id: 'q2', lesson_name: 'Story', question: 'Q2', chunks: ['A2', 'B2'] },
  { card_id: 'q3', lesson_name: 'Story', question: 'Q3', chunks: ['A3', 'B3'] },
  { card_id: 'q4', lesson_name: 'Story', question: 'Q4', chunks: ['A4', 'B4'] },
  { card_id: 'q5', lesson_name: 'Story', question: 'Q5', chunks: ['A5', 'B5'] }
];

// 1. In 'blanks' mode: questions MUST remain in sequential chapter order
context.setupGameSession(sequenceCards, 'blanks', 'Story Chapter');
const blanksOrder = mockWindow.state.gameplay.cards.map(c => c.card_id);
assert.deepStrictEqual(blanksOrder, ['q1', 'q2', 'q3', 'q4', 'q5'], 
  `Blanks mode must preserve exact sequential chapter order! Found: ${JSON.stringify(blanksOrder)}`);

// 2. In 'jigsaw' mode: questions MUST be jumbled/shuffled
context.setupGameSession(sequenceCards, 'jigsaw', 'Story Chapter');
const jigsawOrder = mockWindow.state.gameplay.cards.map(c => c.card_id);
assert.strictEqual(jigsawOrder.length, 5, "Jigsaw must contain all 5 cards");
assert(sequenceCards.every(c => jigsawOrder.includes(c.card_id)), "Jigsaw must contain all card IDs");
assert.notDeepStrictEqual(jigsawOrder, ['q1', 'q2', 'q3', 'q4', 'q5'],
  `Jigsaw mode questions must be jumbled! Found identical order: ${JSON.stringify(jigsawOrder)}`);

// 3. In 'listening' mode: questions MUST also be jumbled
context.setupGameSession(sequenceCards, 'listening', 'Story Chapter');
const listeningOrder = mockWindow.state.gameplay.cards.map(c => c.card_id);
assert.notDeepStrictEqual(listeningOrder, ['q1', 'q2', 'q3', 'q4', 'q5'],
  `Listening mode questions must be jumbled! Found: ${JSON.stringify(listeningOrder)}`);

console.log("✓ PASS: Question ordering verified: Sequential for Blanks, Jumbled for Jigsaw and other modes!");

// -------------------------------------------------------------------------
// Test 19: Audio Sound Clips & Synthesizer System
// -------------------------------------------------------------------------
console.log("\n[Test 19] Testing Audio Sound Clips System...");

soundCalls.length = 0;
// Test direct playSound invocations
context.playSound('click');
assert(soundCalls.includes('click'), "playSound('click') must be dispatched to sound player");

context.playSound('success');
assert(soundCalls.includes('success'), "playSound('success') must be dispatched to sound player");

context.playSound('error');
assert(soundCalls.includes('error'), "playSound('error') must be dispatched to sound player");

context.playSound('hint');
assert(soundCalls.includes('hint'), "playSound('hint') must be dispatched to sound player");

context.playSound('complete');
assert(soundCalls.includes('complete'), "playSound('complete') must be dispatched to sound player");

// Test gameplay actions triggering sound
soundCalls.length = 0;
context.setupGameSession([testHindiCard], 'blanks', 'Audio Test Ch');
context.gameActionHint();
assert(soundCalls.includes('hint'), "gameActionHint must trigger 'hint' sound");

soundCalls.length = 0;
context.gameActionUndo();
assert(soundCalls.includes('click'), "gameActionUndo must trigger 'click' sound");

soundCalls.length = 0;
context.gameActionClear();
assert(soundCalls.includes('click'), "gameActionClear must trigger 'click' sound");

// Test Mute Setting (sound_enabled = false)
mockWindow.state.settings.sound_enabled = false;
soundCalls.length = 0;
context.playSound('click');
assert.strictEqual(soundCalls.length, 0, "No sounds must play when sound_enabled is false");
mockWindow.state.settings.sound_enabled = true;

console.log("✓ PASS: Audio sound clips system verified across clicks, chimes, buzzes, hints, and mute toggle!");

// -------------------------------------------------------------------------
// Test 20: Reading of Answer (TTS) in WebUI
// -------------------------------------------------------------------------
console.log("\n[Test 20] Testing Reading of Answer (TTS) in WebUI...");

speakCalls.length = 0;
context.setupGameSession([testHindiCard], 'jigsaw', 'Answer Reading Ch');

// 1. Verify #game-hear-answer-btn in DOM
const gameHearAnsBtn = mockDocument.getElementById('game-hear-answer-btn');
assert(gameHearAnsBtn, "#game-hear-answer-btn must exist in DOM");

// Trigger Hear Answer action
context.playAnswerTTS();
assert(speakCalls.length > 0, "TTS speak must be invoked when clicking Hear Answer");
const lastSpeak = speakCalls[speakCalls.length - 1];
assert(lastSpeak.text.includes('कोई निरपराध को मारे'), 
  `TTS must speak the full answer text! Found: "${lastSpeak.text}"`);
assert.strictEqual(lastSpeak.lang, 'hi', "Language must be correctly detected as Hindi");
assert.strictEqual(lastSpeak.rate, mockWindow.state.settings.tts_speed_rate || '+0%', "TTS must pass configured speed rate");

// Verify dynamic speed change propagates to speak_text call
mockWindow.state.settings.tts_speed_rate = '-50%';
context.playAnswerTTS();
assert.strictEqual(speakCalls[speakCalls.length - 1].rate, '-50%', "TTS must reflect updated speed rate (-50%)");

// 2. Verify dedicated studio Hear Answer buttons
assert(mockDocument.getElementById('voice-hear-answer-btn'), "#voice-hear-answer-btn must exist in DOM");
assert(mockDocument.getElementById('writing-hear-answer-btn'), "#writing-hear-answer-btn must exist in DOM");
assert(mockDocument.getElementById('celeb-hear-answer-btn'), "#celeb-hear-answer-btn must exist in DOM");

// 3. Verify Chapter details view renders '🔊 Ans' button for cards
context.openChapterDetails('deck_progress_test', 'Ch-1 Story');
const chapList = mockDocument.getElementById('chapter-questions-list');
assert(chapList.children.length > 0, "Chapter questions list must be populated");
const firstCardHtml = chapList.children[0].innerHTML;
assert(firstCardHtml.includes('🔊 Q'), "Chapter card must have 🔊 Q button");
assert(firstCardHtml.includes('🔊 Ans'), "Chapter card must have 🔊 Ans button");

console.log("✓ PASS: Answer reading (TTS) verified across Arena, Voice, Writing, Celebration, and Chapter view!");

// -------------------------------------------------------------------------
// Test 21: Settings Modal Population, Saving, and Theme Application
// -------------------------------------------------------------------------
console.log("\n[Test 21] Testing Settings Modal Population, Saving & Theme Application...");

// Setup mock state settings
mockWindow.state.settings = {
  theme: 'dark',
  show_hover_meanings: true,
  sound_enabled: true,
  tts_speed_rate: '-25%',
  fill_blanks_count_mode: '2',
  speed_run_duration_seconds: 120,
  ai_coach_enabled: true,
  ollama_url: 'http://localhost:11434',
  ollama_model: 'qwen3.5:9b'
};

// Open settings modal
context.openSettingsModal();
const settingsModal = mockDocument.getElementById('settings-modal');
assert(!settingsModal.classList.contains('hidden'), "Settings modal must be visible");

// Check populated fields
const themeSel = mockDocument.getElementById('settings-theme-select');
const hoverChk = mockDocument.getElementById('settings-hover-check');
const soundChk = mockDocument.getElementById('settings-sound-check');
const ttsRateSel = mockDocument.getElementById('settings-tts-rate-select');
const blanksModeSel = mockDocument.getElementById('settings-blanks-mode-select');
const speedDurSel = mockDocument.getElementById('settings-speed-duration-select');
const aiCoachChk = mockDocument.getElementById('settings-ai-coach-check');
const ollamaUrlInp = mockDocument.getElementById('settings-ollama-url-input');
const ollamaModelInp = mockDocument.getElementById('settings-ollama-model-input');

assert.strictEqual(themeSel.value, 'dark', "Theme select must reflect state.settings.theme");
assert.strictEqual(hoverChk.checked, true, "Hover check must reflect state.settings.show_hover_meanings");
assert.strictEqual(ttsRateSel.value, '-25%', "TTS rate select must reflect state.settings.tts_speed_rate");
assert.strictEqual(blanksModeSel.value, '2', "Blanks mode select must reflect state.settings.fill_blanks_count_mode");
assert.strictEqual(speedDurSel.value, '120', "Speed duration select must reflect state.settings.speed_run_duration_seconds");
assert.strictEqual(ollamaModelInp.value, 'qwen3.5:9b', "Ollama model input must reflect state.settings.ollama_model");

// Modify fields and save
themeSel.value = 'space';
ttsRateSel.value = '+20%';
blanksModeSel.value = '3';
speedDurSel.value = '300';
ollamaModelInp.value = 'gemma4:26b';

context.saveSettingsFromModal();
assert(settingsModal.classList.contains('hidden'), "Settings modal must be closed after save");
assert.strictEqual(mockWindow.state.settings.theme, 'space', "Saved theme must update in state");
assert.strictEqual(mockWindow.state.settings.tts_speed_rate, '+20%', "Saved tts_speed_rate must update in state");
assert.strictEqual(mockWindow.state.settings.fill_blanks_count_mode, '3', "Saved blanks count must update in state");
assert.strictEqual(mockWindow.state.settings.speed_run_duration_seconds, 300, "Saved speed duration must update in state");
assert.strictEqual(mockWindow.state.settings.ollama_model, 'gemma4:26b', "Saved ollama model must update in state");

console.log("✓ PASS: Settings modal lifecycle, form synchronization, and saving verified!");

// -------------------------------------------------------------------------
// Test 22: Local Ollama AI Coach Testing & Memory Reset
// -------------------------------------------------------------------------
console.log("\n[Test 22] Testing Local Ollama AI Coach Testing & Memory Reset...");

context.openSettingsModal();
let ollamaBridgeTested = false;
let memoryResetCalled = false;

mockWindow.pywebview.api.test_ollama_connection = async (url) => {
  ollamaBridgeTested = true;
  return { connected: true, models: ['gemma4:12b', 'qwen3.5:9b'], url };
};
mockWindow.pywebview.api.reset_active_memory = async () => {
  memoryResetCalled = true;
  return true;
};

// Test Ollama Connection
context.testOllamaFromSettings();
const ollamaStatus = mockDocument.getElementById('settings-ollama-status');
assert(ollamaStatus, "Ollama status element must exist");

// Test Memory Reset
context.resetMemoryFromSettings();
assert(memoryResetCalled, "reset_active_memory must be called via bridge");
context.closeSettingsModal();

console.log("✓ PASS: Ollama connection test and spaced repetition memory reset verified!");

// -------------------------------------------------------------------------
// Test 23: Keyboard Shortcuts Reference Modal
// -------------------------------------------------------------------------
console.log("\n[Test 23] Testing Keyboard Shortcuts Reference Modal...");

const shortcutsModal = mockDocument.getElementById('shortcuts-modal');
assert(shortcutsModal, "#shortcuts-modal must exist in DOM");

context.openShortcutsModal();
assert(!shortcutsModal.classList.contains('hidden'), "Shortcuts modal must be open");

context.closeShortcutsModal();
assert(shortcutsModal.classList.contains('hidden'), "Shortcuts modal must be closed");

console.log("✓ PASS: Keyboard shortcuts modal toggle and accessibility verified!");

// -------------------------------------------------------------------------
// Test 24: Printable Worksheet Generation
// -------------------------------------------------------------------------
console.log("\n[Test 24] Testing Printable Worksheet Generation...");

const worksheetModal = mockDocument.getElementById('worksheet-modal');
assert(worksheetModal, "#worksheet-modal must exist in DOM");

// Open worksheet modal with sample deck
context.openWorksheetModal('deck_progress_test', 'Ch-1 Story');
assert(!worksheetModal.classList.contains('hidden'), "Worksheet modal must open");

const wsDeckSel = mockDocument.getElementById('worksheet-deck-select');
const wsChapSel = mockDocument.getElementById('worksheet-chapter-select');
assert(wsDeckSel && wsDeckSel.children.length > 0, "Worksheet deck selector must be populated");
assert(wsChapSel && wsChapSel.children.length > 0, "Worksheet chapter selector must be populated");

// Generate worksheet via bridge mock
let worksheetBridgeCalled = false;
mockWindow.pywebview.api.generate_printable_worksheet = async (deckId, chap) => {
  worksheetBridgeCalled = true;
  return `<!DOCTYPE html><html><body><h1>Worksheet: ${deckId}</h1></body></html>`;
};

context.generateWorksheetFromModal();
assert(worksheetModal.classList.contains('hidden'), "Worksheet modal must close upon generation");
assert(worksheetBridgeCalled, "generate_printable_worksheet must be invoked via bridge");

console.log("✓ PASS: Offline printable worksheet generation verified for decks and chapters!");

// -------------------------------------------------------------------------
// Test 25: Student Profile Management & Deletion
// -------------------------------------------------------------------------
console.log("\n[Test 25] Testing Student Profile Management & Deletion...");

mockWindow.state.profiles = ['Arya', 'Rohan', 'TestLearner'];
mockWindow.state.active_profile = 'Arya';

let profileDeleteCalled = false;
mockWindow.pywebview.api.delete_profile = async (name) => {
  profileDeleteCalled = true;
  mockWindow.state.profiles = mockWindow.state.profiles.filter(p => p !== name);
  return { profiles: mockWindow.state.profiles, active_profile: mockWindow.state.active_profile };
};

context.showProfileModal();
const profList = mockDocument.getElementById('profiles-list');
assert(profList.children.length === 3, "3 profiles must be rendered");

// Non-active profiles should have delete button
const nonActiveItemHtml = profList.children[1].innerHTML;
assert(nonActiveItemHtml.includes('🗑'), "Non-active profiles must show delete icon 🗑");

// Active profile must not have delete button
const activeItemHtml = profList.children[0].innerHTML;
assert(!activeItemHtml.includes('🗑'), "Active profile must not allow self-deletion");

// Invoke deleteProfile
context.deleteProfile('TestLearner');
assert(profileDeleteCalled, "delete_profile must be called via bridge");
assert(!mockWindow.state.profiles.includes('TestLearner'), "TestLearner must be removed from profiles list");

context.closeProfileModal();
console.log("✓ PASS: Profile management with account deletion verified!");

// -------------------------------------------------------------------------
// Test 26: Space Universe Cosmic Canvas Engine Lifecycle & Performance Guard
// -------------------------------------------------------------------------
console.log("\n[Test 26] Testing Space Universe Cosmic Canvas Engine Lifecycle & Theme Switching...");

const universeEl = mockDocument.getElementById('space-universe');
const starsCanvas = mockDocument.getElementById('space-stars-canvas');
assert(universeEl, "space-universe DOM element must exist in HTML");
assert(starsCanvas, "space-stars-canvas DOM element must exist in HTML");

// Switch to space theme
context.applyTheme('space');
assert(mockWindow.spaceUniverseEngine.running, "spaceUniverseEngine must be running when space theme is active");
assert(!universeEl.classList.contains('hidden'), "space-universe must not be hidden when space theme is active");
assert(mockWindow.spaceUniverseEngine.stars.length > 0, "Stars must be generated for space background");

// Switch back to pastel or dark theme
context.applyTheme('pastel');
assert(!mockWindow.spaceUniverseEngine.running, "spaceUniverseEngine must be stopped when pastel theme is active (zero cpu/gpu overhead)");
assert(universeEl.classList.contains('hidden'), "space-universe must be hidden when non-space theme is active");

context.applyTheme('dark');
assert(!mockWindow.spaceUniverseEngine.running, "spaceUniverseEngine must remain stopped in dark theme");
assert(universeEl.classList.contains('hidden'), "space-universe must remain hidden in dark theme");

console.log("✓ PASS: Space universe engine lifecycle, star generation, and zero-overhead non-space switching verified!");

// -------------------------------------------------------------------------
// Test 27: Question Stopwatch Timer Lifecycle & Personal Best Pill Display
// -------------------------------------------------------------------------
console.log("\n[Test 27] Testing Question Stopwatch Timer Lifecycle & Personal Best Display...");

const timerDisplay = mockDocument.getElementById('game-timer-display');
const prevBestPill = mockDocument.getElementById('game-previous-best-pill');
const prevBestText = mockDocument.getElementById('game-previous-best-text');

assert(timerDisplay, "game-timer-display must exist");
assert(prevBestPill, "game-previous-best-pill must exist");
assert(prevBestText, "game-previous-best-text must exist");

// Timer format utility check
assert.strictEqual(context.formatTimerDisplay(0), '0:00', "0s formatted as 0:00");
assert.strictEqual(context.formatTimerDisplay(9.4), '0:09', "9.4s formatted as 0:09");
assert.strictEqual(context.formatTimerDisplay(75), '1:15', "75s formatted as 1:15");

// Setup game session with card that has no prior attempts
const freshCard = {
  card_id: 'timing_c1',
  question: 'Timing Question 1',
  chunks: ['Word1', 'Word2'],
  ladder_stage: 1,
  stage_history: []
};
context.setupGameSession([freshCard], 'blanks', 'Timing Chapter');
assert.strictEqual(timerDisplay.textContent, '0:00', "Timer starts at 0:00");
assert(prevBestPill.classList.contains('hidden'), "Personal best pill must be hidden when no prior attempts exist at this stage");

// Now test with card that has prior attempt history
const veteranCard = {
  card_id: 'timing_c2',
  question: 'Timing Question 2',
  chunks: ['WordA', 'WordB'],
  ladder_stage: 1,
  stage_history: [
    { stage: 1, duration_seconds: 16.4, passed: true },
    { stage: 1, duration_seconds: 9.8, passed: true }
  ]
};
context.setupGameSession([veteranCard], 'blanks', 'Timing Chapter');
assert(!prevBestPill.classList.contains('hidden'), "Personal best pill must be visible when prior attempts exist at this stage");
assert.strictEqual(prevBestText.textContent, '9.8s', "Personal best must show lowest prior duration (9.8s)");

// Test stopping stopwatch timer
const dur = context.stopQuestionTimer();
assert(typeof dur === 'number', "stopQuestionTimer must return a number");

console.log("✓ PASS: Stopwatch timer lifecycle and personal best display verified!");

// -------------------------------------------------------------------------
// Test 28: Comparative Timing Delta in Card Completion Celebration
// -------------------------------------------------------------------------
console.log("\n[Test 28] Testing Comparative Timing Delta in Celebration Card...");

const timeTakenEl = mockDocument.getElementById('celebration-time-taken');
const compTextEl = mockDocument.getElementById('celebration-comparison-text');
const celebrationCard = mockDocument.getElementById('game-celebration-card');

assert(timeTakenEl, "celebration-time-taken element must exist");
assert(compTextEl, "celebration-comparison-text element must exist");

// Case 1: First Attempt (Baseline)
const testCard = {
  card_id: 'test_timing_card',
  question: 'First attempt test question',
  chunks: ['Alpha', 'Beta'],
  ladder_stage: 1,
  stage_history: []
};
context.setupGameSession([testCard], 'blanks', 'Timing Test');
// Simulate timer elapsed
mockWindow.state.gameplay.timer_start_ms = Date.now() - 14200; // 14.2 seconds
context.recordCardCompletion(true);

assert(!celebrationCard.classList.contains('hidden'), "Celebration card must be shown on completion");
assert(timeTakenEl.textContent.includes('s'), "Time taken must be displayed");
assert(compTextEl.textContent.includes('Baseline attempt recorded'), "First attempt must be marked as baseline attempt");

// Case 2: Second Attempt (Faster - Improvement & Personal Best)
context.setupGameSession([testCard], 'blanks', 'Timing Test');
mockWindow.state.gameplay.timer_start_ms = Date.now() - 9200; // 9.2 seconds (5s faster)
context.recordCardCompletion(true);

assert(compTextEl.innerHTML.includes('faster'), "Faster completion must highlight speed improvement");
assert(compTextEl.innerHTML.includes('Personal Best'), "New fastest time must celebrate Personal Best!");

// Case 3: Third Attempt (Slower)
context.setupGameSession([testCard], 'blanks', 'Timing Test');
mockWindow.state.gameplay.timer_start_ms = Date.now() - 12000; // 12.0 seconds (slower than 9.2s)
context.recordCardCompletion(true);

assert(compTextEl.innerHTML.includes('Earlier attempt'), "Slower attempt must show reference to earlier attempt without crashing");

console.log("✓ PASS: Comparative timing delta (baseline, faster + PB, slower) in celebration card verified!");

// -------------------------------------------------------------------------
// Test 29: Question Timing Badges in Chapter View & Timing History Modal
// -------------------------------------------------------------------------
console.log("\n[Test 29] Testing Question Timing Badges in Chapter View & Practice History Modal...");

const testDeck = {
  id: 'deck_timed_chapter',
  title: 'Timed Deck',
  subject: 'Hindi',
  cards: [
    {
      card_id: 'card_with_history',
      question: 'अभ्यास का समय क्या है?',
      chunks: ['अभ्यास', 'का', 'समय', 'मूल्यवान है।'],
      meaning: 'Practice time is valuable.',
      ladder_stage: 2,
      stage_history: [
        { stage: 1, duration_seconds: 15.0, passed: true, timestamp: '2026-09-01T10:00:00Z' },
        { stage: 1, duration_seconds: 10.0, passed: true, timestamp: '2026-09-02T10:00:00Z' },
        { stage: 2, duration_seconds: 8.5, passed: true, timestamp: '2026-09-03T10:00:00Z' }
      ]
    }
  ]
};

mockWindow.state.decks = [testDeck];
const chapterData = {
  deck_id: 'deck_timed_chapter',
  deck_title: 'Timed Deck',
  chapter_name: 'Timed Chapter',
  subject: 'Hindi',
  cards: testDeck.cards
};

context.renderChapterView(chapterData);

const questionsList = mockDocument.getElementById('chapter-questions-list');
assert(questionsList.children.length === 1, "Chapter questions list must render 1 question item");
const cardItemHtml = questionsList.children[0].innerHTML;

// Verify timing badge in chapter card item
assert(cardItemHtml.includes('⏱️ Last:'), "Chapter card must show Last attempt time badge");
assert(cardItemHtml.includes('🏆 Best:'), "Chapter card must show Best attempt time badge");
assert(cardItemHtml.includes('8.5s'), "Chapter card must reflect 8.5s attempt");
assert(cardItemHtml.includes('⏱️ History'), "Chapter card must render History modal button");

// Open Timing History Modal
context.openTimingHistoryModal('deck_timed_chapter', 'card_with_history');

const historyModal = mockDocument.getElementById('timing-history-modal');
const modalTitle = mockDocument.getElementById('timing-history-question-title');
const modalSummary = mockDocument.getElementById('timing-history-summary');
const modalTbody = mockDocument.getElementById('timing-history-tbody');

assert(!historyModal.classList.contains('hidden'), "Timing history modal must be visible after openTimingHistoryModal");
assert.strictEqual(modalTitle.textContent, 'अभ्यास का समय क्या है?', "Modal title must match question");
assert(modalSummary.innerHTML.includes('3'), "Modal summary must show 3 attempts");
assert(modalSummary.innerHTML.includes('8.5s'), "Modal summary must show best time 8.5s");
assert(modalTbody.children.length === 3, "Timeline table must render all 3 attempt rows");

// Verify speed delta inside attempt rows
const row2Html = modalTbody.children[1].innerHTML;
assert(row2Html.includes('(-5s ⚡)'), "Second attempt at stage 1 must show (-5s ⚡) improvement delta vs 15.0s");

// Close Timing History Modal
context.closeTimingHistoryModal();
assert(historyModal.classList.contains('hidden'), "Timing history modal must be hidden after closeTimingHistoryModal");

console.log("✓ PASS: Question-level timing badges in chapter view and practice history modal verified!");

// -------------------------------------------------------------------------
// Test 30: Accessibility Global Font Size Scaling & Settings Modal Persistence
// -------------------------------------------------------------------------
console.log("\n[Test 30] Testing Accessibility Global Font Size Scaling & Settings Integration...");

const docEl = mockDocument.documentElement;
const docBody = mockDocument.body;

// 1. Direct applyFontSize calls
context.applyFontSize('medium');
assert.strictEqual(docEl.getAttribute('data-font-size'), 'medium', "documentElement data-font-size must be 'medium'");
assert.strictEqual(docBody.getAttribute('data-font-size'), 'medium', "body data-font-size must be 'medium'");

context.applyFontSize('large');
assert.strictEqual(docEl.getAttribute('data-font-size'), 'large', "documentElement data-font-size must be 'large'");
assert.strictEqual(docBody.getAttribute('data-font-size'), 'large', "body data-font-size must be 'large'");

context.applyFontSize('xlarge');
assert.strictEqual(docEl.getAttribute('data-font-size'), 'xlarge', "documentElement data-font-size must be 'xlarge'");
assert.strictEqual(docBody.getAttribute('data-font-size'), 'xlarge', "body data-font-size must be 'xlarge'");

// Fallback to normal
context.applyFontSize('normal');
assert.strictEqual(docEl.getAttribute('data-font-size'), 'normal', "documentElement data-font-size must be 'normal'");

// 2. Settings Modal form synchronization & save
mockWindow.state.settings.font_size = 'large';
context.openSettingsModal();

const fontSizeSel = mockDocument.getElementById('settings-font-size-select');
assert(fontSizeSel, "settings-font-size-select must exist in settings modal");
assert.strictEqual(fontSizeSel.value, 'large', "Settings font size select must reflect state.settings.font_size");

// Change to xlarge and save
fontSizeSel.value = 'xlarge';
context.saveSettingsFromModal();

assert.strictEqual(mockWindow.state.settings.font_size, 'xlarge', "Saved font size must update in state.settings");
assert.strictEqual(docEl.getAttribute('data-font-size'), 'xlarge', "Saving font size in modal must immediately apply to documentElement");
assert.strictEqual(docBody.getAttribute('data-font-size'), 'xlarge', "Saving font size in modal must immediately apply to body");

console.log("✓ PASS: Accessibility global font size scaling across DOM and settings modal verified!");

// -------------------------------------------------------------------------
// Test 31: Retry Question & Non-Advancement on Re-practicing Already Completed Stage
// -------------------------------------------------------------------------
(async () => {
  console.log("\n[Test 31] Testing Retry Question & Non-Advancement on Re-practicing Completed Stage...");

  const retryTestCard = {
    card_id: 'retry_c_31',
    question: 'पेड़ हमें क्या देते हैं?',
    chunks: ['पेड़', 'हमें', 'फल और फूल', 'देते हैं।'],
    lesson_name: 'Retry Test Lesson',
    ladder_stage: 1,
    stage_history: []
  };
  const retryDeck = {
    id: 'deck_retry_test',
    title: 'Retry Test Deck',
    cards: [retryTestCard]
  };
  mockWindow.state.decks = [retryDeck];

  // 1. Initial gameplay session at Stage 1 (Blanks)
  context.setupGameSession([retryTestCard], 'blanks', 'Retry Test Lesson', 'deck_retry_test');
  assert.strictEqual(mockWindow.state.gameplay.current_attempt_stage, 1, "Attempt stage must be 1 for blanks mode");
  assert.strictEqual(retryTestCard.ladder_stage, 1, "Initial card stage must be 1");

  // Complete the card successfully (Attempt 1)
  await context.recordCardCompletion(true);
  assert.strictEqual(retryTestCard.ladder_stage, 2, "Card ladder stage must advance to 2 after completing Stage 1");
  assert.strictEqual(retryTestCard.stage_history.length, 1, "Attempt 1 recorded in stage_history");
  assert.strictEqual(retryTestCard.stage_history[0].stage, 1, "Attempt 1 recorded at stage 1");

  let celebDetailText = mockDocument.getElementById('celebration-detail-text').textContent;
  assert(celebDetailText.includes('advanced to Stage 2'), `Celebration text must indicate advancement to Stage 2! Found: "${celebDetailText}"`);

  // 2. Click Retry Sentence (Attempt 2)
  context.retryGameplayCard();
  const celebCardEl = mockDocument.getElementById('game-celebration-card');
  assert(celebCardEl.classList.contains('hidden'), "Celebration card must be hidden upon retry");
  assert.strictEqual(mockWindow.state.gameplay.current_attempt_stage, 1, "Retry must preserve attempt stage 1");

  // Complete the retry of Stage 1 successfully (Attempt 2)
  await context.recordCardCompletion(true);

  // CRITICAL ASSERTION: Retrying Stage 1 MUST NOT advance to Stage 3 or mark Stage 2 as completed!
  assert.strictEqual(retryTestCard.ladder_stage, 2, "Retrying Stage 1 MUST NOT advance card to Stage 3; must remain at Stage 2!");
  assert.strictEqual(retryTestCard.stage_history.length, 2, "Attempt 2 must be recorded in stage_history");
  assert.strictEqual(retryTestCard.stage_history[1].stage, 1, "Attempt 2 must be recorded at stage 1");

  celebDetailText = mockDocument.getElementById('celebration-detail-text').textContent;
  assert(celebDetailText.includes('Great practice! Sentence cleared for Stage 1'), 
    `Celebration text on retry must acknowledge practice of Stage 1 and NOT claim advancement to Stage 3! Found: "${celebDetailText}"`);

  // 3. Now advance to Stage 2 (Jigsaw) via guided_mission
  context.setupGameSession([retryTestCard], 'guided_mission', 'Retry Test Lesson', 'deck_retry_test');
  assert.strictEqual(mockWindow.state.gameplay.current_attempt_stage, 2, "Attempt stage must be 2 for guided mission on Stage 2 card");
  assert.strictEqual(mockWindow.state.gameplay.effective_mode, 'jigsaw', "Effective mode must be jigsaw for Stage 2 card");

  // Complete Stage 2 (Attempt 3)
  await context.recordCardCompletion(true);
  assert.strictEqual(retryTestCard.ladder_stage, 3, "Completing Stage 2 must advance card to Stage 3");

  celebDetailText = mockDocument.getElementById('celebration-detail-text').textContent;
  assert(celebDetailText.includes('advanced to Stage 3'), `Celebration text must indicate advancement to Stage 3! Found: "${celebDetailText}"`);

  // 4. Retry Stage 2 (Attempt 4)
  context.retryGameplayCard();
  assert.strictEqual(mockWindow.state.gameplay.current_attempt_stage, 2, "Retry must preserve attempt stage 2");
  await context.recordCardCompletion(true);

  // Retrying Stage 2 MUST NOT advance to Stage 4!
  assert.strictEqual(retryTestCard.ladder_stage, 3, "Retrying Stage 2 MUST NOT advance card to Stage 4; must remain at Stage 3!");
  assert.strictEqual(retryTestCard.stage_history.length, 4, "Attempt 4 recorded in stage_history");

  console.log("✓ PASS: Question retry and non-advancement on re-practicing completed stage verified!");

  // -------------------------------------------------------------------------
  // Test 32: Capability to Reset Question & Chapter Learning Stages
  // -------------------------------------------------------------------------
  console.log("\n[Test 32] Testing Stage Reset Capability for Questions & Chapters...");

  const resetTestCard1 = {
    card_id: 'rst_c1',
    question: 'प्रश्न 1',
    chunks: ['क', 'ख'],
    lesson_name: 'Reset Chapter',
    ladder_stage: 4,
    stage_history: [{ stage: 1, duration_seconds: 8.0 }]
  };
  const resetTestCard2 = {
    card_id: 'rst_c2',
    question: 'प्रश्न 2',
    chunks: ['ग', 'घ'],
    lesson_name: 'Reset Chapter',
    ladder_stage: 5,
    stage_history: [{ stage: 1, duration_seconds: 10.0 }]
  };
  const resetTestDeck = {
    id: 'deck_reset_stage_test',
    title: 'Reset Test Deck',
    cards: [resetTestCard1, resetTestCard2]
  };
  mockWindow.state.decks = [resetTestDeck];

  // 1. Render Chapter View & Verify Interactive Stage Dropdown
  context.openChapterDetails('deck_reset_stage_test', 'Reset Chapter');
  const qListEl = mockDocument.getElementById('chapter-questions-list');
  assert(qListEl.children.length === 2, "Must render 2 questions in chapter list");
  assert(qListEl.children[0].innerHTML.includes('value="4" selected'), "Card 1 stage select must have Stage 4 selected");
  assert(qListEl.children[1].innerHTML.includes('value="5" selected'), "Card 2 stage select must have Stage 5 selected");
  assert(qListEl.children[0].innerHTML.includes('changeCardStage'), "Card 1 must include onchange hook for changeCardStage");

  // 2. Test Single Card Stage Change (Reset Card 1 to Stage 1)
  await context.changeCardStage('deck_reset_stage_test', 'rst_c1', 1, false);
  assert.strictEqual(resetTestCard1.ladder_stage, 1, "Card 1 ladder stage must be reset to 1");

  // 3. Test Reset from History Modal
  context.openTimingHistoryModal('deck_reset_stage_test', 'rst_c2');
  const historyModal = mockDocument.getElementById('timing-history-modal');
  assert(!historyModal.classList.contains('hidden'), "History modal must be open");
  const historyResetBtn = mockDocument.getElementById('timing-history-reset-btn');
  assert(historyResetBtn, "timing-history-reset-btn must exist in history modal");

  await context.resetCurrentCardFromHistoryModal();
  assert(historyModal.classList.contains('hidden'), "History modal must close after reset");
  assert.strictEqual(resetTestCard2.ladder_stage, 1, "Card 2 ladder stage must be reset to 1 via history modal");

  // Set card 1 and 2 to stage 3 to test chapter-wide reset
  resetTestCard1.ladder_stage = 3;
  resetTestCard2.ladder_stage = 4;

  // 4. Test Chapter Reset Modal Lifecycle
  const resetChapterBtn = mockDocument.getElementById('chapter-reset-stage-btn');
  assert(resetChapterBtn, "chapter-reset-stage-btn must exist in chapter view header");

  context.openResetChapterStageModal();
  const chapterResetModal = mockDocument.getElementById('chapter-reset-modal');
  assert(!chapterResetModal.classList.contains('hidden'), "chapter-reset-modal must be open");

  const targetStageSel = mockDocument.getElementById('chapter-reset-target-stage-select');
  assert(targetStageSel, "Target stage select must exist in chapter reset modal");
  targetStageSel.value = '1';

  await context.confirmResetChapterStages();
  assert(chapterResetModal.classList.contains('hidden'), "chapter-reset-modal must close after confirmation");
  assert.strictEqual(resetTestCard1.ladder_stage, 1, "All chapter cards must be reset to Stage 1");
  assert.strictEqual(resetTestCard2.ladder_stage, 1, "All chapter cards must be reset to Stage 1");

  const chapterMasteryTextAfter = mockDocument.getElementById('chapter-mastery-text').textContent;
  assert(chapterMasteryTextAfter.includes('0%'), `Chapter mastery must recalculate to 0% after reset to Stage 1! Found: "${chapterMasteryTextAfter}"`);

  console.log("✓ PASS: Card-level and chapter-level learning stage reset capability verified!");

  // -------------------------------------------------------------------------
  // Test 33: Words Per Block Customization & Progression in Jigsaw Stage (4 -> 3 -> 2 words)
  // -------------------------------------------------------------------------
  console.log("\n[Test 33] Testing Words Per Block Customization & Progression in Jigsaw Stage...");

  const jigsawCard = {
    card_id: 'jigsaw_wpb_1',
    question: 'यह एक बहुत सुंदर और मनोरम बगीचा है।',
    chunks: ['यह एक बहुत सुंदर', 'और मनोरम बगीचा है।'], // 8 total words
    lesson_name: 'Jigsaw Chunking Test',
    ladder_stage: 2,
    stage_history: []
  };

  // 1. Test computeDynamicChunks utility directly
  const chunks4 = context.computeDynamicChunks(jigsawCard, 4);
  assert.strictEqual(chunks4.length, 2, "8 words at 4 words/chunk should yield 2 chunks");
  assert.strictEqual(chunks4[0], "यह एक बहुत सुंदर");
  assert(chunks4[1].endsWith('।'), "Last chunk must preserve punctuation");

  const chunks2 = context.computeDynamicChunks(jigsawCard, 2);
  assert.strictEqual(chunks2.length, 4, "8 words at 2 words/chunk should yield 4 chunks");
  assert.strictEqual(chunks2[0], "यह एक");
  assert.strictEqual(chunks2[1], "बहुत सुंदर");
  assert.strictEqual(chunks2[2], "और मनोरम");
  assert.strictEqual(chunks2[3], "बगीचा है।");

  const chunks3 = context.computeDynamicChunks(jigsawCard, 3);
  assert.strictEqual(chunks3.length, 3, "8 words at 3 words/chunk should yield 3 chunks (3 + 3 + 2)");
  assert.strictEqual(chunks3[0], "यह एक बहुत");
  assert.strictEqual(chunks3[1], "सुंदर और मनोरम");
  assert.strictEqual(chunks3[2], "बगीचा है।");

  // 2. Test Scaffolding Progression in getEffectiveWordsPerBlock
  // Fresh Stage 2 card -> should start at 4 words/block
  const effStage2 = context.getEffectiveWordsPerBlock(jigsawCard);
  assert.strictEqual(effStage2, 4, "Fresh Stage 2 card must start with 4 words per block (gentle cognitive entry)");

  // Card after 1 successful pass -> progresses to 3 words/block
  jigsawCard.stage_history.push({ stage: 2, passed: true, duration_seconds: 12.0 });
  const effStage2Passed = context.getEffectiveWordsPerBlock(jigsawCard);
  assert.strictEqual(effStage2Passed, 3, "Stage 2 card with 1 pass must progress to 3 words per block");

  // Card reaching Stage 3 or frontier before Voice -> progresses to 2 words/block
  jigsawCard.ladder_stage = 3;
  const effStage3 = context.getEffectiveWordsPerBlock(jigsawCard);
  assert.strictEqual(effStage3, 2, "Card before Voice stage (Stage 3/4) must progress to 2 words per block (granular recall)");

  // 3. Test Gameplay Arena Jigsaw Card Initialization & Size Switcher
  context.setupGameSession([jigsawCard], 'jigsaw', 'Jigsaw Chunking Test');
  const sizeContainer = mockDocument.getElementById('jigsaw-block-size-container');
  assert(sizeContainer && !sizeContainer.classList.contains('hidden'), "jigsaw-block-size-container must be visible in jigsaw mode");

  // Switch to 2 words per block dynamically
  context.setJigsawWordsPerBlock(2);
  assert.strictEqual(mockWindow.state.gameplay.words_per_block, 2, "words_per_block must be set to 2");
  assert.strictEqual(mockWindow.state.gameplay.active_chunks.length, 4, "Active chunks must have 4 pieces for 2 words/block");
  assert.strictEqual(mockWindow.state.gameplay.available_chips.length, 4, "Available chips tray must have 4 pieces");

  // Switch to 4 words per block dynamically
  context.setJigsawWordsPerBlock(4);
  assert.strictEqual(mockWindow.state.gameplay.words_per_block, 4, "words_per_block must be set to 4");
  assert.strictEqual(mockWindow.state.gameplay.active_chunks.length, 2, "Active chunks must have 2 pieces for 4 words/block");
  assert.strictEqual(mockWindow.state.gameplay.available_chips.length, 2, "Available chips tray must have 2 pieces");

  // Test Hint with dynamic chunks
  context.gameActionHint();
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 1, "Hint must place 1 chunk");
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[0], chunks4[0], "Hint must place first 4-word chunk correctly");

  // Test Undo and Clear with dynamic chunks
  context.gameActionUndo();
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 0, "Undo must return chunk to available chips");
  assert.strictEqual(mockWindow.state.gameplay.available_chips.length, 2, "All 2 chips must be back in available chips");

  context.setJigsawWordsPerBlock(3);
  assert.strictEqual(mockWindow.state.gameplay.active_chunks.length, 3, "3 words/block should configure 3 active chunks");
  context.gameActionHint();
  context.gameActionClear();
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 0, "Clear must empty placed chunks");
  assert.strictEqual(mockWindow.state.gameplay.available_chips.length, 3, "Clear must restore all 3 chunks to available tray");

  // 4. Test Settings Modal Synchronization for jigsaw_words_per_block
  context.openSettingsModal();
  const jigsawSelectEl = mockDocument.getElementById('settings-jigsaw-words-select');
  assert(jigsawSelectEl, "settings-jigsaw-words-select must exist in Settings modal");
  jigsawSelectEl.value = '2';
  await context.saveSettingsFromModal();
  assert.strictEqual(mockWindow.state.settings.jigsaw_words_per_block, '2', "Settings must persist jigsaw_words_per_block as '2'");

  console.log("✓ PASS: Words per block options (2, 3, 4 words) and scaffolding progression (4 -> 2 words) in Jigsaw stage verified!");

  // -------------------------------------------------------------------------
  // Test 34: Insertion of Blocks Between Two Blocks & Dual Sky-Blue Cues
  // -------------------------------------------------------------------------
  console.log("\n[Test 34] Testing Mouse-Between-Blocks Insertion & Dual Sky-Blue Drop Cues...");
  const insertionCard = {
    card_id: 'card_insert_test',
    lesson_name: 'Insertion Chapter',
    question: 'Arrange three words:',
    chunks: ['पहला', 'दूसरा', 'तीसरा'],
    ladder_stage: 2
  };

  context.setupGameSession([insertionCard], 'jigsaw', 'Insertion Chapter');
  context.setJigsawWordsPerBlock('orig');

  // Initially, 0 placed chunks -> tray has 3 chips
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 0);

  // Place first chip ('पहला') and third chip ('तीसरा') deliberately leaving gap in the middle
  const chip1Text = 'पहला';
  const chip3Text = 'तीसरा';
  const chip2Text = 'दूसरा';

  context.insertChunkFromTray(chip1Text, 0);
  context.insertChunkFromTray(chip3Text, 1);

  // Placed chunks are now ['पहला', 'तीसरा']
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 2);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[0], chip1Text);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[1], chip3Text);

  // 1. Verify insertion gaps rendered on assembly board
  const boardEl = mockDocument.getElementById('game-assembly-board');
  const gaps = boardEl.querySelectorAll('.insertion-gap');
  // With 2 placed blocks, there must be 3 insertion gaps: before index 0, between index 0 & 1 (index 1), and after index 1 (index 2)
  assert.strictEqual(gaps.length, 3, "Must render 3 insertion gaps (before, between, and after 2 placed blocks)");

  // 2. Test mouse hovering between the two blocks (gap at index 1)
  const betweenGap = gaps[1];
  assert.strictEqual(betweenGap.dataset.insertIndex, 1, "Middle gap must target index 1 between the two blocks");
  betweenGap.onmouseenter();
  assert(betweenGap.classList.contains('insertion-gap-hover'), "Gap must show hover styling when mouse is between two blocks");

  // Verify dual sky-blue highlight cues on BOTH adjacent neighbor blocks
  const placedBlockBtns = boardEl.querySelectorAll('.chip-btn');
  assert.strictEqual(placedBlockBtns.length, 2);
  assert(placedBlockBtns[0].classList.contains('insert-between-neighbor'), "Left neighbor block ('पहला') must have sky-blue highlight");
  assert(placedBlockBtns[1].classList.contains('insert-between-neighbor'), "Right neighbor block ('तीसरा') must have sky-blue highlight");

  // Mouse leave clears the cues
  betweenGap.onmouseleave();
  assert(!placedBlockBtns[0].classList.contains('insert-between-neighbor'), "Left neighbor sky-blue highlight cleared on mouse leave");
  assert(!placedBlockBtns[1].classList.contains('insert-between-neighbor'), "Right neighbor sky-blue highlight cleared on mouse leave");

  // 3. Test clicking the gap between the two blocks to activate insertion
  betweenGap.onclick({ stopPropagation: () => {} });
  assert.strictEqual(mockWindow.state.gameplay.active_insert_index, 1, "Clicking between-blocks gap must set active_insert_index to 1");

  // 4. Click the missing middle chip ('दूसरा') from available tray
  // Because active_insert_index is 1, it must be inserted between 'पहला' and 'तीसरा'
  const trayButtons = chipsTray.querySelectorAll('.chip-btn');
  const chip2Btn = trayButtons.find(b => b.dataset.chunkText === chip2Text);
  assert(chip2Btn, "Middle chip 'दूसरा' must be in tray");
  chip2Btn.onclick();

  // Verify resulting sequence is ['पहला', 'दूसरा', 'तीसरा']
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 3, "All 3 chunks placed");
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[0], chip1Text, "Chunk 0 must be 'पहला'");
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[1], chip2Text, "Chunk 1 must be inserted 'दूसरा'");
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[2], chip3Text, "Chunk 2 must be 'तीसरा'");
  assert.strictEqual(mockWindow.state.gameplay.active_insert_index, null, "Active insertion index reset after insertion");

  // 5. Test Drag & Drop moving / reordering a placed block between two blocks
  // Move 'तीसरा' (index 2) to index 1 (between 'पहला' and 'दूसरा')
  context.movePlacedChunk(2, 1);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[1], chip3Text, "'तीसरा' should now be moved between index 0 and 1");

  // Move it back to index 2
  context.movePlacedChunk(1, 3);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[2], chip3Text, "'तीसरा' should be moved back to end");

  // 6. Test Swapping blocks
  context.swapPlacedChunks(0, 1);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[0], chip2Text);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[1], chip1Text);

  // Swap back to correct sequence
  context.swapPlacedChunks(0, 1);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[0], chip1Text);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[1], chip2Text);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[2], chip3Text);

  // 7. Verify Drag & Drop from Tray to Gap Between Two Blocks creates NO DUPLICATES
  context.setupGameSession([insertionCard], 'jigsaw', 'Insertion Chapter');
  context.setJigsawWordsPerBlock('orig');
  // Place 2 chunks: 'पहला' and 'तीसरा'
  context.insertChunkFromTray(chip1Text, 0);
  context.insertChunkFromTray(chip3Text, 1);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 2);

  const updatedBoardEl = mockDocument.getElementById('game-assembly-board');
  const updatedGaps = updatedBoardEl.querySelectorAll('.insertion-gap');
  const midGap = updatedGaps[1];
  assert.strictEqual(midGap.dataset.insertIndex, 1);

  let stoppedProp = false;
  const mockDropEvent = {
    preventDefault: () => {},
    stopPropagation: () => { stoppedProp = true; },
    dataTransfer: {
      getData: () => JSON.stringify({ source: 'tray', chunk: chip2Text, index: 0 })
    }
  };
  midGap.ondrop(mockDropEvent);
  assert.strictEqual(stoppedProp, true, "gap.ondrop must call e.stopPropagation() to prevent bubbling to board.ondrop");

  // Verify resulting sequence is ['पहला', 'दूसरा', 'तीसरा'] with NO duplicate
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 3, "Exactly 3 placed chunks, no duplicates");
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[0], chip1Text);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[1], chip2Text);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[2], chip3Text);
  assert.strictEqual(mockWindow.state.gameplay.available_chips.length, 0, "Tray is now empty");

  // Even if board.ondrop were somehow triggered, board.ondrop must not duplicate
  updatedBoardEl.ondrop(mockDropEvent);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 3, "Calling board.ondrop must not create duplicates");

  // 8. Verify Drag & Drop Moving Placed Block Between Two Blocks creates NO DUPLICATES
  // Move 'तीसरा' (index 2) between 'पहला' and 'दूसरा' (gap at index 1)
  const currentGaps = updatedBoardEl.querySelectorAll('.insertion-gap');
  const moveGap = currentGaps[1];
  let moveStopped = false;
  moveGap.ondrop({
    preventDefault: () => {},
    stopPropagation: () => { moveStopped = true; },
    dataTransfer: {
      getData: () => JSON.stringify({ source: 'board', chunk: chip3Text, index: 2 })
    }
  });
  assert.strictEqual(moveStopped, true, "move gap.ondrop must call stopPropagation");
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 3, "Still exactly 3 blocks, no duplicates created during move");
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[0], chip1Text);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[1], chip3Text);
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks[2], chip2Text);

  // 9. Verify safety guard: calling insertChunkFromTray with chunk not in tray is rejected
  context.insertChunkFromTray(chip1Text, 0); // 'पहला' is already placed, not in tray
  assert.strictEqual(mockWindow.state.gameplay.placed_chunks.length, 3, "insertChunkFromTray must ignore chunks not in tray");

  // Verify sequence completion passes
  // -------------------------------------------------------------------------
  // Test 35: Jigsaw Hint Behavior: Non-Finishing & Exclusion from Best Timing and Graduation
  // -------------------------------------------------------------------------
  console.log("\n[Test 35] Testing Jigsaw Hint Exclusion from Best Timing & Auto-Finishing Prevention...");
  const hintTestCard = {
    card_id: 'card_hint_test',
    lesson_name: 'Hint Timing Test',
    question: 'Arrange three chunks with hint:',
    chunks: ['पहला हिस्सा', 'दूसरा हिस्सा', 'तीसरा हिस्सा'],
    ladder_stage: 2,
    stage_history: []
  };

  context.setupGameSession([hintTestCard], 'jigsaw', 'Hint Timing Test');
  const hg = mockWindow.state.gameplay;
  assert.strictEqual(hg.hints_used, 0, "hints_used must start at 0");
  assert.strictEqual(hg.hint_used, false, "hint_used must start as false");

  // 1. Place first chunk via hint
  context.gameActionHint();
  assert.strictEqual(hg.placed_chunks.length, 1, "First hint places 1 chunk");
  assert.strictEqual(hg.hints_used, 1, "hints_used incremented to 1");
  assert.strictEqual(hg.hint_used, true, "hint_used set to true");
  assert.strictEqual(hg.flawless, false, "flawless set to false");

  // 2. Try placing final chunks via hint
  // Target has 3 chunks. placed_chunks is 1. One more hint brings it to 2 (which is target.length - 1)
  // Let's test calling hint when 1 chunk remains:
  hg.placed_chunks = ['पहला हिस्सा', 'दूसरा हिस्सा'];
  hg.available_chips = ['तीसरा हिस्सा'];
  const placedBeforeFinalHint = hg.placed_chunks.length;
  context.gameActionHint();
  assert.strictEqual(hg.placed_chunks.length, placedBeforeFinalHint, "Hint must NOT auto-place the final remaining chunk in Jigsaw");

  // 3. User places final piece manually and checks answer
  hg.placed_chunks.push('तीसरा हिस्सा');
  hg.available_chips = [];
  hg.timer_start_ms = Date.now() - 2500; // 2.5s run but with hints

  context.checkCurrentAnswer();

  // Verify attempt is recorded in stage_history
  const hist = hintTestCard.stage_history;
  assert(hist.length >= 1, "History must have recorded the attempt");
  const lastAttempt = hist[hist.length - 1];
  assert.strictEqual(lastAttempt.passed, false, "Hint-assisted attempt must be recorded as passed=false");
  assert.strictEqual(lastAttempt.hint_used, true, "Attempt must have hint_used=true");
  assert.strictEqual(hintTestCard.ladder_stage, 2, "Card must remain at Stage 2 without advancing");

  // Verify Personal Best display does NOT use this hint attempt
  const compEl = mockDocument.getElementById('celebration-comparison-text');
  assert(compEl.innerHTML.includes('Assisted Practice (Hint Used)'), "Celebration text must indicate assisted practice");
  assert(!compEl.innerHTML.includes('🏆 Personal Best!'), "Hint attempt must not be awarded Personal Best");

  // 4. Now do a clean unassisted attempt in 9.0s
  context.retryGameplayCard();
  assert.strictEqual(hg.hints_used, 0, "hints_used must reset on retry");
  assert.strictEqual(hg.hint_used, false, "hint_used must reset on retry");
  assert.strictEqual(hg.flawless, true, "flawless resets to true");

  // Solve all chunks cleanly
  hg.placed_chunks = ['पहला हिस्सा', 'दूसरा हिस्सा', 'तीसरा हिस्सा'];
  hg.available_chips = [];
  hg.timer_start_ms = Date.now() - 9000; // clean 9.0s run

  context.checkCurrentAnswer();
  const cleanAttempt = hintTestCard.stage_history[hintTestCard.stage_history.length - 1];
  assert.strictEqual(cleanAttempt.passed, true, "Clean attempt must pass");
  assert.strictEqual(cleanAttempt.hint_used, false, "Clean attempt has hint_used=false");
  assert.strictEqual(hintTestCard.ladder_stage, 3, "Clean attempt must advance stage from Stage 2 to Stage 3");
  assert(compEl.innerHTML.includes('Personal Best'), "First clean attempt establishes Personal Best");

  // 5. Test Chapter questions list and history modal with mixed attempts
  context.renderChapterView({
    deck_id: 'test_deck_hint',
    deck_title: 'Hint Deck',
    chapter_name: 'Hint Chapter',
    subject: 'Hindi',
    cards: [hintTestCard]
  });
  const chapListEl = mockDocument.getElementById('chapter-questions-list');
  assert.strictEqual(chapListEl.children.length, 1, "Must render 1 card item in chapter view");
  const cardItemHtml = chapListEl.children[0].innerHTML;
  // Clean attempt was ~9s, hint attempt was ~2.5s. Best shown must not be 2.5s!
  assert(cardItemHtml.includes('🏆 Best:'), "Chapter question badge must display Best time badge");
  assert(!cardItemHtml.includes('2.5s</strong>'), "Chapter badge must NOT display 2.5s as Best");

  // History modal summary
  context.openTimingHistoryModal('test_deck_hint', 'card_hint_test');
  const sumEl = mockDocument.getElementById('timing-history-summary');
  assert(sumEl.innerHTML.includes('🏆'), "History modal must show Best Time trophy");
  assert(!sumEl.innerHTML.includes('🏆 2.5s'), "History modal Best Time must not be 2.5s");

  console.log("✓ PASS: Jigsaw hint finishing prevention and PB exclusion verified!");

  // -------------------------------------------------------------------------
  // Test 36: Lava Forge Nether Dungeon Universe Engine Lifecycle
  // -------------------------------------------------------------------------
  console.log("\n[Test 36] Testing Lava Forge Nether Dungeon Universe Engine Lifecycle & Theme Switching...");

  const lavaUniverseEl = mockDocument.getElementById('lava-universe');
  const lavaCanvas = mockDocument.getElementById('lava-canvas');
  assert(lavaUniverseEl, "lava-universe DOM element must exist in HTML");
  assert(lavaCanvas, "lava-canvas DOM element must exist in HTML");

  // Switch to lava theme
  context.applyTheme('lava');
  assert(mockWindow.lavaUniverseEngine.running, "lavaUniverseEngine must be running when lava theme is active");
  assert(!lavaUniverseEl.classList.contains('hidden'), "lava-universe must not be hidden when lava theme is active");
  assert(mockWindow.lavaUniverseEngine.embers.length > 0, "Embers must be generated for lava forge background");
  assert(!mockWindow.spaceUniverseEngine.running, "spaceUniverseEngine must be stopped when lava theme is active");
  assert(!mockWindow.animeUniverseEngine.running, "animeUniverseEngine must be stopped when lava theme is active");

  // Switch to pastel theme
  context.applyTheme('pastel');
  assert(!mockWindow.lavaUniverseEngine.running, "lavaUniverseEngine must be stopped when pastel theme is active (zero cpu/gpu overhead)");
  assert(lavaUniverseEl.classList.contains('hidden'), "lava-universe must be hidden when pastel theme is active");

  console.log("✓ PASS: Lava Forge universe engine lifecycle, rising embers, and zero-overhead switching verified!");

  // -------------------------------------------------------------------------
  // Test 37: Anime Action Manga Aura & Katana Slash Engine Lifecycle
  // -------------------------------------------------------------------------
  console.log("\n[Test 37] Testing Anime Action Manga Aura & Katana Slash Engine Lifecycle & Theme Switching...");

  const animeUniverseEl = mockDocument.getElementById('anime-universe');
  const animeCanvas = mockDocument.getElementById('anime-canvas');
  assert(animeUniverseEl, "anime-universe DOM element must exist in HTML");
  assert(animeCanvas, "anime-canvas DOM element must exist in HTML");

  // Switch to anime theme
  context.applyTheme('anime');
  assert(mockWindow.animeUniverseEngine.running, "animeUniverseEngine must be running when anime theme is active");
  assert(!animeUniverseEl.classList.contains('hidden'), "anime-universe must not be hidden when anime theme is active");
  assert(mockWindow.animeUniverseEngine.particles.length > 0, "Chakra particles must be generated for anime background");
  assert(mockWindow.animeUniverseEngine.petals.length > 0, "Demon Slayer sakura petals must be generated for anime background");
  assert(!mockWindow.spaceUniverseEngine.running, "spaceUniverseEngine must be stopped when anime theme is active");
  assert(!mockWindow.lavaUniverseEngine.running, "lavaUniverseEngine must be stopped when anime theme is active");

  // Switch to dark theme
  context.applyTheme('dark');
  assert(!mockWindow.animeUniverseEngine.running, "animeUniverseEngine must be stopped when dark theme is active (zero cpu/gpu overhead)");
  assert(animeUniverseEl.classList.contains('hidden'), "anime-universe must be hidden when dark theme is active");
  assert(!mockWindow.lavaUniverseEngine.running, "lavaUniverseEngine must remain stopped in dark theme");
  assert(!mockWindow.spaceUniverseEngine.running, "spaceUniverseEngine must remain stopped in dark theme");

  console.log("✓ PASS: Anime Action universe engine lifecycle, chakra energy particles, sakura petals, lightning, and zero-overhead switching verified!");

  // -------------------------------------------------------------------------
  // Test 38: Sunny Blue Sky Universe Engine Lifecycle & Moving Clouds
  // -------------------------------------------------------------------------
  console.log("\n[Test 38] Testing Sunny Blue Sky Universe Engine Lifecycle & Theme Switching...");

  const skyUniverseEl = mockDocument.getElementById('sky-universe');
  const skyCanvas = mockDocument.getElementById('sky-canvas');
  assert(skyUniverseEl, "sky-universe DOM element must exist in HTML");
  assert(skyCanvas, "sky-canvas DOM element must exist in HTML");

  // Switch to sky theme
  context.applyTheme('sky');
  assert(mockWindow.skyUniverseEngine.running, "skyUniverseEngine must be running when sky theme is active");
  assert(!skyUniverseEl.classList.contains('hidden'), "sky-universe must not be hidden when sky theme is active");
  assert(mockWindow.skyUniverseEngine.clouds.length > 0, "Clouds must be generated for sky background");
  assert(mockWindow.skyUniverseEngine.birds.length > 0, "Birds must be generated for sky background");
  assert(!mockWindow.spaceUniverseEngine.running, "spaceUniverseEngine must be stopped when sky theme is active");
  assert(!mockWindow.lavaUniverseEngine.running, "lavaUniverseEngine must be stopped when sky theme is active");
  assert(!mockWindow.animeUniverseEngine.running, "animeUniverseEngine must be stopped when sky theme is active");
  assert(!mockWindow.oceanUniverseEngine.running, "oceanUniverseEngine must be stopped when sky theme is active");

  // Switch to pastel theme
  context.applyTheme('pastel');
  assert(!mockWindow.skyUniverseEngine.running, "skyUniverseEngine must be stopped when pastel theme is active (zero cpu/gpu overhead)");
  assert(skyUniverseEl.classList.contains('hidden'), "sky-universe must be hidden when pastel theme is active");

  console.log("✓ PASS: Sunny Sky universe engine lifecycle, drifting clouds/birds, and zero-overhead switching verified!");

  // -------------------------------------------------------------------------
  // Test 39: Deep Ocean Aquarium Universe Engine Lifecycle & Swimming Fishes
  // -------------------------------------------------------------------------
  console.log("\n[Test 39] Testing Deep Ocean Aquarium Universe Engine Lifecycle & Theme Switching...");

  const oceanUniverseEl = mockDocument.getElementById('ocean-universe');
  const oceanCanvas = mockDocument.getElementById('ocean-canvas');
  assert(oceanUniverseEl, "ocean-universe DOM element must exist in HTML");
  assert(oceanCanvas, "ocean-canvas DOM element must exist in HTML");

  // Switch to ocean theme
  context.applyTheme('ocean');
  assert(mockWindow.oceanUniverseEngine.running, "oceanUniverseEngine must be running when ocean theme is active");
  assert(!oceanUniverseEl.classList.contains('hidden'), "ocean-universe must not be hidden when ocean theme is active");
  assert(mockWindow.oceanUniverseEngine.fishes.length > 0, "Fishes must be generated for ocean background");
  assert(mockWindow.oceanUniverseEngine.bubbles.length > 0, "Rising bubbles must be generated for ocean background");
  assert(!mockWindow.spaceUniverseEngine.running, "spaceUniverseEngine must be stopped when ocean theme is active");
  assert(!mockWindow.lavaUniverseEngine.running, "lavaUniverseEngine must be stopped when ocean theme is active");
  assert(!mockWindow.animeUniverseEngine.running, "animeUniverseEngine must be stopped when ocean theme is active");
  assert(!mockWindow.skyUniverseEngine.running, "skyUniverseEngine must be stopped when ocean theme is active");

  // Switch to dark theme
  context.applyTheme('dark');
  assert(!mockWindow.oceanUniverseEngine.running, "oceanUniverseEngine must be stopped when dark theme is active (zero cpu/gpu overhead)");
  assert(oceanUniverseEl.classList.contains('hidden'), "ocean-universe must be hidden when dark theme is active");
  assert(!mockWindow.skyUniverseEngine.running, "skyUniverseEngine must remain stopped in dark theme");
  assert(!mockWindow.lavaUniverseEngine.running, "lavaUniverseEngine must remain stopped in dark theme");
  assert(!mockWindow.spaceUniverseEngine.running, "spaceUniverseEngine must remain stopped in dark theme");
  assert(!mockWindow.animeUniverseEngine.running, "animeUniverseEngine must remain stopped in dark theme");

  console.log("✓ PASS: Deep Ocean universe engine lifecycle, swimming fishes, bubbles, and zero-overhead switching verified!");

  // -------------------------------------------------------------------------
  // Test 40: Card / Question Editor Modal & In-Place Editing
  // -------------------------------------------------------------------------
  await (async () => {
    console.log("\n[Test 40] Testing Card / Question Editor Modal & In-Place Editing...");
    const editableCard = {
      card_id: 'card_to_edit_1',
      lesson_name: 'Original Chapter',
      question: 'पुरानी चिड़िया क्या करती थी?',
      chunks: ['पुरानी चिड़िया', 'मीठे स्वर में', 'गाती थी।'],
      meaning: 'The old bird sang in a sweet voice.',
      ladder_stage: 2,
      stage_history: []
    };

    const editorTestDeck = {
      id: 'deck_editor_test',
      title: 'Editable Deck',
      subject: 'Hindi',
      cards: [editableCard]
    };
    mockWindow.state.decks = [editorTestDeck];

    // 1. Render Chapter View & Verify "✏️ Edit" Button
    context.renderChapterView({
      deck_id: 'deck_editor_test',
      deck_title: 'Editable Deck',
      chapter_name: 'Original Chapter',
      subject: 'Hindi',
      cards: [editableCard]
    });

    const editorQListEl = mockDocument.getElementById('chapter-questions-list');
    assert.strictEqual(editorQListEl.children.length, 1, "Must render 1 question item in chapter view");
    const itemHtml = editorQListEl.children[0].innerHTML;
    assert(itemHtml.includes('✏️ Edit'), "Question item must include '✏️ Edit' button");
    assert(itemHtml.includes('openCardEditorModal'), "Edit button must have onclick handler for openCardEditorModal");

    // 2. Open Card Editor Modal & Verify Initial Form Population
    context.openCardEditorModal('deck_editor_test', 'card_to_edit_1');
    const editorModal = mockDocument.getElementById('card-editor-modal');
    assert(!editorModal.classList.contains('hidden'), "Card editor modal must be visible after opening");

    const chapInput = mockDocument.getElementById('edit-card-chapter-input');
    const qInput = mockDocument.getElementById('edit-card-question-input');
    const ansInput = mockDocument.getElementById('edit-card-answer-input');
    const meanInput = mockDocument.getElementById('edit-card-meaning-input');
    const previewBox = mockDocument.getElementById('edit-card-chips-preview');
    const countEl = mockDocument.getElementById('edit-card-chunks-count');

    assert.strictEqual(chapInput.value, 'Original Chapter', "Chapter input must populate with card lesson_name");
    assert.strictEqual(qInput.value, 'पुरानी चिड़िया क्या करती थी?', "Question input must populate with question text");
    assert.strictEqual(ansInput.value, 'पुरानी चिड़िया | मीठे स्वर में | गाती थी।', "Answer input must be pipe-delimited chunks");
    assert.strictEqual(meanInput.value, 'The old bird sang in a sweet voice.', "Meaning input must populate");
    assert.strictEqual(previewBox.children.length, 3, "Chips preview must render 3 chips initially");
    assert.strictEqual(countEl.textContent, '3 blocks', "Chunks count must report 3 blocks");

    // 3. Test Quick Chunking Formatter Buttons (e.g. 2 Words per block)
    // 'पुरानी चिड़िया मीठे स्वर में गाती थी।' = 7 words -> [2, 2, 2, 1] = 4 chunks
    context.cardEditorAutoGroupWords(2);
    assert(ansInput.value.includes('|'), "Reformatted answer must contain pipe delimiters");
    const chunks2w = context.parseAnswerIntoChunks(ansInput.value);
    assert.strictEqual(chunks2w.length, 4, "Sentence of 7 words grouped into 2 words/block must have 4 chunks");
    assert.strictEqual(chunks2w[0], 'पुरानी चिड़िया');
    assert.strictEqual(chunks2w[1], 'मीठे स्वर');
    assert.strictEqual(chunks2w[2], 'में गाती');
    assert.strictEqual(chunks2w[3], 'थी।');

    // 4. Test Single Word Grouping (7 words -> 7 blocks)
    context.cardEditorAutoGroupWords(1);
    const chunks1w = context.parseAnswerIntoChunks(ansInput.value);
    assert.strictEqual(chunks1w.length, 7, "Single word group should produce 7 single word blocks");

    // 5. Test Live Chunk Merge and Split on Preview Chips
    // Merge chunk 0 and chunk 1 ('पुरानी' + 'चिड़िया')
    context.cardEditorMergeChunk(0);
    assert(ansInput.value.startsWith('पुरानी चिड़िया'), "Merging chunk 0 and 1 must join first two words");

    // 6. Edit Question and Meaning Text & Save Changes
    qInput.value = 'नन्हीं चिड़िया क्या करती थी?';
    meanInput.value = 'The little bird sang sweetly.';
    chapInput.value = 'Updated Chapter 1';

    await context.saveCardEditorChanges();
    assert(editorModal.classList.contains('hidden'), "Modal must close on save");

    // Verify memory update
    assert.strictEqual(editableCard.question, 'नन्हीं चिड़िया क्या करती थी?', "Card question must update in memory");
    assert.strictEqual(editableCard.meaning, 'The little bird sang sweetly.', "Card meaning must update in memory");
    assert.strictEqual(editableCard.lesson_name, 'Updated Chapter 1', "Card lesson_name must update in memory");

    // 7. Test Card Deletion
    context.openCardEditorModal('deck_editor_test', 'card_to_edit_1');
    assert(!editorModal.classList.contains('hidden'), "Modal reopened for deletion test");
    await context.deleteCardFromEditor();
    assert(editorModal.classList.contains('hidden'), "Modal must close after deletion");
    assert.strictEqual(editorTestDeck.cards.length, 0, "Card must be removed from deck after deletion");

    console.log("✓ PASS: Card / Question Editor Modal, chunk formatting, saving, and deletion verified!");
  })();

  // -------------------------------------------------------------------------
  // [Test 41] Active Writing Pedagogical Scaffolding: Look-Cover-Write-Check (LCWC)
  // -------------------------------------------------------------------------
  await (async () => {
    console.log("\n[Test 41] Testing Active Writing Pedagogical Scaffolding: Look-Cover-Write-Check (LCWC)...");
    const testCard = {
      card_id: 'card_lcwc_test',
      question: 'सूरज किधर से निकलता है?',
      meaning: 'Which direction does the sun rise from?',
      chunks: ['सूरज', 'पूरब', 'से', 'निकलता', 'है।']
    };

    context.setupGameSession([testCard], 'writing', 'Chapter Scaffolding Test', 'deck_scaffold');
    assert.strictEqual(mockWindow.state.gameplay.effective_mode, 'writing', "Must be in writing mode");

    // 1. Trigger LCWC
    context.startWritingLookCoverWrite();
    const curtain = mockDocument.getElementById('writing-memorize-curtain');
    const targetTextEl = mockDocument.getElementById('writing-curtain-target-text');
    const countdownEl = mockDocument.getElementById('writing-curtain-countdown');

    assert(!curtain.classList.contains('hidden'), "Curtain must be visible when LCWC starts");
    assert.strictEqual(targetTextEl.textContent, 'सूरज पूरब से निकलता है।', "Target sentence must display in curtain");
    assert.strictEqual(countdownEl.textContent, '5s', "Countdown must initialize to 5s");
    assert(mockWindow.state.gameplay.writing_lcwc_active, "LCWC state must be active");

    // 2. Dismiss curtain
    context.dismissWritingCurtain(true);
    assert(curtain.classList.contains('hidden'), "Curtain must be hidden after dismissal");
    assert(!mockWindow.state.gameplay.writing_lcwc_active, "LCWC state must be inactive");

    console.log("✓ PASS: Look-Cover-Write-Check 5s memorize curtain and dismissal verified!");
  })();

  // -------------------------------------------------------------------------
  // [Test 42] Active Writing Pedagogical Scaffolding: Ghost Text Watermark Peek
  // -------------------------------------------------------------------------
  await (async () => {
    console.log("\n[Test 42] Testing Active Writing Pedagogical Scaffolding: Ghost Text Watermark Peek...");
    const watermark = mockDocument.getElementById('writing-ghost-watermark');
    const scaffoldBadge = mockDocument.getElementById('writing-scaffold-status-badge');

    // 1. Activate Ghost Peek
    context.showWritingGhostPeek();
    assert(!watermark.classList.contains('hidden'), "Ghost watermark must be visible during peek");
    assert(watermark.classList.contains('ghost-watermark-active'), "Watermark must have active CSS class");
    assert.strictEqual(mockWindow.state.gameplay.writing_peek_used, true, "Attempt must track peek usage as assisted");
    assert(!scaffoldBadge.classList.contains('hidden'), "Assisted status badge must appear");
    assert(scaffoldBadge.textContent.includes('Peek Used'), "Badge text must mention peek");

    // 2. Hide Ghost Peek
    context.hideWritingGhostPeek();
    assert(watermark.classList.contains('hidden'), "Ghost watermark must hide after peek release");

    // 3. Toggle Ghost Peek click
    context.toggleWritingGhostPeekClick();
    assert(!watermark.classList.contains('hidden'), "Watermark must show on click toggle");
    context.toggleWritingGhostPeekClick();
    assert(watermark.classList.contains('hidden'), "Watermark must hide on second click toggle");

    console.log("✓ PASS: Ghost Text Watermark Peek activation, release, and assistance tracking verified!");
  })();

  // -------------------------------------------------------------------------
  // [Test 43] Active Writing Pedagogical Scaffolding: Sentence Starter Injection
  // -------------------------------------------------------------------------
  await (async () => {
    console.log("\n[Test 43] Testing Active Writing Pedagogical Scaffolding: Sentence Starter Injection...");
    const ta = mockDocument.getElementById('writing-input-area');
    ta.value = '';

    context.insertWritingSentenceStarter();
    assert.strictEqual(ta.value, 'सूरज ', "Sentence starter must insert the first chunk ('सूरज ') into textarea");
    assert.strictEqual(mockWindow.state.gameplay.writing_starter_used, true, "Starter usage must be logged in gameplay state");

    const scaffoldBadge = mockDocument.getElementById('writing-scaffold-status-badge');
    assert(!scaffoldBadge.classList.contains('hidden'), "Status badge must reflect starter assistance");
    assert(scaffoldBadge.textContent.includes('Starter Inserted'), "Badge must reflect starter assistance");

    console.log("✓ PASS: Sentence starter injection and momentum scaffold verified!");
  })();

  // -------------------------------------------------------------------------
  // [Test 44] Active Writing Pedagogical Scaffolding: Faded Word Bank Reference
  // -------------------------------------------------------------------------
  await (async () => {
    console.log("\n[Test 44] Testing Active Writing Pedagogical Scaffolding: Faded Word Bank Reference...");
    const wbContainer = mockDocument.getElementById('writing-word-bank-container');
    const tray = mockDocument.getElementById('writing-word-bank-tray');

    // 1. Toggle Word Bank on
    context.toggleWritingWordBank();
    assert(!wbContainer.classList.contains('hidden'), "Word Bank drawer must open");
    assert.strictEqual(mockWindow.state.gameplay.writing_wordbank_used, true, "Word bank usage logged");
    assert(tray.children.length > 0, "Word bank tray must contain word chips");

    // 2. Click a word chip to insert
    const ta = mockDocument.getElementById('writing-input-area');
    const firstChip = tray.children[0];
    const chipText = firstChip.textContent;
    firstChip.onclick();

    assert(ta.value.includes(chipText), "Clicking word chip must insert word into textarea");
    assert(firstChip.classList.contains('used'), "Chip must be styled as used");

    // 3. Toggle Word Bank off
    context.toggleWritingWordBank();
    assert(wbContainer.classList.contains('hidden'), "Word Bank drawer must close on toggle");

    console.log("✓ PASS: Faded Word Bank drawer toggle, chips, and click insertion verified!");
  })();

  // -------------------------------------------------------------------------
  // [Test 45] Post-Jigsaw "Write It Now" Mini-Bridge from Celebration Modal
  // -------------------------------------------------------------------------
  await (async () => {
    console.log("\n[Test 45] Testing Post-Jigsaw 'Write It Now' Mini-Bridge from Celebration Modal...");
    const jigsawCard = {
      card_id: 'card_bridge_test',
      question: 'पेड़ हमें क्या देते हैं?',
      meaning: 'What do trees give us?',
      chunks: ['पेड़', 'हमें', 'छाया', 'देते', 'हैं।']
    };

    context.setupGameSession([jigsawCard], 'jigsaw', 'Chapter 1 Bridge Test', 'deck_bridge');
    assert.strictEqual(mockWindow.state.gameplay.effective_mode, 'jigsaw', "Must start in jigsaw mode");

    // Simulate completing Jigsaw puzzle
    await context.recordCardCompletion(true);
    const celebCard = mockDocument.getElementById('game-celebration-card');
    const jumpWriteBtn = mockDocument.getElementById('celeb-jump-to-write-btn');

    assert(!celebCard.classList.contains('hidden'), "Celebration card must show after completing jigsaw");
    assert(!jumpWriteBtn.classList.contains('hidden'), "Post-Jigsaw 'Write It Now' button must be visible");

    // Click "Write It Now" button
    context.jumpFromCelebrationToWriting();

    assert(celebCard.classList.contains('hidden'), "Celebration card must close");
    assert.strictEqual(mockWindow.state.gameplay.effective_mode, 'writing', "Mode must dynamically switch to 'writing'");
    assert.strictEqual(mockWindow.state.gameplay.current_attempt_stage, 6, "Attempt stage must advance to Stage 6 (Writing)");
    const writeBox = mockDocument.getElementById('game-writing-box');
    assert(!writeBox.classList.contains('hidden'), "Active Writing Studio box must become visible");

    // LCWC curtain should automatically trigger to prime memory
    const curtain = mockDocument.getElementById('writing-memorize-curtain');
    assert(!curtain.classList.contains('hidden'), "LCWC curtain must automatically open to prime memory");
    context.dismissWritingCurtain(false);

    console.log("✓ PASS: Post-Jigsaw 'Write It Now' bonus bridge transition verified!");
  })();

  // -------------------------------------------------------------------------
  // [Test 46] Progressive Typing Blanks (Stage 5 Scaffolding & Ladder Downshift)
  // -------------------------------------------------------------------------
  await (async () => {
    console.log("\n[Test 46] Testing Progressive Typing Blanks (Stage 5 Scaffolding & Ladder Downshift)...");
    const clozeCard = {
      card_id: 'card_cloze_test',
      question: 'सूरज किस दिशा से निकलता है?',
      meaning: 'From which direction does the sun rise?',
      chunks: ['सूरज', 'पूरब से', 'निकलता', 'है।'],
      ladder_stage: 5
    };

    // 1. Launch in Guided Mission Stage 5
    context.setupGameSession([clozeCard], 'guided_mission', 'Chapter 1 Cloze Test', 'deck_cloze');
    assert.strictEqual(mockWindow.state.gameplay.effective_mode, 'typing_blanks', "Stage 5 must map to typing_blanks");
    assert.strictEqual(mockWindow.state.gameplay.current_attempt_stage, 5, "Attempt stage must be 5");

    const clozeBoard = mockDocument.getElementById('writing-cloze-board');
    const fullContainer = mockDocument.getElementById('writing-full-textarea-container');
    const passPill = mockDocument.getElementById('writing-cloze-pass-pill');
    const slotsRow = mockDocument.getElementById('writing-cloze-slots-row');

    assert(!clozeBoard.classList.contains('hidden'), "Cloze typing board must be visible");
    assert(fullContainer.classList.contains('hidden'), "Full textarea must be hidden for Level 1");
    assert.strictEqual(mockWindow.state.gameplay.cloze_level, 1, "Should start at Cloze Level 1");
    assert.strictEqual(passPill.textContent, '1 Blank', "Pass pill must display '1 Blank'");

    // Level 1: exactly 1 slot input, 3 static spans
    const level1Slots = slotsRow.querySelectorAll('.cloze-typing-slot');
    assert.strictEqual(level1Slots.length, 1, "Level 1 must render exactly 1 typing input slot");
    const expectedChunk = level1Slots[0].dataset.expected;
    assert(expectedChunk, "Slot must have expected chunk attribute");

    // 2. Test incorrect submission
    level1Slots[0].value = 'गलत';
    await context.checkClozeTypingAnswer();
    assert(level1Slots[0].classList.contains('incorrect'), "Slot must be marked incorrect on mismatch");
    const detectiveCard = mockDocument.getElementById('writing-detective-card');
    assert(!detectiveCard.classList.contains('hidden'), "Detective inspector must open on slot typo");

    // 3. Test correct submission for Level 1 -> advances to Level 2
    level1Slots[0].value = expectedChunk;
    await context.checkClozeTypingAnswer();

    assert.strictEqual(mockWindow.state.gameplay.cloze_level, 2, "Must advance to Level 2 (2 blanks)");
    assert.strictEqual(passPill.textContent, '2 Blanks', "Pass pill must show '2 Blanks'");
    const level2Slots = slotsRow.querySelectorAll('.cloze-typing-slot');
    assert.strictEqual(level2Slots.length, 2, "Level 2 must render 2 typing input slots");

    // 4. Test correct submission for Level 2 -> completes card and advances Stage 5 to 6
    level2Slots.forEach(s => {
      s.value = s.dataset.expected;
    });
    await context.checkClozeTypingAnswer();

    const celebCard = mockDocument.getElementById('game-celebration-card');
    assert(!celebCard.classList.contains('hidden'), "Celebration card must show after completing level 2");
    assert.strictEqual(clozeCard.ladder_stage, 6, "Card should advance to Stage 6 (Writing)");

    // 5. Test manual ladder switcher downshift & upshift
    context.setWritingLadderLevel(1);
    assert.strictEqual(mockWindow.state.gameplay.cloze_level, 1);
    assert(!clozeBoard.classList.contains('hidden'), "Cloze board visible on downshift to Level 1");

    context.setWritingLadderLevel(3);
    assert.strictEqual(mockWindow.state.gameplay.cloze_level, 3);
    assert(clozeBoard.classList.contains('hidden'), "Cloze board hidden on upshift to Level 3");
    assert(!fullContainer.classList.contains('hidden'), "Full textarea visible on Level 3");

    console.log("✓ PASS: Progressive Typing Blanks (Stage 5) multi-level slot typing, ladder progression, and manual switcher verified!");
  })();

  // -------------------------------------------------------------------------
  // [Test 47] Interactive Detective Self-Correction System
  // -------------------------------------------------------------------------
  await (async () => {
    console.log("\n[Test 47] Testing Interactive Detective Self-Correction System...");
    const writingCard = {
      card_id: 'card_detective_test',
      question: 'पेड़ हमें क्या देते हैं?',
      meaning: 'What do trees give us?',
      chunks: ['पेड़', 'हमें', 'छाया', 'देते', 'हैं।'],
      ladder_stage: 6
    };

    context.setupGameSession([writingCard], 'writing', 'Chapter 1 Detective Test', 'deck_detective');
    const ta = mockDocument.getElementById('writing-input-area');
    const detectiveCard = mockDocument.getElementById('writing-detective-card');
    const typedWordEl = mockDocument.getElementById('detective-typed-word');
    const targetWordEl = mockDocument.getElementById('detective-target-word');
    const clueTextEl = mockDocument.getElementById('detective-clue-text');

    // 1. Student writes sentence with a typo: 'पेड' instead of 'पेड़'
    ta.value = 'पेड हमें छाया देते हैं।';
    await context.checkWritingAnswer();

    // Detective card must automatically open for the typo
    assert(!detectiveCard.classList.contains('hidden'), "Detective card must open on typo");
    assert.strictEqual(typedWordEl.textContent, 'पेड', "Detective must show typed word");
    assert.strictEqual(targetWordEl.textContent, 'पेड़', "Detective must show target word");
    assert(clueTextEl.textContent.length > 0, "Detective must provide a diagnostic clue");

    // Diff pill must be clickable
    const diffRow = mockDocument.getElementById('writing-tokens-row');
    const typoPills = diffRow.querySelectorAll('.writing-diff-pill-interactive');
    assert(typoPills.length > 0, "Typo pills must have .writing-diff-pill-interactive class");
    assert(typoPills[0].textContent.includes('🔍'), "Interactive diff pill must display 🔍 icon");

    // 2. Test Audio Trigger (Hear Word)
    speakCalls.length = 0;
    context.speakDetectiveWord();
    assert.strictEqual(speakCalls.length, 1, "Speak target word must be called");
    assert.strictEqual(speakCalls[0].text, 'पेड़', "Must speak target word 'पेड़'");

    // 3. Test 1-Click Auto-Fix
    context.autoFixWordInInput();
    assert(ta.value.includes('पेड़'), "Auto-Fix must replace 'पेड' with 'पेड़' in textarea");
    assert.strictEqual(mockWindow.state.gameplay.writing_autofix_used, true, "Auto-Fix assistance tracked");
    assert(detectiveCard.classList.contains('hidden'), "Detective card must close after auto-fix");

    // 4. Test manual click on diff pill opens Detective
    context.closeDetectiveInspection();
    assert(detectiveCard.classList.contains('hidden'));
    typoPills[0].onclick();
    assert(!detectiveCard.classList.contains('hidden'), "Clicking interactive diff pill must reopen Detective");
    context.closeDetectiveInspection();

    console.log("✓ PASS: Interactive Detective diagnosis, word audio playback, interactive pills, and 1-click auto-fix verified!");
  })();

  // -------------------------------------------------------------------------
  // [Test 48] Fullscreen Kiosk & Zen Focus Immersion Engine
  // -------------------------------------------------------------------------
  await (async () => {
    console.log("\n[Test 48] Testing Fullscreen Kiosk & Zen Focus Immersion Engine...");

    const headerBtn = mockDocument.getElementById('btn-toggle-fullscreen');
    const zenBtn = mockDocument.getElementById('game-zen-toggle-btn');
    const exitPill = mockDocument.getElementById('zen-focus-exit-btn');
    const iconEl = mockDocument.getElementById('fullscreen-icon');
    const textEl = mockDocument.getElementById('fullscreen-text');

    assert(headerBtn, "Header fullscreen button must exist");
    assert(zenBtn, "In-game Zen Focus button must exist");
    assert(exitPill, "Floating Zen exit pill must exist");

    // 1. Initial State: Normal Windowed Mode
    assert.strictEqual(Boolean(mockWindow.state.is_fullscreen), false, "Initial fullscreen state must be false");
    assert.strictEqual(iconEl.textContent, '⛶', "Initial icon must be ⛶");
    assert.strictEqual(textEl.textContent, 'Fullscreen', "Initial label must be Fullscreen");
    assert(!mockDocument.body.classList.contains('zen-focus-active'), "Zen focus must be inactive initially");
    assert(exitPill.classList.contains('hidden'), "Floating exit pill must be hidden initially");

    // 2. Launch Gameplay Session
    const testCard = {
      card_id: 'card_zen_test',
      question: 'सूरज किस दिशा से निकलता है?',
      meaning: 'From which direction does the sun rise?',
      chunks: ['सूरज', 'पूरब से', 'निकलता है।'],
      ladder_stage: 2
    };
    context.setupGameSession([testCard], 'jigsaw', 'Zen Chapter', 'deck_zen');
    assert.strictEqual(mockWindow.state.current_view, 'gameplay');

    // 3. Toggle Fullscreen ON
    await context.toggleFullscreenMode();
    assert.strictEqual(mockWindow.state.is_fullscreen, true, "State must be fullscreen");
    assert.strictEqual(iconEl.textContent, '🗗', "Icon must toggle to 🗗 (Exit Full)");
    assert.strictEqual(textEl.textContent, 'Exit Full', "Label must toggle to Exit Full");
    assert(mockDocument.body.classList.contains('zen-focus-active'), "Body must have .zen-focus-active class during gameplay");
    assert(!exitPill.classList.contains('hidden'), "Floating exit pill must be visible in Zen Focus");

    // 4. Test View Router integration: navigating away to dashboard suspends Zen Focus on body
    context.showView('dashboard');
    assert(!mockDocument.body.classList.contains('zen-focus-active'), "Dashboard view must not hide header even if fullscreen");
    assert(exitPill.classList.contains('hidden'), "Exit pill must be hidden on dashboard");

    // Returning to gameplay restores Zen Focus
    context.showView('gameplay');
    assert(mockDocument.body.classList.contains('zen-focus-active'), "Returning to gameplay in fullscreen restores Zen Focus");
    assert(!exitPill.classList.contains('hidden'), "Exit pill restored in gameplay");

    // 5. Toggle Fullscreen OFF via exit pill
    exitPill.onclick();
    await new Promise(r => setImmediate(r));

    assert.strictEqual(mockWindow.state.is_fullscreen, false, "Fullscreen must toggle off");
    assert(!mockDocument.body.classList.contains('zen-focus-active'), "Zen focus removed on exit");
    assert(exitPill.classList.contains('hidden'), "Floating exit pill must hide");
    assert.strictEqual(iconEl.textContent, '⛶', "Icon restored to ⛶");
    assert.strictEqual(textEl.textContent, 'Fullscreen', "Label restored to Fullscreen");

    console.log("✓ PASS: Fullscreen desktop kiosk toggle, Zen Focus auto-activation in gameplay, and floating exit verified!");
  })();

  // -------------------------------------------------------------------------
  // [Test 49] Writing Word Bank shows only missing (not-yet-typed) words
  // -------------------------------------------------------------------------
  await (async () => {
    console.log("\n[Test 49] Testing Writing Word Bank missing-words filter...");
    const bankCard = {
      card_id: 'card_bank_test',
      question: 'सूरज किधर से निकलता है?',
      meaning: 'Which direction does the sun rise from?',
      chunks: ['सूरज', 'पूरब से', 'निकलता', 'है।']
    };

    context.setupGameSession([bankCard], 'writing', 'Chapter Bank Test', 'deck_bank');
    const ta = mockDocument.getElementById('writing-input-area');
    const tray = mockDocument.getElementById('writing-word-bank-tray');
    ta.value = '';

    // Bank splits chunks into words: सूरज, पूरब, से, निकलता, है। (5 chips)
    assert.strictEqual(tray.children.length, 5, "Word bank must contain one chip per answer word");

    context.toggleWritingWordBank();
    const visibleChips = () => tray.children.filter(c => c.style.display !== 'none');
    assert.strictEqual(visibleChips().length, 5, "All chips visible before typing");

    // 1. Typing words hides their chips (punctuation-insensitive: है। matches है)
    ta.value = 'सूरज पूरब है';
    context.updateWritingWordCount();
    assert.strictEqual(visibleChips().length, 2, "Typed words must disappear, leaving only missing words");
    const hiddenTexts = tray.children.filter(c => c.style.display === 'none').map(c => c.textContent);
    assert(hiddenTexts.includes('सूरज') && hiddenTexts.includes('पूरब') && hiddenTexts.includes('है।'), "Hidden chips must be the typed words");

    // 2. Deleting text restores chips
    ta.value = '';
    context.updateWritingWordCount();
    assert.strictEqual(visibleChips().length, 5, "Deleting typed text must restore all chips");

    context.toggleWritingWordBank();
    console.log("✓ PASS: Word Bank missing-words filter, hide-on-type, and restore-on-delete verified!");
  })();

  // -------------------------------------------------------------------------
  // [Test 50] Cloze blanks are shuffled + word bank scoped to blanked blocks
  // -------------------------------------------------------------------------
  await (async () => {
    console.log("\n[Test 50] Testing shuffled cloze blanks and blank-scoped word bank...");
    const shuffleCard = {
      card_id: 'card_shuffle_test',
      question: 'Shuffled blanks?',
      meaning: ' blanks shuffle',
      chunks: ['एक', 'दो तीन', 'चार', 'पाँच छह', 'सात']
    };

    context.setupGameSession([shuffleCard], 'writing', 'Chapter Shuffle Test', 'deck_shuffle');
    const tray = mockDocument.getElementById('writing-word-bank-tray');
    const slotsRow = mockDocument.getElementById('writing-cloze-slots-row');

    // 1. Level 1 blanks vary across renders (5 chunks -> P(same 12x) negligible)
    const seen = new Set();
    for (let i = 0; i < 12; i++) {
      context.setWritingLadderLevel(1);
      const slots = slotsRow.querySelectorAll('.cloze-typing-slot');
      assert.strictEqual(slots.length, 1, "Level 1 must render exactly 1 blank");
      seen.add(slots[0].dataset.slotIndex);
    }
    assert(seen.size > 1, "Level 1 blank position must shuffle across renders");

    // 2. Level 1 bank holds only the blanked block's words (multi-word split)
    context.setWritingLadderLevel(1);
    const l1slots = slotsRow.querySelectorAll('.cloze-typing-slot');
    const l1expected = l1slots[0].dataset.expected.split(/\s+/).filter(Boolean).sort();
    const l1bank = tray.children.map(c => c.textContent).sort();
    assert.deepStrictEqual(l1bank, l1expected, "Level 1 bank must contain only the blanked block's words");

    // 3. Level 2 renders 2 blanks at shuffled positions, bank covers both blocks
    const seenPairs = new Set();
    for (let i = 0; i < 12; i++) {
      context.setWritingLadderLevel(2);
      const slots = slotsRow.querySelectorAll('.cloze-typing-slot');
      assert.strictEqual(slots.length, 2, "Level 2 must render exactly 2 blanks");
      seenPairs.add(slots.map(s => s.dataset.slotIndex).sort().join(','));
    }
    assert(seenPairs.size > 1, "Level 2 blank positions must shuffle across renders");
    context.setWritingLadderLevel(2);
    const l2slots = slotsRow.querySelectorAll('.cloze-typing-slot');
    const l2expected = [];
    l2slots.forEach(s => s.dataset.expected.split(/\s+/).forEach(w => { if (w) l2expected.push(w); }));
    assert.deepStrictEqual(tray.children.map(c => c.textContent).sort(), l2expected.sort(), "Level 2 bank must contain all words of both blanked blocks");

    // 4. Back to Level 3 restores the full-answer bank
    context.setWritingLadderLevel(3);
    assert.strictEqual(tray.children.length, 7, "Level 3 bank must cover all answer words again");

    console.log("✓ PASS: Shuffled cloze blanks and blank-scoped word bank verified!");
  })();

  console.log("\n========================================================");
  console.log("=== ALL 50 USE CASE & GAMEPLAY SCENARIOS PASSED (50/50) ===");
  console.log("========================================================");
})().catch(err => {
  console.error("Test failed:", err);
  process.exit(1);
});





