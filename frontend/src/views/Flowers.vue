<template>
  <div>
    <v-card elevation="2" class="mb-4" rounded="lg">
      <v-card-item>
        <div class="d-flex align-center justify-space-between">
          <div>
            <v-card-title class="text-h6">花材管理</v-card-title>
            <v-card-subtitle>管理花材基础信息</v-card-subtitle>
          </div>
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()">
            新增花材
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
                label="花材编号/名称"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="query.category_id"
                :items="categoryOptions"
                item-title="category_name"
                item-value="_id"
                label="花材分类"
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
                v-model="query.preservation_status"
                :items="preservationOptions"
                label="保鲜状态"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
              />
            </v-col>
            <v-col cols="12">
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
            <th>花材编号</th>
            <th>花材名称</th>
            <th>分类</th>
            <th>所在花桶</th>
            <th>所属门店</th>
            <th>当前数量</th>
            <th>保鲜状态</th>
            <th>入桶日期</th>
            <th class="text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in data" :key="item._id">
            <td class="font-weight-medium">{{ item.flower_code }}</td>
            <td>{{ item.flower_name }}</td>
            <td>
              <v-chip size="small" variant="tonal" color="primary">
                {{ item.category?.category_name || '-' }}
              </v-chip>
            </td>
            <td>{{ item.bucket?.bucket_code || '-' }}</td>
            <td>{{ item.store?.store_name || '-' }}</td>
            <td>{{ item.current_quantity }} 枝</td>
            <td>
              <v-chip
                :color="preservationColor[item.preservation_status]"
                size="small"
                variant="flat"
              >
                {{ preservationLabel[item.preservation_status] }}
              </v-chip>
            </td>
            <td>{{ item.in_bucket_date ? formatDate(item.in_bucket_date) : '-' }}</td>
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

    <v-dialog v-model="dialogVisible" max-width="600" persistent>
      <v-card rounded="lg">
        <v-card-item>
          <v-card-title>{{ editing ? '编辑花材' : '新增花材' }}</v-card-title>
        </v-card-item>
        <v-divider />
        <v-form ref="formRef" @submit.prevent="submitForm">
          <v-card-text>
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="form.flower_code"
                  label="花材编号 *"
                  variant="outlined"
                  :rules="[(v: string) => !!v || '请输入花材编号']"
                  :disabled="editing"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="form.flower_name"
                  label="花材名称 *"
                  variant="outlined"
                  :rules="[(v: string) => !!v || '请输入花材名称']"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="6">
                <v-select
                  v-model="form.category_id"
                  :items="categoryOptions"
                  item-title="category_name"
                  item-value="_id"
                  label="花材分类 *"
                  variant="outlined"
                  :rules="[(v: string) => !!v || '请选择分类']"
                />
              </v-col>
              <v-col cols="6">
                <v-select
                  v-model="form.store_id"
                  :items="storeOptions"
                  item-title="store_name"
                  item-value="_id"
                  label="所属门店"
                  variant="outlined"
                  clearable
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="6">
                <v-select
                  v-model="form.bucket_id"
                  :items="bucketOptions"
                  item-title="bucket_code"
                  item-value="_id"
                  label="所在花桶"
                  variant="outlined"
                  clearable
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="form.current_quantity"
                  type="number"
                  label="当前数量(枝)"
                  variant="outlined"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="6">
                <v-select
                  v-model="form.preservation_status"
                  :items="preservationOptions"
                  label="保鲜状态"
                  variant="outlined"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="form.in_bucket_date"
                  label="入桶日期"
                  type="datetime-local"
                  variant="outlined"
                  clearable
                />
              </v-col>
            </v-row>
            <v-textarea
              v-model="form.remark"
              label="备注"
              variant="outlined"
              rows="2"
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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { flowerApi } from '@/api/flower'
import { categoryApi } from '@/api/category'
import { storeApi } from '@/api/store'
import { bucketApi } from '@/api/bucket'
import type {
  Flower,
  FlowerCategory,
  Store,
  Bucket,
  PreservationStatus,
  FlowerCreate,
  FlowerUpdate,
} from '@/types'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const data = ref<Flower[]>([])
const total = ref(0)
const categoryOptions = ref<FlowerCategory[]>([])
const storeOptions = ref<Store[]>([])
const bucketOptions = ref<Bucket[]>([])

