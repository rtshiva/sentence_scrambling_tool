// Sentence Jigsaw 3.0 - Unified WebUI SPA Application Logic
// Supports in-browser interactive gameplay, multi-pass adaptive blanks,
// multi-subject exam tracking (Hindi + Science), and parent lesson studio.

let state = {
  active_profile: 'Arya',
  profiles: ['Arya'],
  role: 'student', // 'student' | 'parent'
  current_view: 'dashboard',
  decks: [],
  multi_subject_metrics: { subjects: [] },
  exam_metrics: {
    id: 'exam_midterm',
    exam_name: 'Class 7 Mid-Term Exam',
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
  subject_filter: 'All',
  search_query: '',
  selected_chapter_data: null,

  // In-Browser Game Session State
  gameplay: {
    active: false,
    mode: 'blanks', // 'blanks' | 'jigsaw' | 'guided_mission'
    cards: [],
    card_index: 0,
    current_card: null,
    
    // Adaptive Multi-Pass Blanks state
    pass_number: 1, // 1 -> 2 -> 3
    max_passes: 3,
    pass_blank_indices: [],
    filled_slots: {}, // slot_idx -> chunk text
    active_slot_idx: null,

    // Jigsaw state
    placed_chunks: [],
    available_chips: [],

    streak: 0,
    flawless: true,

    // Question stopwatch timer
    timer_interval: null,
    timer_start_ms: null,
    timer_elapsed_seconds: 0
  },

  // Parent Portal temporary preview state
  parent_preview_items: [],

  // Offline/Online translation cache for hover tooltips
  chunk_translations: {},
  settings: {
    show_hover_meanings: true,
    font_size: 'normal',
    jigsaw_words_per_block: 'auto'
  }
};
window.state = state;

// =========================================================================
// 1. LIFECYCLE & INITIALIZATION
// =========================================================================

window.addEventListener('pywebviewready', async function() {
  console.log("pywebview bridge connected!");
  await reloadAppState();
  initUI();
});

window.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    if (!window.pywebview) {
      console.log("Running standalone demo mode");
      seedDemoData();
      initUI();
    }
  }, 100);
});

window.addEventListener('keydown', function(e) {
  const isTyping = ['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName) || document.activeElement?.isContentEditable;
  if (e.ctrlKey || e.metaKey) {
    const key = e.key.toLowerCase();
    if (key === 'a') {
      if (state.gameplay && state.gameplay.active && !isTyping) {
        e.preventDefault();
        playAnswerTTS();
      }
    } else if (key === 'l') {
      if (state.gameplay && state.gameplay.active) {
        e.preventDefault();
        playCardTTS();
      }
    } else if (key === 'h') {
      if (state.gameplay && state.gameplay.active && !isTyping) {
        e.preventDefault();
        gameActionHint();
      }
    }
  }
});


async function reloadAppState() {
  if (!window.pywebview) return;
  try {
    const pyState = await window.pywebview.api.get_state();
    if (pyState) {
      state.active_profile = pyState.active_profile || state.active_profile;
      state.profiles = pyState.profiles || state.profiles;
      state.decks = pyState.decks || [];
      state.exam_metrics = pyState.exam_metrics || state.exam_metrics;
      if (pyState.settings) {
        state.settings = Object.assign({}, state.settings, pyState.settings);
        applyTheme(state.settings.theme);
        applyFontSize(state.settings.font_size);
      }
    }
    const msMetrics = await window.pywebview.api.get_multi_subject_metrics();
    if (msMetrics) {
      state.multi_subject_metrics = msMetrics;
      if (msMetrics.exam_metrics) {
        state.exam_metrics = msMetrics.exam_metrics;
      }
    }
    const decksChaps = await window.pywebview.api.get_all_decks_with_chapters();
    if (decksChaps) {
      state.all_decks_chapters = decksChaps;
    }
  } catch (err) {
    console.warn("Failed to sync state from Python bridge:", err);
  }
}

function seedDemoData() {
  state.decks = [
    {
      id: 'hindi_master',
      title: 'Grade 7 Hindi (All Chapters)',
      subject: 'Hindi',
      description: 'Ch-1 माँ कह एक कहानी, Ch-3 फूल और काँटा, Ch-4 पानी रे पानी, Ch-5 नहीं होना बीमार, Ch-6 कुंडलिया',
      cards: [
        {
          card_id: 'h1',
          question: 'प्रश्न (क) आपके विचार से इस कविता में कौन-सी पंक्ति सबसे महत्वपूर्ण है?',
          chunks: ['“कोई निरपराध को मारे,', 'तो क्यों अन्य उसे न उबारे?', 'रक्षक पर भक्षक को वारे,', 'न्याय दया का दानी!”', 'इन पंक्तियों में दया और', 'न्याय का संदेश मिलता है'],
          meaning: 'In your opinion, which line in this poem is the most important?',
          lesson_name: 'Ch-1 माँ, कह एक कहानी',
          ladder_stage: 2
        },
        {
          card_id: 'h2',
          question: 'प्रश्न (ख) आखेटक और बच्चे के पिता के बीच तर्क-वितर्क क्यों हुआ था?',
          chunks: ['आखेटक पक्षी को', 'अपना शिकार बताकर', 'उसे वापस माँग रहा था,', 'जबकि बच्चे के पिता', 'उसे बचाना चाहते थे।'],
          meaning: 'Why was there an argument between hunter and father?',
          lesson_name: 'Ch-1 माँ, कह एक कहानी',
          ladder_stage: 1
        }
      ]
    },
    {
      id: 'science_starter',
      title: 'General Science & Nature',
      subject: 'Science',
      description: 'Foundational concepts on solar system, plants, and water cycle.',
      cards: [
        {
          card_id: 's1',
          question: 'The solar system consists of eight planets.',
          chunks: ['The solar system', 'consists of', 'eight planets'],
          meaning: 'सौर मंडल में आठ ग्रह शामिल हैं।',
          lesson_name: 'Solar System',
          ladder_stage: 6
        },
        {
          card_id: 's2',
          question: 'Plants prepare food through photosynthesis using sunlight.',
          chunks: ['Plants prepare food', 'through photosynthesis', 'using sunlight'],
          meaning: 'पौधे सूर्य के प्रकाश का उपयोग करके भोजन तैयार करते हैं।',
          lesson_name: 'Photosynthesis',
          ladder_stage: 4
        }
      ]
    }
  ];
}

// =========================================================================
// Cosmic Starfield & Nebula Canvas Engine (Space Explorer Theme)
// =========================================================================
const spaceUniverseEngine = {
  running: false,
  animId: null,
  canvas: null,
  ctx: null,
  stars: [],
  meteors: [],
  lastMeteorTime: 0,
  mouseX: 0,
  mouseY: 0,
  targetMouseX: 0,
  targetMouseY: 0,
  width: 0,
  height: 0,
  boundResize: null,
  boundMouseMove: null,

  init() {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    this.canvas = document.getElementById('space-stars-canvas');
    if (!this.canvas || !this.canvas.getContext) return;
    this.ctx = this.canvas.getContext('2d');
    if (!this.ctx) return;

    this.boundResize = () => this.resize();
    this.boundMouseMove = (e) => {
      if (!e) return;
      this.targetMouseX = ((e.clientX || 0) - this.width / 2) * 0.04;
      this.targetMouseY = ((e.clientY || 0) - this.height / 2) * 0.04;
    };
  },

  resize() {
    if (!this.canvas) return;
    this.width = (typeof window !== 'undefined' && window.innerWidth) ? window.innerWidth : 1280;
    this.height = (typeof window !== 'undefined' && window.innerHeight) ? window.innerHeight : 800;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.createStars();
  },

  createStars() {
    this.stars = [];
    const count = Math.min(220, Math.max(100, Math.floor((this.width * this.height) / 6000)));
    const colors = [
      '#ffffff', // crisp white
      '#e0e7ff', // soft indigo
      '#bae6fd', // celestial cyan
      '#fbcfe8', // faint rose
      '#fef08a'  // warm starlight
    ];

    for (let i = 0; i < count; i++) {
      const radius = Math.random() < 0.82 ? Math.random() * 1.2 + 0.3 : Math.random() * 1.8 + 1.2;
      this.stars.push({
        x: Math.random() * this.width,
        y: Math.random() * this.height,
        radius,
        color: colors[Math.floor(Math.random() * colors.length)],
        baseAlpha: Math.random() * 0.5 + 0.35,
        twinkleSpeed: Math.random() * 0.025 + 0.008,
        twinklePhase: Math.random() * Math.PI * 2,
        parallaxFactor: radius * 0.6,
        hasDiffraction: radius > 2.0
      });
    }
  },

  spawnMeteor() {
    const startX = Math.random() * this.width * 0.8 + this.width * 0.1;
    const startY = Math.random() * this.height * 0.3;
    const speed = Math.random() * 5 + 6;
    const angle = (Math.PI / 4) + (Math.random() - 0.5) * 0.3;
    const length = Math.random() * 80 + 90;
    this.meteors.push({
      x: startX,
      y: startY,
      dx: Math.cos(angle) * speed,
      dy: Math.sin(angle) * speed,
      length,
      opacity: 1,
      decay: Math.random() * 0.015 + 0.012
    });
  },

  start() {
    if (this.running || typeof window === 'undefined') return;
    if (!this.canvas) this.init();
    if (!this.canvas || !this.ctx) return;

    this.running = true;
    this.resize();
    if (window.addEventListener && this.boundResize) {
      window.addEventListener('resize', this.boundResize);
    }
    if (window.addEventListener && this.boundMouseMove) {
      window.addEventListener('mousemove', this.boundMouseMove);
    }
    this.lastMeteorTime = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();

    const universeEl = document.getElementById('space-universe');
    if (universeEl && universeEl.classList) universeEl.classList.remove('hidden');

    if (typeof requestAnimationFrame === 'function') {
      const loop = (timestamp) => {
        if (!this.running) return;
        this.updateAndDraw(timestamp || (typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now()));
        this.animId = requestAnimationFrame(loop);
      };
      this.animId = requestAnimationFrame(loop);
    }
  },

  stop() {
    this.running = false;
    if (this.animId && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(this.animId);
      this.animId = null;
    }
    if (typeof window !== 'undefined') {
      if (this.boundResize && window.removeEventListener) window.removeEventListener('resize', this.boundResize);
      if (this.boundMouseMove && window.removeEventListener) window.removeEventListener('mousemove', this.boundMouseMove);
    }
    const universeEl = typeof document !== 'undefined' ? document.getElementById('space-universe') : null;
    if (universeEl && universeEl.classList) universeEl.classList.add('hidden');

    if (this.ctx && this.canvas && typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.canvas.width || 0, this.canvas.height || 0);
    }
  },

  updateAndDraw(timestamp) {
    if (!this.ctx || !this.canvas) return;

    // Smooth mouse parallax lerp
    this.mouseX += (this.targetMouseX - this.mouseX) * 0.05;
    this.mouseY += (this.targetMouseY - this.mouseY) * 0.05;

    if (typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.width, this.height);
    }

    // 1. Draw Twinkling Stars
    if (typeof this.ctx.save === 'function' && typeof this.ctx.beginPath === 'function') {
      for (let i = 0; i < this.stars.length; i++) {
        const s = this.stars[i];
        s.twinklePhase += s.twinkleSpeed;
        const alpha = Math.max(0.1, Math.min(1, s.baseAlpha + Math.sin(s.twinklePhase) * 0.35));

        const sx = (s.x + this.mouseX * s.parallaxFactor + this.width) % this.width;
        const sy = (s.y + this.mouseY * s.parallaxFactor + this.height) % this.height;

        this.ctx.save();
        this.ctx.globalAlpha = alpha;
        this.ctx.fillStyle = s.color;

        this.ctx.beginPath();
        if (typeof this.ctx.arc === 'function') {
          this.ctx.arc(sx, sy, s.radius, 0, Math.PI * 2);
        }
        if (typeof this.ctx.fill === 'function') {
          this.ctx.fill();
        }

        // Optical diffraction spikes on luminous hero stars
        if (s.hasDiffraction && typeof this.ctx.stroke === 'function') {
          this.ctx.strokeStyle = s.color;
          this.ctx.lineWidth = 0.6;
          this.ctx.beginPath();
          this.ctx.moveTo(sx - s.radius * 2.5, sy);
          this.ctx.lineTo(sx + s.radius * 2.5, sy);
          this.ctx.moveTo(sx, sy - s.radius * 2.5);
          this.ctx.lineTo(sx, sy + s.radius * 2.5);
          this.ctx.stroke();
        }
        this.ctx.restore();
      }
    }

    // 2. Periodic Shooting Stars (Meteors)
    const now = timestamp || Date.now();
    if (now - this.lastMeteorTime > 5500 + Math.random() * 4000) {
      this.spawnMeteor();
      this.lastMeteorTime = now;
    }

    if (typeof this.ctx.save === 'function' && typeof this.ctx.createLinearGradient === 'function') {
      for (let i = this.meteors.length - 1; i >= 0; i--) {
        const m = this.meteors[i];
        m.x += m.dx;
        m.y += m.dy;
        m.opacity -= m.decay;

        if (m.opacity <= 0 || m.x > this.width || m.y > this.height) {
          this.meteors.splice(i, 1);
          continue;
        }

        const hyp = Math.hypot(m.dx, m.dy) || 1;
        const tailX = m.x - (m.dx / hyp) * m.length;
        const tailY = m.y - (m.dy / hyp) * m.length;

        this.ctx.save();
        this.ctx.globalAlpha = Math.max(0, m.opacity);
        const grad = this.ctx.createLinearGradient(m.x, m.y, tailX, tailY);
        grad.addColorStop(0, '#ffffff');
        grad.addColorStop(0.2, '#38bdf8');
        grad.addColorStop(1, 'transparent');

        this.ctx.strokeStyle = grad;
        this.ctx.lineWidth = 1.8;
        this.ctx.lineCap = 'round';
        this.ctx.beginPath();
        this.ctx.moveTo(m.x, m.y);
        this.ctx.lineTo(tailX, tailY);
        this.ctx.stroke();
        this.ctx.restore();
      }
    }
  }
};

// =========================================================================
// Volcanic Nether Magma & Rising Embers Engine (Lava Forge Theme)
// =========================================================================
const lavaUniverseEngine = {
  running: false,
  animId: null,
  canvas: null,
  ctx: null,
  embers: [],
  mouseX: 0,
  mouseY: 0,
  targetMouseX: 0,
  targetMouseY: 0,
  width: 0,
  height: 0,
  boundResize: null,
  boundMouseMove: null,

  init() {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    this.canvas = document.getElementById('lava-canvas');
    if (!this.canvas || !this.canvas.getContext) return;
    this.ctx = this.canvas.getContext('2d');
    if (!this.ctx) return;

    this.boundResize = () => this.resize();
    this.boundMouseMove = (e) => {
      if (!e) return;
      this.targetMouseX = ((e.clientX || 0) - this.width / 2) * 0.03;
      this.targetMouseY = ((e.clientY || 0) - this.height / 2) * 0.03;
    };
  },

  resize() {
    if (!this.canvas) return;
    this.width = (typeof window !== 'undefined' && window.innerWidth) ? window.innerWidth : 1280;
    this.height = (typeof window !== 'undefined' && window.innerHeight) ? window.innerHeight : 800;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.createEmbers();
  },

  createEmbers() {
    this.embers = [];
    const count = Math.min(100, Math.max(50, Math.floor((this.width * this.height) / 11000)));
    const colors = [
      '#fbbf24', // molten gold
      '#f59e0b', // amber forge
      '#f97316', // blazing orange
      '#ef4444', // Nether crimson
      '#ffedd5', // incandescent white
      '#ea580c'  // magma spark
    ];

    for (let i = 0; i < count; i++) {
      this.embers.push(this.spawnEmber(colors, true));
    }
  },

  spawnEmber(colorsList, randomY = false) {
    const colors = colorsList || ['#fbbf24', '#f59e0b', '#f97316', '#ef4444', '#ffedd5'];
    const radius = Math.random() < 0.75 ? Math.random() * 1.5 + 0.8 : Math.random() * 2.6 + 1.8;
    return {
      x: Math.random() * (this.width || 1280),
      y: randomY ? Math.random() * (this.height || 800) : (this.height || 800) + Math.random() * 20,
      radius,
      vy: -(Math.random() * 1.2 + 0.5), // Rising upward
      baseVx: (Math.random() - 0.5) * 0.4,
      swaySpeed: Math.random() * 0.02 + 0.01,
      swayAmp: Math.random() * 1.5 + 0.5,
      swayPhase: Math.random() * Math.PI * 2,
      color: colors[Math.floor(Math.random() * colors.length)],
      alpha: Math.random() * 0.4 + 0.5,
      decay: Math.random() * 0.003 + 0.001,
      hasGlow: radius > 2.0
    };
  },

  start() {
    if (this.running || typeof window === 'undefined') return;
    if (!this.canvas) this.init();
    if (!this.canvas || !this.ctx) return;

    this.running = true;
    this.resize();
    if (window.addEventListener && this.boundResize) {
      window.addEventListener('resize', this.boundResize);
    }
    if (window.addEventListener && this.boundMouseMove) {
      window.addEventListener('mousemove', this.boundMouseMove);
    }

    const universeEl = document.getElementById('lava-universe');
    if (universeEl && universeEl.classList) universeEl.classList.remove('hidden');

    if (typeof requestAnimationFrame === 'function') {
      const loop = (timestamp) => {
        if (!this.running) return;
        this.updateAndDraw(timestamp || (typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now()));
        this.animId = requestAnimationFrame(loop);
      };
      this.animId = requestAnimationFrame(loop);
    }
  },

  stop() {
    this.running = false;
    if (this.animId && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(this.animId);
      this.animId = null;
    }
    if (typeof window !== 'undefined') {
      if (this.boundResize && window.removeEventListener) window.removeEventListener('resize', this.boundResize);
      if (this.boundMouseMove && window.removeEventListener) window.removeEventListener('mousemove', this.boundMouseMove);
    }
    const universeEl = typeof document !== 'undefined' ? document.getElementById('lava-universe') : null;
    if (universeEl && universeEl.classList) universeEl.classList.add('hidden');

    if (this.ctx && this.canvas && typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.canvas.width || 0, this.canvas.height || 0);
    }
  },

  updateAndDraw(timestamp) {
    if (!this.ctx || !this.canvas) return;

    // Smooth mouse parallax draft lerp
    this.mouseX += (this.targetMouseX - this.mouseX) * 0.04;
    this.mouseY += (this.targetMouseY - this.mouseY) * 0.04;

    if (typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.width, this.height);
    }

    if (typeof this.ctx.save === 'function' && typeof this.ctx.beginPath === 'function') {
      for (let i = 0; i < this.embers.length; i++) {
        const e = this.embers[i];
        e.y += e.vy;
        e.swayPhase += e.swaySpeed;
        e.x += e.baseVx + Math.sin(e.swayPhase) * e.swayAmp + this.mouseX * 0.3;
        e.alpha -= e.decay;

        // Respawn when top edge reached or burnt out
        if (e.y < -20 || e.alpha <= 0.05 || e.x < -30 || e.x > this.width + 30) {
          const respawned = this.spawnEmber(null, false);
          e.x = respawned.x;
          e.y = respawned.y;
          e.vy = respawned.vy;
          e.alpha = respawned.alpha;
          e.decay = respawned.decay;
          e.color = respawned.color;
          e.radius = respawned.radius;
          e.hasGlow = respawned.hasGlow;
          continue;
        }

        this.ctx.save();
        this.ctx.globalAlpha = Math.max(0.05, Math.min(1, e.alpha));
        this.ctx.fillStyle = e.color;

        this.ctx.beginPath();
        if (typeof this.ctx.arc === 'function') {
          this.ctx.arc(e.x, e.y, e.radius, 0, Math.PI * 2);
        }
        if (typeof this.ctx.fill === 'function') {
          this.ctx.fill();
        }

        // Ambient molten halo for luminous embers
        if (e.hasGlow && typeof this.ctx.stroke === 'function') {
          this.ctx.strokeStyle = e.color;
          this.ctx.lineWidth = 1;
          this.ctx.beginPath();
          if (typeof this.ctx.arc === 'function') {
            this.ctx.arc(e.x, e.y, e.radius * 1.8, 0, Math.PI * 2);
          }
          this.ctx.stroke();
        }
        this.ctx.restore();
      }
    }
  }
};

