
// Sentence Jigsaw 3.0 Web Application Logic
let state = {
  active_profile: 'Arya',
  profiles: ['Arya'],
  decks: [],
  exam_metrics: {
    id: 'exam_midterm',
    exam_name: 'Class 4 Mid-Term English Exam',
    target_date: '',
    days_left: 14,
    total_cards: 0,
    mastered_cards: 0,
    daily_quota: 3,
    readiness_percent: 0,
    status_tag: 'On Track',
    selected_scope: {},
    chapters_breakdown: []
  },
  all_decks_chapters: [],
  mission_queue: [],
  current_scope: 'all',
  selected_step: 4,
  chapter_filter: 'all'
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
  await reloadState();
  refreshUI();
});

async function reloadState() {
  try {
    if (window.pywebview) {
      const pyState = await window.pywebview.api.get_state();
      if (pyState) {
        state = { ...state, ...pyState };
      }
      const decksChaps = await window.pywebview.api.get_all_decks_with_chapters();
      if (decksChaps) {
        state.all_decks_chapters = decksChaps;
      }
    }
  } catch (e) {
    console.warn("Failed to load state from Python:", e);
  }
}

// Development preview fallback
window.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    if (!window.pywebview) {
      console.log("Running in standalone preview mode with sample data.");
      if (!state.decks || state.decks.length === 0) {
        state.decks = [
          {
            id: 'deck_1',
            title: 'English Class 4 - Reader',
            subject: 'English Grammar',
            description: 'Core reading vocabulary and sentence patterns from Reader.',
            cards: [
              { question: 'The wind whispered softly.', chunks: ['The wind', 'whispered', 'softly.'], lesson_name: 'Chapter 1: The Wind', ladder_stage: 6 },
              { question: 'Leaves danced in the autumn sky.', chunks: ['Leaves', 'danced in', 'the autumn sky.'], lesson_name: 'Chapter 1: The Wind', ladder_stage: 6 },
              { question: 'The ant worked tirelessly all summer.', chunks: ['The ant', 'worked tirelessly', 'all summer.'], lesson_name: 'Chapter 2: The Ant & Grasshopper', ladder_stage: 4 },
              { question: 'Winter arrived with bitter frost.', chunks: ['Winter', 'arrived with', 'bitter frost.'], lesson_name: 'Chapter 2: The Ant & Grasshopper', ladder_stage: 2 },
              { question: 'Birds migrate south for warmth.', chunks: ['Birds', 'migrate south', 'for warmth.'], lesson_name: 'Chapter 3: Flying High', ladder_stage: 1 }
            ],
            tags: ['exam']
          },
          {
            id: 'deck_2',
            title: 'Science Concepts Class 4',
            subject: 'Science',
            description: 'Plant biology, habitats, and solar system concepts.',
            cards: [
              { question: 'Chlorophyll absorbs green light.', chunks: ['Chlorophyll', 'absorbs', 'green light.'], lesson_name: 'Chapter 1: Photosynthesis', ladder_stage: 6 },
              { question: 'Roots anchor the plant firmly in soil.', chunks: ['Roots', 'anchor the plant', 'firmly in soil.'], lesson_name: 'Chapter 1: Photosynthesis', ladder_stage: 5 },
              { question: 'Jupiter is the largest planet.', chunks: ['Jupiter', 'is the largest', 'planet.'], lesson_name: 'Chapter 2: Solar System', ladder_stage: 3 }
            ],
            tags: ['exam']
          }
        ];

        state.exam_metrics = {
          id: 'exam_midterm',
          exam_name: 'Class 4 Mid-Term English & Science Exam',
          target_date: '2026-09-20',
          days_left: 14,
          total_cards: 7,
          mastered_cards: 3,
          daily_quota: 2,
          readiness_percent: 65,
          status_tag: 'On Track',
          selected_scope: {
            'deck_1': ['Chapter 1: The Wind', 'Chapter 2: The Ant & Grasshopper'],
            'deck_2': ['Chapter 1: Photosynthesis']
          },
          chapters_breakdown: [
            { deck_id: 'deck_1', deck_title: 'English Class 4 - Reader', chapter_name: 'Chapter 1: The Wind', total_cards: 2, mastered_cards: 2, readiness_percent: 100, status: '⭐ Mastered', is_mastered: true },
            { deck_id: 'deck_1', deck_title: 'English Class 4 - Reader', chapter_name: 'Chapter 2: The Ant & Grasshopper', total_cards: 2, mastered_cards: 0, readiness_percent: 50, status: '🔄 In Progress', is_mastered: false },
            { deck_id: 'deck_2', deck_title: 'Science Concepts Class 4', chapter_name: 'Chapter 1: Photosynthesis', total_cards: 2, mastered_cards: 1, readiness_percent: 85, status: '🔄 In Progress', is_mastered: false }
          ]
        };
      }
      refreshUI();
    }
  }, 100);
});

