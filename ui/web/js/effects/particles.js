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
  mobs: [],
  nextMobSpawn: 0,
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
    this.mobs = [];
    this.nextMobSpawn = 0;
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

    // 2. Minecraft mob walkers — random background appearances
    const nowMs = timestamp || Date.now();
    if (!this.nextMobSpawn) this.nextMobSpawn = nowMs + 1200;
    if (nowMs >= this.nextMobSpawn) {
      if (this.mobs.length < 4) this.spawnMob();
      this.nextMobSpawn = nowMs + 3500 + Math.random() * 5500;
    }
    this.updateAndDrawMobs();
  },

  groundY() {
    return (this.height || 800) - 44;
  },

  spawnMob() {
    const types = ['creeper', 'steve', 'enderman', 'pig', 'zombie', 'ghast'];
    const type = types[Math.floor(Math.random() * types.length)];
    const flying = type === 'ghast';
    const fromLeft = Math.random() < 0.5;
    const u = Math.random() * 0.9 + 1.8; // pixel unit 1.8–2.7px
    this.mobs.push({
      type,
      flying,
      x: fromLeft ? -60 : (this.width || 1280) + 60,
      dir: fromLeft ? 1 : -1,
      speed: (Math.random() * 0.5 + 0.45) * (flying ? 0.7 : 1),
      u,
      walkPhase: Math.random() * Math.PI * 2,
      bobPhase: Math.random() * Math.PI * 2,
      yOff: flying ? 0 : Math.random() * 10,
      alpha: Math.random() * 0.15 + 0.85
    });
  },

  updateAndDrawMobs() {
    if (!this.ctx || !this.canvas) return;
    const gy = this.groundY();

    // Nether ground strip
    if (typeof this.ctx.save === 'function') {
      this.ctx.save();
      this.ctx.globalAlpha = 0.55;
      this.ctx.fillStyle = '#170903';
      this.ctx.fillRect(0, gy + 14, this.width, this.height - gy);
      this.ctx.globalAlpha = 0.8;
      this.ctx.fillStyle = '#7c2d12';
      this.ctx.fillRect(0, gy + 14, this.width, 2);
      this.ctx.restore();
    }

    for (let i = this.mobs.length - 1; i >= 0; i--) {
      const m = this.mobs[i];
      m.walkPhase += 0.09;
      m.bobPhase += 0.05;
      m.x += m.speed * m.dir + this.mouseX * 0.1;

      if ((m.dir > 0 && m.x > this.width + 80) || (m.dir < 0 && m.x < -80)) {
        this.mobs.splice(i, 1);
        continue;
      }

      const feetY = m.flying
        ? this.height * 0.28 + Math.sin(m.bobPhase) * 12
        : gy + 14 + m.yOff;
      this.drawMob(m, feetY);
    }
  },

  drawMob(m, feetY) {
    const ctx = this.ctx;
    const u = m.u;
    const frame = Math.floor(m.walkPhase / Math.PI) % 2 === 0 ? 1 : -1; // 2-frame stride
    ctx.save();
    ctx.globalAlpha = m.alpha;

    // Soft shadow under walkers
    if (!m.flying) {
      ctx.fillStyle = 'rgba(0,0,0,0.35)';
      ctx.beginPath();
      ctx.ellipse(m.x, feetY + 2, 14 * u / 2, 3.5, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    const R = (dx, dy, w, h, c) => {
      ctx.fillStyle = c;
      // mirror horizontal pixels when facing left so faces lead the walk
      const mx = m.dir > 0 ? dx : (-dx - w);
      ctx.fillRect(m.x + mx * u, feetY + dy * u, w * u, h * u);
    };

    if (m.type === 'creeper') {
      const g = '#4caf50', gd = '#357a38', dk = '#111111';
      R(-3, -14, 6, 5, g);            // head
      R(-3, -14, 6, 1, gd);
      R(-2, -13, 1, 2, dk);           // eyes
      R(1, -13, 1, 2, dk);
      R(-1, -12, 2, 1, dk);           // mouth top
      R(-1, -11, 2, 2, dk);           // mouth stem
      R(-2, -10, 1, 1, dk);
      R(1, -10, 1, 1, dk);
      R(-2, -9, 4, 5, g);             // body
      R(-2, -9, 4, 1, gd);
      const l = frame > 0 ? 0 : -1;   // waddle legs
      R(-2, -4 + l, 1.8, 4 - l, gd);
      R(0.2, -4 - l, 1.8, 4 + l, g);
    } else if (m.type === 'steve') {
      const skin = '#e0ac69', hair = '#3b2a1a', shirt = '#00a8a8', pants = '#2b3a9e';
      R(-3, -17, 6, 1.5, hair);       // hair
      R(-3, -15.5, 6, 3.5, skin);     // face
      R(-2, -14.5, 1, 1, '#ffffff');
      R(1, -14.5, 1, 1, '#ffffff');
      R(-2, -14.5, 1, 1, '#3b3bbf');
      R(1, -14.5, 1, 1, '#3b3bbf');
      R(-3, -12, 6, 5, shirt);        // torso
      R(-3, -12, 6, 1, '#008080');
      R(-4, -12, 1, 4, shirt);        // arms
      R(3, -12, 1, 4, shirt);
      R(-4, -8, 1, 2, skin);
      R(3, -8, 1, 2, skin);
      const l = frame > 0 ? 0 : -1.2; // stride legs
      R(-2.6, -7 + l, 2.2, 7 - l, pants);
      R(0.4, -7 - l, 2.2, 7 + l, '#1e2a7a');
      R(-2.6, -0.8 + l, 2.2, 0.8, '#5b5b5b');
      R(0.4, -0.8 - l, 2.2, 0.8, '#5b5b5b');
    } else if (m.type === 'enderman') {
      const b = '#0d0d12', eye = '#e08ae0';
      R(-2.5, -21, 5, 4, b);          // head
      R(-2, -19.5, 4, 1, eye);        // glowing eyes
      R(-2, -17, 4, 6, b);            // torso
      R(-3.4, -17, 1.2, 7, b);        // long arms
      R(2.2, -17, 1.2, 7, b);
      const l = frame > 0 ? 0 : -1.2;
      R(-2, -11 + l, 1.7, 11 - l, b); // long legs
      R(0.3, -11 - l, 1.7, 11 + l, '#1a1a22');
    } else if (m.type === 'pig') {
      const p = '#f4a7b9', pd = '#e58aa0', sn = '#d9758f';
      R(-4, -9, 7, 4.5, p);           // body
      R(-4, -9, 7, 1, pd);
      R(1.5, -12, 4, 4, p);           // head (faces walk dir via mirror)
      R(1.5, -12, 4, 1, pd);
      R(2.2, -11, 1, 1, '#222222');   // eye
      R(2.6, -10, 1.6, 1.4, sn);      // snout
      R(-3.5, -14.5, 1.4, 2.5, p);    // ears
      const l = frame > 0 ? 0 : -1;   // trotter legs
      R(-3.4, -4.5 + l, 1.5, 4.5 - l, pd);
      R(-0.6, -4.5 - l, 1.5, 4.5 + l, p);
      R(1.6, -4.5 + l, 1.5, 4.5 - l, p);
    } else if (m.type === 'zombie') {
      const skin = '#5da87a', shirt = '#2a7a9e', pants = '#3b3b6e';
      R(-3, -17, 6, 1.2, '#3f6b4f');
      R(-3, -15.8, 6, 3.8, skin);
      R(-2, -14.8, 1, 1, '#123312');
      R(1, -14.8, 1, 1, '#123312');
      R(-3, -12, 6, 5, shirt);
      R(-4.5, -12, 1.2, 5, skin);     // outstretched arms
      R(3.3, -12, 1.2, 5, skin);
      const l = frame > 0 ? 0 : -1.2; // shamble legs
      R(-2.6, -7 + l, 2.2, 7 - l, pants);
      R(0.4, -7 - l, 2.2, 7 + l, '#2c2c55');
    } else if (m.type === 'ghast') {
      const w = '#f2ede4', fd = '#d8d0c0';
      const bobY = feetY;
      R(-4, -6, 8, 7, w);             // floating cube body
      R(-4, -6, 8, 1, fd);
      R(-2.5, -4, 1.4, 1, '#3a3a3a'); // closed sad eyes
      R(1.1, -4, 1.4, 1, '#3a3a3a');
      R(-1, -2, 2, 1.6, '#3a3a3a');   // mouth
      for (let t = -3; t <= 3; t += 1.5) { // dangling tentacles
        const sway = Math.sin(m.walkPhase * 1.4 + t) * 0.8;
        R(t - 0.4 + sway * 0.3, 1, 0.9, 3 + ((t * 7) % 2), fd);
      }
      void bobY;
    }

    ctx.restore();
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
  walkers: [],
  crow: null,
  nextWalkerSpawn: 0,
  nextCrowSpawn: 0,
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
    this.walkers = [];
    this.crow = null;
    this.nextWalkerSpawn = 0;
    this.nextCrowSpawn = 0;
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

    // 0. Demon Slayer corps walkers + Kasugai crow (random background appearances)
    const nowWalk = timestamp || Date.now();
    if (!this.nextWalkerSpawn) this.nextWalkerSpawn = nowWalk + 1500;
    if (nowWalk >= this.nextWalkerSpawn) {
      if (this.walkers.length < 3) this.spawnWalker();
      this.nextWalkerSpawn = nowWalk + 4000 + Math.random() * 5000;
    }
    if (!this.nextCrowSpawn) this.nextCrowSpawn = nowWalk + 6000;
    if (nowWalk >= this.nextCrowSpawn) {
      if (!this.crow) this.spawnCrow();
      this.nextCrowSpawn = nowWalk + 9000 + Math.random() * 9000;
    }
    this.updateAndDrawWalkers();

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
  },

  walkerGroundY() {
    return (this.height || 800) - 40;
  },

  spawnWalker() {
    const chars = ['tanjiro', 'nezuko', 'zenitsu', 'inosuke'];
    const char = chars[Math.floor(Math.random() * chars.length)];
    const fromLeft = Math.random() < 0.5;
    this.walkers.push({
      char,
      x: fromLeft ? -70 : (this.width || 1280) + 70,
      dir: fromLeft ? 1 : -1,
      speed: Math.random() * 0.5 + 0.5,
      scale: Math.random() * 0.25 + 0.9,
      walkPhase: Math.random() * Math.PI * 2,
      yOff: Math.random() * 8,
      alpha: Math.random() * 0.12 + 0.88
    });
  },

  spawnCrow() {
    const fromLeft = Math.random() < 0.5;
    this.crow = {
      x: fromLeft ? -50 : (this.width || 1280) + 50,
      dir: fromLeft ? 1 : -1,
      y: (this.height || 800) * (Math.random() * 0.2 + 0.12),
      speed: Math.random() * 1.2 + 1.6,
      flapPhase: 0,
      bobPhase: Math.random() * Math.PI * 2
    };
  },

  updateAndDrawWalkers() {
    if (!this.ctx || !this.canvas) return;
    const gy = this.walkerGroundY();

    // Moonlit training-ground strip
    if (typeof this.ctx.save === 'function') {
      this.ctx.save();
      this.ctx.globalAlpha = 0.5;
      this.ctx.fillStyle = '#0d1526';
      this.ctx.fillRect(0, gy + 16, this.width, this.height - gy);
      this.ctx.globalAlpha = 0.75;
      this.ctx.fillStyle = '#274060';
      this.ctx.fillRect(0, gy + 16, this.width, 2);
      this.ctx.restore();
    }

    for (let i = this.walkers.length - 1; i >= 0; i--) {
      const w = this.walkers[i];
      w.walkPhase += 0.1;
      w.x += w.speed * w.dir + this.mouseX * 0.08;
      if ((w.dir > 0 && w.x > this.width + 90) || (w.dir < 0 && w.x < -90)) {
        this.walkers.splice(i, 1);
        continue;
      }
      this.drawWalker(w, gy + 16 + w.yOff);
    }

    // Kasugai crow messenger overhead
    if (this.crow) {
      const c = this.crow;
      c.flapPhase += 0.35;
      c.bobPhase += 0.04;
      c.x += c.speed * c.dir;
      c.y += Math.sin(c.bobPhase) * 0.5;
      if ((c.dir > 0 && c.x > this.width + 60) || (c.dir < 0 && c.x < -60)) {
        this.crow = null;
      } else {
        this.drawCrow(c);
      }
    }
  },

  drawWalker(w, feetY) {
    const ctx = this.ctx;
    const s = w.scale;
    const step = Math.floor(w.walkPhase / Math.PI) % 2 === 0 ? 1 : -1;
    const bounce = Math.abs(Math.sin(w.walkPhase)) * 1.5;
    ctx.save();
    ctx.globalAlpha = w.alpha;

    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.beginPath();
    ctx.ellipse(w.x, feetY + 2, 11 * s, 3, 0, 0, Math.PI * 2);
    ctx.fill();

    const R = (dx, dy, ww, hh, c) => {
      ctx.fillStyle = c;
      const mx = w.dir > 0 ? dx : (-dx - ww);
      ctx.fillRect(w.x + mx * s, feetY + (dy - bounce * 0.15) * s, ww * s, hh * s);
    };
    const C = (dx, dy, r, c) => {
      ctx.fillStyle = c;
      ctx.beginPath();
      ctx.arc(w.x + dx * s, feetY + (dy - bounce * 0.15) * s, r * s, 0, Math.PI * 2);
      ctx.fill();
    };

    const skin = '#ffd9b3', dark = '#1f2430';
    // Striding legs (black tabi / pants)
    const l = step > 0 ? 0 : -2;
    R(-5, -10 + l, 4, 10 - l, dark);
    R(1, -10 - l, 4, 10 + l, '#2b3242');
    R(-5, -2.4 + l, 4, 2.4, '#e8e8e8');
    R(1, -2.4 - l, 4, 2.4, '#e8e8e8');

    if (w.char === 'tanjiro') {
      R(-7, -30, 14, 20, '#2d6a4f');      // green haori
      for (let cx = -7; cx < 7; cx += 3.5) // black ichimatsu checks
        for (let cy = -30; cy < -10; cy += 4) R(cx, cy, 1.8, 2, '#101418');
      R(-5, -46, 10, 3, '#7a2b2b');       // burgundy hair base
      C(0, -38, 8, skin);                 // face
      R(-8, -46, 16, 6, '#7a2b2b');       // hair cap
      R(-8, -41, 16, 2, '#5c1f1f');
      R(-4.5, -39, 2, 2.6, '#222222');    // determined eyes
      R(2.5, -39, 2, 2.6, '#222222');
      R(-5.5, -40, 1.2, 1.2, '#c0392b');  // forehead scar
      C(-8.5, -36, 1.4, '#c0392b');       // hanafuda earrings
      C(8.5, -36, 1.4, '#27ae60');
      R(4, -28, 7, 1.6, '#5b3a1e');       // sword hilt at hip
      R(8, -34, 1.8, 7, '#8e2323');       // nichirin blade hint
    } else if (w.char === 'nezuko') {
      R(-6, -28, 12, 18, '#f5a3c0');      // pink kimono
      R(-6, -28, 12, 2.5, '#f7c6d9');
      C(-3, -22, 1.1, '#ffffff');         // hemp-leaf dots
      C(3, -18, 1.1, '#ffffff');
      C(-3, -14, 1.1, '#ffffff');
      R(-6, -18, 12, 3, '#e07b39');       // orange obi
      C(0, -36, 7.5, skin);               // face
      R(-7.5, -50, 15, 15, '#1c1c22');    // long dark hair
      R(-7.5, -38, 15, 6, '#e07b39');     // orange hair tips
      R(-5, -36, 10, 2.6, '#4caf50');     // bamboo muzzle
      R(-5, -36, 10, 0.8, '#388e3c');
      C(-3.4, -40, 1.3, '#5b3a5e');       // pink demon eyes
      C(3.4, -40, 1.3, '#5b3a5e');
    } else if (w.char === 'zenitsu') {
      R(-7, -30, 14, 20, '#f2b705');      // yellow haori
      R(-5, -28, 3, 3, '#ffffff');        // white triangles
      R(2, -24, 3, 3, '#ffffff');
      R(-5, -18, 3, 3, '#ffffff');
      R(2, -14, 3, 3, '#ffffff');
      C(0, -38, 8, skin);
      R(-8, -47, 16, 7, '#f7c948');       // blonde spiky hair
      R(-8, -47, 3, 4, '#e0a92e');
      R(-1, -47, 3, 5, '#e0a92e');
      R(5, -47, 3, 4, '#e0a92e');
      R(-4.5, -38.5, 2.4, 1.2, '#222222'); // >_< scared eyes
      R(2.1, -38.5, 2.4, 1.2, '#222222');
      R(4, -28, 7, 1.6, '#5b3a1e');       // sword hilt
      R(8, -34, 1.8, 7, '#d9d9d9');
    } else if (w.char === 'inosuke') {
      R(-7, -24, 14, 8, '#8fa3b8');       // boar-mask head mass
      C(0, -30, 8, '#9fb2c6');            // mask dome
      R(-3, -31, 2.4, 2.4, '#f5d020');    // mask eyes
      R(0.6, -31, 2.4, 2.4, '#f5d020');
      R(-2.5, -27.5, 5, 3, '#7d92a8');    // snout
      R(-4.5, -26, 1.4, 3, '#f2f2f2');    // tusks
      R(3.1, -26, 1.4, 3, '#f2f2f2');
      R(-6, -22, 12, 12, skin);           // bare muscular torso
      R(-6, -22, 12, 2, '#eab88f');
      R(-3, -20, 1.5, 8, '#eab88f');      // pec lines
      R(1.5, -20, 1.5, 8, '#eab88f');
      R(-6, -12, 12, 3, '#6b4a2f');       // fur belt
      R(-6, -12, 12, 1, '#8a6238');
      R(-8, -30, 2, 10, '#c0c8d0');       // dual serrated swords on back
      R(6, -30, 2, 10, '#c0c8d0');
    }

    ctx.restore();
  },

  drawCrow(c) {
    const ctx = this.ctx;
    ctx.save();
    ctx.globalAlpha = 0.92;
    const flap = Math.sin(c.flapPhase) * 0.9;
    ctx.translate(c.x, c.y);
    ctx.scale(c.dir, 1);
    ctx.fillStyle = '#14141c';
    ctx.beginPath();                      // body
    ctx.ellipse(0, 0, 9, 5.5, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();                      // head
    ctx.arc(8, -3, 4.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#f39c12';            // beak
    ctx.beginPath();
    ctx.moveTo(12, -4);
    ctx.lineTo(16, -2.5);
    ctx.lineTo(12, -1);
    ctx.fill();
    ctx.fillStyle = '#ffffff';            // eye
    ctx.beginPath();
    ctx.arc(9, -3.5, 1.1, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#1e1e28';            // flapping wing
    ctx.save();
    ctx.translate(-1, -2);
    ctx.rotate(-0.5 - flap * 0.55);
    ctx.beginPath();
    ctx.ellipse(-6, 0, 9, 3.4, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    ctx.fillStyle = '#1e1e28';            // tail feathers
    ctx.fillRect(-14, -1.5, 6, 3);
    ctx.restore();
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

if (typeof globalThis !== 'undefined') {
  globalThis.spaceUniverseEngine = spaceUniverseEngine;
  globalThis.lavaUniverseEngine = lavaUniverseEngine;
  globalThis.animeUniverseEngine = animeUniverseEngine;
  globalThis.skyUniverseEngine = skyUniverseEngine;
  globalThis.oceanUniverseEngine = oceanUniverseEngine;
  globalThis.sakuraUniverseEngine = sakuraUniverseEngine;
  globalThis.fairyUniverseEngine = fairyUniverseEngine;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    spaceUniverseEngine,
    lavaUniverseEngine,
    animeUniverseEngine,
    skyUniverseEngine,
    oceanUniverseEngine,
    sakuraUniverseEngine,
    fairyUniverseEngine
  };
}
