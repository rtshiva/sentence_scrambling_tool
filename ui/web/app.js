
// Sentence Jigsaw 3.0 Web Application Logic
let state = {
  active_profile: 'Arya',
  profiles: ['Arya', 'Student 2'],
  decks: [],
  exam_metrics: {
    exam_name: 'Class 4 Mid-Term English Exam',
    days_left: 14,
    total_cards: 85,
    mastered_cards: 53,
    daily_quota: 3,
    readiness_percent: 62,
    status_tag: 'On Track'
  },
  mission_queue: [],
  current_scope: 'all',
  selected_step: 4
};

const ladderStepsInfo = {
  1: {
    title: 'Stage 1: Fill-in-the-Blanks Scaffolding',
    goal: 'Goal: Master contextual recognition (1-2 key words hidden)',
    desc: 'The sentence is presented with 1-2 chunks hidden as slots. The student chooses the correct missing chunk from a small candidate pool. Builds early sentence familiarity without cognitive overload.'
  },
  2: {
    title: 'Stage 2: Jigsaw Scramble Puzzle',
    goal: 'Goal: Full grammatical and syntax assembly',
    desc: 'All words and phrase chunks are scrambled. The student reconstructs the full sentence structure in proper order. Reinforces word ordering and grammatical clauses.'
  },
  3: {
    title: 'Stage 3: Listening Comprehension',
    goal: 'Goal: Auditory decoding with masked text prompt',
    desc: 'Sentence text is masked. The student listens to the native audio recording and clicks chips to recreate the heard sentence. Connects phonemes directly to orthography.'
  },
  4: {
    title: 'Stage 4: Voice Mastery Production',
    goal: 'Goal: Spoken fluency (≥ 80% pronunciation score)',
    desc: 'The sentence text is displayed. The learner speaks aloud into the microphone. Whisper AI transcribes and provides word-by-word phonics feedback. Mastered cards graduate to Stage 5!'
  },
  5: {
    title: 'Stage 5: Speed Run Fluency',
    goal: 'Goal: Rapid automatic recall under timed challenge',
    desc: 'Rapid-fire recall with countdown timer. Encourages retrieval automaticity, building fluency and exam confidence.'
  },
  6: {
    title: 'Stage 6: Active Writing & Spelling',
    goal: 'Goal: Unassisted active recall & exact orthography',
    desc: 'No jigsaw chips or scaffolding. The learner types the full sentence from memory or prompt. Spelling, punctuation, and capitalization are evaluated word-by-word.'
  }
};

// Initialize bridge or fallback to demo data
window.addEventListener('pywebviewready', async function() {
  console.log("pywebview bridge is ready!");
  try {
    const pyState = await window.pywebview.api.get_state();
    if (pyState) {
      state = { ...state, ...pyState };
    }
  } catch (e) {
    console.warn("Failed to load initial state from Python:", e);
  }
  refreshUI();
});

// If opened in plain browser (development preview)
window.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    if (!window.pywebview) {
      console.log("Running in standalone preview mode with sample data.");
      // Seed sample decks if empty
      if (!state.decks || state.decks.length === 0) {
        state.decks = [
          {
            id: 'deck_1',
            title: 'English Class 4 - Chapter 1',
            subject: 'English Grammar',
            description: 'Core reading vocabulary and sentence patterns from Chapter 1.',
            cards: [
              { question: 'Q1', chunks: ['The', 'cat', 'slept'], ladder_stage: 6 },
              { question: 'Q2', chunks: ['The', 'sun', 'rose'], ladder_stage: 4 },
              { question: 'Q3', chunks: ['Birds', 'sing', 'sweetly'], ladder_stage: 2 }
            ],
            tags: ['exam', 'ch1']
          },
          {
            id: 'deck_2',
            title: 'Science: Plants & Photosynthesis',
            subject: 'Science',
            description: 'Scientific facts and plant lifecycle sentences.',
            cards: [
              { question: 'Q1', chunks: ['Plants', 'absorb', 'sunlight'], ladder_stage: 5 },
              { question: 'Q2', chunks: ['Chlorophyll', 'traps', 'light'], ladder_stage: 3 }
            ],
            tags: ['exam']
          },
          {
            id: 'deck_3',
            title: 'French Basics: Greetings & Numbers',
            subject: 'French Basics',
            description: 'Daily conversational expressions and numbers in French.',
            cards: [
              { question: 'Q1', chunks: ['Bonjour', 'mon', 'ami'], ladder_stage: 1 }
            ],
            tags: []
          }
        ];
      }
      refreshUI();
    }
  }, 100);
});

