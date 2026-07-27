<template>
  <div>
    <div style="margin-bottom: 12px;">
      <div style="font-size: 18px; font-weight: 700;">Интеграция и бэкап</div>
      <div class="muted" style="font-size: 13px;">Support API основного сервера и экспорт/импорт настроек</div>
    </div>

    <!-- Support API -->
    <div class="panel card" style="padding: 16px; border-radius: var(--app-radius); margin-bottom: 16px;">
      <div style="font-weight: 700; margin-bottom: 4px;">Support API</div>
      <div class="muted" style="font-size: 13px; margin-bottom: 12px;">
        Получение данных о клиенте (баланс, подписки, ключи) по Telegram ID.
        Данные автоматически передаются AI для ответов и менеджеру при эскалации.
      </div>

      <div style="display:flex; flex-direction:column; gap:12px; max-width: 640px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <InputSwitch v-model="form.enabled" />
          <span>Интеграция включена</span>
        </div>

        <div>
          <label class="f-label">URL сервера</label>
          <InputText v-model="form.url" placeholder="https://web.deltavpn.me" style="width:100%;" />
        </div>

        <div>
          <label class="f-label">
            Токен (sup_...)
            <span v-if="tokenSet" class="muted" style="font-weight:400;"> — установлен: {{ tokenPreview }}</span>
          </label>
          <InputText v-model="form.token" type="password" :placeholder="tokenSet ? 'Оставьте пустым, чтобы не менять' : 'sup_...'" style="width:100%;" autocomplete="new-password" />
        </div>

        <div>
          <label class="f-label">TTL кеша данных (сек)</label>
          <InputText v-model="form.cache_ttl" type="number" style="width: 160px;" />
        </div>

        <div style="display:flex; gap:8px; align-items:center;">
          <Button label="Сохранить" icon="pi pi-check" :loading="saving" @click="save" />
          <Button v-if="tokenSet" label="Удалить токен" icon="pi pi-trash" severity="danger" text @click="clearToken" />
        </div>
        <div v-if="msg" :style="{ color: msgOk ? '#22c55e' : '#ef4444', fontSize: '13px' }">{{ msg }}</div>
      </div>

      <div style="border-top: 1px solid var(--app-border); margin: 16px 0; padding-top: 14px;">
        <div style="font-weight: 600; margin-bottom: 8px;">Проверка подключения</div>
        <div style="display:flex; gap:8px; align-items:center; flex-wrap: wrap;">
          <InputText v-model="testUserId" placeholder="Telegram ID клиента" style="width: 220px;" />
          <Button label="Проверить" icon="pi pi-bolt" :loading="testing" @click="runTest" />
        </div>
        <div v-if="testError" style="color:#ef4444; font-size: 13px; margin-top: 8px;">{{ testError }}</div>
        <div v-if="testResult" style="display:grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px;">
          <div>
            <div class="muted" style="font-size: 12px; margin-bottom: 4px;">Контекст для AI</div>
            <pre class="preview-pre">{{ testResult.ai_context }}</pre>
          </div>
          <div>
            <div class="muted" style="font-size: 12px; margin-bottom: 4px;">Карточка для менеджера</div>
            <pre class="preview-pre">{{ testResult.manager_card }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Экспорт / импорт -->
    <div class="panel card" style="padding: 16px; border-radius: var(--app-radius);">
      <div style="font-weight: 700; margin-bottom: 4px;">Экспорт / импорт настроек</div>
      <div class="muted" style="font-size: 13px; margin-bottom: 12px;">
        Один JSON-файл: системные настройки, промпты, база знаний, AI-провайдеры. Чаты и пользователи панели не переносятся.
      </div>

      <div style="display:flex; flex-direction:column; gap:12px; max-width: 640px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <Checkbox v-model="includeSecrets" binary inputId="incsec" />
          <label for="incsec">Включить секреты (API-ключи и токены)</label>
        </div>
        <div>
          <Button label="Скачать экспорт" icon="pi pi-download" :loading="exporting" @click="doExport" />
        </div>

        <div style="border-top: 1px solid var(--app-border); padding-top: 14px;">
          <div style="font-weight: 600; margin-bottom: 8px;">Импорт</div>
          <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
            <input ref="fileInput" type="file" accept="application/json,.json" @change="onFile" />
            <Dropdown v-model="importMode" :options="importModes" optionLabel="label" optionValue="value" style="width: 260px;" />
            <Button label="Импортировать" icon="pi pi-upload" :disabled="!importData" :loading="importing" @click="doImport" />
          </div>
          <div class="muted" style="font-size: 12px; margin-top: 6px;">
            «Слияние» — обновляет и дополняет; «Замена» — база знаний и провайдеры будут полностью заменены содержимым файла.
          </div>
          <div v-if="importMsg" :style="{ color: importOk ? '#22c55e' : '#ef4444', fontSize: '13px', marginTop: '8px' }">{{ importMsg }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputSwitch from 'primevue/inputswitch'
import Checkbox from 'primevue/checkbox'
import Dropdown from 'primevue/dropdown'

const form = ref({ enabled: false, url: '', token: '', cache_ttl: '120' })
const tokenSet = ref(false)
const tokenPreview = ref('')
const saving = ref(false)
const msg = ref('')
const msgOk = ref(false)

const testUserId = ref('')
const testing = ref(false)
const testError = ref('')
const testResult = ref<{ ai_context: string; manager_card: string } | null>(null)

const includeSecrets = ref(true)
const exporting = ref(false)
const importMode = ref('merge')
const importModes = [
  { label: 'Слияние (merge)', value: 'merge' },
  { label: 'Полная замена (replace)', value: 'replace' }
]
const importData = ref<any>(null)
const importing = ref(false)
const importMsg = ref('')
const importOk = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

async function load() {
  const res = await fetch('/api/settings/support-api', { credentials: 'include' })
  if (!res.ok) return
  const data = await res.json()
  form.value.enabled = !!data.enabled
  form.value.url = data.url || ''
  form.value.cache_ttl = String(data.cache_ttl ?? 120)
  form.value.token = ''
  tokenSet.value = !!data.token_set
  tokenPreview.value = data.token_preview || ''
}

async function save() {
  msg.value = ''
  saving.value = true
  try {
    const body: any = {
      enabled: form.value.enabled,
      url: form.value.url,
      cache_ttl: form.value.cache_ttl
    }
    if (form.value.token.trim()) body.token = form.value.token.trim()
    const res = await fetch('/api/settings/support-api', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(body)
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({ detail: 'Ошибка' }))
      throw new Error(data.detail || 'Ошибка')
    }
    msgOk.value = true
    msg.value = 'Сохранено'
    await load()
  } catch (e: any) {
    msgOk.value = false
    msg.value = e?.message || 'Ошибка'
  } finally {
    saving.value = false
  }
}

async function clearToken() {
  await fetch('/api/settings/support-api', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ clear_token: true })
  })
  await load()
}

