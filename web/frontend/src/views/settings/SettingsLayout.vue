<template>
  <div class="panel card" style="height: 100%; overflow: hidden;">
    <div style="display:grid; grid-template-columns: 260px 1fr; height:100%;">
      <div style="border-right: 1px solid var(--app-border); padding: var(--app-padding);">
        <div style="font-weight:700; margin: calc(var(--app-gap)*0.25) calc(var(--app-gap)*0.5) calc(var(--app-gap)*0.75);">Настройки</div>
        <div class="muted" style="font-size: 12px; margin: 0 calc(var(--app-gap)*0.5) calc(var(--app-gap)*0.75);">
          Профиль, пользователи, бот
        </div>
        <div style="display:flex; flex-direction:column; gap:calc(var(--app-gap)*0.5);">
          <RouterLink class="s-item" to="/settings/appearance"><i class="pi pi-palette" />Внешний вид</RouterLink>
          <RouterLink class="s-item" to="/settings/bot"><i class="pi pi-send" />Bot & AI</RouterLink>
          <RouterLink class="s-item" to="/settings/telegram"><i class="pi pi-comments" />Telegram топики</RouterLink>
          <RouterLink class="s-item" to="/settings/ai"><i class="pi pi-microchip" />AI контекст</RouterLink>
          <RouterLink class="s-item" to="/settings/ai-providers"><i class="pi pi-server" />AI Провайдеры</RouterLink>
          <RouterLink class="s-item" to="/settings/kb"><i class="pi pi-book" />База знаний</RouterLink>
          <RouterLink class="s-item" to="/settings/integration"><i class="pi pi-link" />Интеграция и бэкап</RouterLink>
          <RouterLink class="s-item" to="/settings/automation"><i class="pi pi-clock" />Автоматизация</RouterLink>
          <RouterLink class="s-item" to="/settings/media"><i class="pi pi-images" />Медиа</RouterLink>
          <RouterLink class="s-item" to="/settings/profile"><i class="pi pi-user" />Профиль</RouterLink>
          <RouterLink class="s-item" to="/settings/users"><i class="pi pi-users" />Пользователи</RouterLink>
        </div>
      </div>
      <div style="padding: var(--app-padding); overflow:auto;">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

onMounted(() => {
  if (auth.me?.role !== 'admin') {
    router.replace('/chats')
  }
})
</script>

<style scoped>
.s-item{
  display:flex;
  align-items:center;
  gap: calc(var(--app-gap) * 0.75);
  padding: calc(var(--app-padding) * 0.6) calc(var(--app-padding) * 0.75);
  border-radius: var(--app-radius);
  color: var(--app-text);
  text-decoration:none;
  border: 1px solid transparent;
  transition: background 0.15s;
}
.s-item:hover{ background: rgba(148, 163, 184, 0.08); }
.router-link-active{
  background: color-mix(in srgb, var(--app-brand) 12%, transparent) !important;
  border-color: color-mix(in srgb, var(--app-brand) 20%, transparent) !important;
  color: var(--app-brand) !important;
}
</style>
