<template>
  <div class="space-y-6">
    <!-- Header -->
    <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom: 12px;">
      <div>
        <div style="font-size: 18px; font-weight: 700;">Настройки бота</div>
        <div class="muted" style="font-size: 13px;">Проект, приветствие и управление AI</div>
      </div>
      <div class="btn-row">
        <Button v-if="auth.isAdmin" label="Сохранить" icon="pi pi-check" :loading="saving" @click="saveAll" />
      </div>
    </div>

    <div class="space-y-4">
      <!-- Project Section -->
      <div class="panel card" style="padding: 16px; border-radius: 16px;">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom: 16px;">
          <i class="pi pi-info-circle" style="color: var(--app-brand)"></i>
          <span style="font-weight: 700;">Информация о проекте</span>
        </div>
        
        <div class="grid-form">
          <div class="field">
            <label class="muted label-small">Название проекта</label>
            <InputText v-model="form.project_name" style="width: 100%;" />
          </div>
          <div class="field full-width">
            <label class="muted label-small">Описание проекта</label>
            <Textarea v-model="form.project_description" rows="3" style="width: 100%;" />
          </div>
          <div class="field">
            <label class="muted label-small">Сайт</label>
            <InputText v-model="form.project_website" style="width: 100%;" />
          </div>
          <div class="field">
            <label class="muted label-small">Ссылка на бота</label>
            <InputText v-model="form.project_bot_link" style="width: 100%;" />
          </div>
        </div>
      </div>

      <!-- Welcome Message Section -->
      <div class="panel card" style="padding: 16px; border-radius: 16px;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 16px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <i class="pi pi-comment" style="color: var(--app-brand)"></i>
            <span style="font-weight: 700;">Приветственное сообщение</span>
          </div>
          <HelpTip :text="welcomeHelp" />
        </div>
        <Textarea v-model="form.bot_welcome_message" rows="5" style="width: 100%;" placeholder="Текст приветствия..." />
      </div>

      <!-- AI Global Section -->
      <div class="panel card" style="padding: 16px; border-radius: 16px;">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom: 16px;">
          <i class="pi pi-bolt" style="color: var(--app-brand)"></i>
          <span style="font-weight: 700;">AI Поддержка</span>
        </div>

        <div class="grid-form">
          <div class="field full-width">
            <div style="display:flex; align-items:center; gap:10px; padding: 12px; background: rgba(34, 197, 94, 0.05); border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.1);">
              <Checkbox v-model="form.ai_support_enabled" :binary="true" inputId="ai_enabled" />
              <label for="ai_enabled" style="cursor: pointer; font-weight: 600;">AI поддержка включена</label>
            </div>
          </div>

          <div class="field full-width">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 8px;">
              <label class="muted label-small">Системный промпт (Инструкция для AI)</label>
              <HelpTip :text="promptHelp" />
            </div>
            <Textarea v-model="form.ai_system_prompt" rows="8" style="width: 100%; min-height: 200px;" />
          </div>

          <!-- Embedded AI Providers Section -->
          <div class="field full-width" style="margin-top: 10px;">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 12px;">
              <div style="font-size: 14px; font-weight: 700;">Активные провайдеры</div>
              <Button label="Добавить" icon="pi pi-plus" size="small" text @click="openCreateModal" />
            </div>

            <div v-if="providers.length === 0" style="padding: 20px; text-align: center; background: rgba(148, 163, 184, 0.05); border-radius: 12px; border: 1px dashed var(--app-border);">
              <div class="muted" style="font-size: 13px;">Нет настроенных провайдеров. AI не будет работать.</div>
            </div>

            <div class="providers-list">
              <div v-for="p in providers" :key="p.id" class="provider-item" :class="{ 'p-off': !p.is_active }">
                <div class="p-info">
                  <div class="p-name">
                    <i :class="getProviderIcon(p.api_type)" style="margin-right: 6px; color: var(--app-brand);"></i>
                    {{ p.name }} 
                    <span style="font-size: 10px; font-weight: normal; opacity: 0.7;">({{ p.model_name }})</span>
                  </div>
                  <div class="p-meta">Приоритет: {{ p.priority }} • {{ p.is_active ? 'Активен' : 'Отключен' }}</div>
                </div>
                <div class="p-actions">
                  <Button icon="pi pi-pencil" text rounded size="small" @click="editProvider(p)" />
                  <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="deleteProvider(p.id)" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="err" style="color:#ef4444; font-size: 13px; padding: 10px; background: rgba(239, 68, 68, 0.05); border-radius: 10px; border: 1px solid rgba(239, 68, 68, 0.2);">
        {{ err }}
      </div>
    </div>

    <!-- Provider Modal -->
    <Dialog v-model:visible="showModal" :header="isEditing ? 'Редактировать провайдера' : 'Новый провайдер'" modal :style="{ width: '420px' }">
      <div class="form-grid-modal">
        <div class="field">
          <label class="muted label-small">Название</label>
          <InputText v-model="pForm.name" style="width: 100%" placeholder="Например: DeepSeek" />
        </div>
        <div class="field">
          <label class="muted label-small">Тип API</label>
          <Dropdown v-model="pForm.api_type" :options="apiTypes" optionLabel="label" optionValue="value" style="width: 100%" />
        </div>
        <div class="field">
          <label class="muted label-small">Base URL</label>
          <InputText v-model="pForm.base_url" style="width: 100%" placeholder="https://api.deepseek.com/v1" />
        </div>
        <div class="field">
          <label class="muted label-small">Модель</label>
          <InputText v-model="pForm.model_name" style="width: 100%" placeholder="deepseek-chat" />
        </div>
        <div class="field">
          <label class="muted label-small">API Ключ</label>
          <Password v-model="pForm.api_key" style="width: 100%" :feedback="false" toggleMask inputStyle="width: 100%" placeholder="sk-..." />
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div class="field">
            <label class="muted label-small">Приоритет</label>
            <InputText v-model.number="pForm.priority" type="number" style="width: 100%" />
          </div>
          <div class="field" style="display: flex; align-items: flex-end; padding-bottom: 8px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <Checkbox v-model="pForm.is_active" :binary="true" inputId="p_active" />
              <label for="p_active" style="font-size: 13px; cursor: pointer;">Активен</label>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Отмена" text @click="showModal = false" />
        <Button :label="isEditing ? 'Сохранить' : 'Создать'" :loading="modalLoading" @click="saveProvider" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Checkbox from 'primevue/checkbox'