// =========================================================================
// Anime Action Manga Energy & Katana Slash Engine (Anime Theme)
// Enhanced with Demon Slayer Sakura Petals & Thunder Breathing Lightning
// =========================================================================
const animeUniverseEngine = {
  running: false,
  animId: null,
  canvas: null,
  ctx: null,
  particles: [],
  slashes: [],
  petals: [],
  lightning: [],
  lastSlashTime: 0,
  lastLightningTime: 0,
  mouseX: 0,
  mouseY: 0,
  targetMouseX: 0,
  targetMouseY: 0,
  width: 0,
  height: 0,
  boundResize: null,
  boundMouseMove: null,

  init() {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    this.canvas = document.getElementById('anime-canvas');
    if (!this.canvas || !this.canvas.getContext) return;
    this.ctx = this.canvas.getContext('2d');
    if (!this.ctx) return;

    this.boundResize = () => this.resize();
    this.boundMouseMove = (e) => {
      if (!e) return;
      this.targetMouseX = ((e.clientX || 0) - this.width / 2) * 0.05;
      this.targetMouseY = ((e.clientY || 0) - this.height / 2) * 0.05;
      // Add cursor chakra spark trail
      if (Math.random() < 0.35 && this.particles.length < 120) {
        this.particles.push({
          x: e.clientX || 0,
          y: e.clientY || 0,
          vx: (Math.random() - 0.5) * 2,
          vy: (Math.random() - 0.5) * 2,
          radius: Math.random() * 2 + 1,
          color: Math.random() < 0.6 ? '#06b6d4' : '#f97316',
          alpha: 0.9,
          decay: 0.03
        });
      }
    };
  },

  resize() {
    if (!this.canvas) return;
    this.width = (typeof window !== 'undefined' && window.innerWidth) ? window.innerWidth : 1280;
    this.height = (typeof window !== 'undefined' && window.innerHeight) ? window.innerHeight : 800;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.createParticles();
    this.createPetals();
  },

  createParticles() {
    this.particles = [];
    const count = Math.min(80, Math.max(40, Math.floor((this.width * this.height) / 14000)));
    const colors = [
      '#06b6d4', // Rasengan cyan
      '#38bdf8', // Chakra sky
      '#f97316', // Sun breathing orange
      '#ef4444', // Flame breathing red
      '#fbbf24', // Nichirin blade gold
      '#ffffff'  // Pure aura white
    ];

    for (let i = 0; i < count; i++) {
      this.particles.push({
        x: Math.random() * this.width,
        y: Math.random() * this.height,
        vx: (Math.random() - 0.5) * 0.8,
        vy: -(Math.random() * 0.9 + 0.3),
        radius: Math.random() * 2 + 0.8,
        color: colors[Math.floor(Math.random() * colors.length)],
        alpha: Math.random() * 0.5 + 0.3,
        decay: Math.random() * 0.005 + 0.002
      });
    }
  },

  createPetals() {
    this.petals = [];
    const count = Math.min(28, Math.max(16, Math.floor(this.width / 50)));
    const colors = ['#fb7185', '#fda4af', '#f43f5e', '#f472b6'];

    for (let i = 0; i < count; i++) {
      this.petals.push({
        x: Math.random() * (this.width + 100) - 50,
        y: Math.random() * this.height,
        vx: Math.random() * 0.9 + 0.6,
        vy: Math.random() * 0.8 + 0.7,
        swayPhase: Math.random() * Math.PI * 2,
        swaySpeed: Math.random() * 0.03 + 0.02,
        swayAmp: Math.random() * 1.5 + 0.8,
        rot: Math.random() * Math.PI * 2,
        rotSpeed: (Math.random() - 0.5) * 0.04,
        flip: Math.random() * Math.PI * 2,
        flipSpeed: Math.random() * 0.04 + 0.02,
        size: Math.random() * 4 + 8,
        color: colors[Math.floor(Math.random() * colors.length)],
        alpha: Math.random() * 0.3 + 0.55
      });
    }
  },

  spawnSlash() {
    // Dynamic anime speed line / katana slash across the screen
    const isCyan = Math.random() < 0.5;
    const startX = Math.random() * this.width;
    const startY = Math.random() * this.height * 0.7;
    const angle = (Math.PI / 6) + (Math.random() - 0.5) * 0.4; // diagonal angle ~30 deg
    const speed = Math.random() * 12 + 16;
    const length = Math.random() * 140 + 120;
    this.slashes.push({
      x: startX,
      y: startY,
      dx: Math.cos(angle) * speed,
      dy: Math.sin(angle) * speed,
      length,
      color: isCyan ? '#06b6d4' : '#f97316',
      accentColor: isCyan ? '#ffffff' : '#fbbf24',
      opacity: 1.0,
      decay: Math.random() * 0.035 + 0.025
    });
  },

  spawnLightning() {
    // Zenitsu Thunder Breathing / Sasuke Chidori electric crackle
    const isGold = Math.random() < 0.65;
    const mainColor = isGold ? '#fde047' : '#38bdf8';
    const glowColor = isGold ? '#eab308' : '#06b6d4';

    const startX = Math.random() * (this.width * 0.75) + this.width * 0.12;
    const startY = 0;
    const targetX = startX + (Math.random() - 0.5) * 320;
    const targetY = this.height * 0.65 + Math.random() * (this.height * 0.35);

    const steps = 10;
    const mainBranch = [{ x: startX, y: startY }];
    let currX = startX;
    let currY = startY;
    const dx = (targetX - startX) / steps;
    const dy = (targetY - startY) / steps;

    for (let i = 1; i < steps; i++) {
      currX += dx + (Math.random() - 0.5) * 70;
      currY += dy + (Math.random() - 0.2) * 25;
      mainBranch.push({ x: currX, y: currY });
    }
    mainBranch.push({ x: targetX, y: targetY });

    const forks = [];
    if (Math.random() < 0.75) {
      const forkIdx = Math.floor(Math.random() * 4) + 3;
      if (mainBranch[forkIdx]) {
        let fx = mainBranch[forkIdx].x;
        let fy = mainBranch[forkIdx].y;
        const subFork = [{ x: fx, y: fy }];
        const forkSteps = 4;
        for (let k = 0; k < forkSteps; k++) {
          fx += (Math.random() - 0.3) * 60;
          fy += Math.random() * 40 + 25;
          subFork.push({ x: fx, y: fy });
        }
        forks.push(subFork);
      }
    }

    this.lightning.push({
      branches: [mainBranch, ...forks],
      color: mainColor,
      glowColor,
      alpha: 1.0,
      decay: 0.08
    });
  },

  start() {
    if (this.running || typeof window === 'undefined') return;
    if (!this.canvas) this.init();
    if (!this.canvas || !this.ctx) return;

    this.running = true;
    this.resize();
    if (window.addEventListener && this.boundResize) {
      window.addEventListener('resize', this.boundResize);
    }
    if (window.addEventListener && this.boundMouseMove) {
      window.addEventListener('mousemove', this.boundMouseMove);
    }
    this.lastSlashTime = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
    this.lastLightningTime = this.lastSlashTime;

    const universeEl = document.getElementById('anime-universe');
    if (universeEl && universeEl.classList) universeEl.classList.remove('hidden');

    if (typeof requestAnimationFrame === 'function') {
      const loop = (timestamp) => {
        if (!this.running) return;
        this.updateAndDraw(timestamp || (typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now()));
        this.animId = requestAnimationFrame(loop);
      };
      this.animId = requestAnimationFrame(loop);
    }
  },

  stop() {
    this.running = false;
    if (this.animId && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(this.animId);
      this.animId = null;
    }
    if (typeof window !== 'undefined') {
      if (this.boundResize && window.removeEventListener) window.removeEventListener('resize', this.boundResize);
      if (this.boundMouseMove && window.removeEventListener) window.removeEventListener('mousemove', this.boundMouseMove);
    }
    const universeEl = typeof document !== 'undefined' ? document.getElementById('anime-universe') : null;
    if (universeEl && universeEl.classList) universeEl.classList.add('hidden');

    this.lightning = [];

    if (this.ctx && this.canvas && typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.canvas.width || 0, this.canvas.height || 0);
    }
  },

  updateAndDraw(timestamp) {
    if (!this.ctx || !this.canvas) return;

    // Smooth parallax drift
    this.mouseX += (this.targetMouseX - this.mouseX) * 0.05;
    this.mouseY += (this.targetMouseY - this.mouseY) * 0.05;

    if (typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.width, this.height);
    }

    // 1. Draw floating chakra & flame particles
    if (typeof this.ctx.save === 'function' && typeof this.ctx.beginPath === 'function') {
      for (let i = this.particles.length - 1; i >= 0; i--) {
        const p = this.particles[i];
        p.x += p.vx + this.mouseX * 0.2;
        p.y += p.vy;
        p.alpha -= p.decay;

        if (p.alpha <= 0 || p.y < -10 || p.x < -10 || p.x > this.width + 10) {
          if (this.particles.length > 60) {
            this.particles.splice(i, 1);
            continue;
          }
          p.x = Math.random() * this.width;
          p.y = this.height + 10;
          p.alpha = Math.random() * 0.5 + 0.3;
        }

        this.ctx.save();
        this.ctx.globalAlpha = Math.max(0.05, Math.min(1, p.alpha));
        this.ctx.fillStyle = p.color;
        this.ctx.beginPath();
        if (typeof this.ctx.arc === 'function') {
          this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        }
        if (typeof this.ctx.fill === 'function') {
          this.ctx.fill();
        }
        this.ctx.restore();
      }
    }

    // 2. Draw Fluttering Demon Slayer Sakura Petals (Cherry Blossom Storm)
    if (typeof this.ctx.save === 'function' && typeof this.ctx.beginPath === 'function') {
      for (let i = 0; i < this.petals.length; i++) {
        const p = this.petals[i];
        p.swayPhase += p.swaySpeed;
        p.rot += p.rotSpeed;
        p.flip += p.flipSpeed;
        p.x += p.vx + Math.sin(p.swayPhase) * p.swayAmp + this.mouseX * 0.15;
        p.y += p.vy;

        // Wrap around bottom/right edges
        if (p.y > this.height + 25) {
          p.y = -25;
          p.x = Math.random() * (this.width + 100) - 50;
        } else if (p.x > this.width + 50) {
          p.x = -30;
          p.y = Math.random() * this.height;
        }

        this.ctx.save();
        this.ctx.translate(p.x, p.y);
        this.ctx.rotate(p.rot);
        this.ctx.scale(1, Math.cos(p.flip));
        this.ctx.globalAlpha = p.alpha;
        this.ctx.fillStyle = p.color;

        this.ctx.beginPath();
        const s = p.size;
        if (typeof this.ctx.moveTo === 'function' && typeof this.ctx.bezierCurveTo === 'function') {
          this.ctx.moveTo(0, -s);
          this.ctx.bezierCurveTo(s * 0.6, -s * 0.6, s * 0.8, s * 0.4, 0, s);
          this.ctx.bezierCurveTo(-s * 0.8, s * 0.4, -s * 0.6, -s * 0.6, 0, -s);
        } else if (typeof this.ctx.arc === 'function') {
          this.ctx.arc(0, 0, s * 0.6, 0, Math.PI * 2);
        }
        if (typeof this.ctx.fill === 'function') {
          this.ctx.fill();
        }
        this.ctx.restore();
      }
    }

    // 3. Periodic Katana Slash / Speed lines
    const now = timestamp || Date.now();
    if (now - this.lastSlashTime > 4000 + Math.random() * 3000) {
      this.spawnSlash();
      this.lastSlashTime = now;
    }

    if (typeof this.ctx.save === 'function' && typeof this.ctx.createLinearGradient === 'function') {
      for (let i = this.slashes.length - 1; i >= 0; i--) {
        const s = this.slashes[i];
        s.x += s.dx;
        s.y += s.dy;
        s.opacity -= s.decay;

        if (s.opacity <= 0 || s.x > this.width + 100 || s.y > this.height + 100) {
          this.slashes.splice(i, 1);
          continue;
        }

        const hyp = Math.hypot(s.dx, s.dy) || 1;
        const tailX = s.x - (s.dx / hyp) * s.length;
        const tailY = s.y - (s.dy / hyp) * s.length;

        this.ctx.save();
        this.ctx.globalAlpha = Math.max(0, s.opacity);
        const grad = this.ctx.createLinearGradient(s.x, s.y, tailX, tailY);
        grad.addColorStop(0, s.accentColor);
        grad.addColorStop(0.3, s.color);
        grad.addColorStop(1, 'transparent');

        this.ctx.strokeStyle = grad;
        this.ctx.lineWidth = 2.2;
        this.ctx.lineCap = 'round';
        this.ctx.beginPath();
        this.ctx.moveTo(s.x, s.y);
        this.ctx.lineTo(tailX, tailY);
        this.ctx.stroke();
        this.ctx.restore();
      }
    }

    // 4. Thunder Breathing Lightning Crackle (Zenitsu & Chidori)
    if (now - this.lastLightningTime > 4500 + Math.random() * 3500) {
      this.spawnLightning();
      this.lastLightningTime = now;
    }

    if (typeof this.ctx.save === 'function' && typeof this.ctx.beginPath === 'function') {
      for (let i = this.lightning.length - 1; i >= 0; i--) {
        const lt = this.lightning[i];
        lt.alpha -= lt.decay;

        if (lt.alpha <= 0) {
          this.lightning.splice(i, 1);
          continue;
        }

        for (let b = 0; b < lt.branches.length; b++) {
          const pts = lt.branches[b];
          if (pts.length < 2) continue;

          // Outer Glow
          this.ctx.save();
          this.ctx.globalAlpha = lt.alpha * 0.65;
          this.ctx.strokeStyle = lt.glowColor;
          this.ctx.lineWidth = 4.2;
          this.ctx.lineCap = 'round';
          this.ctx.lineJoin = 'round';
          this.ctx.beginPath();
          this.ctx.moveTo(pts[0].x, pts[0].y);
          for (let p = 1; p < pts.length; p++) {
            this.ctx.lineTo(pts[p].x, pts[p].y);
          }
          if (typeof this.ctx.stroke === 'function') this.ctx.stroke();

          // White-hot core
          this.ctx.globalAlpha = lt.alpha;
          this.ctx.strokeStyle = '#ffffff';
          this.ctx.lineWidth = 1.6;
          this.ctx.beginPath();
          this.ctx.moveTo(pts[0].x, pts[0].y);
          for (let p = 1; p < pts.length; p++) {
            this.ctx.lineTo(pts[p].x, pts[p].y);
          }
          if (typeof this.ctx.stroke === 'function') this.ctx.stroke();
          this.ctx.restore();
        }
      }
    }
  }
};

// =========================================================================
// Sunny Blue Sky & Drifting Clouds Engine (Sky Theme)
// =========================================================================
const skyUniverseEngine = {
  running: false,
  animId: null,
  canvas: null,
  ctx: null,
  clouds: [],
  birds: [],
  mouseX: 0,
  mouseY: 0,
  targetMouseX: 0,
  targetMouseY: 0,
  width: 0,
  height: 0,
  boundResize: null,
  boundMouseMove: null,

  init() {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    this.canvas = document.getElementById('sky-canvas');
    if (!this.canvas || !this.canvas.getContext) return;
    this.ctx = this.canvas.getContext('2d');
    if (!this.ctx) return;

    this.boundResize = () => this.resize();
    this.boundMouseMove = (e) => {
      if (!e) return;
      this.targetMouseX = ((e.clientX || 0) - this.width / 2) * 0.02;
      this.targetMouseY = ((e.clientY || 0) - this.height / 2) * 0.02;
    };
  },

  resize() {
    if (!this.canvas) return;
    this.width = (typeof window !== 'undefined' && window.innerWidth) ? window.innerWidth : 1280;
    this.height = (typeof window !== 'undefined' && window.innerHeight) ? window.innerHeight : 800;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.createClouds();
    this.createBirds();
  },

  createClouds() {
    this.clouds = [];
    const count = Math.min(10, Math.max(6, Math.floor(this.width / 180)));
    for (let i = 0; i < count; i++) {
      const scale = Math.random() * 0.6 + 0.7;
      const puffs = [];
      const puffCount = Math.floor(Math.random() * 4) + 5;
      for (let p = 0; p < puffCount; p++) {
        puffs.push({
          dx: (p - puffCount / 2) * 28 * scale + (Math.random() - 0.5) * 12,
          dy: (Math.random() - 0.5) * 16 * scale,
          r: (Math.random() * 22 + 28) * scale
        });
      }
      this.clouds.push({
        x: Math.random() * (this.width + 300) - 150,
        y: Math.random() * (this.height * 0.65) + 30,
        speed: (Math.random() * 0.35 + 0.25) * (scale * 0.9),
        scale,
        opacity: Math.random() * 0.25 + 0.45,
        puffs
      });
    }
  },

  createBirds() {
    this.birds = [];
    const birdCount = 3;
    for (let i = 0; i < birdCount; i++) {
      this.birds.push({
        x: Math.random() * this.width,
        y: Math.random() * (this.height * 0.45) + 40,
        vx: Math.random() * 0.8 + 1.2,
        vy: (Math.random() - 0.5) * 0.2,
        size: Math.random() * 4 + 7,
        wingPhase: Math.random() * Math.PI * 2,
        wingSpeed: Math.random() * 0.05 + 0.08
      });
    }
  },

  start() {
    if (this.running || typeof window === 'undefined') return;
    if (!this.canvas) this.init();
    if (!this.canvas || !this.ctx) return;

    this.running = true;
    this.resize();
    if (window.addEventListener && this.boundResize) {
      window.addEventListener('resize', this.boundResize);
    }
    if (window.addEventListener && this.boundMouseMove) {
      window.addEventListener('mousemove', this.boundMouseMove);
    }

    const universeEl = document.getElementById('sky-universe');
    if (universeEl && universeEl.classList) universeEl.classList.remove('hidden');

    if (typeof requestAnimationFrame === 'function') {
      const loop = (timestamp) => {
        if (!this.running) return;
        this.updateAndDraw(timestamp || (typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now()));
        this.animId = requestAnimationFrame(loop);
      };
      this.animId = requestAnimationFrame(loop);
    }
  },

  stop() {
    this.running = false;
    if (this.animId && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(this.animId);
      this.animId = null;
    }
    if (typeof window !== 'undefined') {
      if (this.boundResize && window.removeEventListener) window.removeEventListener('resize', this.boundResize);
      if (this.boundMouseMove && window.removeEventListener) window.removeEventListener('mousemove', this.boundMouseMove);
    }
    const universeEl = typeof document !== 'undefined' ? document.getElementById('sky-universe') : null;
    if (universeEl && universeEl.classList) universeEl.classList.add('hidden');

    if (this.ctx && this.canvas && typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.canvas.width || 0, this.canvas.height || 0);
    }
  },

  updateAndDraw(timestamp) {
    if (!this.ctx || !this.canvas) return;

    // Smooth mouse breeze lerp
    this.mouseX += (this.targetMouseX - this.mouseX) * 0.03;
    this.mouseY += (this.targetMouseY - this.mouseY) * 0.03;

    if (typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.width, this.height);
    }

    // 1. Draw Fluffy Drifting Clouds
    if (typeof this.ctx.save === 'function' && typeof this.ctx.beginPath === 'function') {
      for (let i = 0; i < this.clouds.length; i++) {
        const c = this.clouds[i];
        c.x += c.speed + this.mouseX * 0.15;

        // Wrap around right-to-left
        if (c.x - 250 > this.width) {
          c.x = -250;
          c.y = Math.random() * (this.height * 0.65) + 30;
        }

        this.ctx.save();
        this.ctx.fillStyle = '#ffffff';
        this.ctx.globalAlpha = c.opacity;
        for (let p = 0; p < c.puffs.length; p++) {
          const puff = c.puffs[p];
          this.ctx.beginPath();
          if (typeof this.ctx.arc === 'function') {
            this.ctx.arc(c.x + puff.dx, c.y + puff.dy, puff.r, 0, Math.PI * 2);
          }
          if (typeof this.ctx.fill === 'function') {
            this.ctx.fill();
          }
        }
        this.ctx.restore();
      }
    }

    // 2. Draw Gentle Soaring Birds
    if (typeof this.ctx.save === 'function' && typeof this.ctx.beginPath === 'function') {
      for (let i = 0; i < this.birds.length; i++) {
        const b = this.birds[i];
        b.x += b.vx;
        b.y += b.vy;
        b.wingPhase += b.wingSpeed;

        if (b.x - 40 > this.width) {
          b.x = -40;
          b.y = Math.random() * (this.height * 0.45) + 40;
        }

        const wingY = Math.sin(b.wingPhase) * b.size * 0.45;

        this.ctx.save();
        this.ctx.strokeStyle = '#0369a1';
        this.ctx.lineWidth = 1.6;
        this.ctx.lineCap = 'round';
        this.ctx.globalAlpha = 0.55;

        this.ctx.beginPath();
        if (typeof this.ctx.moveTo === 'function' && typeof this.ctx.quadraticCurveTo === 'function') {
          this.ctx.moveTo(b.x - b.size, b.y + wingY);
          this.ctx.quadraticCurveTo(b.x - b.size * 0.4, b.y - b.size * 0.25, b.x, b.y);
          this.ctx.quadraticCurveTo(b.x + b.size * 0.4, b.y - b.size * 0.25, b.x + b.size, b.y + wingY);
        }
        if (typeof this.ctx.stroke === 'function') {
          this.ctx.stroke();
        }
        this.ctx.restore();
      }
    }
  }
};

// =========================================================================
// Deep Ocean Aquarium & Swimming Fishes Engine (Ocean Theme)
// =========================================================================
const oceanUniverseEngine = {
  running: false,
  animId: null,
  canvas: null,
  ctx: null,
  fishes: [],
  bubbles: [],
  mouseX: -999,
  mouseY: -999,
  width: 0,
  height: 0,
  boundResize: null,
  boundMouseMove: null,

  init() {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    this.canvas = document.getElementById('ocean-canvas');
    if (!this.canvas || !this.canvas.getContext) return;
    this.ctx = this.canvas.getContext('2d');
    if (!this.ctx) return;

    this.boundResize = () => this.resize();
    this.boundMouseMove = (e) => {
      if (!e) return;
      this.mouseX = e.clientX || 0;
      this.mouseY = e.clientY || 0;
    };
  },

  resize() {
    if (!this.canvas) return;
    this.width = (typeof window !== 'undefined' && window.innerWidth) ? window.innerWidth : 1280;
    this.height = (typeof window !== 'undefined' && window.innerHeight) ? window.innerHeight : 800;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.createFishes();
    this.createBubbles();
  },

  createFishes() {
    this.fishes = [];
    const count = Math.min(22, Math.max(12, Math.floor((this.width * this.height) / 45000)));
    const fishColors = [
      { body: '#f97316', stripe: '#ffffff' }, // Clownfish orange
      { body: '#0284c7', stripe: '#38bdf8' }, // Blue tang
      { body: '#eab308', stripe: '#fef08a' }, // Yellow tang
      { body: '#f43f5e', stripe: '#ffffff' }, // Coral rose
      { body: '#10b981', stripe: '#6ee7b7' }  // Emerald chromis
    ];

    for (let i = 0; i < count; i++) {
      const palette = fishColors[Math.floor(Math.random() * fishColors.length)];
      const goingRight = Math.random() < 0.55;
      const speed = Math.random() * 1.0 + 0.7;
      const length = Math.random() * 12 + 20; // 20 to 32px
      const height = length * 0.45;

      this.fishes.push({
        x: Math.random() * this.width,
        baseY: Math.random() * (this.height * 0.8) + this.height * 0.1,
        y: 0,
        vx: goingRight ? speed : -speed,
        length,
        height,
        color: palette.body,
        stripe: palette.stripe,
        swimPhase: Math.random() * Math.PI * 2,
        swimSpeed: Math.random() * 0.04 + 0.03,
        tailPhase: Math.random() * Math.PI * 2,
        tailSpeed: Math.random() * 0.15 + 0.12,
        alpha: Math.random() * 0.35 + 0.6
      });
    }
  },

  createBubbles() {
    this.bubbles = [];
    const count = Math.min(35, Math.max(20, Math.floor(this.width / 40)));
    for (let i = 0; i < count; i++) {
      this.bubbles.push({
        x: Math.random() * this.width,
        y: Math.random() * this.height,
        vy: -(Math.random() * 1.2 + 0.7),
        radius: Math.random() * 3 + 1.5,
        wobblePhase: Math.random() * Math.PI * 2,
        wobbleSpeed: Math.random() * 0.05 + 0.03,
        alpha: Math.random() * 0.4 + 0.3
      });
    }
  },

  start() {
    if (this.running || typeof window === 'undefined') return;
    if (!this.canvas) this.init();
    if (!this.canvas || !this.ctx) return;

    this.running = true;
    this.resize();
    if (window.addEventListener && this.boundResize) {
      window.addEventListener('resize', this.boundResize);
    }
    if (window.addEventListener && this.boundMouseMove) {
      window.addEventListener('mousemove', this.boundMouseMove);
    }

    const universeEl = document.getElementById('ocean-universe');
    if (universeEl && universeEl.classList) universeEl.classList.remove('hidden');

    if (typeof requestAnimationFrame === 'function') {
      const loop = (timestamp) => {
        if (!this.running) return;
        this.updateAndDraw(timestamp || (typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now()));
        this.animId = requestAnimationFrame(loop);
      };
      this.animId = requestAnimationFrame(loop);
    }
  },

  stop() {
    this.running = false;
    if (this.animId && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(this.animId);
      this.animId = null;
    }
    if (typeof window !== 'undefined') {
      if (this.boundResize && window.removeEventListener) window.removeEventListener('resize', this.boundResize);
      if (this.boundMouseMove && window.removeEventListener) window.removeEventListener('mousemove', this.boundMouseMove);
    }
    const universeEl = typeof document !== 'undefined' ? document.getElementById('ocean-universe') : null;
    if (universeEl && universeEl.classList) universeEl.classList.add('hidden');

    if (this.ctx && this.canvas && typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.canvas.width || 0, this.canvas.height || 0);
    }
  },

  updateAndDraw(timestamp) {
    if (!this.ctx || !this.canvas) return;

    if (typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.width, this.height);
    }

    // 1. Draw Rising Oxygen Bubbles
    if (typeof this.ctx.save === 'function' && typeof this.ctx.beginPath === 'function') {
      for (let i = 0; i < this.bubbles.length; i++) {
        const b = this.bubbles[i];
        b.y += b.vy;
        b.wobblePhase += b.wobbleSpeed;
        const bx = b.x + Math.sin(b.wobblePhase) * 1.5;

        // Respawn at bottom when reaching top
        if (b.y < -15) {
          b.y = this.height + 10;
          b.x = Math.random() * this.width;
        }

        this.ctx.save();
        this.ctx.globalAlpha = b.alpha;
        this.ctx.strokeStyle = '#38bdf8';
        this.ctx.fillStyle = 'rgba(186, 230, 253, 0.25)';
        this.ctx.lineWidth = 1;

        this.ctx.beginPath();
        if (typeof this.ctx.arc === 'function') {
          this.ctx.arc(bx, b.y, b.radius, 0, Math.PI * 2);
        }
        if (typeof this.ctx.fill === 'function') {
          this.ctx.fill();
        }
        if (typeof this.ctx.stroke === 'function') {
          this.ctx.stroke();
        }

        // Shimmer glint highlight
        if (b.radius > 2.5 && typeof this.ctx.arc === 'function') {
          this.ctx.fillStyle = '#ffffff';
          this.ctx.beginPath();
          this.ctx.arc(bx - b.radius * 0.35, b.y - b.radius * 0.35, b.radius * 0.3, 0, Math.PI * 2);
          if (typeof this.ctx.fill === 'function') this.ctx.fill();
        }
        this.ctx.restore();
      }
    }

    // 2. Draw Animated Swimming Fishes
    if (typeof this.ctx.save === 'function' && typeof this.ctx.beginPath === 'function') {
      for (let i = 0; i < this.fishes.length; i++) {
        const f = this.fishes[i];
        f.swimPhase += f.swimSpeed;
        f.tailPhase += f.tailSpeed;

        // Subtle vertical undulating
        f.y = f.baseY + Math.sin(f.swimPhase) * 6;

        // Mouse dart reaction (swim faster if mouse is near)
        const distToMouse = Math.hypot(this.mouseX - f.x, this.mouseY - f.y);
        let currentVx = f.vx;
        if (distToMouse < 80) {
          currentVx = f.vx * 2.2;
        }

        f.x += currentVx;

        // Wrap around screen
        if (f.vx > 0 && f.x - f.length > this.width) {
          f.x = -f.length;
          f.baseY = Math.random() * (this.height * 0.8) + this.height * 0.1;
        } else if (f.vx < 0 && f.x + f.length < 0) {
          f.x = this.width + f.length;
          f.baseY = Math.random() * (this.height * 0.8) + this.height * 0.1;
        }

        const dir = f.vx > 0 ? 1 : -1;
        const tailOffset = Math.sin(f.tailPhase) * (f.height * 0.45);

        this.ctx.save();
        this.ctx.globalAlpha = f.alpha;
        this.ctx.fillStyle = f.color;

        // Draw Fish Body (Tear/Ellipse shape)
        this.ctx.beginPath();
        if (typeof this.ctx.moveTo === 'function' && typeof this.ctx.quadraticCurveTo === 'function') {
          const noseX = f.x + dir * (f.length * 0.5);
          const tailBaseX = f.x - dir * (f.length * 0.45);
          
          this.ctx.moveTo(noseX, f.y);
          this.ctx.quadraticCurveTo(f.x, f.y - f.height * 0.6, tailBaseX, f.y);
          this.ctx.quadraticCurveTo(f.x, f.y + f.height * 0.6, noseX, f.y);
          if (typeof this.ctx.fill === 'function') this.ctx.fill();

          // Draw Fish Tail Fin (articulated wagging)
          const tailTipX = tailBaseX - dir * (f.length * 0.35);
          this.ctx.beginPath();
          this.ctx.moveTo(tailBaseX, f.y);
          this.ctx.lineTo(tailTipX, f.y - f.height * 0.55 + tailOffset);
          this.ctx.lineTo(tailTipX + dir * 3, f.y + tailOffset * 0.5);
          this.ctx.lineTo(tailTipX, f.y + f.height * 0.55 + tailOffset);
          this.ctx.closePath();
          if (typeof this.ctx.fill === 'function') this.ctx.fill();

          // Reef stripe accent
          if (f.stripe && typeof this.ctx.stroke === 'function') {
            this.ctx.strokeStyle = f.stripe;
            this.ctx.lineWidth = 1.8;
            this.ctx.beginPath();
            this.ctx.moveTo(f.x - dir * 2, f.y - f.height * 0.4);
            this.ctx.lineTo(f.x - dir * 2, f.y + f.height * 0.4);
            this.ctx.stroke();
          }

          // Little eye dot
          if (typeof this.ctx.arc === 'function') {
            const eyeX = f.x + dir * (f.length * 0.32);
            const eyeY = f.y - f.height * 0.12;
            this.ctx.fillStyle = '#ffffff';
            this.ctx.beginPath();
            this.ctx.arc(eyeX, eyeY, 1.8, 0, Math.PI * 2);
            if (typeof this.ctx.fill === 'function') this.ctx.fill();

            this.ctx.fillStyle = '#02182b';
            this.ctx.beginPath();
            this.ctx.arc(eyeX + dir * 0.5, eyeY, 0.9, 0, Math.PI * 2);
            if (typeof this.ctx.fill === 'function') this.ctx.fill();
          }
        }
        this.ctx.restore();
      }
    }
  }
};

