import { createRouter, createWebHistory } from 'vue-router'
import Chats from '@/views/Chats.vue'
import Login from '@/views/Login.vue'
import SettingsLayout from '@/views/settings/SettingsLayout.vue'
import AppearanceSettings from '@/views/settings/AppearanceSettings.vue'
import AiContextSettings from '@/views/settings/AiContextSettings.vue'
import KnowledgeBaseSettings from '@/views/settings/KnowledgeBaseSettings.vue'
import MediaSettings from '@/views/settings/MediaSettings.vue'
import ProfileSettings from '@/views/settings/ProfileSettings.vue'
import UsersSettings from '@/views/settings/UsersSettings.vue'
import TelegramSettings from '@/views/settings/TelegramSettings.vue'
import BotSettings from '@/views/settings/BotSettings.vue'
import AiProvidersSettings from '@/views/settings/AiProvidersSettings.vue'
import NotFound from '@/views/NotFound.vue'

async function getMe() {
  try {
    const res = await fetch('/api/auth/me', { credentials: 'include' })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

const routes = [
  { path: '/', redirect: '/chats' },
  { path: '/login', component: Login },
  { path: '/chats/:id?', component: Chats },
  {
    path: '/settings',
    component: SettingsLayout,
    children: [
      { path: '', redirect: '/settings/profile' },
      { path: 'appearance', component: AppearanceSettings },
      { path: 'telegram', component: TelegramSettings },
      { path: 'bot', component: BotSettings },
      { path: 'ai', component: AiContextSettings },
      { path: 'ai-providers', component: AiProvidersSettings },
      { path: 'kb', component: KnowledgeBaseSettings },
      { path: 'media', component: MediaSettings },
      { path: 'profile', component: ProfileSettings },
      { path: 'users', component: UsersSettings }
    ]
  },
  { path: '/:pathMatch(.*)*', component: NotFound }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  const me = await getMe()
  const isAuthed = !!me

  if (to.path === '/login') {
    if (isAuthed) return '/chats'
    return true
  }

  if (!isAuthed) return '/login'
  
  // Если залогинен, но не админ и лезет в настройки
  if (to.path.startsWith('/settings') && me.role !== 'admin') {
    return '/chats'
  }
  
  return true
})

export default router