const query = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  category_id: '',
  bucket_id: '',
  store_id: '',
  preservation_status: undefined as PreservationStatus | undefined,
})

const totalPages = computed(() => Math.ceil(total.value / query.page_size))

const preservationOptions: { title: string; value: PreservationStatus }[] = [
  { title: '新鲜', value: 'fresh' },
  { title: '一般', value: 'normal' },
  { title: '萎蔫', value: 'wilted' },
]
const preservationLabel: Record<PreservationStatus, string> = {
  fresh: '新鲜',
  normal: '一般',
  wilted: '萎蔫',
}
const preservationColor: Record<PreservationStatus, string> = {
  fresh: 'success',
  normal: 'warning',
  wilted: 'error',
}

const dialogVisible = ref(false)
const editing = ref(false)
const editId = ref<string | null>(null)
const formRef = ref()
const form = reactive<FlowerCreate>({
  flower_code: '',
  flower_name: '',
  category_id: '',
  bucket_id: '',
  store_id: '',
  current_quantity: 0,
  preservation_status: 'fresh',
  in_bucket_date: '',
  remark: '',
})

function formatDate(d: string) {
  return dayjs(d).format('YYYY-MM-DD HH:mm')
}

function resetForm() {
  Object.assign(form, {
    flower_code: '',
    flower_name: '',
    category_id: '',
    bucket_id: '',
    store_id: '',
    current_quantity: 0,
    preservation_status: 'fresh',
    in_bucket_date: '',
    remark: '',
  })
  editing.value = false
  editId.value = null
}

function openDialog(item?: Flower) {
  resetForm()
  if (item) {
    editing.value = true
    editId.value = item._id
    form.flower_code = item.flower_code
    form.flower_name = item.flower_name
    form.category_id = item.category?.id || ''
    form.bucket_id = item.bucket?.id || ''
    form.store_id = item.store?.id || ''
    form.current_quantity = item.current_quantity
    form.preservation_status = item.preservation_status
    form.in_bucket_date = item.in_bucket_date
      ? dayjs(item.in_bucket_date).format('YYYY-MM-DDTHH:mm')
      : ''
    form.remark = item.remark || ''
  }
  dialogVisible.value = true
}

function resetQuery() {
  query.page = 1
  query.keyword = ''
  query.category_id = ''
  query.bucket_id = ''
  query.store_id = ''
  query.preservation_status = undefined
  loadData()
}

async function loadOptions() {
  categoryOptions.value = await categoryApi.listAll()
  storeOptions.value = await storeApi.listAll()
  bucketOptions.value = await bucketApi.listAll()
}

async function loadBucketsByStore() {
  if (form.store_id) {
    bucketOptions.value = await bucketApi.listAll({ store_id: form.store_id })
  } else {
    bucketOptions.value = await bucketApi.listAll()
  }
}

watch(
  () => form.store_id,
  () => {
    loadBucketsByStore()
  }
)

async function loadData() {
  loading.value = true
  try {
    const q: any = { ...query }
    if (!q.category_id) delete q.category_id
    if (!q.bucket_id) delete q.bucket_id
    if (!q.store_id) delete q.store_id
    if (!q.preservation_status) delete q.preservation_status
    const res = await flowerApi.list(q)
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
    const payload: any = { ...form }
    if (!payload.bucket_id) payload.bucket_id = undefined
    if (!payload.store_id) payload.store_id = undefined
    if (!payload.in_bucket_date) payload.in_bucket_date = undefined

    if (editing.value && editId.value) {
      const d: FlowerUpdate = payload
      await flowerApi.update(editId.value, d)
    } else {
      await flowerApi.create(payload)
    }
    dialogVisible.value = false
    loadData()
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '操作失败')
  } finally {
    submitting.value = false
  }
}

async function deleteItem(item: Flower) {
  if (!confirm(`确定删除花材「${item.flower_name}」吗？`)) return
  try {
    await flowerApi.delete(item._id)
    loadData()
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '删除失败')
  }
}

onMounted(async () => {
  await loadOptions()
  loadData()
})
</script>