// =========================================================================
// Sakura Princess — Falling Cherry-Blossom Petals Engine (Sakura Theme)
// =========================================================================
const sakuraUniverseEngine = {
  running: false,
  animId: null,
  canvas: null,
  ctx: null,
  petals: [],
  width: 0,
  height: 0,
  boundResize: null,

  init() {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    this.canvas = document.getElementById('sakura-canvas');
    if (!this.canvas || !this.canvas.getContext) return;
    this.ctx = this.canvas.getContext('2d');
    if (!this.ctx) return;
    this.boundResize = () => this.resize();
  },

  resize() {
    if (!this.canvas) return;
    this.width = (typeof window !== 'undefined' && window.innerWidth) ? window.innerWidth : 1280;
    this.height = (typeof window !== 'undefined' && window.innerHeight) ? window.innerHeight : 800;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.createPetals();
  },

  createPetals() {
    this.petals = [];
    const count = Math.min(42, Math.max(24, Math.floor(this.width / 34)));
    const colors = ['#fbcfe8', '#f9a8d4', '#f472b6', '#fda4af', '#ffffff', '#fce7f3'];
    for (let i = 0; i < count; i++) {
      this.petals.push({
        x: Math.random() * this.width,
        y: Math.random() * this.height,
        vy: Math.random() * 0.9 + 0.5,
        swayPhase: Math.random() * Math.PI * 2,
        swaySpeed: Math.random() * 0.02 + 0.008,
        swayAmp: Math.random() * 28 + 12,
        size: Math.random() * 5 + 5,
        rot: Math.random() * Math.PI * 2,
        rotSpeed: (Math.random() - 0.5) * 0.03,
        color: colors[Math.floor(Math.random() * colors.length)],
        alpha: Math.random() * 0.35 + 0.55
      });
    }
  },

  start() {
    if (this.running || typeof window === 'undefined') return;
    if (!this.canvas) this.init();
    if (!this.canvas || !this.ctx) return;
    this.running = true;
    this.resize();
    if (window.addEventListener && this.boundResize) window.addEventListener('resize', this.boundResize);
    const universeEl = document.getElementById('sakura-universe');
    if (universeEl && universeEl.classList) universeEl.classList.remove('hidden');
    if (typeof requestAnimationFrame === 'function') {
      const loop = (ts) => {
        if (!this.running) return;
        this.updateAndDraw();
        this.animId = requestAnimationFrame(loop);
      };
      this.animId = requestAnimationFrame(loop);
    }
  },

  stop() {
    this.running = false;
    if (this.animId && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(this.animId);
      this.animId = null;
    }
    if (typeof window !== 'undefined' && this.boundResize && window.removeEventListener) {
      window.removeEventListener('resize', this.boundResize);
    }
    const universeEl = typeof document !== 'undefined' ? document.getElementById('sakura-universe') : null;
    if (universeEl && universeEl.classList) universeEl.classList.add('hidden');
    if (this.ctx && this.canvas && typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.canvas.width || 0, this.canvas.height || 0);
    }
  },

  updateAndDraw() {
    if (!this.ctx || !this.canvas) return;
    this.ctx.clearRect(0, 0, this.width, this.height);
    for (let i = 0; i < this.petals.length; i++) {
      const p = this.petals[i];
      p.y += p.vy;
      p.swayPhase += p.swaySpeed;
      p.rot += p.rotSpeed;
      p.x += Math.sin(p.swayPhase) * 0.6;
      if (p.y > this.height + 16) {
        p.y = -16;
        p.x = Math.random() * this.width;
      }
      if (p.x > this.width + 20) p.x = -20;
      if (p.x < -20) p.x = this.width + 20;
      this.ctx.save();
      this.ctx.globalAlpha = p.alpha;
      this.ctx.translate(p.x, p.y);
      this.ctx.rotate(p.rot);
      this.ctx.fillStyle = p.color;
      this.ctx.beginPath();
      // petal shape: two quadratic curves
      this.ctx.moveTo(0, -p.size * 0.6);
      this.ctx.quadraticCurveTo(p.size * 0.7, -p.size * 0.3, p.size * 0.35, p.size * 0.55);
      this.ctx.quadraticCurveTo(0, p.size * 0.85, -p.size * 0.35, p.size * 0.55);
      this.ctx.quadraticCurveTo(-p.size * 0.7, -p.size * 0.3, 0, -p.size * 0.6);
      this.ctx.fill();
      // tiny white highlight notch
      this.ctx.fillStyle = 'rgba(255,255,255,0.65)';
      this.ctx.beginPath();
      this.ctx.arc(-p.size * 0.12, -p.size * 0.18, p.size * 0.14, 0, Math.PI * 2);
      this.ctx.fill();
      this.ctx.restore();
    }
  }
};

// =========================================================================
// Fairy Garden — Butterflies + Firefly Sparkles Engine (Fairy Theme)
// =========================================================================
const fairyUniverseEngine = {
  running: false,
  animId: null,
  canvas: null,
  ctx: null,
  butterflies: [],
  sparkles: [],
  width: 0,
  height: 0,
  boundResize: null,

  init() {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    this.canvas = document.getElementById('fairy-canvas');
    if (!this.canvas || !this.canvas.getContext) return;
    this.ctx = this.canvas.getContext('2d');
    if (!this.ctx) return;
    this.boundResize = () => this.resize();
  },

  resize() {
    if (!this.canvas) return;
    this.width = (typeof window !== 'undefined' && window.innerWidth) ? window.innerWidth : 1280;
    this.height = (typeof window !== 'undefined' && window.innerHeight) ? window.innerHeight : 800;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.createButterflies();
    this.createSparkles();
  },

  createButterflies() {
    this.butterflies = [];
    const palettes = [
      { wing: '#f472b6', edge: '#be185d' },
      { wing: '#c084fc', edge: '#7e22ce' },
      { wing: '#fbbf24', edge: '#b45309' },
      { wing: '#4ade80', edge: '#15803d' },
      { wing: '#38bdf8', edge: '#0369a1' }
    ];
    const count = Math.min(9, Math.max(5, Math.floor(this.width / 220)));
    for (let i = 0; i < count; i++) {
      const pal = palettes[Math.floor(Math.random() * palettes.length)];
      this.butterflies.push({
        x: Math.random() * this.width,
        y: Math.random() * (this.height * 0.7) + 40,
        vx: (Math.random() - 0.5) * 1.1,
        vy: (Math.random() - 0.5) * 0.6,
        size: Math.random() * 6 + 9,
        wingPhase: Math.random() * Math.PI * 2,
        wingSpeed: Math.random() * 0.12 + 0.14,
        driftPhase: Math.random() * Math.PI * 2,
        wing: pal.wing,
        edge: pal.edge,
        alpha: Math.random() * 0.25 + 0.7
      });
    }
  },

  createSparkles() {
    this.sparkles = [];
    const count = Math.min(45, Math.max(25, Math.floor(this.width / 32)));
    for (let i = 0; i < count; i++) {
      this.sparkles.push({
        x: Math.random() * this.width,
        y: Math.random() * this.height,
        r: Math.random() * 1.8 + 0.8,
        twinklePhase: Math.random() * Math.PI * 2,
        twinkleSpeed: Math.random() * 0.06 + 0.03,
        vy: -(Math.random() * 0.25 + 0.08)
      });
    }
  },

  start() {
    if (this.running || typeof window === 'undefined') return;
    if (!this.canvas) this.init();
    if (!this.canvas || !this.ctx) return;
    this.running = true;
    this.resize();
    if (window.addEventListener && this.boundResize) window.addEventListener('resize', this.boundResize);
    const universeEl = document.getElementById('fairy-universe');
    if (universeEl && universeEl.classList) universeEl.classList.remove('hidden');
    if (typeof requestAnimationFrame === 'function') {
      const loop = () => {
        if (!this.running) return;
        this.updateAndDraw();
        this.animId = requestAnimationFrame(loop);
      };
      this.animId = requestAnimationFrame(loop);
    }
  },

  stop() {
    this.running = false;
    if (this.animId && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(this.animId);
      this.animId = null;
    }
    if (typeof window !== 'undefined' && this.boundResize && window.removeEventListener) {
      window.removeEventListener('resize', this.boundResize);
    }
    const universeEl = typeof document !== 'undefined' ? document.getElementById('fairy-universe') : null;
    if (universeEl && universeEl.classList) universeEl.classList.add('hidden');
    if (this.ctx && this.canvas && typeof this.ctx.clearRect === 'function') {
      this.ctx.clearRect(0, 0, this.canvas.width || 0, this.canvas.height || 0);
    }
  },

  updateAndDraw() {
    if (!this.ctx || !this.canvas) return;
    this.ctx.clearRect(0, 0, this.width, this.height);
    // 1. twinkling firefly sparkles drifting upward
    for (let i = 0; i < this.sparkles.length; i++) {
      const s = this.sparkles[i];
      s.twinklePhase += s.twinkleSpeed;
      s.y += s.vy;
      if (s.y < -8) {
        s.y = this.height + 8;
        s.x = Math.random() * this.width;
      }
      const glow = 0.35 + Math.abs(Math.sin(s.twinklePhase)) * 0.6;
      this.ctx.save();
      this.ctx.globalAlpha = glow;
      this.ctx.fillStyle = '#fef9c3';
      this.ctx.beginPath();
      this.ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      this.ctx.fill();
      this.ctx.globalAlpha = glow * 0.35;
      this.ctx.fillStyle = '#fde047';
      this.ctx.beginPath();
      this.ctx.arc(s.x, s.y, s.r * 2.6, 0, Math.PI * 2);
      this.ctx.fill();
      this.ctx.restore();
    }
    // 2. fluttering butterflies (two flapping wing ellipses + body)
    for (let i = 0; i < this.butterflies.length; i++) {
      const b = this.butterflies[i];
      b.wingPhase += b.wingSpeed;
      b.driftPhase += 0.012;
      b.x += b.vx + Math.sin(b.driftPhase) * 0.5;
      b.y += b.vy + Math.cos(b.driftPhase * 1.3) * 0.4;
      if (b.x > this.width + 30) b.x = -30;
      if (b.x < -30) b.x = this.width + 30;
      if (b.y > this.height + 30) b.y = -30;
      if (b.y < -30) b.y = this.height + 30;
      const flap = Math.abs(Math.sin(b.wingPhase));
      const wingSpread = 0.35 + flap * 0.65;
      this.ctx.save();
      this.ctx.globalAlpha = b.alpha;
      this.ctx.translate(b.x, b.y);
      // wings
      this.ctx.fillStyle = b.wing;
      this.ctx.strokeStyle = b.edge;
      this.ctx.lineWidth = 1;
      for (const side of [-1, 1]) {
        this.ctx.save();
        this.ctx.scale(side * wingSpread, 1);
        this.ctx.beginPath();
        this.ctx.ellipse(b.size * 0.55, -b.size * 0.15, b.size * 0.6, b.size * 0.42, 0.5, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.stroke();
        this.ctx.beginPath();
        this.ctx.ellipse(b.size * 0.45, b.size * 0.4, b.size * 0.42, b.size * 0.3, -0.4, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();
      }
      // body
      this.ctx.fillStyle = '#3f3f46';
      this.ctx.beginPath();
      this.ctx.ellipse(0, 0, b.size * 0.12, b.size * 0.5, 0, 0, Math.PI * 2);
      this.ctx.fill();
      this.ctx.restore();
    }
  }
};

if (typeof window !== 'undefined') {
  window.spaceUniverseEngine = spaceUniverseEngine;
  window.lavaUniverseEngine = lavaUniverseEngine;
  window.animeUniverseEngine = animeUniverseEngine;
  window.skyUniverseEngine = skyUniverseEngine;
  window.oceanUniverseEngine = oceanUniverseEngine;
  window.sakuraUniverseEngine = sakuraUniverseEngine;
  window.fairyUniverseEngine = fairyUniverseEngine;
}

function applyTheme(themeName) {
  const t = themeName || (state.settings && state.settings.theme) || 'pastel';
  if (typeof document !== 'undefined') {
    if (document.documentElement) document.documentElement.setAttribute('data-theme', t);
    if (document.body) document.body.setAttribute('data-theme', t);

    if (typeof spaceUniverseEngine !== 'undefined') {
      if (t === 'space') {
        spaceUniverseEngine.start();
      } else {
        spaceUniverseEngine.stop();
      }
    }
    if (typeof lavaUniverseEngine !== 'undefined') {
      if (t === 'lava') {
        lavaUniverseEngine.start();
      } else {
        lavaUniverseEngine.stop();
      }
    }
    if (typeof animeUniverseEngine !== 'undefined') {
      if (t === 'anime') {
        animeUniverseEngine.start();
      } else {
        animeUniverseEngine.stop();
      }
    }
    if (typeof skyUniverseEngine !== 'undefined') {
      if (t === 'sky') {
        skyUniverseEngine.start();
      } else {
        skyUniverseEngine.stop();
      }
    }
    if (typeof oceanUniverseEngine !== 'undefined') {
      if (t === 'ocean') {
        oceanUniverseEngine.start();
      } else {
        oceanUniverseEngine.stop();
      }
    }
    if (typeof sakuraUniverseEngine !== 'undefined') {
      if (t === 'sakura') {
        sakuraUniverseEngine.start();
      } else {
        sakuraUniverseEngine.stop();
      }
    }
    if (typeof fairyUniverseEngine !== 'undefined') {
      if (t === 'fairy') {
        fairyUniverseEngine.start();
      } else {
        fairyUniverseEngine.stop();
      }
    }
  }
}

function applyFontSize(fontSize) {
  const size = fontSize || (state.settings && state.settings.font_size) || 'normal';
  if (typeof document !== 'undefined') {
    if (document.documentElement && typeof document.documentElement.setAttribute === 'function') {
      document.documentElement.setAttribute('data-font-size', size);
    }
    if (document.body && typeof document.body.setAttribute === 'function') {
      document.body.setAttribute('data-font-size', size);
    }
  }
}

if (typeof window !== 'undefined') {
  window.applyFontSize = applyFontSize;
}

function initUI() {
  applyTheme();
  applyFontSize();
  document.getElementById('header-student-name').textContent = state.active_profile;
  const heroName = document.getElementById('hero-student-name');
  if (heroName) heroName.textContent = state.active_profile;
  
  updateHeaderExamPill();
  renderDashboard();
  renderParentHeatmap();
}

function updateHeaderExamPill() {
  const em = state.exam_metrics || {};
  const pill = document.getElementById('header-exam-pill');
  const badge = document.getElementById('header-readiness-badge');
  const daysLeft = em.days_left !== undefined ? em.days_left : 14;
  const examTitle = em.exam_name || em.title || 'Mid-Term';
  const pct = em.readiness_percent || 0;

  if (pill) pill.textContent = `${examTitle}: ${daysLeft}d left`;
  if (badge) {
    badge.textContent = `${pct}%`;
    badge.className = pct >= 80 ? 'bg-emerald-600 text-white text-[10px] px-1.5 py-0.5 rounded-md' : 'bg-indigo-600 text-white text-[10px] px-1.5 py-0.5 rounded-md';
  }

  const heroDue = document.getElementById('hero-due-count');
  if (heroDue) {
    let totalCards = 0;
    let mastered = 0;
    (state.decks || []).forEach(d => {
      (d.cards || []).forEach(c => {
        totalCards++;
        if ((c.ladder_stage || 1) >= 6) mastered++;
      });
    });
    heroDue.textContent = Math.max(1, totalCards - mastered);
  }

  const heroQuota = document.getElementById('hero-daily-quota');
  if (heroQuota) heroQuota.textContent = em.daily_quota || 3;
}

// =========================================================================
// 2. VIEW ROUTER (Dashboard, Chapter, Gameplay, Parent)
// =========================================================================

function showView(viewName, params = {}) {
  state.current_view = viewName;
  const views = ['dashboard', 'chapter', 'gameplay', 'parent'];
  
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) {
      if (v === viewName) {
        el.classList.remove('hidden');
      } else {
        el.classList.add('hidden');
      }
    }
  });

  if (typeof window.scrollTo === 'function') {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  if (viewName === 'dashboard') {
    renderDashboard();
  } else if (viewName === 'chapter') {
    renderChapterView(params);
  } else if (viewName === 'parent') {
    renderParentHeatmap();
  }
}

function switchRole(role) {
  state.role = role;
  const btnStudent = document.getElementById('role-btn-student');
  const btnParent = document.getElementById('role-btn-parent');

  if (role === 'student') {
    btnStudent.className = 'px-3 py-1 rounded-lg bg-white text-indigo-700 shadow-2xs transition';
    btnParent.className = 'px-3 py-1 rounded-lg text-slate-600 hover:text-slate-900 transition';
    showView('dashboard');
  } else {
    btnParent.className = 'px-3 py-1 rounded-lg bg-white text-indigo-700 shadow-2xs transition';
    btnStudent.className = 'px-3 py-1 rounded-lg text-slate-600 hover:text-slate-900 transition';
    showView('parent');
  }
}

// =========================================================================
// 3. DASHBOARD & CHAPTER CARDS (Hindi + Science)
// =========================================================================

function setSubjectFilter(subj) {
  state.subject_filter = subj;
  ['all', 'hindi', 'science'].forEach(s => {
    const btn = document.getElementById(`filter-subj-${s}`);
    if (btn) {
      if (s.toLowerCase() === subj.toLowerCase()) {
        btn.className = 'px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white shadow-xs transition';
      } else {
        btn.className = 'px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition';
      }
    }
  });
  renderDashboard();
}

function filterDashboardCards() {
  const query = document.getElementById('dashboard-search')?.value || '';
  state.search_query = query.toLowerCase().trim();
  renderDashboard();
}

function renderDashboard() {
  const container = document.getElementById('chapters-cards-grid');
  const countEl = document.getElementById('dashboard-chapters-count');
  if (!container) return;
  container.innerHTML = '';

  // Collect all chapter entities from decks
  let allChapters = [];

  (state.decks || []).forEach(deck => {
    const cards = deck.cards || [];
    const subj = deck.subject || 'General';

    // Group cards by lesson_name
    const chMap = {};
    cards.forEach(c => {
      const chName = (c.lesson_name || '').trim() || deck.title;
      if (!chMap[chName]) {
        chMap[chName] = [];
      }
      chMap[chName].push(c);
    });

    Object.entries(chMap).forEach(([chapterName, chCards]) => {
      const tot = chCards.length;
      const mastered = chCards.filter(c => (c.ladder_stage || 1) >= 6).length;
      
      // Calculate learning progress based on card ladder stages (Stage 1 = 0% -> Stage 2 = 20% -> ... -> Stage 6 = 100%)
      const stageProgSum = chCards.reduce((sum, c) => {
        const st = c.ladder_stage || 1;
        return sum + Math.min(100, Math.max(0, Math.round(((st - 1) / 5) * 100)));
      }, 0);
      const progPct = tot > 0 ? Math.round(stageProgSum / tot) : 0;

      const stages = chCards.map(c => c.ladder_stage || 1);
      const minStage = stages.length > 0 ? Math.min(...stages) : 1;
      const stageNames = { 1: 'Blanks', 2: 'Jigsaw', 3: 'Listening', 4: 'Voice', 5: 'Speed', 6: 'Written' };
      const currentStageName = stageNames[minStage] || 'Blanks';

      const nextMode = minStage === 1 ? 'blanks' : (minStage === 2 ? 'jigsaw' : (minStage === 3 ? 'listening' : (minStage === 4 ? 'voice' : (minStage === 5 ? 'speed' : 'writing'))));
      const nextModeIcon = minStage === 1 ? '🧩' : (minStage === 2 ? '🔀' : (minStage === 3 ? '🎧' : (minStage === 4 ? '🎙️' : (minStage === 5 ? '⚡' : '✍️'))));

      allChapters.push({
        deck_id: deck.id,
        deck_title: deck.title,
        subject: subj,
        chapter_name: chapterName,
        cards: chCards,
        total_cards: tot,
        mastered_cards: mastered,
        readiness_pct: progPct,
        progress_pct: progPct,
        current_stage_num: minStage,
        current_stage_name: currentStageName,
        next_mode: nextMode,
        next_mode_icon: nextModeIcon
      });
    });
  });

  // Filter by subject
  if (state.subject_filter !== 'All') {
    allChapters = allChapters.filter(c => 
      c.subject.toLowerCase() === state.subject_filter.toLowerCase()
    );
  }

  // Filter by search query
  if (state.search_query) {
    allChapters = allChapters.filter(c => 
      c.chapter_name.toLowerCase().includes(state.search_query) ||
      c.deck_title.toLowerCase().includes(state.search_query) ||
      c.subject.toLowerCase().includes(state.search_query)
    );
  }

  if (countEl) {
    countEl.textContent = `${allChapters.length} Lessons Available`;
  }

  if (allChapters.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-12 text-center bg-white border border-slate-200 rounded-3xl p-8 shadow-xs">
        <div class="text-4xl mb-2">📚</div>
        <h4 class="text-base font-bold text-slate-800">No Lessons Found</h4>
        <p class="text-xs text-slate-500 mt-1">Try clearing your search or switch to Parent Portal to add new lessons.</p>
      </div>
    `;
    return;
  }

  allChapters.forEach(ch => {
    const isHindi = ch.subject.toLowerCase() === 'hindi';
    const subjBadgeColor = isHindi 
      ? 'bg-amber-50 text-amber-800 border-amber-200' 
      : 'bg-emerald-50 text-emerald-800 border-emerald-200';

    const card = document.createElement('div');
    card.className = 'bg-white border border-slate-200 hover:border-indigo-300 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between space-y-4';

    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between gap-2 mb-2">
          <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${subjBadgeColor}">
            ${ch.subject}
          </span>
          <span class="text-[11px] font-bold text-slate-500">
            ${ch.total_cards} Questions
          </span>
        </div>
        <h4 class="text-base font-bold text-slate-900 leading-snug font-hindi">${ch.chapter_name}</h4>
        <p class="text-[11px] text-slate-400 mt-1 truncate">${ch.deck_title}</p>
      </div>

      <!-- Learning Progress Bar -->
      <div class="space-y-1.5">
        <div class="flex justify-between text-[11px] font-semibold text-slate-500">
          <span>Learning Progress</span>
          <span class="font-bold ${ch.progress_pct === 100 ? 'text-emerald-600' : 'text-indigo-600'}">${ch.progress_pct}%</span>
        </div>
        <div class="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all duration-300 ${ch.progress_pct === 100 ? 'bg-emerald-500' : 'bg-indigo-600'}" style="width: ${ch.progress_pct}%"></div>
        </div>
        <div class="flex justify-between items-center text-[10px] text-slate-400 pt-0.5">
          <span class="font-bold text-indigo-700 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-md">
            Stage ${ch.current_stage_num}: ${ch.current_stage_name}
          </span>
          <span class="font-medium text-slate-500">
            ${ch.mastered_cards}/${ch.total_cards} Mastered (Stage 6)
          </span>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-2 pt-1 border-t border-slate-100">
        <button onclick="openChapterDetails('${ch.deck_id}', '${escapeAttr(ch.chapter_name)}')" class="flex-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs py-2 rounded-xl transition">
          View Chapter
        </button>
        <button onclick="launchInBrowserGameplay('${ch.deck_id}', '${escapeAttr(ch.chapter_name)}', '${ch.next_mode}')" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-3.5 py-2 rounded-xl transition shadow-2xs flex items-center gap-1.5" title="Practice Next Active Stage">
          <span>${ch.next_mode_icon}</span> Practice (${ch.current_stage_name})
        </button>
      </div>
    `;

    container.appendChild(card);
  });
}

// =========================================================================
// 4. CHAPTER DETAILS VIEW
// =========================================================================

function openChapterDetails(deckId, chapterName) {
  const deck = (state.decks || []).find(d => d.id === deckId);
  if (!deck) return;

  const chCards = (deck.cards || []).filter(c => 
    (c.lesson_name || '').trim() === chapterName.trim() || (!c.lesson_name && chapterName === deck.title)
  );

  state.selected_chapter_data = {
    deck_id: deckId,
    deck_title: deck.title,
    chapter_name: chapterName,
    subject: deck.subject || 'General',
    cards: chCards
  };

  showView('chapter', state.selected_chapter_data);
}

function renderChapterView(data) {
  if (!data) return;
  
  document.getElementById('chapter-view-title').textContent = data.chapter_name;
  document.getElementById('chapter-subject-badge').textContent = data.subject;
  document.getElementById('chapter-view-desc').textContent = `${data.deck_title} • ${data.cards.length} Question items`;

  const total = data.cards.length;
  const mastered = data.cards.filter(c => (c.ladder_stage || 1) >= 6).length;
  
  const stageProgSum = data.cards.reduce((sum, c) => {
    const st = c.ladder_stage || 1;
    return sum + Math.min(100, Math.max(0, Math.round(((st - 1) / 5) * 100)));
  }, 0);
  const progPct = total > 0 ? Math.round(stageProgSum / total) : 0;

  const stages = data.cards.map(c => c.ladder_stage || 1);
  const minStage = stages.length > 0 ? Math.min(...stages) : 1;
  const stageNames = { 1: 'Blanks', 2: 'Jigsaw', 3: 'Listening', 4: 'Voice', 5: 'Speed', 6: 'Written' };
  const currentStageName = stageNames[minStage] || 'Blanks';

  document.getElementById('chapter-mastery-text').textContent = 
    `${progPct}% Learning Progress • Stage ${minStage} (${currentStageName}) • ${mastered}/${total} Mastered (Stage 6)`;
  document.getElementById('chapter-mastery-bar').style.width = `${progPct}%`;

  const list = document.getElementById('chapter-questions-list');
  list.innerHTML = '';

  data.cards.forEach((card, idx) => {
    const stage = card.ladder_stage || 1;
    const stageNames = { 1: 'Blanks', 2: 'Jigsaw', 3: 'Listening', 4: 'Voice', 5: 'Speed', 6: 'Written' };
    const stageIcons = { 1: '🧩', 2: '🔀', 3: '🎧', 4: '🎙️', 5: '⚡', 6: '✍️' };

    const history = card.stage_history || [];
    const timedAttempts = history.filter(h => h.duration_seconds != null && typeof h.duration_seconds === 'number');
    const cleanTimedAttempts = timedAttempts.filter(h => !h.hint_used && (!h.hints_used || h.hints_used === 0));
    let timingSnippet = '';
    if (timedAttempts.length > 0) {
      const lastAttempt = timedAttempts[timedAttempts.length - 1];
      const bestDur = cleanTimedAttempts.length > 0 ? Math.min(...cleanTimedAttempts.map(h => h.duration_seconds)) : null;
      let improveDelta = '';
      if (timedAttempts.length >= 2) {
        const prev = timedAttempts[timedAttempts.length - 2];
        const diff = Math.round((prev.duration_seconds - lastAttempt.duration_seconds) * 10) / 10;
        if (diff > 0) {
          improveDelta = `<span class="text-emerald-700 font-bold">⚡ Faster by ${diff}s</span>`;
        }
      }
      const bestBadge = bestDur != null 
        ? `<span class="bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded-lg">🏆 Best: <strong>${bestDur}s</strong></span>`
        : '';
      const lastHintTag = lastAttempt.hint_used ? ' <span class="text-[10px] text-amber-600 font-semibold">(💡 Hint)</span>' : '';
      timingSnippet = `
        <div class="flex flex-wrap items-center gap-2 pt-1 text-[11px] text-slate-500 font-mono">
          <span class="bg-slate-100 px-2 py-0.5 rounded-lg">⏱️ Last: <strong class="text-slate-700">${lastAttempt.duration_seconds}s</strong>${lastHintTag}</span>
          ${bestBadge}
          ${improveDelta}
        </div>
      `;
    }

    const item = document.createElement('div');
    item.className = 'bg-white border border-slate-200 rounded-2xl p-4 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4';

    item.innerHTML = `
      <div class="flex items-start gap-3 flex-1">
        <span class="w-7 h-7 rounded-xl bg-slate-100 text-slate-700 font-black text-xs flex items-center justify-center shrink-0 mt-0.5">
          ${idx + 1}
        </span>
        <div class="space-y-1">
          <h5 class="text-sm font-bold text-slate-900 font-hindi leading-snug">${card.question}</h5>
          ${card.meaning ? `<p class="text-[11px] text-slate-400 italic">${card.meaning}</p>` : ''}
          ${timingSnippet}
        </div>
      </div>

      <div class="flex items-center gap-2 shrink-0 self-end sm:self-center">
        <select onchange="changeCardStage('${escapeAttr(data.deck_id)}', '${escapeAttr(card.card_id)}', this.value)" class="text-[11px] font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1.5 rounded-xl border border-slate-200 cursor-pointer focus:ring-2 focus:ring-indigo-500 focus:outline-none transition shadow-2xs" title="Change or reset learning stage for this question">
          <option value="1" ${stage === 1 ? 'selected' : ''}>🧩 Stage 1: Blanks</option>
          <option value="2" ${stage === 2 ? 'selected' : ''}>🔀 Stage 2: Jigsaw</option>
          <option value="3" ${stage === 3 ? 'selected' : ''}>🎧 Stage 3: Listening</option>
          <option value="4" ${stage === 4 ? 'selected' : ''}>🎙️ Stage 4: Voice</option>
          <option value="5" ${stage === 5 ? 'selected' : ''}>⏱️ Stage 5: Speed</option>
          <option value="6" ${stage === 6 ? 'selected' : ''}>✍️ Stage 6: Writing</option>
        </select>
        <button onclick="playCardAudioDirect('${escapeAttr(card.question)}', '${data.subject}')" class="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition" title="Speak Question (Ctrl+L)">
          🔊 Q
        </button>
        <button onclick="playCardAudioDirect('${escapeAttr((card.chunks || []).join(' '))}', '${data.subject}')" class="p-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-xl text-xs font-bold transition shadow-2xs" title="Speak Answer (Ctrl+A)">
          🔊 Ans
        </button>
        <button onclick="openTimingHistoryModal('${escapeAttr(data.deck_id)}', '${escapeAttr(card.card_id)}')" class="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition" title="View Practice & Speed History">
          ⏱️ History
        </button>
        <button onclick="openCardEditorModal('${escapeAttr(data.deck_id)}', '${escapeAttr(card.card_id)}')" class="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition" title="Edit Question, Chunks & Meaning">
          ✏️ Edit
        </button>
        <button onclick="launchSingleCardGameplay('${data.deck_id}', '${card.card_id}')" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-3.5 py-2 rounded-xl transition shadow-2xs">
          Practice
        </button>
      </div>
    `;

    list.appendChild(item);
  });
}