function refreshUI() {
  // Update header student info
  document.getElementById('active-student-name').textContent = state.active_profile;
  
  // Update target exam banner
  if (state.exam_metrics) {
    const em = state.exam_metrics;
    document.getElementById('target-exam-text').textContent = `${em.exam_name || 'Class 4 Mid-Term'} (${em.days_left || 14} Days)`;
    
    // Tab 3 elements
    document.getElementById('exam-title').textContent = em.exam_name || 'Class 4 Mid-Term English Exam';
    document.getElementById('exam-meta').textContent = `Exam Date: In ${em.days_left || 14} Days • ${em.total_cards || 0} Cards in Scope`;
    document.getElementById('exam-readiness-val').textContent = `${em.readiness_percent || 0}% Complete`;
    document.getElementById('exam-progress-bar').style.width = `${em.readiness_percent || 0}%`;
    document.getElementById('stat-days-left').textContent = em.days_left || 0;
    document.getElementById('stat-cards-count').textContent = `${em.mastered_cards || 0} / ${em.total_cards || 0}`;
    document.getElementById('stat-daily-quota').textContent = `${em.daily_quota || 0} Cards/Day`;
    document.getElementById('exam-status-tag').textContent = em.status_tag || 'On Track';
    
    // Status tag styling
    const tagEl = document.getElementById('exam-status-tag');
    if (em.status_tag === 'Intensive') {
      tagEl.className = 'text-xs bg-rose-100 text-rose-800 font-bold px-3 py-1.5 rounded-full';
    } else if (em.status_tag === 'Moderate') {
      tagEl.className = 'text-xs bg-amber-100 text-amber-800 font-bold px-3 py-1.5 rounded-full';
    } else {
      tagEl.className = 'text-xs bg-emerald-100 text-emerald-800 font-bold px-3 py-1.5 rounded-full';
    }
  }

  // Populate subject filter options
  populateSubjectFilter();

  // Render decks
  filterDecks();

  // Render mission queue
  renderMissionQueue();
}

function populateSubjectFilter() {
  const subjects = new Set();
  (state.decks || []).forEach(d => {
    if (d.subject) subjects.add(d.subject);
  });
  const sel = document.getElementById('deck-subject-filter');
  const currVal = sel.value;
  sel.innerHTML = '<option value="All">All Subjects</option>';
  subjects.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s;
    opt.textContent = s;
    sel.appendChild(opt);
  });
  if (subjects.has(currVal)) sel.value = currVal;
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('tab-active');
    btn.classList.add('border-transparent', 'text-slate-500');
  });

  const target = document.getElementById(tabId);
  if (target) target.classList.remove('hidden');

  const activeBtn = document.getElementById('btn-' + tabId);
  if (activeBtn) {
    activeBtn.classList.add('tab-active');
    activeBtn.classList.remove('border-transparent', 'text-slate-500');
  }
}

function setScope(scope) {
  state.current_scope = scope;
  ['all', 'exam', 'due'].forEach(s => {
    const btn = document.getElementById('scope-' + s);
    if (s === scope) {
      btn.className = 'px-3 py-1 rounded-lg bg-white shadow-xs text-indigo-700 font-bold';
    } else {
      btn.className = 'px-3 py-1 rounded-lg text-slate-600 hover:text-slate-900';
    }
  });
  filterDecks();
}

function filterDecks() {
  const query = (document.getElementById('deck-search').value || '').toLowerCase();
  const subject = document.getElementById('deck-subject-filter').value;
  const scope = state.current_scope;

  const filtered = (state.decks || []).filter(deck => {
    const matchesSearch = !query || 
      (deck.title && deck.title.toLowerCase().includes(query)) ||
      (deck.subject && deck.subject.toLowerCase().includes(query)) ||
      (deck.description && deck.description.toLowerCase().includes(query));

    const matchesSubject = (subject === 'All') || (deck.subject === subject);

    let matchesScope = true;
    if (scope === 'exam') {
      matchesScope = (deck.tags && deck.tags.includes('exam'));
    } else if (scope === 'due') {
      matchesScope = true; // In full engine, checks spaced repetition
    }

    return matchesSearch && matchesSubject && matchesScope;
  });

  renderDecksGrid(filtered);
}

