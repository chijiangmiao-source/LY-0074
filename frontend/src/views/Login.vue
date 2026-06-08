<template>
  <v-container fluid class="login-container d-flex align-center justify-center">
    <v-card class="login-card" elevation="24" width="420">
      <v-card-item>
        <div class="text-center mb-2">
          <v-icon size="56" color="primary">mdi-flower</v-icon>
        </div>
        <v-card-title class="text-center text-h5 font-weight-bold">
          花店花桶周转管理系统
        </v-card-title>
        <v-card-subtitle class="text-center text-medium-emphasis">
          连锁花店花桶周转与保鲜液补充管理
        </v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-form @submit.prevent="handleLogin" ref="loginForm">
          <v-text-field
            v-model="form.username"
            label="用户名"
            prepend-inner-icon="mdi-account"
            variant="outlined"
            :rules="[(v: string) => !!v || '请输入用户名']"
            hide-details="auto"
            class="mb-3"
          />
          <v-text-field
            v-model="form.password"
            label="密码"
            prepend-inner-icon="mdi-lock"
            :type="showPassword ? 'text' : 'password'"
            variant="outlined"
            :rules="[(v: string) => !!v || '请输入密码']"
            hide-details="auto"
            :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
            @click:append-inner="showPassword = !showPassword"
            class="mb-4"
          />
          <v-btn
            type="submit"
            block
            size="large"
            color="primary"
            variant="flat"
            :loading="loading"
            class="mb-3"
          >
            登 录
          </v-btn>
          <v-alert
            v-if="errorMsg"
            type="error"
            variant="tonal"
            density="comfortable"
            class="mb-0"
          >
            {{ errorMsg }}
          </v-alert>
        </v-form>
      </v-card-text>

      <v-divider />

      <v-card-actions class="justify-center py-3">
        <v-btn variant="text" size="small" color="primary" @click="initAdmin">
          初始化管理员账号
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ username: '', password: '' })
const showPassword = ref(false)
const loading = ref(false)
const errorMsg = ref('')
const loginForm = ref()

async function handleLogin() {
  errorMsg.value = ''
  const valid = await loginForm.value?.validate()
  if (!valid?.valid) return

  loading.value = true
  try {
    await auth.login(form.username, form.password)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (err: any) {
    errorMsg.value = typeof err === 'string' ? err : '登录失败，请检查账号密码'
  } finally {
    loading.value = false
  }
}

async function initAdmin() {
  try {
    const res = await authApi.initAdmin()
    alert(res.message)
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '初始化失败')
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  border-radius: 12px;
}
</style>