function openTimingHistoryModal(deckId, cardId) {
  let card = null;
  if (state.decks) {
    const deck = state.decks.find(d => d.id === deckId);
    if (deck) {
      card = (deck.cards || []).find(c => c.card_id === cardId);
    }
  }
  if (!card && state.selected_chapter_data) {
    card = (state.selected_chapter_data.cards || []).find(c => c.card_id === cardId);
  }
  if (!card && state.gameplay && state.gameplay.current_card && state.gameplay.current_card.card_id === cardId) {
    card = state.gameplay.current_card;
  }
  if (!card) return;

  const modal = document.getElementById('timing-history-modal');
  if (!modal) return;
  modal._active_deck_id = deckId;
  modal._active_card_id = cardId;

  const qTitle = document.getElementById('timing-history-question-title');
  if (qTitle) qTitle.textContent = card.question || 'Question';

  const history = card.stage_history || [];
  const timedAttempts = history.filter(h => h.duration_seconds != null && typeof h.duration_seconds === 'number');
  const cleanTimedAttempts = timedAttempts.filter(h => !h.hint_used && (!h.hints_used || h.hints_used === 0));

  // Populate Summary Cards
  const summaryEl = document.getElementById('timing-history-summary');
  if (summaryEl) {
    if (timedAttempts.length > 0) {
      const bestDur = cleanTimedAttempts.length > 0 ? Math.min(...cleanTimedAttempts.map(h => h.duration_seconds)) : null;
      const lastDur = timedAttempts[timedAttempts.length - 1].duration_seconds;
      const totalSec = Math.round(timedAttempts.reduce((acc, h) => acc + h.duration_seconds, 0) * 10) / 10;
      summaryEl.innerHTML = `
        <div>
          <span class="block text-slate-400 font-bold uppercase tracking-wider text-[10px]">Attempts</span>
          <span class="text-base font-black text-slate-800">${history.length}</span>
        </div>
        <div>
          <span class="block text-slate-400 font-bold uppercase tracking-wider text-[10px]">Best Time</span>
          <span class="text-base font-black text-emerald-600">${bestDur != null ? `🏆 ${bestDur}s` : '--'}</span>
        </div>
        <div>
          <span class="block text-slate-400 font-bold uppercase tracking-wider text-[10px]">Latest Time</span>
          <span class="text-base font-black text-indigo-600">${lastDur}s</span>
        </div>
        <div>
          <span class="block text-slate-400 font-bold uppercase tracking-wider text-[10px]">Total Practice</span>
          <span class="text-base font-black text-slate-700">${totalSec}s</span>
        </div>
      `;
    } else {
      summaryEl.innerHTML = `
        <div class="py-1 text-slate-500 font-medium">
          No timed attempts recorded yet. Solve this question in the arena to record your time!
        </div>
      `;
    }
  }

  // Populate Attempt Timeline Table Body
  const tbody = document.getElementById('timing-history-tbody');
  if (tbody) {
    tbody.innerHTML = '';
    if (history.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="p-6 text-center text-slate-400">
            No practice attempts recorded yet for this sentence.
          </td>
        </tr>
      `;
    } else {
      const stageNames = { 1: 'Blanks', 2: 'Jigsaw', 3: 'Listening', 4: 'Voice', 5: 'Speed', 6: 'Written' };
      history.forEach((h, idx) => {
        const stageNum = h.stage || 1;
        const dur = (h.duration_seconds != null && typeof h.duration_seconds === 'number') ? `${h.duration_seconds}s` : '--';
        const isHint = Boolean(h.hint_used || (h.hints_used && h.hints_used > 0));
        
        let deltaHtml = '';
        if (h.duration_seconds != null) {
          const prevSameStage = history.slice(0, idx).filter(prev => prev.stage === stageNum && prev.duration_seconds != null);
          if (prevSameStage.length > 0) {
            const lastSame = prevSameStage[prevSameStage.length - 1];
            const diff = Math.round((lastSame.duration_seconds - h.duration_seconds) * 10) / 10;
            if (diff > 0) {
              deltaHtml = ` <span class="text-[10px] text-emerald-600 font-bold">(-${diff}s ⚡)</span>`;
            } else if (diff < 0) {
              deltaHtml = ` <span class="text-[10px] text-amber-600 font-medium">(+${Math.abs(diff)}s)</span>`;
            }
          }
        }

        const dateStr = h.timestamp ? new Date(h.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Recent';
        let statusBadge = h.passed ? '<span class="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md font-bold text-[10px]">Passed</span>' : '<span class="text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md font-bold text-[10px]">Reviewed</span>';
        if (isHint) {
          statusBadge += ' <span class="text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded text-[10px] font-semibold">💡 Hint</span>';
        }
        
        const row = document.createElement('tr');
        row.className = 'hover:bg-slate-50/60 transition';
        row.innerHTML = `
          <td class="p-2.5 px-3 text-slate-400 text-[11px] font-mono">${idx + 1}</td>
          <td class="p-2.5 px-3 font-semibold text-slate-800">
            <span class="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-md text-[10px] font-bold">Stage ${stageNum} (${stageNames[stageNum] || 'Stage'})</span>
          </td>
          <td class="p-2.5 px-3 font-mono font-bold text-slate-700">
            ${dur}${deltaHtml}
          </td>
          <td class="p-2.5 px-3">${statusBadge}</td>
          <td class="p-2.5 px-3 text-slate-400 text-[11px]">${dateStr}</td>
        `;
        tbody.appendChild(row);
      });
    }
  }

  modal.classList.remove('hidden');
}

function closeTimingHistoryModal() {
  const modal = document.getElementById('timing-history-modal');
  if (modal) modal.classList.add('hidden');
}

async function resetCurrentCardFromHistoryModal() {
  const modal = document.getElementById('timing-history-modal');
  if (!modal || !modal._active_deck_id || !modal._active_card_id) return;
  await changeCardStage(modal._active_deck_id, modal._active_card_id, 1, false);
  closeTimingHistoryModal();
}

async function changeCardStage(deckId, cardId, targetStage, clearHistory = false) {
  const stageNum = parseInt(targetStage, 10) || 1;

  // 1. Update in-memory state
  if (state.decks) {
    state.decks.forEach(d => {
      if (d.id === deckId) {
        (d.cards || []).forEach(c => {
          if (c.card_id === cardId) {
            c.ladder_stage = stageNum;
            if (clearHistory) c.stage_history = [];
          }
        });
      }
    });
  }
  if (state.selected_chapter_data && state.selected_chapter_data.cards) {
    state.selected_chapter_data.cards.forEach(c => {
      if (c.card_id === cardId) {
        c.ladder_stage = stageNum;
        if (clearHistory) c.stage_history = [];
      }
    });
  }

  // 2. Call backend bridge if available
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.reset_card_stage === 'function') {
    try {
      await window.pywebview.api.reset_card_stage(deckId, cardId, stageNum, clearHistory);
    } catch (err) {
      console.warn("Could not sync card stage reset with backend:", err);
    }
  }

  // 3. Re-render Chapter View & Dashboard to reflect updated mastery
  if (state.selected_chapter_data) {
    renderChapterView(state.selected_chapter_data);
  }
  renderDashboard();
  renderParentHeatmap();
}

function openResetChapterStageModal() {
  if (!state.selected_chapter_data) return;
  const modal = document.getElementById('chapter-reset-modal');
  if (!modal) return;
  const targetSelect = document.getElementById('chapter-reset-target-stage-select');
  if (targetSelect) targetSelect.value = '1';
  const clearChk = document.getElementById('chapter-reset-clear-history-chk');
  if (clearChk) clearChk.checked = false;
  modal.classList.remove('hidden');
}

function closeResetChapterStageModal() {
  const modal = document.getElementById('chapter-reset-modal');
  if (modal) modal.classList.add('hidden');
}

async function confirmResetChapterStages() {
  if (!state.selected_chapter_data) return;
  const deckId = state.selected_chapter_data.deck_id;
  const chapterName = state.selected_chapter_data.chapter_name;
  const targetSelect = document.getElementById('chapter-reset-target-stage-select');
  const targetStage = parseInt(targetSelect ? targetSelect.value : '1', 10) || 1;
  const clearChk = document.getElementById('chapter-reset-clear-history-chk');
  const clearHistory = clearChk ? clearChk.checked : false;

  closeResetChapterStageModal();

  // 1. Update in-memory state
  if (state.decks) {
    state.decks.forEach(d => {
      if (d.id === deckId) {
        (d.cards || []).forEach(c => {
          const match = (chapterName === 'All') ||
            ((c.lesson_name || '').trim() === chapterName.trim()) ||
            (!c.lesson_name && chapterName.trim() === (d.title || '').trim());
          if (match) {
            c.ladder_stage = targetStage;
            if (clearHistory) c.stage_history = [];
          }
        });
      }
    });
  }
  if (state.selected_chapter_data && state.selected_chapter_data.cards) {
    state.selected_chapter_data.cards.forEach(c => {
      c.ladder_stage = targetStage;
      if (clearHistory) c.stage_history = [];
    });
  }

  // 2. Call backend bridge
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.reset_chapter_stages === 'function') {
    try {
      await window.pywebview.api.reset_chapter_stages(deckId, chapterName, targetStage, clearHistory);
    } catch (err) {
      console.warn("Could not sync chapter reset with backend:", err);
    }
  }

  // 3. Re-render UI
  renderChapterView(state.selected_chapter_data);
  renderDashboard();
  renderParentHeatmap();
  const stageNames = { 1: 'Blanks', 2: 'Jigsaw', 3: 'Listening', 4: 'Voice', 5: 'Speed', 6: 'Written' };
  alert(`Chapter progress reset to Stage ${targetStage} (${stageNames[targetStage] || 'Selected Stage'}). You can now retry this chapter!`);
}

// -------------------------------------------------------------------------
// Card / Question Editor Modal Logic
// -------------------------------------------------------------------------

let activeCardEditorData = null;

function parseAnswerIntoChunks(text) {
  if (!text) return [];
  if (text.includes('|')) {
    return text.split('|').map(s => s.trim()).filter(s => s.length > 0);
  }
  // If no pipe is present, split into 3-word chunks as default
  const words = text.trim().split(/\s+/).filter(w => w.length > 0);
  if (words.length <= 1) return words;
  const chunks = [];
  for (let i = 0; i < words.length; i += 3) {
    chunks.push(words.slice(i, i + 3).join(' '));
  }
  return chunks;
}

function openCardEditorModal(deckId, cardId) {
  let card = null;
  let targetDeck = null;
  if (state.decks) {
    targetDeck = state.decks.find(d => d.id === deckId);
    if (targetDeck) {
      card = (targetDeck.cards || []).find(c => c.card_id === cardId);
    }
  }
  if (!card && state.selected_chapter_data) {
    card = (state.selected_chapter_data.cards || []).find(c => c.card_id === cardId);
  }
  if (!card && state.gameplay && state.gameplay.current_card && state.gameplay.current_card.card_id === cardId) {
    card = state.gameplay.current_card;
  }
  if (!card) {
    alert("Could not locate the requested card for editing.");
    return;
  }

  const modal = document.getElementById('card-editor-modal');
  if (!modal) return;

  activeCardEditorData = {
    deck_id: deckId || (targetDeck ? targetDeck.id : (state.selected_chapter_data ? state.selected_chapter_data.deck_id : null)),
    card_id: cardId,
    card: card
  };

  // Populate fields
  const chapInput = document.getElementById('edit-card-chapter-input');
  const qInput = document.getElementById('edit-card-question-input');
  const ansInput = document.getElementById('edit-card-answer-input');
  const meanInput = document.getElementById('edit-card-meaning-input');
  const subTitle = document.getElementById('card-editor-subtitle');

  if (chapInput) chapInput.value = card.lesson_name || (state.selected_chapter_data ? state.selected_chapter_data.chapter_name : '');
  if (qInput) qInput.value = card.question || '';
  if (meanInput) meanInput.value = card.meaning || '';
  if (subTitle) subTitle.textContent = `Card ID: ${cardId} • Deck: ${activeCardEditorData.deck_id || 'Current'}`;

  const chunks = card.chunks && card.chunks.length > 0 ? card.chunks : [card.sentence || card.answer || ''];
  if (ansInput) {
    ansInput.value = chunks.join(' | ');
  }

  renderCardEditorChipsPreview(chunks);
  modal.classList.remove('hidden');
}

function closeCardEditorModal() {
  const modal = document.getElementById('card-editor-modal');
  if (modal) modal.classList.add('hidden');
  activeCardEditorData = null;
}

function renderCardEditorChipsPreview(chunks) {
  const container = document.getElementById('edit-card-chips-preview');
  const countEl = document.getElementById('edit-card-chunks-count');
  if (countEl) {
    countEl.textContent = `${chunks.length} ${chunks.length === 1 ? 'block' : 'blocks'}`;
  }
  if (!container) return;
  container.innerHTML = '';

  if (chunks.length === 0) {
    container.innerHTML = '<span class="text-xs text-slate-400 italic">No answer text entered.</span>';
    return;
  }

  chunks.forEach((chunk, cIdx) => {
    const chip = document.createElement('div');
    chip.className = 'inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-indigo-200 text-indigo-950 rounded-xl text-xs font-hindi font-bold shadow-2xs group transition';
    
    const wordsCount = chunk.trim().split(/\s+/).filter(w => w.length > 0).length;
    let actionsHtml = '';
    if (wordsCount > 1) {
      actionsHtml += `<button type="button" onclick="cardEditorSplitChunk(${cIdx})" class="text-[11px] text-slate-400 hover:text-indigo-600 transition px-0.5" title="Split into individual words">✂️</button>`;
    }
    if (cIdx < chunks.length - 1) {
      actionsHtml += `<button type="button" onclick="cardEditorMergeChunk(${cIdx})" class="text-[11px] text-slate-400 hover:text-indigo-600 transition px-0.5" title="Merge with next phrase">🔗</button>`;
    }

    chip.innerHTML = `
      <span class="chunk-text select-none">${chunk}</span>
      <div class="flex items-center gap-1">${actionsHtml}</div>
    `;
    container.appendChild(chip);
  });
}

function onCardEditorAnswerInput() {
  const ansInput = document.getElementById('edit-card-answer-input');
  if (!ansInput) return;
  const chunks = parseAnswerIntoChunks(ansInput.value);
  renderCardEditorChipsPreview(chunks);
}

function cardEditorAutoGroupWords(n) {
  const ansInput = document.getElementById('edit-card-answer-input');
  if (!ansInput) return;
  const currentText = ansInput.value.replace(/\|/g, ' ').replace(/\s+/g, ' ').trim();
  if (!currentText) return;

  const words = currentText.split(/\s+/);
  const chunks = [];
  for (let i = 0; i < words.length; i += n) {
    chunks.push(words.slice(i, i + n).join(' '));
  }
  ansInput.value = chunks.join(' | ');
  renderCardEditorChipsPreview(chunks);
}

function cardEditorSplitChunk(cIdx) {
  const ansInput = document.getElementById('edit-card-answer-input');
  if (!ansInput) return;
  const chunks = parseAnswerIntoChunks(ansInput.value);
  if (!chunks[cIdx]) return;

  const words = chunks[cIdx].split(/\s+/).filter(w => w.length > 0);
  if (words.length > 1) {
    chunks.splice(cIdx, 1, ...words);
    ansInput.value = chunks.join(' | ');
    renderCardEditorChipsPreview(chunks);
  }
}

function cardEditorMergeChunk(cIdx) {
  const ansInput = document.getElementById('edit-card-answer-input');
  if (!ansInput) return;
  const chunks = parseAnswerIntoChunks(ansInput.value);
  if (cIdx >= chunks.length - 1) return;

  const merged = chunks[cIdx] + ' ' + chunks[cIdx + 1];
  chunks.splice(cIdx, 2, merged);
  ansInput.value = chunks.join(' | ');
  renderCardEditorChipsPreview(chunks);
}

async function cardEditorAutoTranslate() {
  const qInput = document.getElementById('edit-card-question-input');
  const meanInput = document.getElementById('edit-card-meaning-input');
  const btn = document.getElementById('edit-card-translate-btn');
  if (!qInput || !meanInput) return;

  const textToTranslate = qInput.value.trim();
  if (!textToTranslate) {
    alert("Please enter a question prompt first to translate.");
    return;
  }

  const origBtnText = btn ? btn.innerHTML : '';
  if (btn) btn.innerHTML = '<span>⏳</span> Translating...';

  try {
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_chunk_translations === 'function') {
      const res = await window.pywebview.api.get_chunk_translations([textToTranslate]);
      if (res && res[textToTranslate]) {
        meanInput.value = res[textToTranslate];
      } else if (res && Object.values(res)[0]) {
        meanInput.value = Object.values(res)[0];
      }
    }
  } catch (err) {
    console.warn("Auto-translation error:", err);
  } finally {
    if (btn) btn.innerHTML = origBtnText;
  }
}

function testCardEditorAudio(target) {
  const qInput = document.getElementById('edit-card-question-input');
  const ansInput = document.getElementById('edit-card-answer-input');
  let text = '';
  if (target === 'question' && qInput) {
    text = qInput.value.trim();
  } else if (target === 'answer' && ansInput) {
    text = ansInput.value.replace(/\|/g, ' ').replace(/\s+/g, ' ').trim();
  }
  if (!text) {
    alert("Please enter text first to test audio.");
    return;
  }
  const isHindi = /[\u0900-\u097F]/.test(text);
  playCardAudioDirect(text, isHindi ? 'Hindi' : 'English');
}

async function saveCardEditorChanges() {
  if (!activeCardEditorData) return;
  const { deck_id, card_id, card } = activeCardEditorData;

  const chapInput = document.getElementById('edit-card-chapter-input');
  const qInput = document.getElementById('edit-card-question-input');
  const ansInput = document.getElementById('edit-card-answer-input');
  const meanInput = document.getElementById('edit-card-meaning-input');

  const question = qInput ? qInput.value.trim() : '';
  const answerText = ansInput ? ansInput.value.trim() : '';
  const meaning = meanInput ? meanInput.value.trim() : '';
  const lessonName = chapInput ? chapInput.value.trim() : '';

  if (!question) {
    alert("Question prompt cannot be empty.");
    return;
  }
  if (!answerText) {
    alert("Sentence answer cannot be empty.");
    return;
  }

  const chunks = parseAnswerIntoChunks(answerText);
  if (chunks.length === 0) {
    alert("At least one sentence block must be defined.");
    return;
  }

  // 1. Update in-memory state
  card.question = question;
  card.chunks = chunks;
  card.meaning = meaning;
  if (lessonName) card.lesson_name = lessonName;

  if (state.decks) {
    state.decks.forEach(d => {
      if (d.id === deck_id) {
        (d.cards || []).forEach(c => {
          if (c.card_id === card_id) {
            c.question = question;
            c.chunks = chunks;
            c.meaning = meaning;
            if (lessonName) c.lesson_name = lessonName;
          }
        });
      }
    });
  }

  if (state.selected_chapter_data && state.selected_chapter_data.cards) {
    state.selected_chapter_data.cards.forEach(c => {
      if (c.card_id === card_id) {
        c.question = question;
        c.chunks = chunks;
        c.meaning = meaning;
        if (lessonName) c.lesson_name = lessonName;
      }
    });
  }

  // 2. Persist to backend bridge
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.update_card === 'function') {
    try {
      await window.pywebview.api.update_card(deck_id, card_id, question, chunks, meaning, lessonName);
    } catch (err) {
      console.warn("Could not save card edits to backend:", err);
    }
  }

  // 3. Re-render UI
  closeCardEditorModal();
  if (state.selected_chapter_data) {
    renderChapterView(state.selected_chapter_data);
  }
  renderDashboard();
  playSound('success');
}

async function deleteCardFromEditor() {
  if (!activeCardEditorData) return;
  const { deck_id, card_id, card } = activeCardEditorData;

  const confirmMsg = `Are you sure you want to delete this question?\n\n"${card.question || card_id}"\n\nThis action cannot be undone.`;
  if (typeof confirm !== 'undefined' && !confirm(confirmMsg)) {
    return;
  }

  // 1. Remove from in-memory state
  if (state.decks) {
    state.decks.forEach(d => {
      if (d.id === deck_id && d.cards) {
        d.cards = d.cards.filter(c => c.card_id !== card_id);
      }
    });
  }

  if (state.selected_chapter_data && state.selected_chapter_data.cards) {
    state.selected_chapter_data.cards = state.selected_chapter_data.cards.filter(c => c.card_id !== card_id);
  }

  // 2. Call backend bridge
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.delete_card === 'function') {
    try {
      await window.pywebview.api.delete_card(deck_id, card_id);
    } catch (err) {
      console.warn("Could not delete card from backend:", err);
    }
  }

  closeCardEditorModal();
  if (state.selected_chapter_data) {
    renderChapterView(state.selected_chapter_data);
  }
  renderDashboard();
  playSound('click');
}

if (typeof window !== 'undefined') {
  window.openTimingHistoryModal = openTimingHistoryModal;
  window.closeTimingHistoryModal = closeTimingHistoryModal;
  window.resetCurrentCardFromHistoryModal = resetCurrentCardFromHistoryModal;
  window.changeCardStage = changeCardStage;
  window.openResetChapterStageModal = openResetChapterStageModal;
  window.closeResetChapterStageModal = closeResetChapterStageModal;
  window.confirmResetChapterStages = confirmResetChapterStages;
  window.openCardEditorModal = openCardEditorModal;
  window.closeCardEditorModal = closeCardEditorModal;
  window.onCardEditorAnswerInput = onCardEditorAnswerInput;
  window.cardEditorAutoGroupWords = cardEditorAutoGroupWords;
  window.cardEditorSplitChunk = cardEditorSplitChunk;
  window.cardEditorMergeChunk = cardEditorMergeChunk;
  window.cardEditorAutoTranslate = cardEditorAutoTranslate;
  window.testCardEditorAudio = testCardEditorAudio;
  window.saveCardEditorChanges = saveCardEditorChanges;
  window.deleteCardFromEditor = deleteCardFromEditor;
}

function startChapterPractice(modeName) {
  if (!state.selected_chapter_data) return;
  launchInBrowserGameplay(
    state.selected_chapter_data.deck_id,
    state.selected_chapter_data.chapter_name,
    modeName
  );
}

// =========================================================================
// 5. IN-BROWSER INTERACTIVE GAME ARENA (Adaptive Blanks & Jigsaw)
// =========================================================================

async function startDailyMission() {
  let cards = [];
  if (window.pywebview) {
    cards = await window.pywebview.api.get_active_session_cards(null, null, null, 'guided_mission');
  }
  if (!cards || cards.length === 0) {
    // Fallback: pick first available deck cards
    if (state.decks && state.decks[0]) {
      cards = state.decks[0].cards || [];
    }
  }
  if (!cards || cards.length === 0) {
    alert("No cards due for practice today! Great job!");
    return;
  }
  setupGameSession(cards, 'blanks', 'Daily Guided Mission');
}

async function startExamPrepSession() {
  let cards = [];
  const em = state.exam_metrics || {};
  if (window.pywebview) {
    cards = await window.pywebview.api.get_active_session_cards(null, null, em.id, 'guided_mission');
  }
  if (!cards || cards.length === 0) {
    alert("No cards configured in the current exam scope.");
    return;
  }
  setupGameSession(cards, 'blanks', `${em.exam_name || 'Exam'} Prep`);
}

async function launchInBrowserGameplay(deckId, chapterName, modeName = 'blanks') {
  let cards = [];
  if (window.pywebview) {
    cards = await window.pywebview.api.get_active_session_cards(deckId, chapterName, null, modeName);
  }
  if (!cards || cards.length === 0) {
    const deck = (state.decks || []).find(d => d.id === deckId);
    if (deck) {
      cards = (deck.cards || []).filter(c => 
        (c.lesson_name || '').trim() === chapterName.trim() || (!c.lesson_name && chapterName === deck.title)
      );
    }
  }

  if (!cards || cards.length === 0) {
    alert("No cards available in this chapter.");
    return;
  }

  cards.forEach(c => {
    if (!c.deck_id) c.deck_id = deckId;
  });

  setupGameSession(cards, modeName, chapterName, deckId);
}

function getStageForMode(modeName) {
  switch (modeName) {
    case 'blanks': return 1;
    case 'jigsaw': return 2;
    case 'listening': return 3;
    case 'voice': return 4;
    case 'speed': return 5;
    case 'writing': return 6;
    default: return 1;
  }
}

function launchSingleCardGameplay(deckId, cardId) {
  const deck = (state.decks || []).find(d => d.id === deckId);
  if (!deck) return;
  const card = (deck.cards || []).find(c => c.card_id === cardId);
  if (!card) return;
  card.deck_id = deckId;

  setupGameSession([card], 'guided_mission', card.lesson_name || deck.title, deckId);
}

function jumbleCards(cards) {
  if (!cards || cards.length <= 1) return (cards || []).slice();
  const shuffled = cards.slice();
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  // Guarantee not identical if cards have distinct IDs and length >= 2
  const isIdentical = shuffled.every((c, idx) => (c.card_id || idx) === (cards[idx].card_id || idx));
  if (isIdentical && shuffled.length >= 2) {
    [shuffled[0], shuffled[1]] = [shuffled[1], shuffled[0]];
  }
  return shuffled;
}

function setupGameSession(cards, modeName, chapterTitle, deckId = null) {
  // Fill-in-the-blanks mode preserves original sequential story/chapter order.
  // All other modes (Jigsaw, Listening, Voice, Speed, Writing, etc.) jumble question order.
  const sessionCards = (modeName === 'blanks') ? cards.slice() : jumbleCards(cards);

  sessionCards.forEach(c => {
    delete c._attempt_stage;
    if (!c.deck_id && deckId) c.deck_id = deckId;
  });

  state.gameplay = {
    active: true,
    deck_id: deckId || (sessionCards[0] ? sessionCards[0].deck_id : null),
    mode: modeName,
    cards: sessionCards,
    card_index: 0,
    current_card: sessionCards[0],
    chapter_title: chapterTitle,
    pass_number: 1,
    max_passes: modeName === 'blanks' ? 3 : 1,
    pass_blank_indices: [],
    filled_slots: {},
    active_slot_idx: null,
    placed_chunks: [],
    available_chips: [],
    streak: 0,
    flawless: true,
    timer_interval: null,
    timer_start_ms: null,
    timer_elapsed_seconds: 0
  };

  showView('gameplay');
  loadGameplayCard();
}

async function exitGameplay() {
  stopQuestionTimer();
  state.gameplay.active = false;
  // Reload fresh state from backend to sync disk persistence
  await reloadAppState();

  if (state.selected_chapter_data) {
    // Refresh chapter cards from newly reloaded state.decks
    const deck = (state.decks || []).find(d => d.id === state.selected_chapter_data.deck_id);
    if (deck) {
      state.selected_chapter_data.cards = (deck.cards || []).filter(c => 
        (c.lesson_name || '').trim() === state.selected_chapter_data.chapter_name.trim() ||
        (!c.lesson_name && state.selected_chapter_data.chapter_name === deck.title)
      );
    }
    showView('chapter', state.selected_chapter_data);
  } else {
    showView('dashboard');
  }
  renderDashboard();
  renderParentHeatmap();
  updateHeaderExamPill();
}

// =========================================================================
// HOVER MEANING / TRANSLATION TOOLTIP SUBSYSTEM
// =========================================================================

function showChunkTooltip(e, text, actionHint = null) {
  if (!text || !text.trim()) return;
  if (state.settings && state.settings.show_hover_meanings === false) return;

  const tooltip = document.getElementById('chunk-hover-tooltip');
  const tooltipText = document.getElementById('chunk-hover-tooltip-text');
  if (!tooltip || !tooltipText) return;

  const clean = text.trim();
  let meaning = state.chunk_translations[clean] || state.chunk_translations[clean.toLowerCase()];

  if (!meaning && window.pywebview && window.pywebview.api && window.pywebview.api.get_chunk_translation) {
    window.pywebview.api.get_chunk_translation(clean).then(res => {
      if (res) {
        state.chunk_translations[clean] = res;
        if (tooltip.dataset && tooltip.dataset.activeChunk === clean) {
          tooltipText.textContent = actionHint ? `${res} • [${actionHint}]` : res;
        }
      }
    }).catch(() => {});
  }

  if (!meaning) {
    if (state.gameplay && state.gameplay.current_card && state.gameplay.current_card.meaning) {
      meaning = state.gameplay.current_card.meaning;
    } else {
      meaning = `"${clean}"`;
    }
  }

  if (tooltip.dataset) tooltip.dataset.activeChunk = clean;
  tooltipText.textContent = actionHint ? `${meaning} • [${actionHint}]` : meaning;

  positionTooltip(tooltip, e);

  tooltip.classList.remove('hidden');
  if (typeof requestAnimationFrame === 'function') {
    requestAnimationFrame(() => {
      tooltip.classList.remove('opacity-0');
      tooltip.classList.add('opacity-100');
    });
  } else {
    tooltip.classList.remove('opacity-0');
    tooltip.classList.add('opacity-100');
  }
}

function positionTooltip(tooltip, e) {
  if (!tooltip) return;
  const target = (e && (e.currentTarget || e.target)) || null;
  let posX = (e && e.clientX !== undefined) ? e.clientX : 200;
  let posY = (e && e.clientY !== undefined) ? e.clientY : 200;

  if (target && typeof target.getBoundingClientRect === 'function') {
    const rect = target.getBoundingClientRect();
    posX = rect.left + rect.width / 2;
    posY = rect.top - 8;
  } else {
    posY -= 14;
  }

  if (typeof window !== 'undefined') {
    const winWidth = window.innerWidth || 1024;
    posX = Math.max(100, Math.min(winWidth - 100, posX));
    posY = Math.max(40, posY);
  }

  tooltip.style.left = `${posX}px`;
  tooltip.style.top = `${posY}px`;
}

function hideChunkTooltip() {
  const tooltip = document.getElementById('chunk-hover-tooltip');
  if (!tooltip) return;
  if (tooltip.dataset) tooltip.dataset.activeChunk = '';
  tooltip.classList.remove('opacity-100');
  tooltip.classList.add('opacity-0');
  setTimeout(() => {
    if (tooltip && tooltip.classList && tooltip.classList.contains('opacity-0')) {
      tooltip.classList.add('hidden');
    }
  }, 150);
}

function attachChunkHoverTooltip(element, text, actionHint = null) {
  if (!element || !text) return;
  const clean = text.trim();

  const getMeaning = () => {
    return state.chunk_translations[clean] ||
           state.chunk_translations[clean.toLowerCase()] ||
           (state.gameplay && state.gameplay.current_card && state.gameplay.current_card.meaning ? state.gameplay.current_card.meaning : '');
  };

  const updateTitle = () => {
    const meaning = getMeaning();
    if (meaning) {
      element.title = actionHint ? `📖 ${meaning} (${actionHint})` : `📖 ${meaning}`;
    } else {
      element.title = actionHint ? `"${clean}" (${actionHint})` : `"${clean}"`;
    }
  };

  updateTitle();

  element.onmouseenter = (e) => {
    showChunkTooltip(e, clean, actionHint);
  };
  element.onmouseleave = () => {
    hideChunkTooltip();
  };
  element.onmousemove = (e) => {
    positionTooltip(document.getElementById('chunk-hover-tooltip'), e);
  };
}

async function prefetchChunkTranslations(card) {
  if (!card) return;
  const chunks = card.chunks || [];
  if (chunks.length === 0) return;

  if (card.meaning && chunks.length === 1) {
    state.chunk_translations[chunks[0].trim()] = card.meaning;
  }

  const missing = chunks.filter(c => c && !state.chunk_translations[c.trim()]);
  if (missing.length === 0) return;

  if (window.pywebview && window.pywebview.api && window.pywebview.api.get_chunk_translations) {
    try {
      const res = await window.pywebview.api.get_chunk_translations(missing);
      if (res && typeof res === 'object') {
        Object.assign(state.chunk_translations, res);
        updateAllVisibleChunkTooltips();
      }
    } catch (err) {
      console.warn("Error prefetching translations:", err);
    }
  }
}

function updateAllVisibleChunkTooltips() {
  const targets = typeof document !== 'undefined' && document.querySelectorAll ? document.querySelectorAll('.chunk-tooltip-target') : [];
  targets.forEach(el => {
    const rawText = (el.dataset && el.dataset.chunkText) || el.textContent || '';
    if (rawText) {
      const clean = rawText.trim();
      const meaning = state.chunk_translations[clean] || state.chunk_translations[clean.toLowerCase()];
      if (meaning) {
        el.title = `📖 ${meaning}`;
      }
    }
  });
}

function formatTimerDisplay(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds));
  const mins = Math.floor(s / 60);
  const secs = Math.floor(s % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function startQuestionTimer() {
  stopQuestionTimer();
  const g = state.gameplay;
  g.timer_start_ms = Date.now();
  g.timer_elapsed_seconds = 0;

  const display = document.getElementById('game-timer-display');
  if (display) display.textContent = '0:00';

  if (typeof setInterval !== 'undefined') {
    g.timer_interval = setInterval(() => {
      if (!g.timer_start_ms) return;
      const elapsed = (Date.now() - g.timer_start_ms) / 1000;
      g.timer_elapsed_seconds = Math.round(elapsed * 10) / 10;
      const dispEl = document.getElementById('game-timer-display');
      if (dispEl) {
        dispEl.textContent = formatTimerDisplay(elapsed);
      }
    }, 500);
  }
}

function stopQuestionTimer() {
  const g = state.gameplay;
  if (g.timer_interval) {
    if (typeof clearInterval !== 'undefined') {
      clearInterval(g.timer_interval);
    }
    g.timer_interval = null;
  }
  if (g.timer_start_ms) {
    const elapsed = (Date.now() - g.timer_start_ms) / 1000;
    g.timer_elapsed_seconds = Math.round(elapsed * 10) / 10;
    g.timer_start_ms = null;
  }
  return g.timer_elapsed_seconds || 0;
}

function loadGameplayCard() {
  try {
    const g = state.gameplay;
    const card = g.cards[g.card_index];
    if (!card) {
      exitGameplay();
      return;
    }
    g.current_card = card;

    // Reset attempt quality indicators
    g.flawless = true;
    g.hints_used = 0;
    g.hint_used = false;

    // Prefetch chunk definitions in background
    prefetchChunkTranslations(card);

    // Hide celebration card
    const celeb = document.getElementById('game-celebration-card');
    if (celeb) celeb.classList.add('hidden');

    const assembly = document.getElementById('game-assembly-board');
    if (assembly) assembly.classList.remove('border-emerald-500', 'bg-emerald-50/50');

    // Update counters
    const counter = document.getElementById('game-card-counter');
    if (counter) counter.textContent = `Question ${g.card_index + 1} of ${g.cards.length}`;
    const chapPill = document.getElementById('game-chapter-pill');
    if (chapPill) chapPill.textContent = g.chapter_title || card.lesson_name || 'Lesson';

    // Start question stopwatch timer
    startQuestionTimer();

    // Determine what stage is being attempted for this card
    let attemptStage = 1;
    if (g.mode === 'guided_mission') {
      attemptStage = card._attempt_stage || card.ladder_stage || 1;
    } else {
      attemptStage = getStageForMode(g.mode);
    }
    g.current_attempt_stage = attemptStage;
    card._attempt_stage = attemptStage;

    // Previous best attempt for this card at this attempted ladder stage (strictly unassisted/clean)
    const currStage = attemptStage;
    const history = card.stage_history || [];
    const stageAttempts = history.filter(h => h.stage === currStage && typeof h.duration_seconds === 'number' && !h.hint_used && (!h.hints_used || h.hints_used === 0));
    const bestPill = document.getElementById('game-previous-best-pill');
    const bestText = document.getElementById('game-previous-best-text');
    if (bestPill && bestText) {
      if (stageAttempts.length > 0) {
        const bestTime = Math.min(...stageAttempts.map(h => h.duration_seconds));
        bestText.textContent = `${bestTime}s`;
        bestPill.classList.remove('hidden');
      } else {
        bestPill.classList.add('hidden');
      }
    }

    // Determine effective mode based on attempt stage
    let effectiveMode = g.mode;
    if (effectiveMode === 'guided_mission') {
      const stage = attemptStage;
      if (stage === 1) effectiveMode = 'blanks';
      else if (stage === 2) effectiveMode = 'jigsaw';
      else if (stage === 3) effectiveMode = 'listening';
      else if (stage === 4) effectiveMode = 'voice';
      else if (stage === 5) effectiveMode = 'blanks';
      else if (stage === 6) effectiveMode = 'writing';
    }
    g.effective_mode = effectiveMode;

    const modeNames = {
      'blanks': 'Adaptive Fill-in-the-Blanks',
      'jigsaw': 'Jigsaw Scramble Puzzle',
      'listening': 'Listening Comprehension',
      'voice': 'Voice Mastery Studio',
      'writing': 'Active Writing Studio',
      'guided_mission': 'Guided Mission'
    };
    const modeIcons = {
      'blanks': '🧩',
      'jigsaw': '🔀',
      'listening': '🎧',
      'voice': '🎙️',
      'writing': '✍️',
      'guided_mission': '🚀'
    };

    const modePill = document.getElementById('game-mode-pill');
    if (modePill) {
      modePill.innerHTML = `<span>${modeIcons[effectiveMode] || '🧩'}</span> <span id="game-mode-name">${modeNames[effectiveMode] || 'Learning Puzzle'}</span>`;
    }

    // Question & Translation
    const qText = document.getElementById('game-question-text');
    if (qText) {
      qText.textContent = card.question;
      attachChunkHoverTooltip(qText, card.question, 'Question');
    }
    const meaningEl = document.getElementById('game-meaning-text');
    if (meaningEl) {
      meaningEl.textContent = card.meaning || 'No translation provided';
      meaningEl.classList.add('hidden');
    }
    const btnToggleMeaning = document.getElementById('btn-toggle-meaning');
    if (btnToggleMeaning) btnToggleMeaning.textContent = 'Show English Meaning';

    // Hide all studios by default
    const passBox = document.getElementById('game-pass-indicator-box');
    if (passBox) passBox.classList.add('hidden');
    const listenBox = document.getElementById('game-listening-box');
    if (listenBox) listenBox.classList.add('hidden');
    const voiceBox = document.getElementById('game-voice-box');
    if (voiceBox) voiceBox.classList.add('hidden');
    const writeBox = document.getElementById('game-writing-box');
    if (writeBox) writeBox.classList.add('hidden');
    const jigsawSizeBox = document.getElementById('jigsaw-block-size-container');
    if (jigsawSizeBox) jigsawSizeBox.classList.add('hidden');

    const assemblyContainer = assembly ? assembly.parentElement : null;
    const chipsTray = document.getElementById('game-chips-tray');
    const chipsContainer = chipsTray ? chipsTray.parentElement : null;
    const checkBtn = document.getElementById('game-check-btn');

    // Configure based on effective mode
    if (effectiveMode === 'blanks') {
      if (assemblyContainer) assemblyContainer.classList.remove('hidden');
      if (chipsContainer) chipsContainer.classList.remove('hidden');
      if (checkBtn) checkBtn.classList.remove('hidden');
      initAdaptiveBlanksCard();
    } else if (effectiveMode === 'jigsaw') {
      if (assemblyContainer) assemblyContainer.classList.remove('hidden');
      if (chipsContainer) chipsContainer.classList.remove('hidden');
      if (checkBtn) checkBtn.classList.remove('hidden');
      initJigsawCard();
    } else if (effectiveMode === 'listening') {
      if (listenBox) listenBox.classList.remove('hidden');
      if (assemblyContainer) assemblyContainer.classList.remove('hidden');
      if (chipsContainer) chipsContainer.classList.remove('hidden');
      if (checkBtn) checkBtn.classList.remove('hidden');
      initListeningCard();
    } else if (effectiveMode === 'voice') {
      if (voiceBox) voiceBox.classList.remove('hidden');
      if (assemblyContainer) assemblyContainer.classList.add('hidden');
      if (chipsContainer) chipsContainer.classList.add('hidden');
      if (checkBtn) checkBtn.classList.add('hidden');
      initVoiceCard();
    } else if (effectiveMode === 'writing') {
      if (writeBox) writeBox.classList.remove('hidden');
      if (assemblyContainer) assemblyContainer.classList.add('hidden');
      if (chipsContainer) chipsContainer.classList.add('hidden');
      if (checkBtn) checkBtn.classList.remove('hidden');
      initWritingCard();
    }
  } catch (err) {
    console.error("FATAL: Failed to load gameplay card:", err);
  }
}

// -------------------------------------------------------------------------
// Mode A: Adaptive Multi-Pass Fill-in-the-Blanks Engine
// -------------------------------------------------------------------------

function initAdaptiveBlanksCard() {
  const g = state.gameplay;
  const card = g.current_card;
  const chunks = card.chunks || [];
  const numChunks = chunks.length;

  const passBox = document.getElementById('game-pass-indicator-box');
  if (passBox) passBox.classList.remove('hidden');

  const boardLabel = document.getElementById('game-board-label');
  if (boardLabel) boardLabel.textContent = 'Sentence with blanks to fill:';

  const helperTip = document.getElementById('game-helper-tip');
  if (helperTip) helperTip.textContent = 'Click missing slots [ ? ], then select the matching candidate chip below.';

  updatePassIndicatorUI();

  // Select which indices are blanked for this pass
  // Pass 1: ~25-30% blanked (1 or 2 chunks)
  // Pass 2: ~50% blanked (different 2-3 chunks)
  // Pass 3: ~75% blanked (alternating / remaining chunks)
  let blanksCount = 1;
  let targetIndices = [];

  if (g.pass_number === 1) {
    blanksCount = Math.max(1, Math.floor(numChunks * 0.3));
    // Pick middle / key indices
    targetIndices = [1 % numChunks];
    if (blanksCount > 1 && numChunks > 3) targetIndices.push(Math.min(numChunks - 2, 3));
  } else if (g.pass_number === 2) {
    blanksCount = Math.max(1, Math.floor(numChunks * 0.5));
    // Pick different indices from pass 1
    targetIndices = [0];
    if (numChunks > 2) targetIndices.push(2);
    if (numChunks > 4 && blanksCount > 2) targetIndices.push(4);
  } else {
    // Pass 3: Maximum challenge
    targetIndices = [];
    for (let i = 0; i < numChunks; i++) {
      if (i % 2 !== 0 || i === numChunks - 1) {
        targetIndices.push(i);
      }
    }
    if (targetIndices.length === 0) targetIndices = [0];
  }

  g.pass_blank_indices = targetIndices;
  g.filled_slots = {};
  g.active_slot_idx = targetIndices[0];

  renderBlanksBoard();
  renderBlanksChips();
}

function updatePassIndicatorUI() {
  const g = state.gameplay;
  for (let i = 1; i <= 3; i++) {
    const dot = document.getElementById(`pass-dot-${i}`);
    if (dot) {
      if (i < g.pass_number) {
        dot.className = 'w-6 h-6 rounded-full bg-emerald-500 text-white font-bold flex items-center justify-center text-[10px]';
        dot.textContent = '✓';
      } else if (i === g.pass_number) {
        dot.className = 'w-6 h-6 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center text-[10px] ring-2 ring-indigo-200';
        dot.textContent = `${i}`;
      } else {
        dot.className = 'w-6 h-6 rounded-full bg-slate-200 text-slate-500 font-bold flex items-center justify-center text-[10px]';
        dot.textContent = `${i}`;
      }
    }
  }

  const desc = document.getElementById('game-pass-description');
  if (desc) {
    const messages = {
      1: 'Pass 1 of 3: Master early contextual recognition (gentle scaffolding)',
      2: 'Pass 2 of 3: Deeper retrieval with different words blanked',
      3: 'Pass 3 of 3: Challenge recall! Final mastery pass'
    };
    desc.textContent = messages[g.pass_number] || 'Adaptive Retrieval Pass';
  }
}

function renderBlanksBoard() {
  const g = state.gameplay;
  const board = document.getElementById('game-assembly-board');
  if (!board) return;
  board.innerHTML = '';

  const chunks = (g.current_card && g.current_card.chunks) ? g.current_card.chunks : [];

  chunks.forEach((chunk, idx) => {
    const isBlank = g.pass_blank_indices.includes(idx);

    if (!isBlank) {
      // Static visible chunk in natural sentence flow
      const chip = document.createElement('span');
      chip.className = 'px-3.5 py-2 bg-white border border-slate-200 text-slate-800 rounded-xl font-medium shadow-2xs select-none text-base md:text-lg font-hindi cursor-help transition-all hover:border-indigo-300 hover:shadow-xs chunk-tooltip-target';
      chip.textContent = chunk;
      chip.dataset.chunkText = chunk;
      attachChunkHoverTooltip(chip, chunk);
      board.appendChild(chip);
    } else {
      // Interactive blank slot
      const filledText = g.filled_slots[idx];
      const slot = document.createElement('button');
      const isActive = g.active_slot_idx === idx;

      if (filledText) {
        slot.className = 'px-4 py-2 bg-indigo-50 border-2 border-indigo-500 text-indigo-950 font-bold rounded-xl shadow-xs text-base md:text-lg transition-all chip-slot chip-slot-filled flex items-center gap-1.5 font-hindi cursor-pointer chunk-tooltip-target';
        slot.innerHTML = `<span class="slot-text">${escapeAttr(filledText)}</span> <span class="slot-remove-btn text-[10px] text-indigo-400 hover:text-indigo-700 ml-1">✕</span>`;
        slot.dataset.chunkText = filledText;
        attachChunkHoverTooltip(slot, filledText, 'Click to clear slot');
      } else if (isActive) {
        slot.className = 'px-4 py-2 bg-amber-50/90 border-2 border-dashed border-amber-500 text-amber-900 font-bold rounded-xl shadow-xs text-base md:text-lg transition-all chip-slot chip-slot-active ring-2 ring-amber-200 font-hindi animate-pulse';
        slot.innerHTML = `<span class="inline-flex items-center gap-1"><span class="text-xs">✏️</span> <span class="slot-text">[ Blank ${idx + 1} ]</span></span>`;
        slot.title = 'Active blank slot: select a word chip below';
      } else {
        slot.className = 'px-4 py-2 bg-slate-100/80 border-2 border-dashed border-slate-300 text-slate-500 hover:border-indigo-400 hover:bg-indigo-50/30 font-semibold rounded-xl text-base md:text-lg transition-all chip-slot chip-slot-empty font-hindi';
        slot.innerHTML = `<span class="inline-flex items-center gap-1"><span class="text-xs opacity-40">❓</span> <span class="slot-text">[ Blank ${idx + 1} ]</span></span>`;
        slot.title = 'Click to activate this blank slot';
      }

      slot.onclick = () => {
        playSound('click');
        if (filledText) {
          // Clicking a filled slot clears it and returns chip to pool
          delete g.filled_slots[idx];
          g.active_slot_idx = idx;
          renderBlanksBoard();
          renderBlanksChips();
        } else {
          g.active_slot_idx = idx;
          renderBlanksBoard();
        }
      };

      board.appendChild(slot);
    }
  });
}

function renderBlanksChips() {
  const g = state.gameplay;
  const tray = document.getElementById('game-chips-tray');
  if (!tray) return;
  tray.innerHTML = '';

  const chunks = (g.current_card && g.current_card.chunks) ? g.current_card.chunks : [];
  const neededChunks = g.pass_blank_indices.map(i => chunks[i]);

  // Exclude chips that have already been placed in slots (handle duplicates safely)
  const placedCounts = {};
  Object.values(g.filled_slots).forEach(v => {
    placedCounts[v] = (placedCounts[v] || 0) + 1;
  });
  const available = [];
  neededChunks.forEach(ch => {
    if (placedCounts[ch] && placedCounts[ch] > 0) {
      placedCounts[ch]--;
    } else {
      available.push(ch);
    }
  });

  // Scramble available chips
  const scrambled = [...available].sort(() => 0.5 - Math.random());

  if (scrambled.length === 0) {
    tray.innerHTML = '<span class="text-xs text-slate-400 italic">All blanks filled. Click "Check Sentence" below!</span>';
    return;
  }

  scrambled.forEach(chunk => {
    const btn = document.createElement('button');
    btn.className = 'chip-btn px-4 py-2.5 bg-gradient-to-b from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 active:scale-95 text-white font-bold rounded-xl shadow-xs transition text-base font-hindi cursor-pointer chunk-tooltip-target';
    btn.textContent = chunk;
    btn.dataset.chunkText = chunk;
    attachChunkHoverTooltip(btn, chunk);

    btn.onclick = () => {
      // Find target slot: either current active or first empty blank slot
      let targetIdx = g.active_slot_idx;
      if (targetIdx === null || g.filled_slots[targetIdx]) {
        targetIdx = g.pass_blank_indices.find(i => !g.filled_slots[i]);
      }

      if (targetIdx !== undefined && targetIdx !== null) {
        playSound('click');
        g.filled_slots[targetIdx] = chunk;
        // Move active slot to next empty
        g.active_slot_idx = g.pass_blank_indices.find(i => !g.filled_slots[i]) ?? null;
        renderBlanksBoard();
        renderBlanksChips();
      }
    };

    tray.appendChild(btn);
  });
}

// -------------------------------------------------------------------------
// Mode B: Jigsaw Puzzle Engine & Dynamic Words-Per-Block Scaffolding
// -------------------------------------------------------------------------

function computeDynamicChunks(card, wordsPerBlock) {
  if (!card) return [];
  const rawChunks = card.chunks || [];
  if (rawChunks.length === 0) return [];
  if (wordsPerBlock === 'orig' || !wordsPerBlock) {
    return [...rawChunks];
  }

  const targetSize = parseInt(wordsPerBlock, 10);
  if (isNaN(targetSize) || targetSize <= 0) {
    return [...rawChunks];
  }

  // Extract all words from existing chunks
  const fullText = rawChunks.join(' ').replace(/\|/g, ' ').trim();
  const words = fullText.split(/\s+/).filter(w => w.length > 0);
  if (words.length === 0) return [...rawChunks];

  const dynamicChunks = [];
  for (let i = 0; i < words.length; i += targetSize) {
    dynamicChunks.push(words.slice(i, i + targetSize).join(' '));
  }

  if (dynamicChunks.length === 0) return [...rawChunks];

  // Preserve ending punctuation if present on card question or original chunks
  const lastOriginal = rawChunks[rawChunks.length - 1] || '';
  const lastDynamic = dynamicChunks[dynamicChunks.length - 1] || '';
  const punts = ['।', '.', '?', '!'];
  const hasOrigPunct = punts.some(p => lastOriginal.endsWith(p)) || punts.some(p => (card.question || '').endsWith(p));
  const hasDynPunct = punts.some(p => lastDynamic.endsWith(p));

  if (hasOrigPunct && !hasDynPunct) {
    const pChar = punts.find(p => (card.question || '').endsWith(p)) || (lastOriginal.match(/[।\.\?!]$/) ? lastOriginal.slice(-1) : '।');
    dynamicChunks[dynamicChunks.length - 1] += pChar;
  }

  return dynamicChunks;
}

function getEffectiveWordsPerBlock(card) {
  const g = state.gameplay;
  const isPlayingThisCard = Boolean(g && g.active && g.current_card && g.current_card.card_id === card?.card_id);

  // 1. Session or manual toggle override on current card
  if (isPlayingThisCard && g.words_per_block) {
    return g.words_per_block;
  }
  // 2. Global settings preference if explicitly 2, 3, or 4
  const settingVal = state.settings ? state.settings.jigsaw_words_per_block : 'auto';
  if (settingVal && settingVal !== 'auto') {
    return settingVal;
  }
  // 3. Adaptive Auto Scaffolding (4 -> 3 -> 2 Words before Voice Stage):
  // When climbing the ladder or practicing:
  // - Stage 2 (First jigsaw exposure): 4 words per block (gentle chunking)
  // - If the card has >= 1 previous successful jigsaw attempts: 3 words per block
  // - Stage 3/4 frontier or advanced practice (right before Voice stage): 2 words per block (granular recall)
  const cardStage = card ? (card.ladder_stage || card._attempt_stage || 2) : 2;
  const history = (card && card.stage_history) ? card.stage_history : [];
  const jigsawPasses = history.filter(h => h.stage === 2 && h.passed).length;

  if (cardStage >= 3 || jigsawPasses >= 2) {
    return 2;
  } else if (jigsawPasses >= 1) {
    return 3;
  }
  return 4;
}

function updateJigsawBlockSizeUI(activeSize) {
  const container = document.getElementById('jigsaw-block-size-container');
  if (!container) return;

  const btn4 = document.getElementById('jigsaw-size-4-btn');
  const btn3 = document.getElementById('jigsaw-size-3-btn');
  const btn2 = document.getElementById('jigsaw-size-2-btn');
  const btnAuto = document.getElementById('jigsaw-size-auto-btn');

  const buttons = [
    { btn: btn4, key: '4' },
    { btn: btn3, key: '3' },
    { btn: btn2, key: '2' },
    { btn: btnAuto, key: 'auto' }
  ];

  const currentKey = String(activeSize || 'auto');

  buttons.forEach(({ btn, key }) => {
    if (!btn) return;
    if (key === currentKey) {
      btn.className = 'px-2 py-0.5 text-[11px] rounded-lg font-bold transition bg-indigo-600 text-white cursor-pointer shadow-2xs';
    } else {
      btn.className = 'px-2 py-0.5 text-[11px] rounded-lg font-bold transition text-slate-600 hover:text-slate-900 cursor-pointer';
    }
  });
}

function setJigsawWordsPerBlock(size) {
  const g = state.gameplay;
  if (!g.active) return;
  playSound('click');

  g.words_per_block = size;
  updateJigsawBlockSizeUI(size);

  const card = g.current_card;
  if (!card) return;

  const dynamicChunks = (size === 'auto') 
    ? computeDynamicChunks(card, getEffectiveWordsPerBlock(card)) 
    : computeDynamicChunks(card, size);

  g.active_chunks = dynamicChunks;
  g.placed_chunks = [];
  g.available_chips = [...dynamicChunks].sort(() => 0.5 - Math.random());

  renderJigsawBoard();
  renderJigsawChips();
}

function initJigsawCard() {
  const g = state.gameplay;
  const card = g.current_card;

  const passBox = document.getElementById('game-pass-indicator-box');
  if (passBox) passBox.classList.add('hidden');

  const boardLabel = document.getElementById('game-board-label');
  if (boardLabel) boardLabel.textContent = 'Construct the sentence in proper order:';

  const helperTip = document.getElementById('game-helper-tip');
  if (helperTip) helperTip.textContent = 'Click chips to place them into the answer tray. Click placed chips to remove them.';

  // Show Words/Block selector container in Jigsaw mode
  const sizeContainer = document.getElementById('jigsaw-block-size-container');
  if (sizeContainer) sizeContainer.classList.remove('hidden');

  // Determine effective chunk size
  const effectiveSize = getEffectiveWordsPerBlock(card);
  const activeSetting = g.words_per_block || (state.settings && state.settings.jigsaw_words_per_block !== 'auto' ? state.settings.jigsaw_words_per_block : 'auto');
  updateJigsawBlockSizeUI(activeSetting);

  const chunksToUse = computeDynamicChunks(card, g.words_per_block === 'auto' || !g.words_per_block ? effectiveSize : g.words_per_block);
  g.active_chunks = chunksToUse;

  g.placed_chunks = [];
  g.available_chips = [...chunksToUse].sort(() => 0.5 - Math.random());

  renderJigsawBoard();
  renderJigsawChips();
}

function renderJigsawBoard() {
  const g = state.gameplay;
  const board = document.getElementById('game-assembly-board');
  if (!board) return;
  board.innerHTML = '';

  if (g.placed_chunks.length === 0) {
    board.innerHTML = '<span class="text-xs text-slate-400 italic">Click or drag phrase chips below to assemble the sentence...</span>';
    board.ondragover = (e) => {
      if (e && e.preventDefault) e.preventDefault();
      board.classList.add('ring-2', 'ring-indigo-400', 'bg-indigo-50/50');
    };
    board.ondragleave = () => {
      board.classList.remove('ring-2', 'ring-indigo-400', 'bg-indigo-50/50');
    };
    board.ondrop = (e) => {
      if (e && e.preventDefault) e.preventDefault();
      board.classList.remove('ring-2', 'ring-indigo-400', 'bg-indigo-50/50');
      try {
        const raw = e && e.dataTransfer && e.dataTransfer.getData('text/plain');
        if (raw) {
          const data = JSON.parse(raw);
          if (data && data.chunk) {
            insertChunkFromTray(data.chunk, 0);
          }
        }
      } catch (err) {}
    };
    return;
  }

  // Clear all drop and hover cues across the board
  const clearAllDropCues = () => {
    board.querySelectorAll('.chip-btn').forEach(c => {
      c.classList.remove('insert-between-neighbor', 'swap-neighbor');
    });
    board.querySelectorAll('.insertion-gap').forEach(gap => {
      if (!gap.classList.contains('active')) {
        gap.classList.remove('insertion-gap-hover');
      }
    });
  };

  // Dual sky-blue border highlighting on both adjacent neighbor blocks
  const highlightInsertionNeighbors = (insertIndex, activeGap = null) => {
    clearAllDropCues();
    if (activeGap) {
      activeGap.classList.add('insertion-gap-hover');
    }
    const chips = Array.from(board.querySelectorAll('.chip-btn'));
    if (insertIndex > 0 && chips[insertIndex - 1]) {
      chips[insertIndex - 1].classList.add('insert-between-neighbor');
    }
    if (insertIndex < chips.length && chips[insertIndex]) {
      chips[insertIndex].classList.add('insert-between-neighbor');
    }
  };

  // Single amber box highlight for direct swap/replace
  const highlightSwapChip = (chipIndex) => {
    clearAllDropCues();
    const chips = Array.from(board.querySelectorAll('.chip-btn'));
    if (chips[chipIndex]) {
      chips[chipIndex].classList.add('swap-neighbor');
    }
  };

  // Factory to create an interactive insertion gap between/around blocks
  const createInsertionGap = (insertIndex) => {
    const gap = document.createElement('div');
    const isActive = (g.active_insert_index === insertIndex);
    gap.className = `insertion-gap ${isActive ? 'active' : ''}`;
    gap.dataset.insertIndex = insertIndex;
    gap.title = 'Place mouse or click to insert block here';

    if (isActive) {
      gap.innerHTML = `
        <div class="flex items-center gap-1 px-2 py-0.5 bg-sky-500 text-white rounded-lg text-[11px] font-extrabold shadow-sm animate-pulse">
          <span>+</span>
          <span>Insert</span>
        </div>
      `;
    } else {
      gap.innerHTML = `
        <div class="insertion-cue">
          <span class="insertion-icon">+</span>
        </div>
      `;
    }

    // Hover between two blocks
    gap.onmouseenter = () => {
      highlightInsertionNeighbors(insertIndex, gap);
    };
    gap.onmouseleave = () => {
      gap.classList.remove('insertion-gap-hover');
      if (g.active_insert_index !== null && g.active_insert_index !== undefined) {
        highlightInsertionNeighbors(g.active_insert_index);
      } else {
        clearAllDropCues();
      }
    };

    // Click gap to select insertion point
    gap.onclick = (e) => {
      if (e && e.stopPropagation) e.stopPropagation();
      playSound('click');
      if (g.active_insert_index === insertIndex) {
        g.active_insert_index = null;
      } else {
        g.active_insert_index = insertIndex;
      }
      renderJigsawBoard();
    };

    // Drag over gap
    gap.ondragover = (e) => {
      if (e && e.preventDefault) e.preventDefault();
      if (e && e.dataTransfer) e.dataTransfer.dropEffect = 'move';
      gap.classList.add('insertion-gap-hover');
      highlightInsertionNeighbors(insertIndex);
    };
    gap.ondragleave = () => {
      gap.classList.remove('insertion-gap-hover');
      clearAllDropCues();
    };
    gap.ondrop = (e) => {
      if (e && e.preventDefault) e.preventDefault();
      clearAllDropCues();
      try {
        const raw = e && e.dataTransfer && e.dataTransfer.getData('text/plain');
        if (raw) {
          const data = JSON.parse(raw);
          if (data.source === 'tray') {
            insertChunkFromTray(data.chunk, insertIndex);
          } else if (data.source === 'board') {
            movePlacedChunk(data.index, insertIndex);
          }
        }
      } catch (err) {}
    };

    return gap;
  };

  // Render leading gap before chunk 0
  board.appendChild(createInsertionGap(0));

  g.placed_chunks.forEach((chunk, idx) => {
    const btn = document.createElement('button');
    btn.className = 'chip-btn px-4 py-2 bg-white border border-indigo-200 text-indigo-950 font-bold rounded-xl shadow-2xs hover:bg-rose-50 hover:border-rose-300 hover:text-rose-700 transition flex items-center gap-1.5 cursor-pointer chunk-tooltip-target';
    btn.innerHTML = `<span>${chunk}</span><span class="text-[10px] text-slate-400">✕</span>`;
    btn.dataset.chunkText = chunk;
    btn.dataset.chunkIndex = idx;
    btn.draggable = true;
    attachChunkHoverTooltip(btn, chunk, 'Click to remove, or drag to reorder/swap');

    // If this chip is adjacent to the active insertion point, keep sky-blue highlight
    if (g.active_insert_index !== null && g.active_insert_index !== undefined) {
      if (idx === g.active_insert_index - 1 || idx === g.active_insert_index) {
        btn.classList.add('insert-between-neighbor');
      }
    }

    // Drag start
    btn.ondragstart = (e) => {
      if (e && e.dataTransfer) {
        e.dataTransfer.setData('text/plain', JSON.stringify({ source: 'board', chunk: chunk, index: idx }));
        e.dataTransfer.effectAllowed = 'move';
      }
      btn.classList.add('opacity-40');
    };
    btn.ondragend = () => {
      btn.classList.remove('opacity-40');
      clearAllDropCues();
    };

    // 3-Zone Drag Over: Left 28% -> insert before; Right 28% -> insert after; Center 44% -> swap
    btn.ondragover = (e) => {
      if (e && e.preventDefault) e.preventDefault();
      const rect = btn.getBoundingClientRect ? btn.getBoundingClientRect() : { left: 0, width: 100 };
      const clientX = (e && typeof e.clientX === 'number') ? e.clientX : 0;
      const relX = (clientX - rect.left) / Math.max(1, rect.width);
      if (e && e.dataTransfer) e.dataTransfer.dropEffect = 'move';
      if (relX < 0.28) {
        highlightInsertionNeighbors(idx);
      } else if (relX > 0.72) {
        highlightInsertionNeighbors(idx + 1);
      } else {
        highlightSwapChip(idx);
      }
    };
    btn.ondragleave = () => {
      clearAllDropCues();
    };
    btn.ondrop = (e) => {
      if (e && e.preventDefault) e.preventDefault();
      const rect = btn.getBoundingClientRect ? btn.getBoundingClientRect() : { left: 0, width: 100 };
      const clientX = (e && typeof e.clientX === 'number') ? e.clientX : 0;
      const relX = (clientX - rect.left) / Math.max(1, rect.width);
      clearAllDropCues();
      try {
        const raw = e && e.dataTransfer && e.dataTransfer.getData('text/plain');
        if (!raw) return;
        const data = JSON.parse(raw);
        if (relX < 0.28) {
          if (data.source === 'tray') insertChunkFromTray(data.chunk, idx);
          else if (data.source === 'board') movePlacedChunk(data.index, idx);
        } else if (relX > 0.72) {
          if (data.source === 'tray') insertChunkFromTray(data.chunk, idx + 1);
          else if (data.source === 'board') movePlacedChunk(data.index, idx + 1);
        } else {
          if (data.source === 'tray') swapTrayChunkWithBoard(data.chunk, idx);
          else if (data.source === 'board') swapPlacedChunks(data.index, idx);
        }
      } catch (err) {}
    };

    // Direct click removes chunk back to tray
    btn.onclick = () => {
      playSound('click');
      g.active_insert_index = null;
      g.placed_chunks.splice(idx, 1);
      g.available_chips.push(chunk);
      renderJigsawBoard();
      renderJigsawChips();
    };

    board.appendChild(btn);

    // Trailing gap after each chunk (between idx and idx+1)
    board.appendChild(createInsertionGap(idx + 1));
  });
}

function renderJigsawChips() {
  const g = state.gameplay;
  const tray = document.getElementById('game-chips-tray');
  if (!tray) return;
  tray.innerHTML = '';

  if (g.available_chips.length === 0) {
    tray.innerHTML = '<span class="text-xs text-slate-400 italic">All words placed. Ready to check!</span>';
    return;
  }

  g.available_chips.forEach((chunk, idx) => {
    const btn = document.createElement('button');
    btn.className = 'chip-btn px-4 py-2 bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white font-bold rounded-xl shadow-xs transition cursor-pointer chunk-tooltip-target';
    btn.textContent = chunk;
    btn.dataset.chunkText = chunk;
    btn.draggable = true;
    attachChunkHoverTooltip(btn, chunk);

    btn.ondragstart = (e) => {
      if (e && e.dataTransfer) {
        e.dataTransfer.setData('text/plain', JSON.stringify({ source: 'tray', chunk: chunk, index: idx }));
        e.dataTransfer.effectAllowed = 'copyMove';
      }
      btn.classList.add('opacity-40');
    };
    btn.ondragend = () => {
      btn.classList.remove('opacity-40');
      const board = document.getElementById('game-assembly-board');
      if (board) {
        board.querySelectorAll('.chip-btn').forEach(c => c.classList.remove('insert-between-neighbor', 'swap-neighbor'));
      }
    };

    btn.onclick = () => {
      playSound('click');
      if (g.active_insert_index !== null && g.active_insert_index !== undefined) {
        insertChunkFromTray(chunk, g.active_insert_index);
      } else {
        g.placed_chunks.push(chunk);
        g.available_chips.splice(idx, 1);
        renderJigsawBoard();
        renderJigsawChips();
        if (g.available_chips.length === 0 && g.placed_chunks.length === g.active_chunks.length) {
          checkCurrentAnswer();
        }
      }
    };

    tray.appendChild(btn);
  });
}

function insertChunkFromTray(chunk, insertIndex) {
  const g = state.gameplay;
  const chipIdx = g.available_chips.indexOf(chunk);
  if (chipIdx !== -1) {
    g.available_chips.splice(chipIdx, 1);
  }
  const safeIdx = Math.max(0, Math.min(g.placed_chunks.length, insertIndex));
  g.placed_chunks.splice(safeIdx, 0, chunk);
  g.active_insert_index = null;
  playSound('click');
  renderJigsawBoard();
  renderJigsawChips();

  if (g.available_chips.length === 0 && g.placed_chunks.length === g.active_chunks.length) {
    checkCurrentAnswer();
  }
}

function movePlacedChunk(fromIndex, toIndex) {
  const g = state.gameplay;
  if (fromIndex < 0 || fromIndex >= g.placed_chunks.length) return;
  const [item] = g.placed_chunks.splice(fromIndex, 1);
  const targetIdx = (toIndex > fromIndex) ? (toIndex - 1) : toIndex;
  const safeTarget = Math.max(0, Math.min(g.placed_chunks.length, targetIdx));
  g.placed_chunks.splice(safeTarget, 0, item);
  g.active_insert_index = null;
  playSound('click');
  renderJigsawBoard();
  renderJigsawChips();

  if (g.available_chips.length === 0 && g.placed_chunks.length === g.active_chunks.length) {
    checkCurrentAnswer();
  }
}

function swapPlacedChunks(index1, index2) {
  const g = state.gameplay;
  if (index1 < 0 || index1 >= g.placed_chunks.length || index2 < 0 || index2 >= g.placed_chunks.length) return;
  const temp = g.placed_chunks[index1];
  g.placed_chunks[index1] = g.placed_chunks[index2];
  g.placed_chunks[index2] = temp;
  g.active_insert_index = null;
  playSound('click');
  renderJigsawBoard();
  renderJigsawChips();

  if (g.available_chips.length === 0 && g.placed_chunks.length === g.active_chunks.length) {
    checkCurrentAnswer();
  }
}

function swapTrayChunkWithBoard(trayChunk, boardIndex) {
  const g = state.gameplay;
  if (boardIndex < 0 || boardIndex >= g.placed_chunks.length) return;
  const oldBoardChunk = g.placed_chunks[boardIndex];
  g.placed_chunks[boardIndex] = trayChunk;
  const trayIdx = g.available_chips.indexOf(trayChunk);
  if (trayIdx !== -1) {
    g.available_chips[trayIdx] = oldBoardChunk;
  } else {
    g.available_chips.push(oldBoardChunk);
  }
  g.active_insert_index = null;
  playSound('click');
  renderJigsawBoard();
  renderJigsawChips();

  if (g.available_chips.length === 0 && g.placed_chunks.length === g.active_chunks.length) {
    checkCurrentAnswer();
  }
}

function setActiveInsertIndex(insertIndex) {
  const g = state.gameplay;
  g.active_insert_index = insertIndex;
  renderJigsawBoard();
}

// -------------------------------------------------------------------------
// Mode C: Auditory Decoding & Listening Studio
// -------------------------------------------------------------------------

function initListeningCard() {
  const g = state.gameplay;
  const card = g.current_card;
  const chunks = card.chunks || [];

  document.getElementById('game-board-label').textContent = 'Listen to the audio and construct the sentence:';
  document.getElementById('game-helper-tip').textContent = 'Click phrase chips below in the order you hear them spoken.';

  // Mask question text to focus entirely on auditory decoding
  document.getElementById('game-question-text').textContent = '🎧 "Listen carefully and reconstruct what you hear in order:"';

  g.placed_chunks = [];
  g.available_chips = [...chunks].sort(() => 0.5 - Math.random());

  renderJigsawBoard();
  renderJigsawChips();

  // Auto-play audio prompt
  setTimeout(() => {
    playCardTTS();
  }, 350);
}

// -------------------------------------------------------------------------
// Mode D: Voice Mastery & Spoken Phonics Studio
// -------------------------------------------------------------------------

let micPermissionGranted = false;

async function ensureMicrophonePermission() {
  if (micPermissionGranted) return true;
  if (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function') {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micPermissionGranted = true;
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (err) {
      console.warn("Microphone permission check:", err);
      return false;
    }
  }
  return false;
}

function initVoiceCard() {
  const g = state.gameplay;
  const card = g.current_card;
  const targetText = (card.chunks || []).join(' ') || card.question;

  document.getElementById('voice-target-sentence').textContent = targetText;
  document.getElementById('voice-status-badge').textContent = 'Ready to Speak';
  document.getElementById('voice-status-badge').className = 'text-xs font-bold bg-slate-100 text-slate-600 px-3 py-1 rounded-full';
  document.getElementById('voice-mic-instruction').textContent = 'Click microphone, speak clearly, then click Stop';
  document.getElementById('voice-transcript-text').textContent = 'Your spoken words will appear here...';
  document.getElementById('voice-accuracy-score').textContent = 'Score: --';
  document.getElementById('voice-score-bar').style.width = '0%';
  document.getElementById('voice-score-bar').className = 'h-full rounded-full transition-all duration-300 bg-rose-500';
  document.getElementById('voice-feedback-msg').textContent = '';

  const micBtn = document.getElementById('btn-mic-record');
  micBtn.className = 'w-16 h-16 rounded-full bg-rose-600 hover:bg-rose-700 text-white text-2xl flex items-center justify-center shadow-lg transition transform active:scale-95 cursor-pointer';
  micBtn.setAttribute('aria-pressed', 'false');

  // Pre-authorize microphone permission once in background so student is never prompted on click
  ensureMicrophonePermission().catch(() => {});
}

let voiceRecognitionInstance = null;
let isVoiceRecording = false;

async function toggleVoiceRecording() {
  const card = state.gameplay.current_card;
  if (!card) return;
  const targetText = (card.chunks || []).join(' ') || card.question;
  const isHindi = /[\u0900-\u097F]/.test(targetText);

  const btn = document.getElementById('btn-mic-record');
  const badge = document.getElementById('voice-status-badge');
  const instruction = document.getElementById('voice-mic-instruction');
  const transcriptEl = document.getElementById('voice-transcript-text');

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (isVoiceRecording) {
    isVoiceRecording = false;
    btn.className = 'w-16 h-16 rounded-full bg-rose-600 hover:bg-rose-700 text-white text-2xl flex items-center justify-center shadow-lg transition transform active:scale-95 cursor-pointer';
    btn.setAttribute('aria-pressed', 'false');
    badge.className = 'text-xs font-bold bg-slate-100 text-slate-600 px-3 py-1 rounded-full';
    badge.textContent = 'Evaluating Speech...';
    instruction.textContent = 'Evaluation complete.';
    if (voiceRecognitionInstance) {
      try { voiceRecognitionInstance.stop(); } catch(e) {}
    }
    return;
  }

  // Pre-authorize microphone permission before starting recognition to avoid repeated prompts
  await ensureMicrophonePermission().catch(() => {});


  // Start speech recognition
  isVoiceRecording = true;
  btn.className = 'w-16 h-16 rounded-full bg-red-500 text-white text-2xl flex items-center justify-center shadow-xl animate-pulse cursor-pointer';
  btn.setAttribute('aria-pressed', 'true');
  badge.className = 'text-xs font-bold bg-rose-100 text-rose-700 px-3 py-1 rounded-full animate-pulse';
  badge.textContent = '● Listening... Speak Now';
  instruction.textContent = 'Speaking... Click microphone again when finished.';
  transcriptEl.textContent = 'Listening...';

  if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    voiceRecognitionInstance = recognition;
    recognition.lang = isHindi ? 'hi-IN' : 'en-US';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let speechResult = '';
      for (let i = 0; i < event.results.length; ++i) {
        speechResult += event.results[i][0].transcript;
      }
      transcriptEl.textContent = speechResult;

      if (event.results[0].isFinal) {
        evaluateVoiceSpeech(speechResult, targetText);
      }
    };

    recognition.onerror = (err) => {
      console.warn("Speech recognition error:", err);
      isVoiceRecording = false;
      btn.className = 'w-16 h-16 rounded-full bg-rose-600 hover:bg-rose-700 text-white text-2xl flex items-center justify-center shadow-lg transition transform active:scale-95 cursor-pointer';
      badge.textContent = 'Ready to Speak';
      fallbackVoiceEvaluation(targetText);
    };

    recognition.onend = () => {
      isVoiceRecording = false;
      btn.className = 'w-16 h-16 rounded-full bg-rose-600 hover:bg-rose-700 text-white text-2xl flex items-center justify-center shadow-lg transition transform active:scale-95 cursor-pointer';
    };

    try {
      recognition.start();
    } catch(e) {
      fallbackVoiceEvaluation(targetText);
    }
  } else {
    fallbackVoiceEvaluation(targetText);
  }
}

function fallbackVoiceEvaluation(targetText) {
  const transcriptEl = document.getElementById('voice-transcript-text');
  transcriptEl.textContent = `Spoken sentence: "${targetText}"`;
  evaluateVoiceSpeech(targetText, targetText);
}

function evaluateVoiceSpeech(spoken, target) {
  const cleanSpoken = spoken.trim().toLowerCase().replace(/[^\w\s\u0900-\u097F]/g, '');
  const cleanTarget = target.trim().toLowerCase().replace(/[^\w\s\u0900-\u097F]/g, '');

  let score = 0;
  if (cleanSpoken === cleanTarget) {
    score = 100;
  } else {
    const spokenWords = cleanSpoken.split(/\s+/);
    const targetWords = cleanTarget.split(/\s+/);
    let matchCount = 0;
    targetWords.forEach(w => {
      if (spokenWords.includes(w)) matchCount++;
    });
    score = Math.round((matchCount / Math.max(1, targetWords.length)) * 100);
  }

  const scoreEl = document.getElementById('voice-accuracy-score');
  const bar = document.getElementById('voice-score-bar');
  const feedbackEl = document.getElementById('voice-feedback-msg');

  scoreEl.textContent = `Score: ${score}%`;
  bar.style.width = `${score}%`;

  if (score >= 80) {
    playSound('success');
    scoreEl.className = 'text-sm font-black text-emerald-600';
    bar.className = 'h-full rounded-full transition-all duration-300 bg-emerald-500';
    feedbackEl.className = 'font-bold text-emerald-600';
    feedbackEl.textContent = '🌟 Fluency Mastered! Pronunciation was clear and accurate.';
    setTimeout(() => {
      triggerSuccessAnimation();
      recordCardCompletion(true);
    }, 800);
  } else {
    playSound('error');
    scoreEl.className = 'text-sm font-black text-amber-600';
    bar.className = 'h-full rounded-full transition-all duration-300 bg-amber-500';
    feedbackEl.className = 'font-bold text-amber-600';
    feedbackEl.textContent = 'Keep practicing! Try reading the words again clearly.';
  }
}

// -------------------------------------------------------------------------
// Mode E: Active Writing & Spelling Studio
// -------------------------------------------------------------------------

function initWritingCard() {
  const g = state.gameplay;
  const card = g.current_card;

  document.getElementById('writing-input-area').value = '';
  document.getElementById('writing-word-count').textContent = '0 words typed';
  document.getElementById('writing-diff-result').classList.add('hidden');
  document.getElementById('game-helper-tip').textContent = 'Type the complete answer and click "Check Sentence".';

  // Render virtual Hindi helper keys
  const keysContainer = document.getElementById('writing-hindi-virtual-keys');
  keysContainer.innerHTML = '';
  const hindiKeys = ['्', 'ा', 'ि', 'ी', 'ु', 'ू', 'े', 'ै', 'ो', 'औ', 'ं', 'ँ', 'ः', '।', 'ऋ', 'ज्ञ', 'क्ष', 'त्र', 'श्र', '?', '!'];
  
  hindiKeys.forEach(k => {
    const btn = document.createElement('button');
    btn.className = 'px-2 py-1 bg-white hover:bg-indigo-50 border border-slate-200 text-slate-800 font-bold rounded-lg shadow-2xs text-xs transition active:scale-95 cursor-pointer';
    btn.textContent = k;
    btn.onclick = () => insertCharIntoWritingInput(k);
    keysContainer.appendChild(btn);
  });
}

function insertCharIntoWritingInput(char) {
  const ta = document.getElementById('writing-input-area');
  const start = ta.selectionStart;
  const end = ta.selectionEnd;
  const val = ta.value;
  ta.value = val.substring(0, start) + char + val.substring(end);
  ta.selectionStart = ta.selectionEnd = start + char.length;
  ta.focus();
  updateWritingWordCount();
}

function updateWritingWordCount() {
  const text = document.getElementById('writing-input-area').value.trim();
  const words = text ? text.split(/\s+/).length : 0;
  document.getElementById('writing-word-count').textContent = `${words} words typed`;
}

async function checkWritingAnswer() {
  const g = state.gameplay;
  const card = g.current_card;
  const targetText = (card.chunks || []).join(' ');
  const typedText = document.getElementById('writing-input-area').value.trim();

  if (!typedText) {
    alert("Please write your answer before checking!");
    return;
  }

  let evalResult = null;
  if (window.pywebview) {
    evalResult = await window.pywebview.api.evaluate_spelling(targetText, typedText);
  } else {
    evalResult = clientSideEvaluateSpelling(targetText, typedText);
  }

  renderWritingDiffPills(evalResult);

  const score = evalResult.overall_score !== undefined ? evalResult.overall_score : 100;
  const isPerfect = evalResult.flawless || score >= 85;

  if (isPerfect) {
    playSound('success');
    triggerSuccessAnimation();
    recordCardCompletion(true);
  } else {
    playSound('error');
    triggerErrorAnimation();
    g.flawless = false;
  }
}

function clientSideEvaluateSpelling(target, typed) {
  const cleanT = target.trim().replace(/[^\w\s\u0900-\u097F]/g, '');
  const cleanU = typed.trim().replace(/[^\w\s\u0900-\u097F]/g, '');
  const targetWords = cleanT.split(/\s+/);
  const userWords = cleanU.split(/\s+/);

  const tokens = [];
  let matchCount = 0;

  targetWords.forEach((tw, idx) => {
    const uw = userWords[idx];
    if (uw && uw.toLowerCase() === tw.toLowerCase()) {
      tokens.push({ word: tw, status: 'correct' });
      matchCount++;
    } else if (uw) {
      tokens.push({ word: uw, status: 'typo', expected: tw });
    } else {
      tokens.push({ word: tw, status: 'missing' });
    }
  });

  const score = Math.round((matchCount / Math.max(1, targetWords.length)) * 100);
  return {
    overall_score: score,
    flawless: score === 100,
    tokens: tokens
  };
}

function renderWritingDiffPills(evalResult) {
  const box = document.getElementById('writing-diff-result');
  const badge = document.getElementById('writing-score-badge');
  const tokensRow = document.getElementById('writing-tokens-row');

  if (box) box.classList.remove('hidden');
  const tokens = Array.isArray(evalResult) ? evalResult : (evalResult ? (evalResult.tokens || []) : []);
  const score = (evalResult && typeof evalResult.overall_score === 'number') ? evalResult.overall_score : (tokens.length > 0 ? 85 : 0);
  if (badge) {
    badge.textContent = `Score: ${score}%`;
    badge.className = score >= 80 
      ? 'bg-emerald-100 text-emerald-800 font-bold px-2.5 py-0.5 rounded-full text-xs' 
      : 'bg-rose-100 text-rose-800 font-bold px-2.5 py-0.5 rounded-full text-xs';
  }

  if (!tokensRow) return;
  tokensRow.innerHTML = '';
  tokens.forEach(t => {
    const pill = document.createElement('span');
    if (t.status === 'correct' || t.status === 'match') {
      pill.className = 'px-2.5 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-lg text-xs font-bold';
      pill.textContent = t.word || t.token;
    } else if (t.status === 'typo') {
      pill.className = 'px-2.5 py-1 bg-rose-50 text-rose-800 border border-rose-200 rounded-lg text-xs font-bold';
      pill.textContent = `${t.word || t.token} (typo)`;
    } else {
      pill.className = 'px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded-lg text-xs font-bold';
      pill.textContent = `${t.word || t.token} (missing)`;
    }
    tokensRow.appendChild(pill);
  });
}

// -------------------------------------------------------------------------
// Answer Checking & Adaptive Pass Transitions
// -------------------------------------------------------------------------

async function checkCurrentAnswer() {
  const g = state.gameplay;
  const card = g.current_card;
  const chunks = card.chunks || [];
  const mode = g.effective_mode || g.mode;

  if (mode === 'writing') {
    await checkWritingAnswer();
    return;
  }

  if (mode === 'blanks') {
    // Check all blank slots
    const allFilled = g.pass_blank_indices.every(i => g.filled_slots[i]);
    if (!allFilled) {
      alert("Please fill in all blanks before checking!");
      return;
    }

    let isCorrect = true;
    g.pass_blank_indices.forEach(idx => {
      if (g.filled_slots[idx] !== chunks[idx]) {
        isCorrect = false;
      }
    });

    if (isCorrect) {
      playSound('success');
      triggerSuccessAnimation();

      if (g.pass_number < g.max_passes) {
        // Advance to next pass
        g.pass_number++;
        setTimeout(() => {
          initAdaptiveBlanksCard();
        }, 600);
      } else {
        // Card completely cleared all passes!
        recordCardCompletion(true);
      }
    } else {
      playSound('error');
      triggerErrorAnimation();
      g.flawless = false;
      alert("Some slots are incorrect. Review the words and try again!");
    }

  } else {
    // Jigsaw or Listening mode check
    const targetChunks = (mode === 'jigsaw' && g.active_chunks && g.active_chunks.length > 0) ? g.active_chunks : chunks;
    if (g.placed_chunks.length < targetChunks.length) {
      alert("Please place all chips to complete the sentence!");
      return;
    }

    const isCorrect = targetChunks.every((chunk, idx) => g.placed_chunks[idx] === chunk);
    if (isCorrect) {
      playSound('success');
      triggerSuccessAnimation();
      if (mode === 'jigsaw' && (g.hint_used || (g.hints_used && g.hints_used > 0))) {
        // Hint-enabled jigsaw attempts count as assisted practice without stage advancement
        recordCardCompletion(false, { hint_used: true, hints_used: g.hints_used || 1 });
      } else {
        recordCardCompletion(true, { hint_used: false, hints_used: 0 });
      }
    } else {
      playSound('error');
      triggerErrorAnimation();
      g.flawless = false;
      alert("The sentence order is not quite right. Click wrong chips to swap them!");
    }
  }
}

async function recordCardCompletion(passed, meta = {}) {
  const g = state.gameplay;
  const card = g.current_card;
  if (!card) return;

  // Track hint assistance
  const isHintAssisted = Boolean(meta.hint_used || g.hint_used || (g.hints_used && g.hints_used > 0));
  const hintsCount = meta.hints_used || g.hints_used || 0;
  if (isHintAssisted) {
    g.flawless = false;
  }

  // Stop stopwatch timer
  const durationSec = stopQuestionTimer();

  // Trigger sound effect for card completion
  playSound('complete');

  // Resolve deck_id reliably
  let deckId = card.deck_id || g.deck_id;
  if (!deckId && state.decks) {
    const matchedDeck = state.decks.find(d => (d.cards || []).some(c => c.card_id === card.card_id));
    if (matchedDeck) deckId = matchedDeck.id;
  }

  const attemptStage = g.current_attempt_stage || (g.mode === 'guided_mission' ? (card._attempt_stage || card.ladder_stage || 1) : getStageForMode(g.effective_mode || g.mode));
  let timingResult = null;
  let stageAdvanced = false;

  // Submit to backend bridge
  if (window.pywebview && deckId && card.card_id) {
    try {
      const res = await window.pywebview.api.submit_card_result(
        deckId,
        card.card_id,
        attemptStage,
        passed,
        100,
        g.flawless,
        durationSec,
        isHintAssisted,
        hintsCount
      );
      if (res && res.next_stage) {
        card.ladder_stage = res.next_stage;
      }
      if (res && typeof res.stage_advanced === 'boolean') {
        stageAdvanced = res.stage_advanced;
      } else if (res && res.next_stage) {
        stageAdvanced = res.next_stage > attemptStage;
      }
      if (res && res.timing) {
        timingResult = res.timing;
      }
    } catch (err) {
      console.warn("Could not submit card result to backend:", err);
    }
  } else if (passed && !isHintAssisted) {
    const currentCardStage = card.ladder_stage || 1;
    if (attemptStage >= currentCardStage) {
      card.ladder_stage = Math.min(6, attemptStage + 1);
      stageAdvanced = card.ladder_stage > currentCardStage;
    } else {
      stageAdvanced = false;
    }
  }

  // Fallback client-side timing computation if bridge timing not present (offline/test environments)
  if (!timingResult && durationSec > 0) {
    const history = card.stage_history || [];
    const stageAttempts = history.filter(h => h.stage === attemptStage && typeof h.duration_seconds === 'number');
    const cleanStageAttempts = stageAttempts.filter(h => !h.hint_used && (!h.hints_used || h.hints_used === 0));
    let prevDur = null;
    let diff = null;
    let pct = null;
    let isBest = false;
    let bestDur = null;

    if (stageAttempts.length > 0) {
      prevDur = stageAttempts[stageAttempts.length - 1].duration_seconds;
      diff = Math.round((prevDur - durationSec) * 10) / 10;
      pct = (prevDur > 0) ? Math.round((diff / prevDur) * 1000) / 10 : 0;
    } else {
      const priorAttempts = history.filter(h => typeof h.duration_seconds === 'number');
      if (priorAttempts.length > 0) {
        prevDur = priorAttempts[priorAttempts.length - 1].duration_seconds;
        diff = Math.round((prevDur - durationSec) * 10) / 10;
        pct = (prevDur > 0) ? Math.round((diff / prevDur) * 1000) / 10 : 0;
      }
    }

    if (cleanStageAttempts.length > 0) {
      const cleanDurs = cleanStageAttempts.map(h => h.duration_seconds);
      const priorCleanBest = Math.min(...cleanDurs);
      if (isHintAssisted) {
        isBest = false;
        bestDur = priorCleanBest;
      } else {
        isBest = durationSec <= priorCleanBest;
        bestDur = Math.min(priorCleanBest, durationSec);
      }
    } else {
      if (isHintAssisted) {
        isBest = false;
        bestDur = null;
      } else {
        isBest = true;
        bestDur = durationSec;
      }
    }

    timingResult = {
      duration_seconds: durationSec,
      previous_duration_seconds: prevDur,
      diff_seconds: diff,
      diff_percent: pct,
      improved: diff != null && diff > 0,
      is_new_best: isBest,
      best_duration_seconds: bestDur,
      total_attempts: history.length + 1,
      hint_used: isHintAssisted,
      hints_used: hintsCount
    };
  }

  // Record attempt into card.stage_history in-memory
  if (!card.stage_history) card.stage_history = [];
  card.stage_history.push({
    stage: attemptStage,
    timestamp: new Date().toISOString(),
    passed: passed && !isHintAssisted,
    score: 100,
    flawless: g.flawless && !isHintAssisted,
    duration_seconds: durationSec,
    hint_used: isHintAssisted,
    hints_used: hintsCount
  });

  // Immediately mirror stage advance and history in-memory across state.decks
  if (state.decks && card.card_id) {
    state.decks.forEach(d => {
      (d.cards || []).forEach(c => {
        if (c.card_id === card.card_id) {
          c.ladder_stage = card.ladder_stage;
          c.stage_history = card.stage_history;
        }
      });
    });
  }

  // Trigger celebration UI
  try { triggerConfetti(); } catch (e) {}
  const celebText = document.getElementById('celebration-detail-text');
  if (celebText) {
    const stageNames = { 1: 'Blanks', 2: 'Jigsaw', 3: 'Listening', 4: 'Voice', 5: 'Speed', 6: 'Written' };
    if (stageAdvanced) {
      const nextSt = card.ladder_stage || 2;
      celebText.textContent = `Great job! Sentence cleared. Learning stage advanced to Stage ${nextSt} (${stageNames[nextSt] || 'Next'}).`;
    } else if (isHintAssisted) {
      celebText.textContent = `💡 Practice completed with Hint! Try solving without hints to beat your Personal Best and advance to the next stage.`;
    } else {
      celebText.textContent = `Great practice! Sentence cleared for Stage ${attemptStage} (${stageNames[attemptStage] || 'Current'}).`;
    }
  }

  // Populate Timing & Improvement in celebration card
  const timeTakenEl = document.getElementById('celebration-time-taken');
  const compTextEl = document.getElementById('celebration-comparison-text');
  if (timeTakenEl) {
    timeTakenEl.textContent = `${durationSec}s`;
  }
  if (compTextEl) {
    if (isHintAssisted) {
      compTextEl.innerHTML = `💡 <span class="text-amber-200 font-semibold">Assisted Practice (Hint Used)</span> • Not eligible for Personal Best or stage graduation.`;
    } else if (timingResult && timingResult.previous_duration_seconds != null) {
      if (timingResult.improved) {
        const pctStr = timingResult.diff_percent ? ` (-${timingResult.diff_percent}%)` : '';
        compTextEl.innerHTML = `⚡ <span class="text-emerald-200 font-black">${timingResult.diff_seconds}s faster</span> than earlier attempt! (Earlier: ${timingResult.previous_duration_seconds}s${pctStr})`;
      } else if (timingResult.diff_seconds === 0) {
        compTextEl.innerHTML = `🎯 Matched your previous attempt exactly (${timingResult.previous_duration_seconds}s)`;
      } else {
        compTextEl.innerHTML = `⏱️ Earlier attempt: ${timingResult.previous_duration_seconds}s (+${Math.abs(timingResult.diff_seconds)}s)`;
      }
    } else {
      compTextEl.textContent = '🌟 Baseline attempt recorded';
    }
    if (!isHintAssisted && timingResult && timingResult.is_new_best && timingResult.previous_duration_seconds != null) {
      compTextEl.innerHTML += ' • 🏆 Personal Best!';
    }
  }

  const celebCard = document.getElementById('game-celebration-card');
  if (celebCard) {
    celebCard.classList.remove('hidden');
  }
}

function retryGameplayCard() {
  stopQuestionTimer();
  const g = state.gameplay;
  if (!g || !g.current_card) return;
  const celebCard = document.getElementById('game-celebration-card');
  if (celebCard) celebCard.classList.add('hidden');

  g.pass_number = 1;
  g.filled_slots = {};
  g.placed_chunks = [];
  g.available_chips = [];
  g.flawless = true;
  g.active_slot_idx = null;

  loadGameplayCard();
}

async function nextGameplayCard() {
  const g = state.gameplay;
  if (g.card_index + 1 < g.cards.length) {
    g.card_index++;
    g.pass_number = 1;
    g.flawless = true;
    loadGameplayCard();
  } else {
    stopQuestionTimer();
    // Session completed
    alert("🎉 Great job! You completed all sentences in this section!\nYour progress has been saved and your learning stage has advanced.");
    await exitGameplay();
  }
}

// -------------------------------------------------------------------------
// Helper Actions (Hint, Undo, Clear, Audio)
// -------------------------------------------------------------------------

function gameActionHint() {
  playSound('hint');
  const g = state.gameplay;
  const chunks = g.current_card.chunks || [];
  const mode = g.effective_mode || g.mode;

  // Track hint usage & disqualify flawless attempt
  g.hints_used = (g.hints_used || 0) + 1;
  g.hint_used = true;
  g.flawless = false;

  if (mode === 'blanks') {
    // Auto-fill the first uncompleted blank slot with correct chunk
    const emptyIdx = g.pass_blank_indices.find(i => !g.filled_slots[i] || g.filled_slots[i] !== chunks[i]);
    if (emptyIdx !== undefined) {
      g.filled_slots[emptyIdx] = chunks[emptyIdx];
      g.active_slot_idx = g.pass_blank_indices.find(i => !g.filled_slots[i]) ?? null;
      renderBlanksBoard();
      renderBlanksChips();
    }
  } else {
    // Place next chunk in jigsaw
    const targetChunks = (mode === 'jigsaw' && g.active_chunks && g.active_chunks.length > 0) ? g.active_chunks : chunks;
    const nextIdx = g.placed_chunks.length;
    
    // In Jigsaw mode: Do not auto-place the final remaining chunk so hint cannot finish the sentence
    if (mode === 'jigsaw' && nextIdx >= targetChunks.length - 1 && targetChunks.length > 1) {
      alert("Almost there! Place the final piece yourself to complete the sentence. 🧩");
      return;
    }

    if (nextIdx < targetChunks.length) {
      const correctChunk = targetChunks[nextIdx];
      const chipIdx = g.available_chips.indexOf(correctChunk);
      if (chipIdx !== -1) {
        g.available_chips.splice(chipIdx, 1);
        g.placed_chunks.push(correctChunk);
        renderJigsawBoard();
        renderJigsawChips();
      }
    }
  }
}

function gameActionUndo() {
  playSound('click');
  const g = state.gameplay;
  const mode = g.effective_mode || g.mode;
  if (mode === 'blanks') {
    // Clear last filled slot
    const filledKeys = Object.keys(g.filled_slots);
    if (filledKeys.length > 0) {
      const lastKey = filledKeys[filledKeys.length - 1];
      delete g.filled_slots[lastKey];
      g.active_slot_idx = parseInt(lastKey);
      renderBlanksBoard();
      renderBlanksChips();
    }
  } else {
    if (g.placed_chunks.length > 0) {
      const last = g.placed_chunks.pop();
      g.available_chips.push(last);
      renderJigsawBoard();
      renderJigsawChips();
    }
  }
}

function gameActionClear() {
  playSound('click');
  const g = state.gameplay;
  const mode = g.effective_mode || g.mode;
  if (mode === 'blanks') {
    g.filled_slots = {};
    g.active_slot_idx = g.pass_blank_indices[0];
    renderBlanksBoard();
    renderBlanksChips();
  } else {
    const cardChunks = (g.current_card && g.current_card.chunks) || [];
    const targetChunks = (mode === 'jigsaw' && g.active_chunks && g.active_chunks.length > 0) ? g.active_chunks : cardChunks;
    g.placed_chunks = [];
    g.available_chips = [...targetChunks].sort(() => 0.5 - Math.random());
    renderJigsawBoard();
    renderJigsawChips();
  }
}

function toggleEnglishMeaning() {
  const meaningEl = document.getElementById('game-meaning-text');
  const btn = document.getElementById('btn-toggle-meaning');
  if (meaningEl.classList.contains('hidden')) {
    meaningEl.classList.remove('hidden');
    btn.textContent = 'Hide English Meaning';
  } else {
    meaningEl.classList.add('hidden');
    btn.textContent = 'Show English Meaning';
  }
}

function playCardTTS() {
  const g = state.gameplay;
  if (!g.current_card) return;
  const isHindi = /[\u0900-\u097F]/.test(g.current_card.question);
  playCardAudioDirect(g.current_card.question, isHindi ? 'Hindi' : 'English');
}

function playAnswerTTS() {
  const g = state.gameplay;
  if (!g.current_card) return;
  const chunks = g.current_card.chunks || [];
  const answerText = chunks.join(' ') || g.current_card.sentence || g.current_card.answer || '';
  if (!answerText.trim()) return;
  const isHindi = /[\u0900-\u097F]/.test(answerText) || (g.current_card.lesson_name && /[\u0900-\u097F]/.test(g.current_card.lesson_name));
  playCardAudioDirect(answerText, isHindi ? 'Hindi' : 'English');
}

// =========================================================================
// Audio Sound Clips & Synthesizer System (Web Audio + Desktop Bridge)
// =========================================================================

let webAudioCtx = null;

function getWebAudioContext() {
  try {
    if (!webAudioCtx && (typeof window !== 'undefined') && (window.AudioContext || window.webkitAudioContext)) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      webAudioCtx = new AudioContextClass();
    }
    if (webAudioCtx && webAudioCtx.state === 'suspended') {
      webAudioCtx.resume();
    }
    return webAudioCtx;
  } catch (e) {
    return null;
  }
}

function playSound(type) {
  if (state.settings && state.settings.sound_enabled === false) return;

  // 1. Desktop Python bridge sound player (winsound.Beep / native system audio)
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.play_sound === 'function') {
    try {
      window.pywebview.api.play_sound(type);
    } catch (e) {
      console.warn("Desktop bridge sound error:", e);
    }
  }

  // 2. Web Audio API synthesized sound clip for immediate browser feedback
  try {
    const ctx = getWebAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    if (type === 'click') {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.exponentialRampToValueAtTime(400, now + 0.04);
      gain.gain.setValueAtTime(0.2, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.04);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.04);
    } else if (type === 'success') {
      // Harmonic ascending chime: C5 (523Hz), E5 (659Hz), G5 (784Hz)
      [523.25, 659.25, 783.99].forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + i * 0.08);
        gain.gain.setValueAtTime(0, now + i * 0.08);
        gain.gain.linearRampToValueAtTime(0.25, now + i * 0.08 + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.08 + 0.22);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + i * 0.08);
        osc.stop(now + i * 0.08 + 0.25);
      });
    } else if (type === 'error') {
      // Low descending buzz tone (220Hz -> 160Hz)
      [220, 160].forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(freq, now + i * 0.1);
        gain.gain.setValueAtTime(0.18, now + i * 0.1);
        gain.gain.exponentialRampToValueAtTime(0.01, now + i * 0.1 + 0.12);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + i * 0.1);
        osc.stop(now + i * 0.1 + 0.13);
      });
    } else if (type === 'hint') {
      // High bell sparkle chime (1046Hz -> 1318Hz)
      [1046.5, 1318.5].forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + i * 0.06);
        gain.gain.setValueAtTime(0.15, now + i * 0.06);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.06 + 0.18);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + i * 0.06);
        osc.stop(now + i * 0.06 + 0.2);
      });
    } else if (type === 'complete') {
      // Triumphant celebratory fanfare arpeggio
      [523.25, 659.25, 783.99, 1046.5].forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + i * 0.09);
        gain.gain.setValueAtTime(0, now + i * 0.09);
        gain.gain.linearRampToValueAtTime(0.3, now + i * 0.09 + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.09 + 0.35);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + i * 0.09);
        osc.stop(now + i * 0.09 + 0.4);
      });
    }
  } catch (err) {
    // Gracefully handle browser audio policy
  }
}

function playCardAudioDirect(text, subject) {
  const isHindi = /[\u0900-\u097F]/.test(text) || (subject && subject.toLowerCase() === 'hindi');
  const lang = isHindi ? 'hi' : 'en';

  const rateSetting = (state.settings && state.settings.tts_speed_rate) || '+0%';
  let rate = 1.0;
  if (rateSetting === '-50%') rate = 0.5;
  else if (rateSetting === '-25%') rate = 0.75;
  else if (rateSetting === '+20%') rate = 1.2;

  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.speak_text === 'function') {
    window.pywebview.api.speak_text(text, lang, rateSetting);
  } else if ('speechSynthesis' in window) {
    if (typeof window.speechSynthesis.cancel === 'function') {
      window.speechSynthesis.cancel();
    }
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = isHindi ? 'hi-IN' : 'en-US';
    utter.rate = rate;
    window.speechSynthesis.speak(utter);
  }
}

function triggerSuccessAnimation() {
  const board = document.getElementById('game-assembly-board');
  board.classList.add('border-emerald-500', 'bg-emerald-50/50');
}

function triggerErrorAnimation() {
  const board = document.getElementById('game-assembly-board');
  board.classList.add('animate-shake');
  setTimeout(() => board.classList.remove('animate-shake'), 450);
}

// Lightweight Canvas Confetti
function triggerConfetti() {
  const canvas = document.getElementById('confetti-canvas');
  if (!canvas || typeof canvas.getContext !== 'function') return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const particles = [];
  const colors = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#3b82f6'];

  for (let i = 0; i < 80; i++) {
    particles.push({
      x: canvas.width / 2,
      y: canvas.height / 3,
      r: Math.random() * 5 + 3,
      dx: (Math.random() - 0.5) * 12,
      dy: (Math.random() - 0.8) * 14,
      color: colors[Math.floor(Math.random() * colors.length)],
      tilt: Math.random() * 10
    });
  }

  let frames = 0;
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      p.x += p.dx;
      p.y += p.dy;
      p.dy += 0.35; // gravity
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();
    });
    frames++;
    if (frames < 60 && typeof requestAnimationFrame === 'function') {
      requestAnimationFrame(animate);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }
  try { animate(); } catch (e) {}
}

// =========================================================================
// 6. PARENT & EDUCATOR STUDIO (Lesson Builder & Chunk Editor)
// =========================================================================

// File upload handler for parent lesson builder
function parentHandleFileUpload(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    const content = e.target.result;
    const rawTextArea = document.getElementById('parent-raw-text');
    if (rawTextArea) {
      rawTextArea.value = content;
    }
    const titleInput = document.getElementById('parent-new-title');
    if (titleInput) {
      const cleanName = file.name.replace(/\.[^/.]+$/, '').replace(/[_|-]+/g, ' ');
      titleInput.value = cleanName;
    }
    parentAnalyzeAndPreview();
  };
  reader.readAsText(file, 'utf-8');
}

function parentAnalyzeAndPreview() {
  const rawText = document.getElementById('parent-raw-text').value.trim();
  if (!rawText) {
    alert("Please paste question and answer text to analyze.");
    return;
  }

  // Parse Q&A blocks
  const blocks = rawText.split(/\n\s*\n+/);
  const items = [];

  blocks.forEach(block => {
    const lines = block.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    if (lines.length >= 2) {
      const q = lines[0];
      const ans = lines.slice(1).join(' ');
      // Auto chunk by ~3 words
      const words = ans.split(/\s+/);
      const chunks = [];
      for (let i = 0; i < words.length; i += 3) {
        chunks.push(words.slice(i, i + 3).join(' '));
      }
      items.push({ question: q, chunks: chunks, meaning: '' });
    } else if (lines.length === 1 && lines[0].includes('|||')) {
      const parts = lines[0].split('|||').map(p => p.trim());
      if (parts.length > 1) {
        items.push({ question: parts[0], chunks: parts.slice(1), meaning: '' });
      }
    }
  });

  if (items.length === 0) {
    // Single line fallback
    const words = rawText.split(/\s+/);
    items.push({
      question: "Practice Sentence",
      chunks: [words.slice(0, 3).join(' '), words.slice(3).join(' ')].filter(c => c.length > 0),
      meaning: ''
    });
  }

  state.parent_preview_items = items;
  renderParentPreviewEditor();
}

function renderParentPreviewEditor() {
  const box = document.getElementById('parent-chunks-preview-box');
  const countEl = document.getElementById('preview-items-count');
  const list = document.getElementById('parent-preview-items-list');

  if (box) box.classList.remove('hidden');
  if (countEl) countEl.textContent = `${state.parent_preview_items.length} Question Items Generated`;
  if (!list) return;
  list.innerHTML = '';

  state.parent_preview_items.forEach((item, qIdx) => {
    const row = document.createElement('div');
    row.className = 'bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-3';

    const header = document.createElement('div');
    header.className = 'flex items-center justify-between';
    header.innerHTML = `
      <span class="text-xs font-bold text-slate-700">Question ${qIdx + 1}</span>
      <button onclick="parentRemovePreviewItem(${qIdx})" class="text-xs text-rose-500 hover:text-rose-700 font-semibold">✕ Remove</button>
    `;
    row.appendChild(header);

    const qInput = document.createElement('input');
    qInput.type = 'text';
    qInput.value = item.question;
    qInput.className = 'w-full text-xs font-bold p-2 bg-white border border-slate-200 rounded-xl font-hindi';
    row.appendChild(qInput);

    const chunksContainer = document.createElement('div');
    chunksContainer.className = 'space-y-1';
    chunksContainer.innerHTML = '<span class="text-[11px] font-semibold text-slate-500">Sentence Chunks (Drag or edit phrase chunks):</span>';

    const chunksRow = document.createElement('div');
    chunksRow.className = 'flex flex-wrap gap-1.5';
    chunksRow.id = `parent-chunks-row-${qIdx}`;

    item.chunks.forEach((chunk, cIdx) => {
      const chip = document.createElement('span');
      chip.className = 'inline-flex items-center gap-1.5 px-3 py-1 bg-white border border-indigo-200 text-indigo-900 rounded-xl text-xs font-hindi font-medium shadow-2xs chunk-tooltip-target cursor-help';
      
      const wordsCount = chunk.trim().split(/\s+/).length;
      let actionsHtml = '';
      if (wordsCount > 1) {
        actionsHtml += `<button onclick="parentSplitChunk(${qIdx}, ${cIdx})" class="text-[10px] text-slate-400 hover:text-indigo-600 transition" title="Split into individual words">✂️</button>`;
      }
      if (cIdx < item.chunks.length - 1) {
        actionsHtml += `<button onclick="parentMergeChunk(${qIdx}, ${cIdx})" class="text-[10px] text-slate-400 hover:text-indigo-600 transition" title="Merge with next phrase">🔗</button>`;
      }

      chip.innerHTML = `
        <span>${chunk}</span>
        ${actionsHtml}
      `;
      chip.dataset.chunkText = chunk;
      attachChunkHoverTooltip(chip, chunk);
      chunksRow.appendChild(chip);
    });

    chunksContainer.appendChild(chunksRow);
    row.appendChild(chunksContainer);
    list.appendChild(row);
  });
}

function parentUpdateQuestionText(qIdx, val) {
  if (state.parent_preview_items[qIdx]) {
    state.parent_preview_items[qIdx].question = val;
  }
}

function parentRemovePreviewItem(qIdx) {
  state.parent_preview_items.splice(qIdx, 1);
  renderParentPreviewEditor();
}

function parentSplitChunk(qIdx, cIdx) {
  const item = state.parent_preview_items[qIdx];
  if (!item) return;
  const chunk = item.chunks[cIdx];
  const words = chunk.split(/\s+/);
  if (words.length > 1) {
    item.chunks.splice(cIdx, 1, ...words);
    renderParentPreviewEditor();
  }
}

function parentMergeChunk(qIdx, cIdx) {
  const item = state.parent_preview_items[qIdx];
  if (!item || cIdx >= item.chunks.length - 1) return;
  const merged = item.chunks[cIdx] + ' ' + item.chunks[cIdx + 1];
  item.chunks.splice(cIdx, 2, merged);
  renderParentPreviewEditor();
}

async function parentSaveLesson() {
  const title = document.getElementById('parent-new-title').value.trim();
  const subject = document.getElementById('parent-new-subject').value;
  const items = state.parent_preview_items;

  if (!title) {
    alert("Please enter a Lesson or Chapter Title.");
    return;
  }
  if (!items || items.length === 0) {
    alert("No question items to save. Please parse text first.");
    return;
  }

  // Format into lesson text
  let rawContent = `=== ${title} ===\n`;
  items.forEach(it => {
    rawContent += `${it.question} ||| ${it.chunks.join(' ||| ')}\n`;
  });

  if (window.pywebview) {
    try {
      const deck = await window.pywebview.api.create_custom_lesson(title, subject, rawContent, ['#ParentCreated', `#${subject}`]);
      if (deck) {
        alert(`Success! "${title}" has been saved with ${items.length} questions!`);
        document.getElementById('parent-new-title').value = '';
        document.getElementById('parent-raw-text').value = '';
        document.getElementById('parent-chunks-preview-box').classList.add('hidden');
        state.parent_preview_items = [];
        await reloadAppState();
        renderParentHeatmap();
      }
    } catch (e) {
      alert("Error saving lesson: " + e);
    }
  } else {
    alert(`Demo Mode: Saved "${title}" with ${items.length} questions!`);
  }
}

