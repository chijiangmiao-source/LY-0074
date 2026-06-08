<template>
  <div>
    <v-card elevation="2" class="mb-4" rounded="lg">
      <v-card-item>
        <div class="d-flex align-center justify-space-between">
          <div>
            <v-card-title class="text-h6">门店管理</v-card-title>
            <v-card-subtitle>管理连锁门店信息</v-card-subtitle>
          </div>
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()">
            新增门店
          </v-btn>
        </div>
      </v-card-item>

      <v-divider />

      <v-card-text>
        <v-form inline>
          <v-row align="center">
            <v-col cols="12" md="4">
              <v-text-field
                v-model="query.keyword"
                label="搜索门店编号/名称"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
                @keyup.enter="loadData"
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="query.is_active"
                :items="statusOptions"
                label="状态"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
              />
            </v-col>
            <v-col cols="12" md="5">
              <v-btn color="primary" variant="flat" class="me-2" @click="loadData">
                <v-icon start>mdi-magnify</v-icon>查询
              </v-btn>
              <v-btn variant="outlined" @click="resetQuery">
                <v-icon start>mdi-refresh</v-icon>重置
              </v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <v-card elevation="2" rounded="lg">
      <v-table>
        <thead>
          <tr>
            <th>门店编号</th>
            <th>门店名称</th>
            <th>地址</th>
            <th>联系电话</th>
            <th>负责人</th>
            <th>状态</th>
            <th>创建时间</th>
            <th class="text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in data" :key="item._id">
            <td class="font-weight-medium">{{ item.store_code }}</td>
            <td>{{ item.store_name }}</td>
            <td>{{ item.address || '-' }}</td>
            <td>{{ item.phone || '-' }}</td>
            <td>{{ item.manager || '-' }}</td>
            <td>
              <v-chip
                :color="item.is_active ? 'success' : 'error'"
                size="small"
                variant="flat"
              >
                {{ item.is_active ? '启用' : '停用' }}
              </v-chip>
            </td>
            <td>{{ formatDate(item.created_at) }}</td>
            <td class="text-center">
              <v-btn
                variant="text"
                size="small"
                color="primary"
                @click="openDialog(item)"
              >
                编辑
              </v-btn>
              <v-btn
                variant="text"
                size="small"
                color="error"
                @click="deleteItem(item)"
              >
                删除
              </v-btn>
            </td>
          </tr>
          <tr v-if="!loading && data.length === 0">
            <td colspan="8" class="text-center text-medium-emphasis py-8">
              暂无数据
            </td>
          </tr>
        </tbody>
      </v-table>

      <v-divider />

      <v-card-actions class="justify-space-between px-4">
        <span class="text-medium-emphasis text-caption">
          共 {{ total }} 条记录
        </span>
        <v-pagination
          v-model="query.page"
          :length="totalPages"
          :total-visible="7"
          @update:model-value="loadData"
          size="small"
        />
      </v-card-actions>
    </v-card>

    <v-dialog v-model="dialogVisible" max-width="560" persistent>
      <v-card rounded="lg">
        <v-card-item>
          <v-card-title>{{ editing ? '编辑门店' : '新增门店' }}</v-card-title>
        </v-card-item>
        <v-divider />
        <v-form ref="formRef" @submit.prevent="submitForm">
          <v-card-text>
            <v-text-field
              v-model="form.store_code"
              label="门店编号 *"
              variant="outlined"
              :rules="[(v: string) => !!v || '请输入门店编号']"
              :disabled="editing"
              class="mb-3"
            />
            <v-text-field
              v-model="form.store_name"
              label="门店名称 *"
              variant="outlined"
              :rules="[(v: string) => !!v || '请输入门店名称']"
              class="mb-3"
            />
            <v-text-field
              v-model="form.address"
              label="地址"
              variant="outlined"
              class="mb-3"
            />
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="form.phone"
                  label="联系电话"
                  variant="outlined"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="form.manager"
                  label="负责人"
                  variant="outlined"
                />
              </v-col>
            </v-row>
            <v-select
              v-model="form.is_active"
              :items="statusOptions"
              label="状态"
              variant="outlined"
            />
          </v-card-text>
          <v-divider />
          <v-card-actions class="justify-end">
            <v-btn variant="text" @click="dialogVisible = false">取消</v-btn>
            <v-btn color="primary" type="submit" :loading="submitting">
              确定
            </v-btn>
          </v-card-actions>
        </v-form>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { storeApi } from '@/api/store'
import type { Store, StoreCreate, StoreUpdate } from '@/types'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const data = ref<Store[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  is_active: undefined as boolean | undefined,
})

const totalPages = computed(() => Math.ceil(total.value / query.page_size))

const statusOptions = [
  { title: '启用', value: true },
  { title: '停用', value: false },
]

const dialogVisible = ref(false)
const editing = ref(false)
const editId = ref<string | null>(null)
const formRef = ref()
const form = reactive<StoreCreate>({
  store_code: '',
  store_name: '',
  address: '',
  phone: '',
  manager: '',
  is_active: true,
})

function formatDate(d: string) {
  return dayjs(d).format('YYYY-MM-DD HH:mm')
}

function resetForm() {
  form.store_code = ''
  form.store_name = ''
  form.address = ''
  form.phone = ''
  form.manager = ''
  form.is_active = true
  editing.value = false
  editId.value = null
}

function openDialog(item?: Store) {
  resetForm()
  if (item) {
    editing.value = true
    editId.value = item._id
    Object.assign(form, item)
  }
  dialogVisible.value = true
}

function resetQuery() {
  query.page = 1
  query.keyword = ''
  query.is_active = undefined
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const res = await storeApi.list(query)
    data.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  const valid = await formRef.value?.validate()
  if (!valid?.valid) return
  submitting.value = true
  try {
    if (editing.value && editId.value) {
      const d: StoreUpdate = { ...form }
      await storeApi.update(editId.value, d)
    } else {
      await storeApi.create({ ...form })
    }
    dialogVisible.value = false
    loadData()
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '操作失败')
  } finally {
    submitting.value = false
  }
}

async function deleteItem(item: Store) {
  if (!confirm(`确定删除门店「${item.store_name}」吗？`)) return
  try {
    await storeApi.delete(item._id)
    loadData()
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '删除失败')
  }
}

onMounted(loadData)
</script>
