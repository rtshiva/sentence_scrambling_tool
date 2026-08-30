THEMES = {
    'pastel': {
        'app_bg': '#f8f9fa',
        'card_bg': '#ffffff',
        'board_bg_default': '#f0f8ff',
        'board_bg_correct': '#e6ffe6',
        'board_bg_incorrect': '#ffe6e6',
        'text_primary': '#2c3e50',
        'text_secondary': '#7f8c8d',
        'text_correct': '#1e8449',
        'text_incorrect': '#c0392b',
        'button_disabled': '#e0e0e0',
        'chip_bg': '#d4efdf',
        'chip_border': '#27ae60',
        'blank_bg': '#fcf3cf',
        'blank_border': '#f39c12',
        'drop_highlight': '#f9e79f',
        'tile_colors': ['#ffb3ba', '#ffdfba', '#ffffba', '#baffc9', '#bae1ff', '#e8baff']
    },
    'dark': {
        'app_bg': '#181825',
        'card_bg': '#1e1e2e',
        'board_bg_default': '#313244',
        'board_bg_correct': '#2d4f3e',
        'board_bg_incorrect': '#582b35',
        'text_primary': '#cdd6f4',
        'text_secondary': '#a6adc8',
        'text_correct': '#a6e3a1',
        'text_incorrect': '#f38ba8',
        'button_disabled': '#45475a',
        'chip_bg': '#45475a',
        'chip_border': '#a6e3a1',
        'blank_bg': '#585b70',
        'blank_border': '#f9e2af',
        'drop_highlight': '#fab387',
        'tile_colors': ['#f38ba8', '#fab387', '#f9e2af', '#a6e3a1', '#89dceb', '#cba6f7']
    },
    'space': {
        'app_bg': '#0b0f19',
        'card_bg': '#111827',
        'board_bg_default': '#1f2937',
        'board_bg_correct': '#064e3b',
        'board_bg_incorrect': '#7f1d1d',
        'text_primary': '#f3f4f6',
        'text_secondary': '#9ca3af',
        'text_correct': '#34d399',
        'text_incorrect': '#f87171',
        'button_disabled': '#374151',
        'chip_bg': '#374151',
        'chip_border': '#38bdf8',
        'blank_bg': '#4b5563',
        'blank_border': '#fbbf24',
        'drop_highlight': '#38bdf8',
        'tile_colors': ['#f43f5e', '#fb923c', '#facc15', '#4ade80', '#38bdf8', '#c084fc']
    }
}

THEME = THEMES['pastel']

PASTEL_COLORS = THEMES['pastel']['tile_colors']
ENCOURAGEMENTS = ['Awesome!', 'Great Job!', 'Super!', 'Fantastic!', 'Well Done!', 'Brilliant!']
AVATAR_OPTIONS = ['🦁', '🚀', '🐼', '🎨', '🦊', '⭐', '🦉', '🦄', '🐱', '🐶', '⚽', '👑']

def get_theme(theme_name: str) -> dict:
    return THEMES.get(theme_name, THEMES['pastel'])
