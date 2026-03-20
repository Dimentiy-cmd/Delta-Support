<template>
  <div class="panel card" style="border-radius: var(--app-radius); padding: calc(var(--app-padding) * 1.5); max-width: 720px; margin: var(--app-padding) auto;">
    <div style="font-size: 18px; font-weight: 800;">Страница не найдена</div>
    <div class="muted" style="margin-top: calc(var(--app-gap) * 0.5); font-size: 13px;">
      Такой страницы нет. Проверьте адрес или вернитесь на главную.
    </div>
    <div style="margin-top: var(--app-gap);">
      <Button label="Перейти в чаты" icon="pi pi-comments" @click="goChats" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import Button from 'primevue/button'

const router = useRouter()

function goChats() {
  router.push('/chats')
}
</script>

