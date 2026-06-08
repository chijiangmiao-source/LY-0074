<template>
  <div>
    <v-card elevation="2" class="mb-4" rounded="lg">
      <v-card-item>
        <div class="d-flex align-center justify-space-between">
          <div>
            <v-card-title class="text-h6">
              <v-icon start color="primary">mdi-history</v-icon>
              操作轨迹追踪
            </v-card-title>
            <v-card-subtitle>
              按门店、花桶、花材维度查询完整操作轨迹：入桶、回桶、补液、损耗
            </v-card-subtitle>
          </div>
        </div>
      </v-card-item>

      <v-divider />

      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="3">
            <v-select
              v-model="query.store_id"
              :items="storeOptions"
              item-title="store_name"
              item-value="_id"
              label="按门店筛选"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
              @update:model-value="onStoreChange"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="query.bucket_id"
              :items="filteredBucketOptions"
              item-title="bucket_code"
              item-value="_id"
              label="按花桶筛选"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
              :disabled="!storeOptions.length"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="query.flower_id"
              :items="filteredFlowerOptions"
              item-title="flower_name"
              item-value="_id"
              label="按花材筛选"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
              :disabled="!storeOptions.length"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="query.operation_type"
              :items="operationTypeOptions"
              item-title="label"
              item-value="value"
              label="操作类型"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-date-picker
              v-model="query.start_date"
              label="开始日期"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-date-picker
              v-model="query.end_date"
              label="结束日期"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-btn color="primary" variant="flat" class="me-2" @click="loadData">
              <v-icon start>mdi-magnify</v-icon>查询
            </v-btn>
            <v-btn variant="outlined" class="me-2" @click="resetQuery">
              <v-icon start>mdi-refresh</v-icon>重置
            </v-btn>
            <v-btn variant="tonal" color="success" :disabled="!selectedSummary" @click="exportSummary">
              <v-icon start>mdi-file-document-outline</v-icon>查看汇总
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 汇总信息 -->
    <v-card v-if="selectedSummary" elevation="2" class="mb-4" rounded="lg" color="success" theme="dark">
      <v-card-item>
        <v-card-title class="text-subtitle-1">筛选范围汇总</v-card-title>
      </v-card-item>
      <v-divider />
      <v-card-text>
        <v-row>
          <v-col cols="6" sm="3">
            <div class="text-caption text-opacity-75">入桶总计</div>
            <div class="text-h6 font-weight-bold mt-1">
              {{ selectedSummary.in_bucket }} 枝
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="text-caption text-opacity-75">回桶总计</div>
            <div class="text-h6 font-weight-bold mt-1">
              {{ selectedSummary.out_bucket }} 枝
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="text-caption text-opacity-75">补液总计</div>
            <div class="text-h6 font-weight-bold mt-1">
              {{ selectedSummary.preservation }} L
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="text-caption text-opacity-75">损耗总计</div>
            <div class="text-h6 font-weight-bold mt-1">
              {{ selectedSummary.loss }} 枝
            </div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 时间线展示 -->
    <v-card elevation="2" rounded="lg">
      <v-card-item>
        <div class="d-flex align-center justify-space-between">
          <div>
            <v-card-title class="text-subtitle-1">操作轨迹时间线</v-card-title>
            <v-card-subtitle>
              共 {{ total }} 条记录 · 按时间倒序排列
            </v-card-subtitle>
          </div>
          <v-btn-group variant="tonal" density="comfortable">
            <v-btn
              :active="viewMode === 'timeline'"
              @click="viewMode = 'timeline'"
            >
              <v-icon start>mdi-timeline-clock-outline</v-icon>时间线
            </v-btn>
            <v-btn
              :active="viewMode === 'table'"
              @click="viewMode = 'table'"
            >
              <v-icon start>mdi-table</v-icon>表格
            </v-btn>
          </v-btn-group>
        </div>
      </v-card-item>
      <v-divider />

      <!-- 表格视图 -->
      <div v-show="viewMode === 'table'">
        <v-table>
          <thead>
            <tr>
              <th>时间</th>
              <th>操作类型</th>
              <th>门店</th>
              <th>花桶</th>
              <th>花材</th>
              <th>数量</th>
              <th>详情</th>
              <th>操作人</th>
              <th>备注</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in data" :key="item.trace_id">
              <td class="text-caption">{{ formatDate(item.created_at) }}</td>
              <td>
                <v-chip
                  size="small"
                  variant="flat"
                  :color="opColor[item.operation_type]"
                  theme="dark"
                >
                  <v-icon start size="14">{{ opIcon[item.operation_type] }}</v-icon>
                  {{ item.operation_type_label }}
                </v-chip>
              </td>
              <td>{{ item.store_name || '-' }}</td>
              <td>{{ item.bucket_code || '-' }}</td>
              <td>
                <span v-if="item.flower_name">
                  {{ item.flower_name }}
                  <span class="text-caption text-medium-emphasis">({{ item.flower_code }})</span>
                </span>
                <span v-else>-</span>
              </td>
              <td>
                <span
                  :class="
                    item.operation_type === 'loss'
                      ? 'text-error'
                      : item.operation_type === 'preservation' || item.operation_type === 'in_bucket'
                      ? 'text-success'
                      : ''
                  "
                  class="font-weight-medium"
                >
                  {{ item.operation_type === 'loss' ? '-' : item.operation_type === 'out_bucket' ? '-' : '+' }}
                  {{ item.quantity }} {{ item.quantity_unit }}
                </span>
              </td>
              <td class="text-caption">{{ item.detail }}</td>
              <td>{{ item.operator || '-' }}</td>
              <td class="text-caption">{{ item.remark || '-' }}</td>
            </tr>
            <tr v-if="!loading && data.length === 0">
              <td colspan="9" class="text-center text-medium-emphasis py-8">
                <v-icon size="32" class="mb-2">mdi-clipboard-text-search-outline</v-icon>
                <div>暂无操作轨迹记录</div>
              </td>
            </tr>
          </tbody>
        </v-table>
      </div>

      <!-- 时间线视图 -->
      <div v-show="viewMode === 'timeline'">
        <v-card-text>
          <div v-if="!loading && data.length === 0" class="text-center text-medium-emphasis py-8">
            <v-icon size="32" class="mb-2">mdi-clipboard-text-search-outline</v-icon>
            <div>暂无操作轨迹记录</div>
          </div>
          <div v-else style="position: relative">
            <div
              v-for="(item, idx) in data"
              :key="item.trace_id"
              class="d-flex mb-6"
              :style="{ position: 'relative' }"
            >
              <!-- 时间线竖线 -->
              <div
                v-if="idx < data.length - 1"
                style="position: absolute; left: 15px; top: 36px; bottom: -24px; width: 2px; background: rgb(var(--v-theme-outline-variant))"
              ></div>

              <!-- 时间节点圆点 -->
              <div
                class="d-flex align-center justify-center rounded-circle me-4"
                :style="{
                  width: '32px',
                  height: '32px',
                  minWidth: '32px',
                  background: `rgb(var(--v-theme-${opColor[item.operation_type]}))`,
                  color: 'white',
                  zIndex: 1,
                }"
              >
                <v-icon size="16">{{ opIcon[item.operation_type] }}</v-icon>
              </div>

              <!-- 内容卡片 -->
              <v-card
                variant="outlined"
                class="flex-1"
                :color="opColor[item.operation_type]"
                style="border-left-width: 4px"
              >
                <v-card-item style="padding: 12px 16px">
                  <div class="d-flex align-start justify-space-between w-100 flex-wrap" style="gap: 8px">
                    <div>
                      <div class="d-flex align-center" style="gap: 8px">
                        <v-chip
                          size="small"
                          variant="flat"
                          :color="opColor[item.operation_type]"
                          theme="dark"
                        >
                          {{ item.operation_type_label }}
                        </v-chip>
                        <span class="text-caption text-medium-emphasis">
                          {{ formatDate(item.created_at) }}
                        </span>
                      </div>
                      <div class="font-weight-medium mt-2">{{ item.detail }}</div>
                      <div class="text-caption text-medium-emphasis mt-1" style="display: flex; gap: 12px; flex-wrap: wrap">
                        <span v-if="item.store_name">
                          <v-icon size="12">mdi-store</v-icon> {{ item.store_name }}
                        </span>
                        <span v-if="item.bucket_code">
                          <v-icon size="12">mdi-bucket-outline</v-icon> {{ item.bucket_code }}
                        </span>
                        <span v-if="item.flower_name">
                          <v-icon size="12">mdi-flower-outline</v-icon> {{ item.flower_name }} ({{ item.flower_code }})
                        </span>
                        <span v-if="item.operator">
                          <v-icon size="12">mdi-account</v-icon> {{ item.operator }}
                        </span>
                      </div>
                      <div v-if="item.remark" class="text-caption mt-1" style="color: rgb(var(--v-theme-on-surface-variant))">
                        备注：{{ item.remark }}
                      </div>
                    </div>
                    <div class="text-right">
                      <div
                        class="text-h6 font-weight-bold"
                        :class="
                          item.operation_type === 'loss'
                            ? 'text-error'
                            : item.operation_type === 'preservation' || item.operation_type === 'in_bucket'
                            ? 'text-success'
                            : ''
                        "
                      >
                        {{ item.operation_type === 'loss' ? '-' : item.operation_type === 'out_bucket' ? '-' : '+' }}
                        {{ item.quantity }} {{ item.quantity_unit }}
                      </div>
                    </div>
                  </div>
                </v-card-item>
              </v-card>
            </div>
          </div>
        </v-card-text>
      </div>

      <v-divider />

      <v-card-actions class="justify-space-between px-4">
        <span class="text-medium-emphasis text-caption">
          共 {{ total }} 条记录 · 第 {{ query.page }}/{{ totalPages }} 页
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

    <!-- 汇总对话框 -->
    <v-dialog v-model="summaryDialog" max-width="500">
      <v-card rounded="lg">
        <v-card-item>
          <v-card-title>筛选范围汇总统计</v-card-title>
        </v-card-item>
        <v-divider />
        <v-card-text>
          <v-list lines="two">
            <v-list-item>
              <template #prepend>
                <v-icon color="primary">mdi-arrow-down-bold-box-outline</v-icon>
              </template>
              <v-list-item-title class="font-weight-medium">入桶总计</v-list-item-title>
              <v-list-item-subtitle>花材入桶操作</v-list-item-subtitle>
              <template #append>
                <span class="text-success font-weight-bold">{{ selectedSummary?.in_bucket || 0 }} 枝</span>
              </template>
            </v-list-item>
            <v-divider />
            <v-list-item>
              <template #prepend>
                <v-icon color="info">mdi-arrow-up-bold-box-outline</v-icon>
              </template>
              <v-list-item-title class="font-weight-medium">回桶总计</v-list-item-title>
              <v-list-item-subtitle>花材从桶中取出</v-list-item-subtitle>
              <template #append>
                <span class="text-info font-weight-bold">{{ selectedSummary?.out_bucket || 0 }} 枝</span>
              </template>
            </v-list-item>
            <v-divider />
            <v-list-item>
              <template #prepend>
                <v-icon color="success">mdi-water-plus-outline</v-icon>
              </template>
              <v-list-item-title class="font-weight-medium">补液总计</v-list-item-title>
              <v-list-item-subtitle>保鲜液补充总量</v-list-item-subtitle>
              <template #append>
                <span class="text-success font-weight-bold">{{ selectedSummary?.preservation || 0 }} L</span>
              </template>
            </v-list-item>
            <v-divider />
            <v-list-item>
              <template #prepend>
                <v-icon color="error">mdi-alert-circle-outline</v-icon>
              </template>
              <v-list-item-title class="font-weight-medium">损耗总计</v-list-item-title>
              <v-list-item-subtitle>花材损耗数量</v-list-item-subtitle>
              <template #append>
                <span class="text-error font-weight-bold">{{ selectedSummary?.loss || 0 }} 枝</span>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-divider />
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="summaryDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { dashboardApi, type OperationTraceQuery } from '@/api/dashboard'
import { storeApi } from '@/api/store'
import { bucketApi } from '@/api/bucket'
import { flowerApi } from '@/api/flower'
import type { OperationTrace, OperationType, Store, Bucket, Flower } from '@/types'
import dayjs from 'dayjs'

