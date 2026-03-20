<template>
  <div class="space-y-6">
    <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom: 12px;">
      <div>
        <div style="font-size: 18px; font-weight: 700;">Внешний вид</div>
        <div class="muted" style="font-size: 13px;">Настройка темы, цветов и плотности интерфейса</div>
      </div>
      <Button v-if="auth.isAdmin" label="Сохранить" icon="pi pi-check" :loading="saving" @click="saveBranding" />
    </div>

    <!-- Branding (Title, Logo) -->
    <div class="panel card p-0" style="border-radius: var(--app-radius); overflow: hidden; margin-bottom: 16px;">
      <div class="settings-section">
        <div class="section-title">Логотип и название</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--app-gap);">
          <div class="field">
            <label class="muted" style="font-size: 12px; margin-bottom: 4px; display: block;">Название панели</label>
            <InputText v-model="form.name" style="width: 100%" placeholder="Support Desk" />
          </div>
          <div class="field">
            <label class="muted" style="font-size: 12px; margin-bottom: 4px; display: block;">Подзаголовок</label>
            <InputText v-model="form.tagline" style="width: 100%" placeholder="Панель поддержки" />
          </div>
          <div class="field" style="grid-column: 1 / -1;">
            <label class="muted" style="font-size: 12px; margin-bottom: 4px; display: block;">URL логотипа</label>
            <div style="display:flex; gap: calc(var(--app-gap) * 0.5);">
              <InputText v-model="form.logo_url" style="width: 100%" placeholder="https://.../logo.png" />
              <input ref="logoInput" type="file" accept="image/png,image/jpeg,image/webp" style="display:none" @change="onLogoPicked" />
              <Button v-if="auth.isAdmin" label="Загрузить" icon="pi pi-upload" outlined :loading="uploading" @click="pickLogo" />
            </div>
          </div>
        </div>

        <!-- Preview -->
        <div style="margin-top: 16px; padding: 12px; border: 1px dashed var(--app-border); border-radius: var(--app-radius);">
          <div class="muted" style="font-size:12px; margin-bottom: 10px;">Превью</div>
          <div style="display:flex; align-items:center; gap: 10px;">
            <div v-if="form.logo_url" style="width: 42px; height: 42px; border-radius: calc(var(--app-radius) * 0.75); overflow:hidden; border:1px solid var(--app-border); background: rgba(148,163,184,0.08);">
              <img :src="form.logo_url" style="width:100%; height:100%; object-fit: cover;" />
            </div>
            <div v-else style="width: 42px; height: 42px; border-radius: calc(var(--app-radius) * 0.75); display:flex; align-items:center; justify-content:center; border:1px solid var(--app-border); background: color-mix(in srgb, var(--app-brand) 10%, transparent); color: var(--app-brand); font-weight:800;">
              {{ form.name.slice(0, 1).toUpperCase() }}
            </div>
            <div style="min-width: 0;">
              <div style="font-weight:800;">
                <span v-for="(p, idx) in nameParts" :key="idx" :style="{ color: p.color || 'inherit' }">{{ p.text }}</span>
              </div>
              <div class="muted" style="font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                {{ form.tagline }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="err" style="color:#ef4444; font-size:13px; margin-top: 8px;">{{ err }}</div>
      </div>
    </div>

    <div class="panel card p-0" style="border-radius: var(--app-radius); overflow: hidden;">

      
      <!-- Theme Selection -->
      <div class="settings-section">
        <div class="section-title">Тема</div>
        <div class="themes-grid">
          <div v-for="t in themes" :key="t.name" 
               class="theme-card" 
               :class="{ active: ui.theme === t.name }"
               @click="ui.setTheme(t.name)">
            <div class="theme-color" :style="{ background: t.color }"></div>
            <div class="theme-name">{{ t.name }}</div>
          </div>
        </div>
      </div>

      <!-- Color Mode -->
      <div class="settings-section">
        <div class="section-title">Режим</div>
        <div class="toggle-group">
          <button class="toggle-btn" :class="{ active: ui.colorMode === 'light' }" @click="ui.setColorMode('light')">
            <i class="pi pi-sun"></i> Light
          </button>
          <button class="toggle-btn" :class="{ active: ui.colorMode === 'dark' }" @click="ui.setColorMode('dark')">
            <i class="pi pi-moon"></i> Dark
          </button>
          <button class="toggle-btn" :class="{ active: ui.colorMode === 'auto' }" @click="ui.setColorMode('auto')">
            <i class="pi pi-desktop"></i> Auto
          </button>
        </div>
      </div>

      <!-- Density -->
      <div class="settings-section">
        <div class="section-title">Плотность</div>
        <div class="toggle-group">
          <button class="toggle-btn" :class="{ active: ui.density === 'Compact' }" @click="ui.setDensity('Compact')">
            <i class="pi pi-align-justify" style="transform: scaleY(0.7);"></i> Compact
          </button>
          <button class="toggle-btn" :class="{ active: ui.density === 'Comfort' }" @click="ui.setDensity('Comfort')">
            <i class="pi pi-align-justify"></i> Comfort
          </button>
          <button class="toggle-btn" :class="{ active: ui.density === 'Spacious' }" @click="ui.setDensity('Spacious')">
            <i class="pi pi-align-justify" style="transform: scaleY(1.3);"></i> Spacious
          </button>
        </div>
      </div>

      <!-- Corner Radius -->
      <div class="settings-section">
        <div class="section-title">Скругление углов</div>
        <div class="toggle-group">
          <button class="toggle-btn" :class="{ active: ui.radius === 'Sharp' }" @click="ui.setRadius('Sharp')">
            <div style="width:16px; height:16px; border: 2px solid currentColor; border-radius: 0;"></div> Sharp
          </button>
          <button class="toggle-btn" :class="{ active: ui.radius === 'Default' }" @click="ui.setRadius('Default')">
            <div style="width:16px; height:16px; border: 2px solid currentColor; border-radius: 4px;"></div> Default
          </button>
          <button class="toggle-btn" :class="{ active: ui.radius === 'Rounded' }" @click="ui.setRadius('Rounded')">
            <div style="width:16px; height:16px; border: 2px solid currentColor; border-radius: calc(var(--app-radius) * 0.5);"></div> Rounded
          </button>
        </div>
      </div>

      <!-- Font Size -->
      <div class="settings-section">
        <div class="section-title">Размер шрифта</div>
        <div class="toggle-group">
          <button class="toggle-btn" :class="{ active: ui.fontSize === 'S' }" @click="ui.setFontSize('S')" style="font-size: 12px;">A</button>
          <button class="toggle-btn" :class="{ active: ui.fontSize === 'M' }" @click="ui.setFontSize('M')" style="font-size: 15px;">A</button>
          <button class="toggle-btn" :class="{ active: ui.fontSize === 'L' }" @click="ui.setFontSize('L')" style="font-size: 18px;">A</button>
        </div>
      </div>

      <!-- Animations -->
      <div class="settings-section" style="border-bottom: none; display: flex; justify-content: space-between; align-items: center;">
        <div>
          <div class="section-title" style="margin-bottom: 4px;">Анимации</div>
          <div class="muted" style="font-size: 12px;">Плавные переходы и эффекты</div>
        </div>
        <div>
          <Checkbox :modelValue="ui.animations" :binary="true" @update:modelValue="ui.setAnimations($event)" />
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { useBrandingStore } from '@/stores/branding'
import Checkbox from 'primevue/checkbox'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { parseColoredText } from '@/utils/coloredText'

