<template>
  <div class="panel card" style="height: 100%; overflow: auto; padding: var(--app-padding);">
    <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom: 16px; flex-wrap:wrap;">
      <div>
        <div style="font-size: 18px; font-weight: 700;">Дашборд поддержки</div>
        <div class="muted" style="font-size: 13px;">Метрики за период</div>
      </div>
      <div style="display:flex; gap:6px;">
        <Button v-for="d in [7, 14, 30]" :key="d" :label="`${d} дн.`" size="small"
          :outlined="days !== d" @click="days = d; load()" />
      </div>
    </div>

    <!-- Карточки метрик -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-value">{{ data?.totals.chats_new ?? '—' }}</div>
        <div class="stat-label">Новых чатов</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: var(--app-brand);">{{ aiShare }}</div>
        <div class="stat-label">Решено AI без менеджера</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ reaction }}</div>
        <div class="stat-label">Средняя реакция менеджера</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" :style="{ color: (data?.now.waiting_manager || 0) > 0 ? '#f59e0b' : 'inherit' }">
          {{ data?.now.waiting_manager ?? '—' }}
        </div>
        <div class="stat-label">Ждут менеджера сейчас</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ data?.totals.messages_user ?? '—' }}</div>
        <div class="stat-label">Сообщений от клиентов</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ data?.totals.manager_involved_chats ?? '—' }}</div>
        <div class="stat-label">Чатов с менеджером</div>
      </div>
    </div>

    <!-- График по дням -->
    <div class="panel card" style="padding: 16px; margin-top: 16px;">
      <div style="font-weight: 700; margin-bottom: 12px;">Сообщения по дням</div>
      <div v-if="data" class="chart">
        <div v-for="d in data.by_day" :key="d.date" class="chart-col" :title="`${d.date}: клиенты ${d.user}, AI ${d.ai}, менеджеры ${d.manager}, новых чатов ${d.chats}`">
          <div class="chart-bars">
            <div class="bar bar-manager" :style="{ height: barH(d.manager) }"></div>
            <div class="bar bar-ai" :style="{ height: barH(d.ai) }"></div>
            <div class="bar bar-user" :style="{ height: barH(d.user) }"></div>
          </div>
          <div class="chart-x">{{ d.date.slice(8) }}</div>
        </div>
      </div>
      <div style="display:flex; gap:16px; margin-top: 10px; font-size: 12px;" class="muted">
        <span><span class="legend bar-user"></span> Клиенты</span>
        <span><span class="legend bar-ai"></span> AI</span>
        <span><span class="legend bar-manager"></span> Менеджеры</span>
      </div>
    </div>

    <!-- Темы недели -->
    <div class="panel card" style="padding: 16px; margin-top: 16px;">
      <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;">
        <div style="font-weight: 700;">🔥 Топ тем обращений (за 7 дней)</div>
        <Button label="Определить темы (AI)" icon="pi pi-sparkles" size="small" :loading="topicsLoading" @click="loadTopics" />
      </div>
      <pre v-if="topics" class="topics-pre">{{ topics }}</pre>
      <div v-else-if="topicsError" style="color:#ef4444; font-size:13px; margin-top:10px;">{{ topicsError }}</div>
      <div v-else class="muted" style="font-size: 13px; margin-top: 10px;">
        Нажмите кнопку — AI проанализирует сообщения клиентов за неделю и выделит главные темы.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'

type Overview = {
  days: number
  totals: {
    chats_new: number
    messages_user: number
    messages_ai: number
    messages_manager: number
    manager_involved_chats: number
    ai_solved_share: number | null
    avg_manager_reaction_min: number | null
  }
  now: { active: number; waiting_manager: number; closed_total: number }
  by_day: { date: string; chats: number; user: number; ai: number; manager: number }[]
}

const data = ref<Overview | null>(null)
const days = ref(14)
const topics = ref('')
const topicsError = ref('')
const topicsLoading = ref(false)

const aiShare = computed(() => {
  const v = data.value?.totals.ai_solved_share
  return v === null || v === undefined ? '—' : `${v}%`
})
const reaction = computed(() => {
  const v = data.value?.totals.avg_manager_reaction_min
  if (v === null || v === undefined) return '—'
  return v >= 60 ? `${(v / 60).toFixed(1)} ч` : `${v} мин`
})

const maxDay = computed(() => {
  if (!data.value) return 1
  return Math.max(1, ...data.value.by_day.map(d => d.user + d.ai + d.manager))
})

function barH(v: number) {
  const h = Math.round((v / maxDay.value) * 120)
  return v > 0 ? `${Math.max(h, 3)}px` : '0px'
}

async function load() {
  const res = await fetch(`/api/stats/overview?days=${days.value}`, { credentials: 'include' })
  if (res.ok) data.value = await res.json()
}

async function loadTopics() {
  topicsLoading.value = true
  topicsError.value = ''
  try {
    const res = await fetch('/api/stats/topics', { method: 'POST', credentials: 'include' })
    const d = await res.json()
    if (d.ok) topics.value = d.topics
    else topicsError.value = d.error || 'Ошибка'
  } catch (e: any) {
    topicsError.value = e?.message || 'Ошибка'
  } finally {
    topicsLoading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
}
.stat-card {
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  padding: 14px 16px;
}
.stat-value {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.02em;
}
.stat-label {
  font-size: 12px;
  opacity: 0.7;
  margin-top: 2px;
}
.chart {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  min-height: 150px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.chart-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 26px;
}
.chart-bars {
  display: flex;
  flex-direction: column-reverse;
  width: 100%;
  max-width: 34px;
  border-radius: 4px;
  overflow: hidden;
}
.bar { width: 100%; }
.bar-user { background: var(--app-brand, #14b8a6); }
.bar-ai { background: #8b5cf6; }
.bar-manager { background: #f59e0b; }
.chart-x { font-size: 10px; opacity: 0.6; }
.legend {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  margin-right: 4px;
  vertical-align: middle;
}
.topics-pre {
  margin-top: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 14px;
  background: rgba(148, 163, 184, 0.08);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  padding: 12px;
}
</style>
