import { defineStore } from 'pinia'

export type ThemeName = 'Obsidian' | 'Arctic' | 'Sakura' | 'Twilight' | 'Ember' | 'Ocean' | 'Crimson' | 'Sunflower'
export type ColorMode = 'light' | 'dark' | 'auto'
export type Density = 'Compact' | 'Comfort' | 'Spacious'
export type Radius = 'Sharp' | 'Default' | 'Rounded'
export type FontSize = 'S' | 'M' | 'L'

export const useUiStore = defineStore('ui', {
  state: () => ({
    theme: (localStorage.getItem('ui_theme') as ThemeName) || 'Obsidian',
    colorMode: (localStorage.getItem('ui_colorMode') as ColorMode) || 'auto',
    density: (localStorage.getItem('ui_density') as Density) || 'Comfort',
    radius: (localStorage.getItem('ui_radius') as Radius) || 'Default',
    fontSize: (localStorage.getItem('ui_fontSize') as FontSize) || 'M',
    animations: localStorage.getItem('ui_animations') !== 'false' // true by default
  }),
  actions: {
    applyAll() {
      localStorage.setItem('ui_theme', this.theme)
      localStorage.setItem('ui_colorMode', this.colorMode)
      localStorage.setItem('ui_density', this.density)
      localStorage.setItem('ui_radius', this.radius)
      localStorage.setItem('ui_fontSize', this.fontSize)
      localStorage.setItem('ui_animations', this.animations.toString())

      const root = document.documentElement

      // 1. Color Mode
      let isDark = this.colorMode === 'dark'
      if (this.colorMode === 'auto') {
        isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      }
      document.body.classList.toggle('dark', isDark)

      // 2. Theme Colors
      const themes = {
        Obsidian: '#059669', // Brighter Emerald
        Arctic: '#0284c7',   // Brighter Sky/Ocean
        Sakura: '#db2777',   // Brighter Pink
        Twilight: '#7c3aed', // Brighter Violet
        Ember: '#ea580c',    // Brighter Orange
        Ocean: '#2563eb',    // Deep Blue
        Crimson: '#dc2626',  // Red
        Sunflower: '#d97706' // Golden Yellow
      }
      root.style.setProperty('--app-brand', themes[this.theme] || '#059669')

      // 3. Density
      const densities = {
        Compact: { p: '12px', gap: '8px' },
        Comfort: { p: '16px', gap: '16px' },
        Spacious: { p: '24px', gap: '24px' }
      }
      root.style.setProperty('--app-padding', densities[this.density].p)
      root.style.setProperty('--app-gap', densities[this.density].gap)

      // 4. Radius
      const radiuses = {
        Sharp: '0px',
        Default: '12px',
        Rounded: '24px'
      }
      root.style.setProperty('--app-radius', radiuses[this.radius])

      // 5. Font Size
      const fontSizes = {
        S: '13px',
        M: '15px',
        L: '17px'
      }
      root.style.setProperty('--app-font-size', fontSizes[this.fontSize])

      // 6. Animations
      if (this.animations) {
        root.classList.remove('no-animations')
      } else {
        root.classList.add('no-animations')
      }
    },
    setTheme(t: ThemeName) { this.theme = t; this.applyAll() },
    setColorMode(m: ColorMode) { this.colorMode = m; this.applyAll() },
    setDensity(d: Density) { this.density = d; this.applyAll() },
    setRadius(r: Radius) { this.radius = r; this.applyAll() },
    setFontSize(s: FontSize) { this.fontSize = s; this.applyAll() },
    setAnimations(a: boolean) { this.animations = a; this.applyAll() },
    toggleTheme() {
      // Legacy function for header button
      this.colorMode = document.body.classList.contains('dark') ? 'light' : 'dark'
      this.applyAll()
    }
  }
})