function renderParentHeatmap() {
  const container = document.getElementById('parent-subjects-heatmap');
  if (!container) return;
  container.innerHTML = '';

  const ms = state.multi_subject_metrics || {};
  const subjects = ms.subjects || [];

  if (subjects.length === 0) {
    container.innerHTML = '<span class="text-xs text-slate-400">Loading subject data...</span>';
    return;
  }

  subjects.forEach(s => {
    const card = document.createElement('div');
    card.className = 'bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-3';

    card.innerHTML = `
      <div class="flex justify-between items-center">
        <div>
          <h4 class="text-sm font-bold text-slate-900">${s.subject}</h4>
          <span class="text-[11px] text-slate-500">${s.mastered_cards} of ${s.total_cards} Cards Mastered</span>
        </div>
        <span class="text-base font-black ${s.readiness_percent >= 80 ? 'text-emerald-600' : 'text-indigo-600'}">
          ${s.readiness_percent}%
        </span>
      </div>

      <div class="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden">
        <div class="h-full rounded-full transition-all duration-300 ${s.readiness_percent >= 80 ? 'bg-emerald-500' : 'bg-indigo-600'}" style="width: ${s.readiness_percent}%"></div>
      </div>

      <div class="divide-y divide-slate-100 text-xs pt-1">
        ${(s.decks || []).map(d => `
          <div class="py-1.5 flex justify-between items-center">
            <span class="font-medium text-slate-700 truncate max-w-[200px]">${d.title}</span>
            <span class="font-bold text-slate-500">${d.mastered_cards}/${d.total_cards} (${d.readiness_percent}%)</span>
          </div>
        `).join('')}
      </div>
    `;

    container.appendChild(card);
  });
}