function refreshUI() {
  document.getElementById('active-student-name').textContent = state.active_profile;
  
  populateExamSelector();

  if (state.exam_metrics && state.exam_metrics.id) {
    const em = state.exam_metrics;
    document.getElementById('target-exam-text').textContent = `${em.exam_name || 'Target Exam'} (${em.days_left || 0} Days)`;
    
    document.getElementById('exam-meta').textContent = `Target Date: In ${em.days_left || 0} Days • ${em.total_cards || 0} Cards in Scope across Tagged Chapters`;
    document.getElementById('exam-readiness-val').textContent = `${em.readiness_percent || 0}% Complete`;
    document.getElementById('exam-progress-bar').style.width = `${em.readiness_percent || 0}%`;
    document.getElementById('stat-days-left').textContent = em.days_left || 0;
    document.getElementById('stat-cards-count').textContent = `${em.mastered_cards || 0} / ${em.total_cards || 0}`;
    document.getElementById('stat-daily-quota').textContent = `${em.daily_quota || 0} Cards/Day`;
    document.getElementById('exam-status-tag').textContent = em.status_tag || 'On Track';
    
    const tagEl = document.getElementById('exam-status-tag');
    if (em.status_tag && em.status_tag.includes('Urgent')) {
      tagEl.className = 'text-[11px] bg-rose-100 text-rose-800 font-bold px-2.5 py-0.5 rounded-full';
    } else if (em.status_tag && em.status_tag.includes('Steady')) {
      tagEl.className = 'text-[11px] bg-amber-100 text-amber-800 font-bold px-2.5 py-0.5 rounded-full';
    } else {
      tagEl.className = 'text-[11px] bg-emerald-100 text-emerald-800 font-bold px-2.5 py-0.5 rounded-full';
    }

    renderChapterBreakdown();
  } else {
    document.getElementById('target-exam-text').textContent = 'No Exam Active';
    document.getElementById('exam-meta').textContent = 'Click "+ New Exam" to create an exam goal and tag chapters.';
    document.getElementById('exam-readiness-val').textContent = '0%';
    document.getElementById('exam-progress-bar').style.width = '0%';
    document.getElementById('stat-days-left').textContent = '0';
    document.getElementById('stat-cards-count').textContent = '0 / 0';
    document.getElementById('stat-daily-quota').textContent = '0 Cards/Day';
    document.getElementById('exam-status-tag').textContent = 'No Exam';
    document.getElementById('exam-status-tag').className = 'text-[11px] bg-slate-100 text-slate-600 font-bold px-2.5 py-0.5 rounded-full';
    renderChapterBreakdown();
  }

  populateSubjectFilter();
  filterDecks();
  renderMissionQueue();
}

function populateExamSelector() {
  const sel = document.getElementById('exam-selector');
  if (!sel) return;
  sel.innerHTML = '';

  const em = state.exam_metrics || {};
  const allExams = em.all_exams || [];
  const currentId = em.id;

  if (allExams.length === 0) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = '➕ No Exams (Click "+ New Exam")';
    sel.appendChild(opt);
    return;
  }

  allExams.forEach(e => {
    const opt = document.createElement('option');
    opt.value = e.id;
    opt.textContent = `🎯 ${e.title || 'Exam'} (${e.target_date || 'No Date'})`;
    if (e.id === currentId) {
      opt.selected = true;
    }
    sel.appendChild(opt);
  });
}

async function switchExam(examId) {
  if (!examId) return;
  if (window.pywebview) {
    try {
      const refreshed = await window.pywebview.api.switch_exam(examId);
      if (refreshed) {
        state.exam_metrics = refreshed;
      }
    } catch (e) {
      console.warn("Failed to switch exam:", e);
    }
  } else {
    const em = state.exam_metrics || {};
    const found = (em.all_exams || []).find(e => e.id === examId);
    if (found) {
      state.exam_metrics.id = found.id;
      state.exam_metrics.exam_name = found.title;
      state.exam_metrics.target_date = found.target_date;
    }
  }
  refreshUI();
}