async function runTest() {
  testError.value = ''
  testResult.value = null
  if (!testUserId.value.trim()) {
    testError.value = 'Укажите Telegram ID'
    return
  }
  testing.value = true
  try {
    const res = await fetch('/api/settings/support-api/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ user_id: testUserId.value.trim() })
    })
    const data = await res.json()
    if (!data.ok) {
      testError.value = `Ошибка: ${data.error || 'unknown'}${data.detail ? ' — ' + data.detail : ''}`
      return
    }
    testResult.value = { ai_context: data.ai_context, manager_card: data.manager_card }
  } catch (e: any) {
    testError.value = e?.message || 'Ошибка запроса'
  } finally {
    testing.value = false
  }
}

async function doExport() {
  exporting.value = true
  try {
    const res = await fetch(`/api/settings/export?include_secrets=${includeSecrets.value}`, { credentials: 'include' })
    if (!res.ok) return
    const data = await res.json()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    const ts = new Date().toISOString().slice(0, 10)
    a.download = `delta-support-settings-${ts}.json`
    a.click()
    URL.revokeObjectURL(a.href)
  } finally {
    exporting.value = false
  }
}

function onFile(e: Event) {
  importMsg.value = ''
  importData.value = null
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      importData.value = JSON.parse(String(reader.result))
    } catch {
      importOk.value = false
      importMsg.value = 'Файл не является корректным JSON'
    }
  }
  reader.readAsText(file)
}

async function doImport() {
  if (!importData.value) return
  importing.value = true
  importMsg.value = ''
  try {
    const res = await fetch('/api/settings/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ data: importData.value, mode: importMode.value })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || !data.ok) {
      importOk.value = false
      importMsg.value = data.detail || 'Ошибка импорта'
      return
    }
    importOk.value = true
    const c = data.imported || {}
    importMsg.value = `Импортировано: настроек ${c.system_config ?? 0}, база знаний ${c.knowledge_base ?? 0}, провайдеров ${c.ai_providers ?? 0}`
    importData.value = null
    if (fileInput.value) fileInput.value.value = ''
    await load()
  } catch (e: any) {
    importOk.value = false
    importMsg.value = e?.message || 'Ошибка импорта'
  } finally {
    importing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.f-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}
.preview-pre {
  background: rgba(148, 163, 184, 0.08);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  padding: 10px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 320px;
  overflow: auto;
  margin: 0;
}
</style>
