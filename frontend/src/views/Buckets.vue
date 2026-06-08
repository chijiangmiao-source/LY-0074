<template>
  <div>
    <v-card elevation="2" class="mb-4" rounded="lg">
      <v-card-item>
        <div class="d-flex align-center justify-space-between">
          <div>
            <v-card-title class="text-h6">花桶档案</v-card-title>
            <v-card-subtitle>管理花桶档案信息</v-card-subtitle>
          </div>
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()">
            新增花桶
          </v-btn>
        </div>
      </v-card-item>

      <v-divider />

      <v-card-text>
        <v-form inline>
          <v-row align="center">
            <v-col cols="12" md="3">
              <v-text-field
                v-model="query.keyword"
                label="桶编号/责任人"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="query.store_id"
                :items="storeOptions"
                item-title="store_name"
                item-value="_id"
                label="所属门店"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="query.status"
                :items="statusOptions"
                label="桶体状态"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
              />
            </v-col>
            <v-col cols="12" md="3">
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
            <th>桶编号</th>
            <th>所属门店</th>
            <th>容量</th>
            <th>当前数量</th>
            <th>液位</th>
            <th>桶体状态</th>
            <th>责任人</th>
            <th>更新时间</th>
            <th class="text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in data" :key="item._id">
            <td class="font-weight-medium">{{ item.bucket_code }}</td>
            <td>{{ item.store?.store_name || '-' }}</td>
            <td>{{ item.capacity }} L</td>
            <td>{{ item.current_quantity }} L</td>
            <td>
              <v-progress-linear
                :model-value="getUtilization(item)"
                :color="getUtilization(item) > 80 ? 'error' : getUtilization(item) > 50 ? 'warning' : 'success'"
                height="8"
                rounded
                class="my-1"
              >
                <template v-slot:default="{ value }">
                  <span class="text-caption" style="line-height: 8px">{{ value }}%</span>
                </template>
              </v-progress-linear>
            </td>
            <td>
              <v-chip
                :color="statusColor[item.status]"
                size="small"
                variant="flat"
              >
                {{ statusLabel[item.status] }}
              </v-chip>
            </td>
            <td>{{ item.responsible_person || '-' }}</td>
            <td>{{ formatDate(item.updated_at) }}</td>
            <td class="text-center">
              <v-btn variant="text" size="small" color="primary" @click="openDialog(item)">
                编辑
              </v-btn>
              <v-btn variant="text" size="small" color="error" @click="deleteItem(item)">
                删除
              </v-btn>
            </td>
          </tr>
          <tr v-if="!loading && data.length === 0">
            <td colspan="9" class="text-center text-medium-emphasis py-8">暂无数据</td>
          </tr>
        </tbody>
      </v-table>

      <v-divider />

      <v-card-actions class="justify-space-between px-4">
        <span class="text-medium-emphasis text-caption">共 {{ total }} 条记录</span>
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
          <v-card-title>{{ editing ? '编辑花桶' : '新增花桶' }}</v-card-title>
        </v-card-item>
        <v-divider />
        <v-form ref="formRef" @submit.prevent="submitForm">
          <v-card-text>
            <v-text-field
              v-model="form.bucket_code"
              label="桶编号 *"
              variant="outlined"
              counter
              maxlength="20"
              :rules="[
                (v: string) => !!v || '请输入桶编号',
                (v: string) => (v && v.length <= 20) || '桶编号不能超过20个字符',
                (v: string) => /^[A-Za-z0-9_-]+$/.test(v) || '桶编号只能包含字母、数字、下划线和短横线',
              ]"
              :disabled="editing"
              class="mb-3"
            />
            <v-select
              v-model="form.store_id"
              :items="storeOptions"
              item-title="store_name"
              item-value="_id"
              label="所属门店 *"
              variant="outlined"
              :rules="[(v: string) => !!v || '请选择门店']"
              class="mb-3"
            />
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model.number="form.capacity"
                  type="number"
                  label="桶体容量(L) *"
                  variant="outlined"
                  min="0.1"
                  max="1000"
                  step="0.1"
                  :rules="[
                    (v: number) => (v && v > 0) || '容量必须大于0',
                    (v: number) => !v || v <= 1000 || '容量不能超过1000L',
                  ]"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="form.current_quantity"
                  type="number"
                  label="当前数量(L)"
                  variant="outlined"
                  min="0"
                  max="1000"
                  step="0.1"
                  :rules="[
                    (v: number) => v === undefined || v === null || v >= 0 || '当前数量不能为负数',
                  ]"
                />
              </v-col>
            </v-row>
            <v-row class="mt-1">
              <v-col cols="6">
                <v-select
                  v-model="form.status"
                  :items="statusOptions"
                  label="桶体状态"
                  variant="outlined"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="form.responsible_person"
                  label="责任人"
                  variant="outlined"
                  counter
                  maxlength="20"
                  :rules="[(v: string) => !v || v.length <= 20 || '责任人姓名不能超过20个字符']"
                />
              </v-col>
            </v-row>
            <v-textarea
              v-model="form.remark"
              label="备注"
              variant="outlined"
              rows="2"
              counter
              maxlength="200"
              :rules="[(v: string) => !v || v.length <= 200 || '备注不能超过200个字符']"
              class="mt-2"
            />
          </v-card-text>
          <v-divider />
          <v-card-actions class="justify-end">
            <v-btn variant="text" @click="dialogVisible = false">取消</v-btn>
            <v-btn color="primary" type="submit" :loading="submitting">确定</v-btn>
          </v-card-actions>
        </v-form>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { bucketApi } from '@/api/bucket'