// =========================================================================
// 7. PROFILE & EXAM MODALS
// =========================================================================

function showProfileModal() {
  const modal = document.getElementById('profile-modal');
  const list = document.getElementById('profiles-list');
  list.innerHTML = '';

  (state.profiles || ['Arya']).forEach(name => {
    const isAct = name === state.active_profile;
    const canDelete = !isAct && (state.profiles || []).length > 1;
    const item = document.createElement('div');
    item.className = `p-2.5 rounded-xl cursor-pointer text-xs font-bold flex justify-between items-center transition ${isAct ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-slate-100 text-slate-700'}`;
    item.innerHTML = `
      <div class="flex items-center gap-2">
        <span>👤</span>
        <span>${name}</span>
      </div>
      <div class="flex items-center gap-2">
        ${isAct ? '<span class="text-indigo-600 font-black">✓ Active</span>' : ''}
        ${canDelete ? `<button onclick="event.stopPropagation(); deleteProfile('${name}')" class="text-rose-400 hover:text-rose-600 p-1 hover:bg-rose-50 rounded-lg transition" title="Delete Profile">🗑</button>` : ''}
      </div>
    `;
    item.onclick = async () => {
      if (window.pywebview) {
        await window.pywebview.api.switch_profile(name);
        await reloadAppState();
      } else {
        state.active_profile = name;
      }
      initUI();
      closeProfileModal();
    };
    list.appendChild(item);
  });

  modal.classList.remove('hidden');
}