async function deleteCurrentExam() {
  const em = state.exam_metrics;
  if (!em || !em.id) {
    alert("No active exam to delete.");
    return;
  }
  const examName = em.exam_name || 'this exam';
  if (!confirm(`Are you sure you want to delete "${examName}"?`)) {
    return;
  }

  if (window.pywebview) {
    try {
      const refreshed = await window.pywebview.api.delete_exam(em.id);
      if (refreshed) {
        state.exam_metrics = refreshed;
      }
    } catch (e) {
      console.warn("Failed to delete exam:", e);
    }
  } else {
    if (state.exam_metrics.all_exams) {
      state.exam_metrics.all_exams = state.exam_metrics.all_exams.filter(e => e.id !== em.id);
      if (state.exam_metrics.all_exams.length > 0) {
        const nextEx = state.exam_metrics.all_exams[0];
        state.exam_metrics.id = nextEx.id;
        state.exam_metrics.exam_name = nextEx.title;
      } else {
        state.exam_metrics = null;
      }
    }
  }

  await reloadState();
  refreshUI();
}

// ----------------- Chapter Mastery Breakdown -----------------
function filterChapterBreakdown(filterType) {
  state.chapter_filter = filterType;
  ['all', 'in_progress', 'mastered'].forEach(f => {
    const btn = document.getElementById('ch-filter-' + f);
    if (btn) {
      if (f === filterType) {
        btn.className = 'px-3 py-1 rounded-lg bg-white shadow-xs text-indigo-700 font-bold';
      } else {
        btn.className = 'px-3 py-1 rounded-lg text-slate-600 hover:text-slate-900';
      }
    }
  });
  renderChapterBreakdown();
}