import Password from 'primevue/password'
import Dropdown from 'primevue/dropdown'
import Dialog from 'primevue/dialog'
import { useAuthStore } from '@/stores/auth'
import HelpTip from '@/components/HelpTip.vue'

const auth = useAuthStore()
const saving = ref(false)
const err = ref('')

// Bot form
const form = ref({
  project_name: '',
  project_description: '',
  project_website: '',
  project_bot_link: '',
  bot_welcome_message: '',
  ai_system_prompt: '',
  ai_support_enabled: true
})

// Providers data
const providers = ref<any[]>([])
const showModal = ref(false)
const isEditing = ref(false)
const modalLoading = ref(false)
const currentProviderId = ref<number | null>(null)

const pForm = ref({
  name: '',
  api_type: 'openai',
  api_key: '',
  base_url: '',
  model_name: '',
  is_active: true,
  priority: 10
})

const apiTypes = [
  { label: 'OpenAI Compatible', value: 'openai' },
  { label: 'Groq API', value: 'groq' },
  { label: 'Anthropic', value: 'anthropic' }
]

const welcomeHelp = 'Переменные: {first_name}, {username}, {project_name}, {project_bot_link}'
const promptHelp = 'Переменные: {project_name}, {service_context}, {first_name}, {user_id}'

async function load() {
  err.value = ''
  try {
    // Load bot settings
    const bRes = await fetch('/api/settings/bot', { credentials: 'include' })
    if (bRes.ok) {
      const bData = await bRes.json()
      const incoming = bData.effective || {}
      if (typeof incoming.ai_support_enabled === 'string') {
        incoming.ai_support_enabled = ['1', 'true', 'yes', 'y', 'on'].includes(incoming.ai_support_enabled.trim().toLowerCase())
      }
      form.value = { ...form.value, ...incoming }
    }

    // Load providers
    const pRes = await fetch('/api/ai/providers', { credentials: 'include' })
    if (pRes.ok) providers.value = await pRes.json()
  } catch (e) {
    err.value = 'Ошибка загрузки данных'
  }
}

async function saveAll() {
  err.value = ''
  saving.value = true
  try {
    const res = await fetch('/api/settings/bot', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(form.value)
    })
    if (!res.ok) throw new Error('Ошибка сохранения настроек')
    await load()
  } catch (e: any) {
    err.value = e.message
  } finally {
    saving.value = false
  }
}

// Provider methods
const openCreateModal = () => {
  isEditing.value = false
  currentProviderId.value = null
  pForm.value = { name: '', api_type: 'openai', api_key: '', base_url: '', model_name: '', is_active: true, priority: 10 }
  showModal.value = true
}

const editProvider = (p: any) => {
  isEditing.value = true
  currentProviderId.value = p.id
  pForm.value = { ...p, api_key: '' }
  showModal.value = true
}

const saveProvider = async () => {
  if (!pForm.value.name || !pForm.value.model_name) return
  modalLoading.value = true
  try {
    const url = isEditing.value ? `/api/ai/providers/${currentProviderId.value}` : '/api/ai/providers'
    const res = await fetch(url, {
      method: isEditing.value ? 'PATCH' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(pForm.value)
    })
    if (res.ok) {
      showModal.value = false
      await load()
    }
  } finally {
    modalLoading.value = false
  }
}

const deleteProvider = async (id: number) => {
  if (!confirm('Удалить провайдера?')) return
  const res = await fetch(`/api/ai/providers/${id}`, { method: 'DELETE', credentials: 'include' })
  if (res.ok) await load()
}

const getProviderIcon = (type: string) => {
  if (type === 'groq') return 'pi pi-bolt'
  if (type === 'openai') return 'pi pi-prime'
  return 'pi pi-server'
}

onMounted(load)
</script>

<style scoped>
.grid-form { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.field { display: flex; flex-direction: column; }
.full-width { grid-column: 1 / -1; }
.label-small { font-size: 11px; font-weight: 700; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--app-muted); }

.providers-list { display: flex; flex-direction: column; gap: 8px; }
.provider-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(148, 163, 184, 0.05);
  border: 1px solid var(--app-border);
  border-radius: 12px;
}
.p-off { opacity: 0.5; }
.p-name { font-weight: 700; font-size: 14px; display: flex; align-items: center; }
.p-meta { font-size: 11px; color: var(--app-muted); margin-top: 2px; }

.form-grid-modal { display: flex; flex-direction: column; gap: 14px; padding-top: 10px; }

.space-y-6 > * + * { margin-top: 1.5rem; }
.space-y-4 > * + * { margin-top: 1rem; }
</style>
