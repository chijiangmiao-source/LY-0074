<template>
  <div>
    <v-card elevation="2" class="mb-4" rounded="lg">
      <v-card-item>
        <div class="d-flex align-center justify-space-between flex-wrap" style="gap: 12px">
          <div>
            <v-card-title class="text-h6">
              <v-icon start color="primary">mdi-account-clock-outline</v-icon>
              责任追踪详情
            </v-card-title>
            <v-card-subtitle>
              查看某个花桶、花材、预警或批次在整个处理过程中的责任人流转情况
            </v-card-subtitle>
          </div>
          <router-link to="/performance">
            <v-btn variant="outlined" size="small">
              <v-icon start>mdi-arrow-left</v-icon>返回绩效排名
            </v-btn>
          </router-link>
        </div>
      </v-card-item>

      <v-divider />

      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="3">
            <v-select
              v-model="query.target_type"
              :items="targetTypeOptions"
              item-title="label"
              item-value="value"
              label="目标类型"
              variant="outlined"
              density="comfortable"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="query.target_id"
              :label="targetLabel"
              variant="outlined"
              density="comfortable"
              hide-details
              placeholder="请输入目标ID或批次号"
              clearable
              @keyup.enter="loadData"
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
      </v-card-text>
    </v-card>

    <v-card v-if="traceData.target_id" elevation="2" class="mb-4" rounded="lg">
      <v-card-item>
        <v-card-title class="text-subtitle-1">目标信息</v-card-title>
      </v-card-item>
      <v-divider />
      <v-card-text>
        <v-chip
          size="small"
          variant="flat"
          :color="targetTypeColor"
          theme="dark"
          class="me-2"
        >
          {{ traceData.target_type_label }}
        </v-chip>
        <v-chip v-if="traceData.target_info.batch_no || traceData.batch_no" size="small" variant="tonal" color="info" class="me-2">
          批次: {{ traceData.target_info.batch_no || traceData.batch_no }}
        </v-chip>
        <v-chip size="small" variant="tonal" color="secondary" class="me-2">
          目标ID: {{ traceData.target_id }}
        </v-chip>

        <v-row class="mt-3">
          <v-col v-for="(v, k) in displayTargetInfo" :key="k" cols="6" sm="4" md="3">
            <div class="text-caption text-medium-emphasis">{{ v.label }}</div>
            <div class="font-weight-medium">{{ v.value || '-' }}</div>
          </v-col>
        </v-row>

        <v-divider class="my-3" />

        <div>
          <div class="d-flex align-center" style="gap: 16px">
            <div>
              <div class="text-caption text-medium-emphasis">参与处理的责任人数</div>
              <div class="text-h6 font-weight-bold text-primary mt-1">{{ uniqueOperators.length }} 人</div>
            </div>
            <v-divider vertical style="height: 40px" />
            <div>
              <div class="text-caption text-medium-emphasis">责任流转次数</div>
              <div class="text-h6 font-weight-bold text-info mt-1">{{ traceData.total }} 次</div>
            </div>
            <v-divider vertical style="height: 40px" />
            <div>
              <div class="text-caption text-medium-emphasis">处理时长</div>
              <div class="text-h6 font-weight-bold text-success mt-1">{{ handleDuration }}</div>
            </div>
          </div>
          <div v-if="uniqueOperators.length" class="mt-3">
            <div class="text-caption text-medium-emphasis mb-2">责任流转链：</div>
            <div class="d-flex align-center flex-wrap" style="gap: 8px">
              <template v-for="(op, idx) in uniqueOperators" :key="op.id || op.name">
                <v-chip size="small" variant="tonal" color="primary">
                  <v-icon start size="14">mdi-account</v-icon>
                  {{ op.name }}
                  <span class="text-caption ms-1 text-medium-emphasis">({{ op.position || '-' }})</span>
                </v-chip>
                <v-icon v-if="idx < uniqueOperators.length - 1" size="18" class="text-medium-emphasis">mdi-arrow-right</v-icon>
              </template>
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <v-card elevation="2" rounded="lg">
      <v-card-item>
        <v-card-title class="text-subtitle-1">责任流转时间线</v-card-title>
        <v-card-subtitle>共 {{ traceData.total }} 条记录 · 按时间顺序展示完整处理过程</v-card-subtitle>
      </v-card-item>
      <v-divider />
      <v-card-text>
        <div v-if="traceData.traces.length === 0 && !loading" class="text-center text-medium-emphasis py-8">
          <v-icon size="32" class="mb-2">mdi-clipboard-text-search-outline</v-icon>
          <div>请选择目标类型并输入目标ID后查询</div>
        </div>
        <div v-else style="position: relative">
          <div
            v-for="(t, idx) in traceData.traces"
            :key="t._id"
            class="d-flex mb-6"
            style="position: relative"
          >
            <div
              v-if="idx < traceData.traces.length - 1"
              style="position: absolute; left: 15px; top: 36px; bottom: -24px; width: 2px; background: rgb(var(--v-theme-outline-variant))"
            ></div>
            <div
              class="d-flex align-center justify-center rounded-circle me-4"
              :style="{ width: '32px', height: '32px', minWidth: '32px', background: `rgb(var(--v-theme-${actionColor[t.action]}))`, color: 'white', zIndex: 1 }"
            >
              <v-icon size="16">{{ actionIcon[t.action] }}</v-icon>
            </div>
            <v-card variant="outlined" class="flex-1" :color="actionColor[t.action]" style="border-left-width: 4px">
              <v-card-item style="padding: 16px">
                <div class="d-flex align-start justify-space-between w-100 flex-wrap" style="gap: 12px">
                  <div class="flex-1">
                    <div class="d-flex align-center flex-wrap" style="gap: 8px">
                      <v-chip size="small" variant="flat" :color="actionColor[t.action]" theme="dark">
                        <v-icon start size="14">{{ actionIcon[t.action] }}</v-icon>
                        {{ t.action_label }}
                      </v-chip>
                      <span class="text-caption text-medium-emphasis">
                        <v-icon size="12">mdi-clock-outline</v-icon>
                        {{ formatDate(t.created_at) }}
                      </span>
                      <span v-if="t.batch_no">
                        <v-chip size="small" variant="tonal" color="info">
                          <v-icon start size="14">mdi-package-variant-closed</v-icon>
                          批次: {{ t.batch_no }}
                        </v-chip>
                      </span>
                    </div>
                    <div class="font-weight-medium mt-3">{{ t.remark || t.action_label }}</div>
                    <div class="text-caption text-medium-emphasis mt-2" style="display: flex; gap: 16px; flex-wrap: wrap">
                      <span v-if="t.store?.store_name">
                        <v-icon size="12">mdi-store</v-icon> {{ t.store.store_name }}
                        <span v-if="t.store.store_code" class="text-medium-emphasis">({{ t.store.store_code }})</span>
                      </span>
                      <span v-if="t.bucket?.bucket_code">
                        <v-icon size="12">mdi-bucket-outline</v-icon> 花桶 {{ t.bucket.bucket_code }}
                      </span>
                      <span v-if="t.flower?.flower_name">
                        <v-icon size="12">mdi-flower-outline</v-icon> {{ t.flower.flower_name }}
                        <span v-if="t.flower.flower_code" class="text-medium-emphasis">({{ t.flower.flower_code }})</span>
                      </span>
                      <span v-if="t.warning?.message">
                        <v-icon size="12">mdi-alert-outline</v-icon> {{ t.warning.message }}
                      </span>
                    </div>
                  </div>
                  <div class="text-right" style="min-width: 140px">
                    <div class="d-flex align-center justify-end" style="gap: 6px">
                      <v-icon size="16" class="text-medium-emphasis">mdi-account</v-icon>
                      <span class="font-weight-medium">
                        {{ t.operator?.full_name || t.operator_name || '-' }}
                      </span>
                    </div>
                    <div class="text-caption text-medium-emphasis mt-1">
                      {{ t.operator?.position_label || t.operator_position_label || '-' }}
                    </div>
                    <v-chip v-if="idx === 0" size="small" variant="flat" color="primary" theme="dark" class="mt-2">
                      <v-icon start size="12">mdi-flag</v-icon>起始
                    </v-chip>
                    <v-chip v-else-if="idx === traceData.traces.length - 1" size="small" variant="flat" color="success" theme="dark" class="mt-2">
                      <v-icon start size="12">mdi-check</v-icon>当前
                    </v-chip>
                  </div>
                </div>
              </v-card-item>
            </v-card>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { performanceApi } from '@/api/performance'