function renderDecksGrid(decks) {
  const grid = document.getElementById('decks-grid');
  grid.innerHTML = '';

  if (decks.length === 0) {
    grid.innerHTML = `
      <div class="col-span-full text-center py-12 bg-white border border-slate-200 rounded-2xl p-8">
        <div class="text-4xl mb-2">📁</div>
        <h4 class="text-base font-bold text-slate-800">No Decks Found</h4>
        <p class="text-xs text-slate-500 mt-1">Try adjusting your search query or click "+ New Deck" to create one.</p>
      </div>
    `;
    return;
  }

  decks.forEach(deck => {
    const cards = deck.cards || [];
    const totalCount = cards.length;
    const masteredCount = cards.filter(c => (c.ladder_stage || 1) >= 6).length;
    const pct = totalCount > 0 ? Math.round((masteredCount / totalCount) * 100) : 0;
    const isExam = deck.tags && deck.tags.includes('exam');

    const cardEl = document.createElement('div');
    cardEl.className = 'bg-white border border-slate-200 hover:border-indigo-300 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4';

    cardEl.innerHTML = `
      <div>
        <div class="flex items-center justify-between gap-2 mb-2">
          <span class="text-[11px] font-bold bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-full uppercase tracking-wider">
            ${deck.subject || 'General'}
          </span>
          ${isExam ? '<span class="text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full">🎯 Target Exam</span>' : ''}
        </div>
        <h3 class="text-base font-bold text-slate-900">${deck.title}</h3>
        <p class="text-xs text-slate-500 line-clamp-2 mt-1 leading-relaxed">${deck.description || 'No description provided.'}</p>
      </div>

      <!-- Mastery Bar -->
      <div>
        <div class="flex justify-between text-[11px] font-semibold text-slate-500 mb-1.5">
          <span>Mastery</span>
          <span class="font-bold text-slate-700">${pct}%</span>
        </div>
        <div class="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
          <div class="bg-indigo-600 h-full rounded-full transition-all duration-300" style="width: ${pct}%"></div>
        </div>
      </div>

      <!-- Stats Counters -->
      <div class="flex items-center justify-between text-xs text-slate-500 pt-1 border-t border-slate-100">
        <span>Cards: <strong class="text-slate-800">${totalCount}</strong></span>
        <span>Due Today: <strong class="text-indigo-600 font-bold">${Math.max(1, totalCount - masteredCount)}</strong></span>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-2 pt-1">
        <button onclick="launchDeckMission('${deck.id}')" class="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs py-2 rounded-xl transition shadow-xs">
          Study Mission
        </button>
        <button onclick="launchDeckJigsaw('${deck.id}')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs px-3 py-2 rounded-xl transition">
          Play Jigsaw
        </button>
        <button onclick="confirmDeleteDeck('${deck.id}', '${deck.title}')" class="text-slate-400 hover:text-rose-600 text-sm px-2 py-1 transition" title="Delete Deck">
          🗑️
        </button>
      </div>
    `;

    grid.appendChild(cardEl);
  });
}

function renderMissionQueue() {
  const list = document.getElementById('mission-queue-list');
  const countBadge = document.getElementById('queue-count-badge');
  list.innerHTML = '';

  const queue = state.mission_queue && state.mission_queue.length > 0 
    ? state.mission_queue 
    : [
        { question: 'The gentle breeze whispered softly through the trees.', ladder_stage: 4 },
        { question: 'Photosynthesis converts sunlight into usable energy.', ladder_stage: 5 },
        { question: 'Curiosity and perseverance are keys to discovery.', ladder_stage: 2 }
      ];

  countBadge.textContent = `${queue.length} Cards Due`;

  queue.slice(0, 8).forEach(item => {
    const stage = item.ladder_stage || 1;
    const row = document.createElement('div');
    row.className = 'py-3 flex items-center justify-between text-xs';
    row.innerHTML = `
      <div class="flex items-center gap-3">
        <span class="text-base">${getStageIcon(stage)}</span>
        <div>
          <div class="font-bold text-slate-800">${item.question}</div>
          <div class="text-[11px] text-slate-400 font-medium">Stage ${stage}: ${getStageName(stage)}</div>
        </div>
      </div>
      <span class="bg-slate-100 text-slate-600 font-bold px-2.5 py-1 rounded-full">Due Today</span>
    `;
    list.appendChild(row);
  });
}