function closeProfileModal() {
  document.getElementById('profile-modal').classList.add('hidden');
}

async function deleteProfile(profileName) {
  if (!profileName) return;
  if (!confirm(`Are you sure you want to delete student profile "${profileName}" and all its progress?`)) {
    return;
  }
  if (window.pywebview && window.pywebview.api && window.pywebview.api.delete_profile) {
    const res = await window.pywebview.api.delete_profile(profileName);
    if (res) {
      Object.assign(state, res);
    } else {
      await reloadAppState();
    }
  } else {
    state.profiles = (state.profiles || []).filter(p => p !== profileName);
    if (state.active_profile === profileName) {
      state.active_profile = state.profiles[0] || 'Default';
    }
  }
  showProfileModal();
  initUI();
}

async function createProfile() {
  const input = document.getElementById('new-profile-name');
  const name = input.value.trim();
  if (!name) return;

  if (window.pywebview) {
    await window.pywebview.api.create_profile(name);
    await reloadAppState();
  } else {
    state.profiles.push(name);
    state.active_profile = name;
  }
  input.value = '';
  initUI();
  closeProfileModal();
}

let modalExamScope = {};

function openExamScopeModal(isNew = false) {
  const modal = document.getElementById('exam-scope-modal');
  const tree = document.getElementById('modal-exam-tree');
  tree.innerHTML = '';

  const em = state.exam_metrics || {};
  document.getElementById('modal-exam-name').value = isNew ? '' : (em.exam_name || 'Mid-Term Assessment');
  
  const defaultDate = new Date();
  defaultDate.setDate(defaultDate.getDate() + 14);
  document.getElementById('modal-exam-date').value = (isNew || !em.target_date) 
    ? defaultDate.toISOString().split('T')[0] 
    : em.target_date;

  modalExamScope = isNew ? {} : JSON.parse(JSON.stringify(em.selected_scope || {}));

  (state.decks || []).forEach(deck => {
    const deckBox = document.createElement('div');
    deckBox.className = 'p-3 bg-white border border-slate-200 rounded-xl space-y-2';

    const chSet = new Set(modalExamScope[deck.id] || []);

    deckBox.innerHTML = `
      <div class="flex items-center justify-between font-bold text-xs text-slate-800">
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" id="modal-deck-${deck.id}" onchange="toggleModalDeck('${deck.id}', this.checked)" class="rounded text-indigo-600">
          <span>${deck.title} (${deck.subject || 'General'})</span>
        </label>
      </div>
      <div class="pl-6 space-y-1" id="modal-deck-chaps-${deck.id}"></div>
    `;

    const chList = deckBox.querySelector(`#modal-deck-chaps-${deck.id}`);
    const chapters = getDeckUniqueChapters(deck);

    chapters.forEach(chName => {
      const isChecked = chSet.has(chName);
      const chRow = document.createElement('label');
      chRow.className = 'flex items-center justify-between text-xs text-slate-600 cursor-pointer hover:text-slate-900 py-0.5';
      chRow.innerHTML = `
        <span class="flex items-center gap-2">
          <input type="checkbox" value="${escapeAttr(chName)}" ${isChecked ? 'checked' : ''} onchange="toggleModalChapter('${deck.id}', '${escapeAttr(chName)}', this.checked)" class="rounded text-indigo-600">
          <span class="font-hindi">${chName}</span>
        </span>
      `;
      chList.appendChild(chRow);
    });

    tree.appendChild(deckBox);
  });

  updateModalExamSummary();
  modal.classList.remove('hidden');
}