import type { ResponsibilityTraceResponse } from '@/types'
import dayjs from 'dayjs'

const route = useRoute()
const loading = ref(false)

const targetTypeOptions = [
  { label: '花桶', value: 'bucket' },
  { label: '花材', value: 'flower' },
  { label: '预警', value: 'warning' },
  { label: '批次', value: 'batch' },
]

const targetLabelMap: Record<string, string> = {
  bucket: '花桶ID',
  flower: '花材ID',
  warning: '预警ID',
  batch: '批次号',
}

const actionColor: Record<string, string> = {
  assign: 'secondary',
  in_bucket: 'primary',
  out_bucket: 'info',
  preservation: 'success',
  loss: 'error',
  warning_handle: 'warning',
  inspection: 'purple',
  transfer: 'deep-orange',
  complete: 'green',
}

const actionIcon: Record<string, string> = {
  assign: 'mdi-account-arrow-right',
  in_bucket: 'mdi-arrow-down-bold-box-outline',
  out_bucket: 'mdi-arrow-up-bold-box-outline',
  preservation: 'mdi-water-plus-outline',
  loss: 'mdi-alert-circle-outline',
  warning_handle: 'mdi-alert-check-outline',
  inspection: 'mdi-clipboard-check-outline',
  transfer: 'mdi-swap-horizontal',
  complete: 'mdi-check-circle-outline',
}