const ui = useUiStore()
const auth = useAuthStore()
const branding = useBrandingStore()

const saving = ref(false)
const uploading = ref(false)
const err = ref('')
const form = ref({ name: '', tagline: '', logo_url: '' })
const logoInput = ref<HTMLInputElement | null>(null)
const nameParts = computed(() => parseColoredText(form.value.name))

const themes = [
  { name: 'Obsidian', color: '#059669' },
  { name: 'Arctic', color: '#0284c7' },
  { name: 'Sakura', color: '#db2777' },
  { name: 'Twilight', color: '#7c3aed' },
  { name: 'Ember', color: '#ea580c' },
  { name: 'Ocean', color: '#2563eb' },
  { name: 'Crimson', color: '#dc2626' },
  { name: 'Sunflower', color: '#d97706' }
] as const

async function load() {
  form.value.name = branding.data.name
  form.value.tagline = branding.data.tagline
  form.value.logo_url = branding.data.logo_url
}

async function saveBranding() {
  err.value = ''
  saving.value = true
  try {
    await branding.save(form.value)
  } catch (e: any) {
    err.value = e?.message || 'Ошибка'
  } finally {
    saving.value = false
  }
}

function pickLogo() {
  logoInput.value?.click()
}

async function onLogoPicked(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  err.value = ''
  const fd = new FormData()
  fd.append('file', file)
  try {
    const res = await fetch('/api/branding/logo', {
      method: 'POST',
      body: fd,
      credentials: 'include'
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({ detail: 'Ошибка' }))
      throw new Error(data.detail || 'Ошибка')
    }
    const data = await res.json()
    form.value.logo_url = data.logo_url
    await saveBranding()
  } catch (e: any) {
    err.value = e?.message || 'Ошибка'
  } finally {
    uploading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.settings-section {
  padding: calc(var(--app-padding) * 1.25);
  border-bottom: 1px solid var(--app-border);
}

.section-title {
  font-weight: 700;
  margin-bottom: 16px;
}

.themes-grid {
  display: flex;
  gap: calc(var(--app-gap) * 0.75);
  flex-wrap: wrap;
}

.theme-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: var(--app-radius);
  border: 1px solid var(--app-border);
  background: var(--app-bg);
  cursor: pointer;
  transition: var(--app-transition);
}

.theme-card:hover {
  border-color: var(--app-muted);
}

.theme-card.active {
  border-color: var(--app-brand);
  background: color-mix(in srgb, var(--app-brand) 10%, transparent);
  box-shadow: 0 0 0 1px var(--app-brand);
}

.theme-color {
  width: 18px;
  height: 18px;
  border-radius: 99px;
}

.theme-name {
  font-weight: 600;
  font-size: 14px;
}

.toggle-group {
  display: flex;
  background: rgba(148, 163, 184, 0.08);
  padding: 4px;
  border-radius: var(--app-radius);
  gap: 4px;
  width: fit-content;
}

.toggle-btn {
  border: none;
  background: transparent;
  color: var(--app-muted);
  padding: 8px 20px;
  border-radius: calc(var(--app-radius) * 0.5);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: var(--app-transition);
  display: flex;
  align-items: center;
  gap: calc(var(--app-gap) * 0.5);
}

.toggle-btn:hover {
  color: var(--app-text);
  background: rgba(148, 163, 184, 0.1);
}

.toggle-btn.active {
  background: var(--app-panel);
  color: var(--app-brand);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
body.dark .toggle-btn.active {
  background: var(--app-panel-solid);
}
</style>
