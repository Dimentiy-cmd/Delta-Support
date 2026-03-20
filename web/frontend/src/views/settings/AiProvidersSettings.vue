<template>
  <div class="space-y-6">
    <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom: 12px;">
      <div>
        <div style="font-size: 18px; font-weight: 700;">AI Провайдеры</div>
        <div class="muted" style="font-size: 13px;">Управление OpenAI-совместимыми провайдерами и балансировкой</div>
      </div>
      <div class="btn-row">
        <Button label="Добавить" icon="pi pi-plus" @click="openCreateModal" />
      </div>
    </div>

    <div v-if="providers.length === 0" class="panel card" style="padding: 40px; text-align: center; border-radius: 16px;">
      <i class="pi pi-server muted" style="font-size: 2rem; margin-bottom: 12px;"></i>
      <div class="muted">Провайдеры не настроены. Добавьте первый провайдер для работы AI.</div>
    </div>

    <div class="grid-container">
      <div v-for="p in providers" :key="p.id" 
           class="panel card provider-card"
           :class="{'provider-disabled': !p.is_active}">
        <div class="provider-header">
          <div class="provider-info">
            <div class="provider-name">
              <i :class="getProviderIcon(p.api_type)" class="provider-type-icon"></i>
              {{ p.name }}
            </div>
            <div class="muted" style="font-size: 12px;">
              {{ p.model_name }} • {{ p.api_type }}
            </div>
          </div>
          <div class="provider-actions">
            <Button icon="pi pi-pencil" text rounded @click="editProvider(p)" />
            <Button icon="pi pi-trash" text rounded severity="danger" @click="deleteProvider(p.id)" />
          </div>
        </div>

        <div class="provider-details">
          <div class="detail-item">
            <span class="muted">URL:</span>
            <span class="detail-value">{{ p.base_url || 'Default' }}</span>
          </div>
          <div class="detail-item">
            <span class="muted">Приоритет:</span>
            <span class="detail-value">{{ p.priority }}</span>
          </div>
          <div class="detail-item">
            <span class="muted">Статус:</span>
            <span :class="p.is_active ? 'status-active' : 'status-inactive'">
              {{ p.is_active ? 'Активен' : 'Отключен' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal for Create/Edit -->
    <Dialog v-model:visible="showModal" :header="isEditing ? 'Редактировать провайдера' : 'Новый провайдер'" modal :style="{ width: '450px' }">
      <div class="form-grid">
        <div class="field">
          <label class="muted" style="font-size: 12px; margin-bottom: 4px; display: block;">Название</label>
          <InputText v-model="form.name" style="width: 100%" placeholder="Например: DeepSeek / OpenAI" />
        </div>

        <div class="field">
          <label class="muted" style="font-size: 12px; margin-bottom: 4px; display: block;">Тип API</label>
          <Dropdown v-model="form.api_type" :options="apiTypes" optionLabel="label" optionValue="value" style="width: 100%" />
        </div>

        <div class="field">
          <label class="muted" style="font-size: 12px; margin-bottom: 4px; display: block;">Base URL</label>
          <InputText v-model="form.base_url" style="width: 100%" placeholder="https://api.openai.com/v1" />
        </div>

        <div class="field">
          <label class="muted" style="font-size: 12px; margin-bottom: 4px; display: block;">Модель</label>
          <InputText v-model="form.model_name" style="width: 100%" placeholder="gpt-4o / deepseek-chat" />
        </div>

        <div class="field">
          <label class="muted" style="font-size: 12px; margin-bottom: 4px; display: block;">API Ключ</label>
          <Password v-model="form.api_key" style="width: 100%" :feedback="false" toggleMask inputStyle="width: 100%" placeholder="sk-..." />
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div class="field">
            <label class="muted" style="font-size: 12px; margin-bottom: 4px; display: block;">Приоритет</label>
            <InputText v-model.number="form.priority" type="number" style="width: 100%" />
          </div>
          <div class="field" style="display: flex; align-items: flex-end; padding-bottom: 8px;">
            <div class="flex align-items-center">
              <Checkbox v-model="form.is_active" :binary="true" inputId="is_active" />
              <label for="is_active" style="margin-left: 8px; cursor: pointer; font-size: 14px;">Активен</label>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <Button label="Отмена" text @click="showModal = false" />
        <Button :label="isEditing ? 'Сохранить' : 'Создать'" :icon="loading ? 'pi pi-spin pi-spinner' : 'pi pi-check'" :disabled="loading" @click="saveProvider" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Dropdown from 'primevue/dropdown'
import Checkbox from 'primevue/checkbox'
import Dialog from 'primevue/dialog'

const providers = ref<any[]>([])
const showModal = ref(false)
const isEditing = ref(false)
const loading = ref(false)
const currentId = ref<number | null>(null)

const apiTypes = [
  { label: 'OpenAI Compatible', value: 'openai' },
  { label: 'Groq API', value: 'groq' },
  { label: 'Anthropic', value: 'anthropic' }
]

const form = ref({
  name: '',
  api_type: 'openai',
  api_key: '',
  base_url: '',
  model_name: '',
  is_active: true,
  priority: 10
})

const fetchProviders = async () => {
  const res = await fetch('/api/ai/providers', { credentials: 'include' })
  if (res.ok) {
    providers.value = await res.json()
  }
}

const getProviderIcon = (type: string) => {
  if (type === 'groq') return 'pi pi-bolt'
  if (type === 'openai') return 'pi pi-prime'
  return 'pi pi-server'
}

const openCreateModal = () => {
  isEditing.value = false
  currentId.value = null
  form.value = {
    name: '',
    api_type: 'openai',
    api_key: '',
    base_url: '',
    model_name: '',
    is_active: true,
    priority: 10
  }
  showModal.value = true
}

const editProvider = (p: any) => {
  isEditing.value = true
  currentId.value = p.id
  form.value = { ...p, api_key: '' }
  showModal.value = true
}

const saveProvider = async () => {
  if (!form.value.name || !form.value.model_name) return
  
  loading.value = true
  try {
    const url = isEditing.value ? `/api/ai/providers/${currentId.value}` : '/api/ai/providers'
    const res = await fetch(url, {
      method: isEditing.value ? 'PATCH' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(form.value)
    })
    
    if (res.ok) {
      showModal.value = false
      await fetchProviders()
    }
  } finally {
    loading.value = false
  }
}

const deleteProvider = async (id: number) => {
  if (!confirm('Вы уверены, что хотите удалить этого провайдера?')) return
  const res = await fetch(`/api/ai/providers/${id}`, { method: 'DELETE', credentials: 'include' })
  if (res.ok) await fetchProviders()
}

onMounted(fetchProviders)
</script>

<style scoped>
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.provider-card {
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.provider-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.1);
}

.provider-disabled {
  opacity: 0.6;
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.provider-name {
  font-weight: 700;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.provider-type-icon {
  color: var(--app-brand);
}

.provider-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px solid var(--app-border);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.detail-value {
  font-weight: 500;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-active {
  color: #22c55e;
  font-weight: 600;
}

.status-inactive {
  color: var(--app-muted);
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 10px;
}
</style>