const query = reactive<{ target_type: 'bucket' | 'flower' | 'warning' | 'batch'; target_id: string }>({
  target_type: 'flower',
  target_id: '',
})

const traceData = reactive<ResponsibilityTraceResponse>({
  target_type: '',
  target_type_label: '',
  target_id: '',
  target_info: {},
  traces: [],
  total: 0,
})

const targetLabel = computed(() => targetLabelMap[query.target_type] || '目标ID')

const targetTypeColor = computed(() => {
  const colorMap: Record<string, string> = {
    bucket: 'primary',
    flower: 'success',
    warning: 'warning',
    batch: 'info',
  }
  return colorMap[traceData.target_type] || 'secondary'
})

const displayTargetInfo = computed(() => {
  const info: Record<string, { label: string; value: any }> = {}
  const raw = traceData.target_info || {}
  const labelMap: Record<string, string> = {
    bucket_code: '花桶编号',
    capacity: '容量(L)',
    current_quantity: '当前液位(L)',
    status: '状态',
    store_name: '所属门店',
    responsible_person: '负责人',
    flower_code: '花材编号',
    flower_name: '花材名称',
    batch_no: '批次号',
    preservation_status: '保鲜状态',
    warning_type_label: '预警类型',
    severity: '严重程度',
    message: '预警信息',
    flower_count: '批次花材数',
  }
  for (const [k, v] of Object.entries(raw)) {
    if (k === 'id' || k === 'flowers') continue
    info[k] = { label: labelMap[k] || k, value: v }
  }
  return info
})

const uniqueOperators = computed(() => {
  const seen = new Set<string>()
  const ops: { id: string; name: string; position: string }[] = []
  for (const t of traceData.traces) {
    const id = t.operator?.id || t.operator_name || ''
    if (!id || seen.has(id)) continue
    seen.add(id)
    ops.push({
      id,
      name: t.operator?.full_name || t.operator_name || '-',
      position: t.operator?.position_label || t.operator_position_label || '-',
    })
  }
  return ops
})

const handleDuration = computed(() => {
  if (traceData.traces.length < 2) return '-'
  const start = dayjs(traceData.traces[0].created_at)
  const end = dayjs(traceData.traces[traceData.traces.length - 1].created_at)
  const hours = end.diff(start, 'hour')
  if (hours < 1) {
    const mins = end.diff(start, 'minute')
    return `${mins} 分钟`
  }
  if (hours < 24) return `${hours} 小时`
  const days = Math.floor(hours / 24)
  const remainHours = hours % 24
  return `${days} 天 ${remainHours} 小时`
})

function formatDate(d: string) {
  return dayjs(d).format('YYYY-MM-DD HH:mm:ss')
}

function resetQuery() {
  query.target_type = 'flower'
  query.target_id = ''
  traceData.traces = []
  traceData.target_id = ''
  traceData.target_info = {}
  traceData.total = 0
}

async function loadData() {
  if (!query.target_id) return
  loading.value = true
  try {
    const res = await performanceApi.trace({
      target_type: query.target_type,
      target_id: query.target_id,
    })
    Object.assign(traceData, res)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (route.query.target_type && typeof route.query.target_type === 'string') {
    query.target_type = route.query.target_type as any
  }
  if (route.query.target_id && typeof route.query.target_id === 'string') {
    query.target_id = route.query.target_id
    loadData()
  }
})
</script>