import { storeApi } from '@/api/store'
import type { Bucket, BucketStatus, BucketCreate, BucketUpdate, Store } from '@/types'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const data = ref<Bucket[]>([])
const total = ref(0)
const storeOptions = ref<Store[]>([])

const query = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  store_id: '',
  status: undefined as BucketStatus | undefined,
})

const totalPages = computed(() => Math.ceil(total.value / query.page_size))

const statusOptions: { title: string; value: BucketStatus }[] = [
  { title: '启用', value: 'active' },
  { title: '停用', value: 'inactive' },
  { title: '维修中', value: 'maintenance' },
]
const statusLabel: Record<BucketStatus, string> = {
  active: '启用',
  inactive: '停用',
  maintenance: '维修中',
}
const statusColor: Record<BucketStatus, string> = {
  active: 'success',
  inactive: 'error',
  maintenance: 'warning',
}

const dialogVisible = ref(false)
const editing = ref(false)
const editId = ref<string | null>(null)
const formRef = ref()
const form = reactive<BucketCreate>({
  bucket_code: '',
  store_id: '',
  capacity: 0,
  current_quantity: 0,
  status: 'active',
  responsible_person: '',
  remark: '',
})

function formatDate(d: string) {
  return dayjs(d).format('YYYY-MM-DD HH:mm')
}

function getUtilization(b: Bucket) {
  if (!b.capacity) return 0
  return Math.round((b.current_quantity / b.capacity) * 100)
}

function resetForm() {
  form.bucket_code = ''
  form.store_id = ''
  form.capacity = 0
  form.current_quantity = 0
  form.status = 'active'
  form.responsible_person = ''
  form.remark = ''
  editing.value = false
  editId.value = null
}

async function openDialog(item?: Bucket) {
  resetForm()
  if (storeOptions.value.length === 0) {
    storeOptions.value = await storeApi.listAll()
  }
  if (item) {
    editing.value = true
    editId.value = item._id
    form.bucket_code = item.bucket_code
    form.store_id = item.store?.id || ''
    form.capacity = item.capacity
    form.current_quantity = item.current_quantity
    form.status = item.status
    form.responsible_person = item.responsible_person || ''
    form.remark = item.remark || ''
  }
  dialogVisible.value = true
}

function resetQuery() {
  query.page = 1
  query.keyword = ''
  query.store_id = ''
  query.status = undefined
  loadData()
}

async function loadStores() {
  storeOptions.value = await storeApi.listAll()
}

async function loadData() {
  loading.value = true
  try {
    const q: any = { ...query }
    if (!q.store_id) delete q.store_id
    if (!q.status) delete q.status
    const res = await bucketApi.list(q)
    data.value = res.items as any
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
      const d: BucketUpdate = { ...form }
      await bucketApi.update(editId.value, d)
    } else {
      await bucketApi.create({ ...form })
    }
    dialogVisible.value = false
    query.page = 1
    loadData()
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '操作失败')
  } finally {
    submitting.value = false
  }
}

async function deleteItem(item: Bucket) {
  if (!confirm(`确定删除花桶「${item.bucket_code}」吗？`)) return
  try {
    await bucketApi.delete(item._id)
    query.page = 1
    loadData()
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '删除失败')
  }
}

onMounted(async () => {
  await loadStores()
  loadData()
})
</script>
