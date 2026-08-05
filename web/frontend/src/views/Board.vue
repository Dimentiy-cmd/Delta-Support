<template>
  <div class="panel card" style="height: 100%; overflow-y: auto; display:flex; flex-direction:column; padding: var(--app-padding);">
    <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom: 14px; flex-wrap:wrap;">
      <div>
        <div style="font-size: 18px; font-weight: 700;">Канбан-доска</div>
        <div class="muted" style="font-size: 13px;">Обзор чатов по статусам</div>
      </div>
      <div style="display:flex; gap:6px;">
        <Button v-for="p in periods" :key="p.value" :label="p.label" size="small"
          :outlined="period !== p.value" @click="period = p.value; load()" />
        <Button icon="pi pi-refresh" text rounded size="small" :loading="loading" @click="load()" />
      </div>
    </div>

    <div class="board-columns">
      <div v-for="col in columnDefs" :key="col.key" class="board-col">
        <div class="board-col-header">
          <span>{{ col.icon }} {{ col.title }}</span>
          <span class="count-badge">{{ (data?.columns as any)?.[col.key]?.length ?? 0 }}</span>
        </div>
        <div class="board-col-body">
          <div
            v-for="item in (data?.columns as any)?.[col.key] || []"
            :key="item.id"
            class="board-card"
            @click="openChat(item.id)"
          >
            <div style="display:flex; align-items:center; justify-content:space-between; gap:6px;">
              <span style="font-weight:650; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{{ item.name }}</span>
              <span class="muted" style="font-size:11px; white-space:nowrap;">{{ timeAgo(item.updated_at) }}</span>
            </div>
            <div v-if="item.snippet" class="board-snippet">{{ item.snippet }}</div>
            <div v-else class="muted board-snippet">Нет сообщений</div>
            <div class="muted" style="font-size:11px; margin-top:4px;">ID {{ item.user_id }} · чат #{{ item.id }}</div>
          </div>
          <div v-if="!loading && (!(data?.columns as any)?.[col.key] || (data?.columns as any)[col.key].length === 0)" class="scroll-hint" style="padding: 20px 0;">
            Нет чатов
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'

const router = useRouter()

const periods = [
  { label: 'Сегодня', value: 'today' },
  { label: 'Неделя', value: 'week' },
  { label: 'Месяц', value: 'month' }
]

const columnDefs = [
  { key: 'waiting_manager', title: 'Ожидают менеджера', icon: '🟡' },
  { key: 'active', title: 'AI активен', icon: '🟢' },
  { key: 'closed', title: 'Закрыто', icon: '⚪' }
]

const period = ref<'today' | 'week' | 'month'>('today')
const data = ref<{ columns: Record<string, any[]> } | null>(null)
const loading = ref(false)

function timeAgo(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime()
  const min = Math.floor(diffMs / 60000)
  if (min < 1) return 'сейчас'
  if (min < 60) return `${min} мин`
  const h = Math.floor(min / 60)
  if (h < 24) return `${h} ч`
  return `${Math.floor(h / 24)} дн`
}

async function load() {
  loading.value = true
  try {
    const res = await fetch(`/api/chats/board?period=${period.value}`, { credentials: 'include' })
    if (res.ok) data.value = await res.json()
  } finally {
    loading.value = false
  }
}

function openChat(id: number) {
  router.push(`/chats/${id}`)
}

onMounted(load)
</script>

<style scoped>
.board-columns {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(260px, 1fr));
  gap: 12px;
  min-height: 0;
  overflow-x: auto;
}
.board-col {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  overflow: hidden;
}
.board-col-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  font-weight: 700;
  font-size: 13px;
  border-bottom: 1px solid var(--app-border);
  background: rgba(148, 163, 184, 0.06);
}
.board-col-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  min-height: 0;
}
.board-card {
  border: 1px solid var(--app-border);
  border-radius: calc(var(--app-radius) * 0.7);
  padding: 10px 12px;
  margin-bottom: 8px;
  cursor: pointer;
  background: var(--app-panel-solid);
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}
.board-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.10);
}
.board-snippet {
  font-size: 12px;
  margin-top: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (max-width: 900px) {
  .board-columns {
    grid-template-columns: 1fr;
    grid-auto-rows: unset;
    overflow-x: visible;
  }
  .board-col {
    max-height: 60vh;
  }
}
</style>