function getStageIcon(st) {
  const icons = { 1: '🧩', 2: '🎯', 3: '🎧', 4: '🎙️', 5: '⏱️', 6: '✍️' };
  return icons[st] || '🧩';
}

function getStageName(st) {
  const names = { 1: 'Fill Blanks', 2: 'Jigsaw', 3: 'Listening', 4: 'Voice Mastery', 5: 'Speed Run', 6: 'Written Typing' };
  return names[st] || 'Mastery';
}

function setLadderStep(step) {
  state.selected_step = step;
  document.querySelectorAll('.ladder-step').forEach((el, idx) => {
    const curStep = idx + 1;
    el.className = 'ladder-step border-2 rounded-xl p-3 text-center transition-all cursor-pointer';
    if (curStep < step) {
      el.classList.add('completed');
    } else if (curStep === step) {
      el.classList.add('active', 'shadow-sm');
    } else {
      el.classList.add('border-slate-200', 'bg-slate-50', 'text-slate-600');
    }
  });

  const info = ladderStepsInfo[step] || ladderStepsInfo[4];
  document.getElementById('step-preview-title').textContent = info.title;
  document.getElementById('step-preview-desc').innerHTML = info.desc;
}

// ----------------- Writing Sandbox -----------------
async function submitWriting() {
  const target = document.getElementById('writing-target-sentence').textContent.trim();
  const input = document.getElementById('writing-input').value.trim();
  if (!input) return;

  let evalResult = null;
  if (window.pywebview) {
    try {
      evalResult = await window.pywebview.api.evaluate_spelling(target, input);
    } catch (e) {
      console.warn("Bridge evaluate_spelling failed:", e);
    }
  }

  if (!evalResult) {
    // Basic client-side simulation if bridge not present
    const cleanTarget = target.toLowerCase().replace(/[^a-z0-9 ]/g, '');
    const cleanInput = input.toLowerCase().replace(/[^a-z0-9 ]/g, '');
    const match = cleanTarget === cleanInput;
    evalResult = {
      overall_score: match ? 100 : 75,
      flawless: match,
      tokens: input.split(' ').map(w => ({ word: w, status: match ? 'correct' : 'typo' }))
    };
  }

  const outputBox = document.getElementById('writing-eval-output');
  outputBox.classList.remove('hidden');

  const badge = document.getElementById('writing-score-badge');
  badge.textContent = `Score: ${evalResult.overall_score}% Match`;
  badge.className = evalResult.flawless 
    ? 'text-xs font-bold px-3 py-1 rounded-full bg-emerald-100 text-emerald-800'
    : 'text-xs font-bold px-3 py-1 rounded-full bg-rose-100 text-rose-800';

  document.getElementById('writing-flawless-tag').textContent = evalResult.flawless 
    ? '⭐ Flawless Orthography & Punctuation' 
    : '🔄 Review Highlighted Tokens';

  const tokensContainer = document.getElementById('writing-tokens-container');
  tokensContainer.innerHTML = '';
  (evalResult.tokens || []).forEach(t => {
    const chip = document.createElement('span');
    chip.textContent = t.word || '';
    if (t.status === 'correct') {
      chip.className = 'px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300';
    } else if (t.status === 'typo') {
      chip.className = 'px-2.5 py-1 rounded-lg text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300 underline decoration-wavy';
    } else if (t.status === 'missing') {
      chip.className = 'px-2.5 py-1 rounded-lg text-xs font-bold bg-purple-100 text-purple-800 border border-purple-300 italic';
    } else {
      chip.className = 'px-2.5 py-1 rounded-lg text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300';
    }
    tokensContainer.appendChild(chip);
  });
}

function speakCurrentTarget() {
  const target = document.getElementById('writing-target-sentence').textContent.trim();
  if (window.pywebview) {
    window.pywebview.api.speak_text(target, 'en');
  } else if ('speechSynthesis' in window) {
    const u = new SpeechSynthesisUtterance(target);
    window.speechSynthesis.speak(u);
  }
}