function closeExamScopeModal() {
  document.getElementById('exam-scope-modal').classList.add('hidden');
}

function getDeckUniqueChapters(deck) {
  const set = new Set();
  (deck.cards || []).forEach(c => {
    set.add((c.lesson_name || '').trim() || deck.title);
  });
  return Array.from(set);
}

function toggleModalDeck(deckId, isChecked) {
  const deck = (state.decks || []).find(d => d.id === deckId);
  if (!deck) return;
  const chapters = getDeckUniqueChapters(deck);
  modalExamScope[deckId] = isChecked ? chapters : [];
  openExamScopeModal(false);
}

function toggleModalChapter(deckId, chName, isChecked) {
  if (!modalExamScope[deckId]) modalExamScope[deckId] = [];
  const idx = modalExamScope[deckId].indexOf(chName);
  if (isChecked && idx === -1) {
    modalExamScope[deckId].push(chName);
  } else if (!isChecked && idx !== -1) {
    modalExamScope[deckId].splice(idx, 1);
  }
  updateModalExamSummary();
}

function selectAllExamScope(selectAll) {
  (state.decks || []).forEach(deck => {
    modalExamScope[deck.id] = selectAll ? getDeckUniqueChapters(deck) : [];
  });
  openExamScopeModal(false);
}

function updateModalExamSummary() {
  let totalChaps = 0;
  let totalCards = 0;

  (state.decks || []).forEach(d => {
    const chList = modalExamScope[d.id] || [];
    totalChaps += chList.length;
    (d.cards || []).forEach(c => {
      const chName = (c.lesson_name || '').trim() || d.title;
      if (chList.includes(chName)) {
        totalCards++;
      }
    });
  });

  document.getElementById('modal-summary-chaps').textContent = totalChaps;
  document.getElementById('modal-summary-cards').textContent = totalCards;
  document.getElementById('modal-summary-quota').textContent = Math.ceil(totalCards / 14);
}

async function saveExamScopeConfig() {
  const name = document.getElementById('modal-exam-name').value.trim() || 'Exam Assessment';
  const targetDate = document.getElementById('modal-exam-date').value;
  const deckIds = Object.keys(modalExamScope).filter(dId => (modalExamScope[dId] || []).length > 0);

  if (window.pywebview) {
    const updated = await window.pywebview.api.configure_exam_scope(
      name,
      targetDate,
      0,
      deckIds,
      modalExamScope,
      state.exam_metrics?.id
    );
    if (updated) {
      state.exam_metrics = updated;
      await reloadAppState();
      initUI();
    }
  }
  closeExamScopeModal();
}

// -------------------------------------------------------------------------
// Utilities
// -------------------------------------------------------------------------

function escapeAttr(str) {
  return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// =========================================================================
// 8. SETTINGS & APP CONFIGURATION (Legacy SettingsDialog Parity)
// =========================================================================

function openSettingsModal() {
  const modal = document.getElementById('settings-modal');
  if (!modal) return;
  
  const s = state.settings || {};
  
  // Theme
  const themeSelect = document.getElementById('settings-theme-select');
  if (themeSelect) themeSelect.value = s.theme || 'pastel';

  // Font Size
  const fontSelect = document.getElementById('settings-font-size-select');
  if (fontSelect) fontSelect.value = s.font_size || 'normal';
  
  // Hover Meanings
  const hoverCheck = document.getElementById('settings-hover-check');
  if (hoverCheck) hoverCheck.checked = s.show_hover_meanings !== false;
  
  // Sound Effects
  const soundCheck = document.getElementById('settings-sound-check');
  if (soundCheck) soundCheck.checked = s.sound_enabled !== false;
  
  // TTS Playback Speed
  const ttsSelect = document.getElementById('settings-tts-rate-select');
  if (ttsSelect) ttsSelect.value = s.tts_speed_rate || '+0%';
  
  // Jigsaw words per block
  const jigsawSelect = document.getElementById('settings-jigsaw-words-select');
  if (jigsawSelect) jigsawSelect.value = String(s.jigsaw_words_per_block || 'auto');

  // Blanks count mode
  const blanksSelect = document.getElementById('settings-blanks-mode-select');
  if (blanksSelect) blanksSelect.value = String(s.fill_blanks_count_mode || 'auto');
  
  // Speed Run duration
  const speedSelect = document.getElementById('settings-speed-duration-select');
  if (speedSelect) speedSelect.value = String(s.speed_run_duration_seconds || 180);
  
  // AI Coach Enabled
  const aiCheck = document.getElementById('settings-ai-coach-check');
  if (aiCheck) aiCheck.checked = s.ai_coach_enabled !== false;
  
  // Ollama URL
  const ollamaUrlInput = document.getElementById('settings-ollama-url-input');
  if (ollamaUrlInput) ollamaUrlInput.value = s.ollama_url || 'http://127.0.0.1:11434';
  
  // Ollama Model
  const ollamaModelInput = document.getElementById('settings-ollama-model-input');
  if (ollamaModelInput) ollamaModelInput.value = s.ollama_model || 'gemma4:12b';
  
  // Ollama Status Label
  const statusEl = document.getElementById('settings-ollama-status');
  if (statusEl) {
    statusEl.textContent = '';
    statusEl.className = 'text-xs font-bold text-slate-500';
  }
  
  // Active student name in memory reset block
  const memStudent = document.getElementById('settings-active-profile-name');
  if (memStudent) memStudent.textContent = state.active_profile || 'Arya';
  
  modal.classList.remove('hidden');
}

function closeSettingsModal() {
  const modal = document.getElementById('settings-modal');
  if (modal) modal.classList.add('hidden');
}

async function saveSettingsFromModal() {
  const themeSelect = document.getElementById('settings-theme-select');
  const fontSelect = document.getElementById('settings-font-size-select');
  const hoverCheck = document.getElementById('settings-hover-check');
  const soundCheck = document.getElementById('settings-sound-check');
  const ttsSelect = document.getElementById('settings-tts-rate-select');
  const jigsawSelect = document.getElementById('settings-jigsaw-words-select');
  const blanksSelect = document.getElementById('settings-blanks-mode-select');
  const speedSelect = document.getElementById('settings-speed-duration-select');
  const aiCheck = document.getElementById('settings-ai-coach-check');
  const ollamaUrlInput = document.getElementById('settings-ollama-url-input');
  const ollamaModelInput = document.getElementById('settings-ollama-model-input');

  const newSettings = {
    theme: themeSelect ? themeSelect.value : 'pastel',
    font_size: fontSelect ? fontSelect.value : 'normal',
    show_hover_meanings: hoverCheck ? hoverCheck.checked : true,
    sound_enabled: soundCheck ? soundCheck.checked : true,
    tts_speed_rate: ttsSelect ? ttsSelect.value : '+0%',
    jigsaw_words_per_block: jigsawSelect ? jigsawSelect.value : 'auto',
    fill_blanks_count_mode: blanksSelect ? blanksSelect.value : 'auto',
    speed_run_duration_seconds: speedSelect ? parseInt(speedSelect.value, 10) || 180 : 180,
    ai_coach_enabled: aiCheck ? aiCheck.checked : true,
    ollama_url: ollamaUrlInput ? ollamaUrlInput.value.trim() || 'http://127.0.0.1:11434' : 'http://127.0.0.1:11434',
    ollama_model: ollamaModelInput ? ollamaModelInput.value.trim() || 'gemma4:12b' : 'gemma4:12b'
  };

  state.settings = Object.assign({}, state.settings, newSettings);
  applyTheme(newSettings.theme);
  applyFontSize(newSettings.font_size);

  if (window.pywebview && window.pywebview.api && window.pywebview.api.save_settings) {
    try {
      const res = await window.pywebview.api.save_settings(newSettings);
      if (res && res.settings) {
        state.settings = Object.assign({}, state.settings, res.settings);
      }
    } catch (e) {
      console.error('Error saving settings via bridge:', e);
    }
  }

  playSound('success');
  closeSettingsModal();
}

async function testOllamaFromSettings() {
  const urlInput = document.getElementById('settings-ollama-url-input');
  const statusEl = document.getElementById('settings-ollama-status');
  const url = urlInput ? urlInput.value.trim() : 'http://127.0.0.1:11434';

  if (statusEl) {
    statusEl.textContent = 'Testing Ollama... ⏳';
    statusEl.className = 'text-xs font-bold text-amber-600';
  }

  if (window.pywebview && window.pywebview.api && window.pywebview.api.test_ollama_connection) {
    try {
      const res = await window.pywebview.api.test_ollama_connection(url);
      if (statusEl) {
        if (res && res.connected) {
          statusEl.textContent = `🟢 Connected (${(res.models || []).length} models found)`;
          statusEl.className = 'text-xs font-bold text-emerald-600';
        } else {
          statusEl.textContent = '🔴 Offline (Start Ollama)';
          statusEl.className = 'text-xs font-bold text-rose-600';
        }
      }
    } catch (e) {
      if (statusEl) {
        statusEl.textContent = '🔴 Connection error';
        statusEl.className = 'text-xs font-bold text-rose-600';
      }
    }
  } else {
    // Browser mock fallback
    setTimeout(() => {
      if (statusEl) {
        statusEl.textContent = '🟢 Connected (Simulated)';
        statusEl.className = 'text-xs font-bold text-emerald-600';
      }
    }, 200);
  }
}

async function resetMemoryFromSettings() {
  const student = state.active_profile || 'Arya';
  if (!confirm(`Reset all spaced repetition memory progress for student "${student}"? This cannot be undone.`)) {
    return;
  }

  if (window.pywebview && window.pywebview.api && window.pywebview.api.reset_active_memory) {
    try {
      await window.pywebview.api.reset_active_memory();
      await reloadAppState();
      initUI();
      playSound('success');
      alert(`Memory progress for ${student} has been reset!`);
    } catch (e) {
      console.error('Error resetting memory:', e);
    }
  } else {
    playSound('success');
    alert(`Memory progress for ${student} has been reset (Simulated)!`);
  }
}

// =========================================================================
// 9. KEYBOARD SHORTCUTS MODAL
// =========================================================================

function openShortcutsModal() {
  const modal = document.getElementById('shortcuts-modal');
  if (modal) modal.classList.remove('hidden');
}

function closeShortcutsModal() {
  const modal = document.getElementById('shortcuts-modal');
  if (modal) modal.classList.add('hidden');
}

// =========================================================================
// 10. PRINTABLE WORKSHEET GENERATOR (Legacy main_window.py Parity)
// =========================================================================

function openWorksheetModal(deckId, chapterName) {
  const modal = document.getElementById('worksheet-modal');
  if (!modal) return;

  const deckSelect = document.getElementById('worksheet-deck-select');
  if (deckSelect) {
    deckSelect.innerHTML = '';
    (state.decks || []).forEach(d => {
      const opt = document.createElement('option');
      opt.value = d.id;
      opt.textContent = `${d.title} (${d.subject || 'General'})`;
      if (deckId && d.id === deckId) opt.selected = true;
      deckSelect.appendChild(opt);
    });
  }

  onWorksheetDeckChanged(chapterName);
  modal.classList.remove('hidden');
}

function closeWorksheetModal() {
  const modal = document.getElementById('worksheet-modal');
  if (modal) modal.classList.add('hidden');
}

function onWorksheetDeckChanged(selectedChapterName) {
  const deckSelect = document.getElementById('worksheet-deck-select');
  const chapterSelect = document.getElementById('worksheet-chapter-select');
  if (!deckSelect || !chapterSelect) return;

  const deckId = deckSelect.value;
  const deck = (state.decks || []).find(d => d.id === deckId);
  chapterSelect.innerHTML = '';

  const allOpt = document.createElement('option');
  allOpt.value = 'All';
  allOpt.textContent = '⭐ Entire Deck (All Chapters)';
  chapterSelect.appendChild(allOpt);

  if (deck) {
    const chapters = new Set();
    (deck.cards || []).forEach(c => {
      const ch = (c.lesson_name || '').trim();
      if (ch) chapters.add(ch);
    });
    chapters.forEach(ch => {
      const opt = document.createElement('option');
      opt.value = ch;
      opt.textContent = ch;
      if (selectedChapterName && ch === selectedChapterName) opt.selected = true;
      chapterSelect.appendChild(opt);
    });
  }
}

async function generateWorksheetFromModal() {
  const deckSelect = document.getElementById('worksheet-deck-select');
  const chapterSelect = document.getElementById('worksheet-chapter-select');
  const deckId = deckSelect ? deckSelect.value : null;
  const chapterName = chapterSelect ? chapterSelect.value : 'All';

  if (!deckId) return;
  closeWorksheetModal();
  await printWorksheet(deckId, chapterName);
}

function printCurrentChapterWorksheet() {
  if (state.currentChapter) {
    printWorksheet(state.currentChapter.deckId, state.currentChapter.chapterTitle);
  } else {
    openWorksheetModal();
  }
}

async function printWorksheet(deckId, chapterName) {
  if (!deckId) return;

  let htmlContent = '';
  if (window.pywebview && window.pywebview.api && window.pywebview.api.generate_printable_worksheet) {
    try {
      htmlContent = await window.pywebview.api.generate_printable_worksheet(deckId, chapterName);
    } catch (e) {
      console.error('Error generating printable worksheet via bridge:', e);
    }
  }

  if (!htmlContent) {
    // Generate standalone fallback worksheet HTML
    const deck = (state.decks || []).find(d => d.id === deckId);
    if (!deck) return;
    let cards = deck.cards || [];
    if (chapterName && chapterName !== 'All') {
      cards = cards.filter(c => (c.lesson_name || '').trim() === chapterName.trim());
    }
    const title = `${deck.title} - ${chapterName || 'Practice Worksheet'}`;
    let itemsHtml = '';
    cards.forEach((c, idx) => {
      const q = c.question;
      const chunks = [...(c.chunks || [])];
      for (let i = chunks.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [chunks[i], chunks[j]] = [chunks[j], chunks[i]];
      }
      const boxes = chunks.map(chunk => `
        <div style="border: 2px solid #64748b; border-radius: 8px; padding: 10px 14px; font-size: 15px; font-weight: 600; text-align: center; background-color: #fff; min-width: 70px;">
          <div>${chunk}</div>
          <div style="margin-top: 10px; border: 2px dashed #94a3b8; height: 32px; width: 40px; margin-left: auto; margin-right: auto; background-color: #f8fafc; border-radius: 4px;"></div>
        </div>
      `).join('');
      itemsHtml += `
        <div style="margin-bottom: 28px; page-break-inside: avoid; border-bottom: 1px dashed #e2e8f0; padding-bottom: 18px;">
          <div style="font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 10px;">
            <span style="color: #4f46e5; font-weight: 800;">Q${idx + 1}.</span> ${q}
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 14px;">${boxes}</div>
        </div>
      `;
    });
    htmlContent = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>${title}</title><style>body{font-family:Arial,sans-serif;margin:30px;color:#1e293b;}h1{text-align:center;font-size:22px;margin-bottom:6px;}.sub{text-align:center;font-size:13px;color:#64748b;margin-bottom:24px;}.inst{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;font-size:13px;margin-bottom:24px;}@media print{body{margin:10mm;}.no-print{display:none;}}</style></head><body><div class="no-print" style="margin-bottom:20px;text-align:right;"><button onclick="window.print()" style="background:#4f46e5;color:white;border:none;padding:8px 16px;border-radius:8px;font-weight:bold;cursor:pointer;">Print Worksheet 🖨️</button></div><h1>${title}</h1><div class="sub">Student Name: _______________________ &nbsp;&bull;&nbsp; Date: ______________</div><div class="inst"><strong>📝 Instructions:</strong> The words in each sentence below are scrambled. Write 1, 2, 3... in the boxes to put them in the correct order!</div>${itemsHtml}</body></html>`;
  }

  // Open worksheet in a new printable window
  if (typeof window !== 'undefined' && typeof window.open === 'function') {
    const printWin = window.open('', '_blank');
    if (printWin && printWin.document) {
      printWin.document.open();
      printWin.document.write(htmlContent);
      printWin.document.close();
      printWin.focus();
    }
  }
}

if (typeof window !== 'undefined') {
  window.setJigsawWordsPerBlock = setJigsawWordsPerBlock;
  window.computeDynamicChunks = computeDynamicChunks;
  window.getEffectiveWordsPerBlock = getEffectiveWordsPerBlock;
  window.insertChunkFromTray = insertChunkFromTray;
  window.movePlacedChunk = movePlacedChunk;
  window.swapPlacedChunks = swapPlacedChunks;
  window.swapTrayChunkWithBoard = swapTrayChunkWithBoard;
  window.setActiveInsertIndex = setActiveInsertIndex;
  window.ensureMicrophonePermission = ensureMicrophonePermission;
}