function renderChapterBreakdown() {
  const container = document.getElementById('exam-chapters-container');
  if (!container) return;
  container.innerHTML = '';

  const em = state.exam_metrics;
  const chapters = em.chapters_breakdown || [];

  const filtered = chapters.filter(ch => {
    if (state.chapter_filter === 'mastered') return ch.is_mastered;
    if (state.chapter_filter === 'in_progress') return !ch.is_mastered;
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-8 text-center bg-slate-50 border border-slate-200 rounded-xl p-6">
        <div class="text-3xl mb-1">📖</div>
        <div class="text-sm font-bold text-slate-700">No Chapters in this View</div>
        <p class="text-xs text-slate-500 mt-0.5">Click "Edit Exam & Tag Chapters" to select which chapters are included in this exam.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(ch => {
    const card = document.createElement('div');
    card.className = `p-4 rounded-xl border transition flex flex-col justify-between space-y-3 ${ch.is_mastered ? 'bg-emerald-50/50 border-emerald-200' : 'bg-white border-slate-200 shadow-xs'}`;
    
    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between gap-2 mb-1.5">
          <span class="text-[11px] font-bold text-slate-500 truncate max-w-[180px]">${ch.deck_title}</span>
          <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-full ${ch.is_mastered ? 'bg-emerald-100 text-emerald-800' : (ch.mastered_cards > 0 ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600')}">
            ${ch.status}
          </span>
        </div>
        <h4 class="text-sm font-bold text-slate-900 leading-snug">${ch.chapter_name}</h4>
      </div>

      <div>
        <div class="flex justify-between text-[11px] font-semibold text-slate-500 mb-1">
          <span>Mastery: ${ch.mastered_cards} / ${ch.total_cards} Cards</span>
          <span class="font-bold ${ch.is_mastered ? 'text-emerald-700' : 'text-slate-700'}">${ch.readiness_percent}%</span>
        </div>
        <div class="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all duration-300 ${ch.is_mastered ? 'bg-emerald-500' : 'bg-indigo-600'}" style="width: ${ch.readiness_percent}%"></div>
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

// ----------------- Exam Scope Modal & Chapter Tagging -----------------
let modalScopeState = {
  exam_id: null,
  selected_scope: {}, // deck_id -> Set of chapter names
  decks_data: []
};

async function openExamScopeModal(isNew = false) {
  const modal = document.getElementById('exam-scope-modal');
  const treeContainer = document.getElementById('modal-exam-tree');
  treeContainer.innerHTML = '<div class="text-center py-4 text-xs text-slate-400">Loading chapters...</div>';

  const em = state.exam_metrics || {};
  modalScopeState.exam_id = isNew ? null : (em.id || null);
  document.getElementById('modal-exam-name').value = isNew ? '' : (em.exam_name || 'Mid-Term Assessment');
  document.getElementById('modal-exam-name').placeholder = isNew ? 'e.g. Science Term 1 Exam' : 'Exam Title';
  
  const modalTitle = document.getElementById('exam-scope-modal-title');
  if (modalTitle) {
    modalTitle.textContent = isNew ? 'Create New Exam & Tag Chapters' : 'Configure Exam Scope & Tag Chapters';
  }
  
  const defaultDate = new Date();
  defaultDate.setDate(defaultDate.getDate() + 14);
  document.getElementById('modal-exam-date').value = (isNew || !em.target_date) 
    ? defaultDate.toISOString().split('T')[0] 
    : em.target_date;

  // Clone current selected scope
  modalScopeState.selected_scope = {};
  if (!isNew && em.selected_scope) {
    for (const [d_id, chaps] of Object.entries(em.selected_scope)) {
      modalScopeState.selected_scope[d_id] = new Set(chaps);
    }
  }

  modal.classList.remove('hidden');

  // Load all decks with chapters
  let decksWithChaps = state.all_decks_chapters;
  if (window.pywebview) {
    try {
      decksWithChaps = await window.pywebview.api.get_all_decks_with_chapters();
      state.all_decks_chapters = decksWithChaps;
    } catch (e) {
      console.warn("Failed to fetch decks with chapters:", e);
    }
  }

  if (!decksWithChaps || decksWithChaps.length === 0) {
    // Generate from state.decks
    decksWithChaps = (state.decks || []).map(d => {
      const chapsMap = {};
      (d.cards || []).forEach(c => {
        const ch = (c.lesson_name || '').trim() || 'General / Unassigned';
        chapsMap[ch] = (chapsMap[ch] || 0) + 1;
      });
      return {
        id: d.id,
        title: d.title,
        subject: d.subject,
        chapters: Object.entries(chapsMap).map(([name, count]) => ({ chapter_name: name, total_cards: count }))
      };
    });
  }

  modalScopeState.decks_data = decksWithChaps;
  renderModalExamTree();
}

function openCreateExamModal() {
  openExamScopeModal(true);
}

function closeExamScopeModal() {
  document.getElementById('exam-scope-modal').classList.add('hidden');
}

function renderModalExamTree() {
  const treeContainer = document.getElementById('modal-exam-tree');
  treeContainer.innerHTML = '';

  const decks = modalScopeState.decks_data || [];
  if (decks.length === 0) {
    treeContainer.innerHTML = '<div class="text-center py-4 text-xs text-slate-500">No decks found. Please create or import a deck first.</div>';
    return;
  }

  decks.forEach(deck => {
    const deckBox = document.createElement('div');
    deckBox.className = 'bg-white border border-slate-200 rounded-xl p-3 shadow-xs space-y-2';

    const selSet = modalScopeState.selected_scope[deck.id] || new Set();
    const chapters = deck.chapters || [];
    const allChecked = chapters.length > 0 && chapters.every(ch => selSet.has(ch.chapter_name));
    const someChecked = chapters.some(ch => selSet.has(ch.chapter_name));

    // Deck Header Row
    const deckHdr = document.createElement('div');
    deckHdr.className = 'flex items-center justify-between';

    const deckLabel = document.createElement('label');
    deckLabel.className = 'flex items-center gap-2 cursor-pointer font-bold text-xs text-slate-800';

    const deckChk = document.createElement('input');
    deckChk.type = 'checkbox';
    deckChk.id = `deck-chk-${deck.id}`;
    deckChk.checked = allChecked;
    deckChk.indeterminate = (someChecked && !allChecked);
    deckChk.className = 'rounded text-indigo-600 focus:ring-indigo-500';
    deckChk.addEventListener('change', (e) => toggleDeckAllChapters(deck.id, e.target.checked));

    deckLabel.appendChild(deckChk);
    const titleSpan = document.createElement('span');
    titleSpan.textContent = `📁 ${deck.title}`;
    deckLabel.appendChild(titleSpan);

    const subSpan = document.createElement('span');
    subSpan.className = 'text-[10px] font-normal text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full';
    subSpan.textContent = deck.subject || 'General';
    deckLabel.appendChild(subSpan);

    const chapCountSpan = document.createElement('span');
    chapCountSpan.className = 'text-[11px] text-slate-400';
    chapCountSpan.textContent = `${chapters.length} Chapters`;

    deckHdr.appendChild(deckLabel);
    deckHdr.appendChild(chapCountSpan);
    deckBox.appendChild(deckHdr);

    // Chapters Checklist
    const chList = document.createElement('div');
    chList.className = 'pl-6 pt-1 space-y-1.5 border-t border-slate-100';

    chapters.forEach(ch => {
      const isChecked = selSet.has(ch.chapter_name);
      const chRow = document.createElement('label');
      chRow.className = 'flex items-center justify-between text-xs text-slate-700 cursor-pointer hover:bg-slate-50 p-1 rounded-lg';

      const leftDiv = document.createElement('div');
      leftDiv.className = 'flex items-center gap-2';

      const chChk = document.createElement('input');
      chChk.type = 'checkbox';
      chChk.id = `ch-chk-${deck.id}-${escapeId(ch.chapter_name)}`;
      chChk.checked = isChecked;
      chChk.className = 'rounded text-indigo-600 focus:ring-indigo-500';
      chChk.addEventListener('change', (e) => toggleSingleChapter(deck.id, ch.chapter_name, e.target.checked));

      const nameSpan = document.createElement('span');
      nameSpan.className = 'font-medium';
      nameSpan.textContent = ch.chapter_name;

      leftDiv.appendChild(chChk);
      leftDiv.appendChild(nameSpan);

      const countBadge = document.createElement('span');
      countBadge.className = 'text-[10px] bg-indigo-50 text-indigo-700 font-bold px-2 py-0.5 rounded-full';
      countBadge.textContent = `${ch.total_cards || 0} cards`;

      chRow.appendChild(leftDiv);
      chRow.appendChild(countBadge);
      chList.appendChild(chRow);
    });

    deckBox.appendChild(chList);
    treeContainer.appendChild(deckBox);
  });

  updateModalLiveSummary();
}

function escapeId(str) {
  return (str || '').replace(/[^a-zA-Z0-9]/g, '_');
}

function escapeAttr(str) {
  return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function toggleDeckAllChapters(deckId, isChecked) {
  const deck = (modalScopeState.decks_data || []).find(d => d.id === deckId);
  if (!deck) return;
  
  if (!modalScopeState.selected_scope[deckId]) {
    modalScopeState.selected_scope[deckId] = new Set();
  }

  (deck.chapters || []).forEach(ch => {
    if (isChecked) {
      modalScopeState.selected_scope[deckId].add(ch.chapter_name);
    } else {
      modalScopeState.selected_scope[deckId].delete(ch.chapter_name);
    }
  });

  renderModalExamTree();
}

function toggleSingleChapter(deckId, chapterName, isChecked) {
  if (!modalScopeState.selected_scope[deckId]) {
    modalScopeState.selected_scope[deckId] = new Set();
  }
  if (isChecked) {
    modalScopeState.selected_scope[deckId].add(chapterName);
  } else {
    modalScopeState.selected_scope[deckId].delete(chapterName);
  }

  // Update parent deck checkbox state
  const deck = (modalScopeState.decks_data || []).find(d => d.id === deckId);
  if (deck) {
    const deckChk = document.getElementById(`deck-chk-${deckId}`);
    if (deckChk) {
      const selSet = modalScopeState.selected_scope[deckId] || new Set();
      const chaps = deck.chapters || [];
      const allChecked = chaps.length > 0 && chaps.every(c => selSet.has(c.chapter_name));
      const someChecked = chaps.some(c => selSet.has(c.chapter_name));
      deckChk.checked = allChecked;
      deckChk.indeterminate = (someChecked && !allChecked);
    }
  }

  updateModalLiveSummary();
}

function selectAllExamScope(selectAll) {
  (modalScopeState.decks_data || []).forEach(d => {
    const deckId = d.id;
    if (!modalScopeState.selected_scope[deckId]) {
      modalScopeState.selected_scope[deckId] = new Set();
    }
    (d.chapters || []).forEach(ch => {
      if (selectAll) {
        modalScopeState.selected_scope[deckId].add(ch.chapter_name);
      } else {
        modalScopeState.selected_scope[deckId].delete(ch.chapter_name);
      }
    });
  });
  renderModalExamTree();
}

function updateModalLiveSummary() {
  let totalChaps = 0;
  let totalCards = 0;

  (modalScopeState.decks_data || []).forEach(d => {
    const selSet = modalScopeState.selected_scope[d.id] || new Set();
    (d.chapters || []).forEach(ch => {
      if (selSet.has(ch.chapter_name)) {
        totalChaps += 1;
        totalCards += (ch.total_cards || 0);
      }
    });
  });

  document.getElementById('modal-summary-chaps').textContent = totalChaps;
  document.getElementById('modal-summary-cards').textContent = totalCards;

  const dateVal = document.getElementById('modal-exam-date').value;
  let daysLeft = 14;
  if (dateVal) {
    const diff = Math.ceil((new Date(dateVal) - new Date()) / (1000 * 60 * 60 * 24));
    daysLeft = Math.max(1, diff);
  }
  const quota = Math.max(2, Math.ceil(totalCards / daysLeft));
  document.getElementById('modal-summary-quota').textContent = quota;
}

async function saveExamScopeConfig() {
  const name = document.getElementById('modal-exam-name').value.trim();
  const dateStr = document.getElementById('modal-exam-date').value;
  if (!name) {
    alert("Please enter an exam title.");
    return;
  }

  // Convert Set back to arrays
  const serializableScope = {};
  const includedDeckIds = [];
  let totalCardsCount = 0;

  for (const [deckId, chSet] of Object.entries(modalScopeState.selected_scope)) {
    if (chSet.size > 0) {
      serializableScope[deckId] = Array.from(chSet);
      includedDeckIds.push(deckId);
    }
  }

  if (includedDeckIds.length === 0) {
    alert("Please tag at least one chapter for this exam.");
    return;
  }

  if (window.pywebview) {
    try {
      const refreshed = await window.pywebview.api.save_exam_goal(
        name,
        dateStr,
        totalCardsCount,
        includedDeckIds,
        serializableScope,
        modalScopeState.exam_id
      );
      if (refreshed) {
        state.exam_metrics = refreshed;
      }
    } catch (e) {
      console.warn("Failed to save exam config:", e);
    }
  } else {
    // Client-side simulation
    state.exam_metrics.exam_name = name;
    state.exam_metrics.target_date = dateStr;
    state.exam_metrics.selected_scope = serializableScope;
  }

  closeExamScopeModal();
  await reloadState();
  refreshUI();
}

function launchExamMission() {
  const examId = state.exam_metrics ? state.exam_metrics.id : null;
  if (window.pywebview) {
    window.pywebview.api.launch_exam_mission(examId);
  } else {
    alert("Launching Exam Mission scoped to tagged chapters!");
  }
}

// ----------------- Standard Tabs, Search & Decks -----------------
function populateSubjectFilter() {
  const subjects = new Set();
  (state.decks || []).forEach(d => {
    if (d.subject) subjects.add(d.subject);
  });
  const sel = document.getElementById('deck-subject-filter');
  if (!sel) return;
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
    if (btn) {
      if (s === scope) {
        btn.className = 'px-3 py-1 rounded-lg bg-white shadow-xs text-indigo-700 font-bold';
      } else {
        btn.className = 'px-3 py-1 rounded-lg text-slate-600 hover:text-slate-900';
      }
    }
  });
  filterDecks();
}

function filterDecks() {
  const searchEl = document.getElementById('deck-search');
  const subjectEl = document.getElementById('deck-subject-filter');
  if (!searchEl || !subjectEl) return;

  const query = (searchEl.value || '').toLowerCase();
  const subject = subjectEl.value;
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
    }

    return matchesSearch && matchesSubject && matchesScope;
  });

  renderDecksGrid(filtered);
}

function renderDecksGrid(decks) {
  const grid = document.getElementById('decks-grid');
  if (!grid) return;
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
        <button onclick="confirmDeleteDeck('${deck.id}', '${escapeAttr(deck.title)}')" class="text-slate-400 hover:text-rose-600 text-sm px-2 py-1 transition" title="Delete Deck">
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
  if (!list || !countBadge) return;
  list.innerHTML = '';

  const queue = state.mission_queue && state.mission_queue.length > 0 
    ? state.mission_queue 
    : [
        { question: 'The gentle breeze whispered softly through the trees.', ladder_stage: 4 },
        { question: 'Photosynthesis converts sunlight into usable energy.', ladder_stage: 5 }
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