// ----------------- Launch Actions -----------------
function launchDeckMission(deckId) {
  if (window.pywebview) {
    window.pywebview.api.launch_gameplay(deckId, 'guided_mission');
  } else {
    alert("Launching Guided Mission for Deck: " + deckId);
  }
}

function launchDeckJigsaw(deckId) {
  if (window.pywebview) {
    window.pywebview.api.launch_gameplay(deckId, 'mastery');
  } else {
    alert("Launching Jigsaw Puzzle for Deck: " + deckId);
  }
}

function launchMissionGameplay() {
  if (window.pywebview) {
    window.pywebview.api.launch_gameplay(null, 'guided_mission');
  } else {
    alert("Launching Daily Guided Mission Queue!");
  }
}

function launchExamMission() {
  if (window.pywebview) {
    window.pywebview.api.launch_gameplay(null, 'guided_mission');
  } else {
    alert("Launching Exam Goal Mission Queue!");
  }
}

// ----------------- Profile Modal -----------------
function showProfileModal() {
  const modal = document.getElementById('profile-modal');
  const list = document.getElementById('profiles-list');
  list.innerHTML = '';
  (state.profiles || ['Arya']).forEach(name => {
    const item = document.createElement('div');
    const isAct = name === state.active_profile;
    item.className = `p-2.5 rounded-xl cursor-pointer text-xs font-bold flex justify-between items-center transition ${isAct ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-slate-100 text-slate-700'}`;
    item.innerHTML = `<span>👤 ${name}</span>${isAct ? '<span>✓</span>' : ''}`;
    item.onclick = async () => {
      if (window.pywebview) {
        const refreshed = await window.pywebview.api.switch_profile(name);
        if (refreshed) state = { ...state, ...refreshed };
      } else {
        state.active_profile = name;
      }
      refreshUI();
      closeProfileModal();
    };
    list.appendChild(item);
  });
  modal.classList.remove('hidden');
}

function closeProfileModal() {
  document.getElementById('profile-modal').classList.add('hidden');
}

async function createProfile() {
  const inp = document.getElementById('new-profile-name');
  const name = inp.value.trim();
  if (!name) return;
  if (window.pywebview) {
    const refreshed = await window.pywebview.api.create_profile(name);
    if (refreshed) state = { ...state, ...refreshed };
  } else {
    state.profiles.push(name);
    state.active_profile = name;
  }
  inp.value = '';
  refreshUI();
  closeProfileModal();
}

// ----------------- Deck Modal & Management -----------------
function openCreateDeckModal() {
  document.getElementById('deck-modal').classList.remove('hidden');
}

function closeDeckModal() {
  document.getElementById('deck-modal').classList.add('hidden');
}

async function saveNewDeck() {
  const title = document.getElementById('new-deck-title').value.trim();
  const subject = document.getElementById('new-deck-subject').value.trim() || 'General';
  const desc = document.getElementById('new-deck-desc').value.trim();
  if (!title) return;

  const deckData = {
    title: title,
    subject: subject,
    description: desc,
    cards: [],
    tags: []
  };

  if (window.pywebview) {
    const newDeck = await window.pywebview.api.save_deck(deckData);
    if (newDeck) state.decks.push(newDeck);
  } else {
    deckData.id = 'deck_' + Date.now();
    state.decks.push(deckData);
  }

  document.getElementById('new-deck-title').value = '';
  document.getElementById('new-deck-subject').value = '';
  document.getElementById('new-deck-desc').value = '';
  closeDeckModal();
  refreshUI();
}

async function confirmDeleteDeck(deckId, title) {
  if (!confirm(`Are you sure you want to delete deck "${title}"?`)) return;
  if (window.pywebview) {
    await window.pywebview.api.delete_deck(deckId);
  }
  state.decks = state.decks.filter(d => d.id !== deckId);
  refreshUI();
}

async function importDeckFile() {
  if (window.pywebview) {
    const imported = await window.pywebview.api.import_deck_file();
    if (imported) {
      state.decks.push(imported);
      refreshUI();
    }
  } else {
    alert("Importing files is enabled when running through the desktop launcher.");
  }
}