const route = useRoute()

const loading = ref(false)
const data = ref<OperationTrace[]>([])
const total = ref(0)
const storeOptions = ref<Store[]>([])
const bucketOptions = ref<Bucket[]>([])
const flowerOptions = ref<Flower[]>([])
const viewMode = ref<'timeline' | 'table'>('timeline')
const summaryDialog = ref(false)

const query = reactive<OperationTraceQuery & { operation_type?: OperationType }>({
  page: 1,
  page_size: 30,
  store_id: '',
  bucket_id: '',
  flower_id: '',
  start_date: '',
  end_date: '',
  operation_type: undefined,
})

const operationTypeOptions = [
  { label: '入桶', value: 'in_bucket' },
  { label: '回桶', value: 'out_bucket' },
  { label: '补液', value: 'preservation' },
  { label: '损耗', value: 'loss' },
]

const opColor: Record<OperationType, string> = {
  in_bucket: 'primary',
  out_bucket: 'info',
  preservation: 'success',
  loss: 'error',
}

const opIcon: Record<OperationType, string> = {
  in_bucket: 'mdi-arrow-down-bold-box-outline',
  out_bucket: 'mdi-arrow-up-bold-box-outline',
  preservation: 'mdi-water-plus-outline',
  loss: 'mdi-alert-circle-outline',
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / (query.page_size || 30))))

