THEMES = {
    'pastel': {
        'app_bg': '#f8fafc',
        'card_bg': '#ffffff',
        'board_bg_default': '#f1f5f9',
        'board_bg_correct': '#ecfdf5',
        'board_bg_incorrect': '#fff1f2',
        'text_primary': '#0f172a',
        'text_secondary': '#64748b',
        'text_correct': '#059669',
        'text_incorrect': '#e11d48',
        'button_disabled': '#e2e8f0',
        'chip_bg': '#e0f2fe',
        'chip_border': '#0284c7',
        'blank_bg': '#fef3c7',
        'blank_border': '#d97706',
        'drop_highlight': '#fef08a',
        'tile_colors': ['#e0f2fe', '#fef3c7', '#dcfce7', '#fce7f3', '#f3e8ff', '#ffedd5']
    },
    'dark': {
        'app_bg': '#0f172a',
        'card_bg': '#1e293b',
        'board_bg_default': '#1e293b',
        'board_bg_correct': '#064e3b',
        'board_bg_incorrect': '#4c0519',
        'text_primary': '#f8fafc',
        'text_secondary': '#94a3b8',
        'text_correct': '#34d399',
        'text_incorrect': '#fb7185',
        'button_disabled': '#334155',
        'chip_bg': '#334155',
        'chip_border': '#38bdf8',
        'blank_bg': '#475569',
        'blank_border': '#fbbf24',
        'drop_highlight': '#38bdf8',
        'tile_colors': ['#fda4af', '#fdba74', '#fde047', '#86efac', '#7dd3fc', '#d8b4fe']
    },
    'space': {
        'app_bg': '#030712',
        'card_bg': '#111827',
        'board_bg_default': '#111827',
        'board_bg_correct': '#064e3b',
        'board_bg_incorrect': '#4c0519',
        'text_primary': '#f9fafb',
        'text_secondary': '#9ca3af',
        'text_correct': '#34d399',
        'text_incorrect': '#f87171',
        'button_disabled': '#1f2937',
        'chip_bg': '#1f2937',
        'chip_border': '#38bdf8',
        'blank_bg': '#374151',
        'blank_border': '#fbbf24',
        'drop_highlight': '#38bdf8',
        'tile_colors': ['#fb7185', '#fb923c', '#facc15', '#4ade80', '#38bdf8', '#c084fc']
    }
}

THEME = THEMES['pastel']

PASTEL_COLORS = THEMES['pastel']['tile_colors']
ENCOURAGEMENTS = ['Awesome!', 'Great Job!', 'Super!', 'Fantastic!', 'Well Done!', 'Brilliant!']
AVATAR_OPTIONS = ['🦁', '🚀', '🐼', '🎨', '🦊', '⭐', '🦉', '🦄', '🐱', '🐶', '⚽', '👑']

def get_theme(theme_name: str) -> dict:
    return THEMES.get(theme_name, THEMES['pastel'])
