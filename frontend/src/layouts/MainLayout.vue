<template>
  <v-app>
    <v-app-bar app color="primary" dark height="64">
      <v-btn variant="text" @click="drawer = !drawer" class="me-2">
        <v-icon>mdi-menu</v-icon>
      </v-btn>
      <v-icon size="28" class="me-2">mdi-flower</v-icon>
      <v-toolbar-title class="text-h6 font-weight-medium">
        花店花桶周转管理系统
      </v-toolbar-title>

      <v-spacer />

      <v-btn variant="text" class="me-2">
        <v-icon start>mdi-bell-outline</v-icon>
      </v-btn>

      <v-menu offset="12, 12" location="bottom end">
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" variant="text">
            <v-icon start>mdi-account-circle</v-icon>
            {{ auth.user?.full_name || auth.user?.username || '用户' }}
            <v-icon end size="18">mdi-chevron-down</v-icon>
          </v-btn>
        </template>
        <v-list density="compact" min-width="160">
          <v-list-item
            prepend-icon="mdi-account-outline"
            :title="auth.user?.username"
            :subtitle="auth.user?.is_admin ? '管理员' : '普通用户'"
          />
          <v-divider />
          <v-list-item
            prepend-icon="mdi-logout"
            title="退出登录"
            @click="handleLogout"
          />
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" app width="240">
      <v-list nav density="comfortable">
        <v-list-item
          v-for="item in menuItems"
          :key="item.to"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          color="primary"
          :rounded="'lg'"
          class="my-1"
        />
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid class="pa-6">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </v-container>
    </v-main>

    <v-footer app class="py-2 text-center text-medium-emphasis" height="36">
      <span class="text-caption">连锁花店花桶周转与保鲜液补充管理系统 v1.0.0</span>
    </v-footer>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const drawer = ref(true)

const menuItems = computed(() => [
  { to: '/dashboard', title: '数据看板', icon: 'mdi-view-dashboard' },
  { to: '/stores', title: '门店管理', icon: 'mdi-store' },
  { to: '/buckets', title: '花桶档案', icon: 'mdi-bucket-outline' },
  { to: '/categories', title: '花材分类', icon: 'mdi-tag-multiple-outline' },
  { to: '/flowers', title: '花材管理', icon: 'mdi-flower-outline' },
  { to: '/records', title: '业务记录', icon: 'mdi-clipboard-list-outline' },
])

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style lang="scss" scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