const filteredBucketOptions = computed(() => {
  if (!query.store_id) return bucketOptions.value
  return bucketOptions.value
})

const filteredFlowerOptions = computed(() => {
  if (!query.store_id) return flowerOptions.value
  return flowerOptions.value
})

const selectedSummary = computed(() => {
  if (data.value.length === 0) return null
  const summary = {
    in_bucket: 0,
    out_bucket: 0,
    preservation: 0,
    loss: 0,
  }
  for (const item of data.value) {
    if (item.operation_type === 'preservation') {
      summary.preservation += item.quantity
    } else {
      summary[item.operation_type] += item.quantity
    }
  }
  return summary
})

function formatDate(d: string) {
  return dayjs(d).format('YYYY-MM-DD HH:mm:ss')
}

function onStoreChange() {
  query.bucket_id = ''
  query.flower_id = ''
}

function resetQuery() {
  query.page = 1
  query.store_id = ''
  query.bucket_id = ''
  query.flower_id = ''
  query.start_date = ''
  query.end_date = ''
  query.operation_type = undefined
  loadData()
}

function exportSummary() {
  summaryDialog.value = true
}

async function loadOptions() {
  try {
    const [s, b, f] = await Promise.all([
      storeApi.listAll(),
      bucketApi.listAll(),
      flowerApi.listAll(),
    ])
    storeOptions.value = s as any
    bucketOptions.value = b as any
    flowerOptions.value = f as any
  } catch {}
}

async function loadData() {
  loading.value = true
  try {
    const params: OperationTraceQuery = {
      page: query.page,
      page_size: query.page_size,
    }
    if (query.store_id) params.store_id = query.store_id
    if (query.bucket_id) params.bucket_id = query.bucket_id
    if (query.flower_id) params.flower_id = query.flower_id
    if (query.start_date) params.start_date = query.start_date
    if (query.end_date) params.end_date = query.end_date

    const res = await dashboardApi.operationTrace(params)
    let items = res.items
    if (query.operation_type) {
      items = items.filter((t) => t.operation_type === query.operation_type)
    }
    data.value = items
    total.value = query.operation_type ? items.length : res.total
  } finally {
    loading.value = false
  }
}

watch(
  () => route.query,
  (q) => {
    if (q.store_id && typeof q.store_id === 'string') {
      query.store_id = q.store_id
    }
    if (q.bucket_id && typeof q.bucket_id === 'string') {
      query.bucket_id = q.bucket_id
    }
    if (q.flower_id && typeof q.flower_id === 'string') {
      query.flower_id = q.flower_id
    }
  },
  { immediate: true }
)

onMounted(async () => {
  await loadOptions()
  loadData()
})
</script>
