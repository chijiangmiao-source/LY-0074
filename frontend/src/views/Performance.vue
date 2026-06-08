<template>
  <div>
    <v-card elevation="2" class="mb-4" rounded="lg">
      <v-card-item>
        <div class="d-flex align-center justify-space-between flex-wrap" style="gap: 12px">
          <div>
            <v-card-title class="text-h6">
              <v-icon start color="primary">mdi-account-tie</v-icon>
              员工绩效与责任追踪
            </v-card-title>
            <v-card-subtitle>
              自动统计员工工作量、操作及时率、异常处理时效和责任损耗数据，支持按门店、岗位、时间范围查询排名
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
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="query.position"
              :items="positionOptions"
              item-title="label"
              item-value="code"
              label="按岗位筛选"
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
          <v-col cols="12" md="3">
            <v-select
              v-model="query.sort_by"
              :items="sortOptions"
              item-title="label"
              item-value="value"
              label="排序方式"
              variant="outlined"
              density="comfortable"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="9">
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

    <v-row class="mb-4">
      <v-col cols="6" sm="3">
        <v-card elevation="2" rounded="lg" color="primary" theme="dark">
          <v-card-text>
            <div class="text-caption text-opacity-75">统计员工数</div>
            <div class="text-h4 font-weight-bold mt-1">{{ summary.total_employees }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card elevation="2" rounded="lg" color="info" theme="dark">
          <v-card-text>
            <div class="text-caption text-opacity-75">总操作量</div>
            <div class="text-h4 font-weight-bold mt-1">{{ summary.total_operations }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card elevation="2" rounded="lg" color="success" theme="dark">
          <v-card-text>
            <div class="text-caption text-opacity-75">平均及时率</div>
            <div class="text-h4 font-weight-bold mt-1">{{ summary.avg_on_time_rate }}%</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card elevation="2" rounded="lg" color="error" theme="dark">
          <v-card-text>
            <div class="text-caption text-opacity-75">总责任损耗</div>
            <div class="text-h4 font-weight-bold mt-1">{{ summary.total_loss_quantity }} 枝</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-card elevation="2" rounded="lg">
      <v-card-item>
        <div class="d-flex align-center justify-space-between">
          <div>
            <v-card-title class="text-subtitle-1">员工绩效排名</v-card-title>
            <v-card-subtitle>共 {{ total }} 条记录 · 按综合评分排序</v-card-subtitle>
          </div>
        </div>
      </v-card-item>
      <v-divider />
      <v-table>
        <thead>
          <tr>
            <th class="text-center">排名</th>
            <th>员工</th>
            <th>岗位</th>
            <th>门店</th>
            <th class="text-center">综合评分</th>
            <th class="text-center">总操作量</th>
            <th class="text-center">入桶</th>
            <th class="text-center">回桶</th>
            <th class="text-center">补液</th>
            <th class="text-center">损耗处理</th>
            <th class="text-center">预警处置</th>
            <th class="text-center">巡检</th>
            <th class="text-center">及时率</th>
            <th class="text-center">平均预警耗时</th>
            <th class="text-center">责任损耗</th>
            <th class="text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in rankingList" :key="item.user.id">
            <td class="text-center">
              <v-chip
                size="small"
                :color="item.rank === 1 ? 'error' : item.rank === 2 ? 'warning' : item.rank === 3 ? 'info' : 'default'"
                variant="flat"
                theme="dark"
              >
                {{ item.rank }}
              </v-chip>
            </td>
            <td>
              <div class="font-weight-medium">{{ item.user.full_name || item.user.username }}</div>
              <div class="text-caption text-medium-emphasis">@{{ item.user.username }}</div>
            </td>
            <td>
              <v-chip size="small" variant="tonal" color="primary">
                {{ item.user.position_label || '-' }}
              </v-chip>
            </td>
            <td>{{ item.store?.store_name || '-' }}</td>
            <td class="text-center">
              <span class="font-weight-bold text-primary">{{ item.score }}</span>
            </td>
            <td class="text-center font-weight-medium">
              {{ item.workload.total_operations }}
            </td>
            <td class="text-center">{{ item.workload.in_bucket_count }}</td>
            <td class="text-center">{{ item.workload.out_bucket_count }}</td>
            <td class="text-center">{{ item.workload.preservation_count }}</td>
            <td class="text-center">{{ item.workload.loss_count }}</td>
            <td class="text-center">{{ item.workload.warning_handled_count }}</td>
            <td class="text-center">{{ item.workload.inspection_count }}</td>
            <td class="text-center">
              <v-chip
                size="small"
                variant="flat"
                :color="item.timeliness.on_time_rate >= 90 ? 'success' : item.timeliness.on_time_rate >= 70 ? 'warning' : 'error'"
                theme="dark"
              >
                {{ item.timeliness.on_time_rate }}%
              </v-chip>
            </td>
            <td class="text-center">
              {{ item.timeliness.avg_warning_handle_hours }} h
            </td>
            <td class="text-center">
              <span class="text-error font-weight-medium">
                {{ item.loss.responsible_loss_quantity }} 枝
              </span>
              <span class="text-caption text-medium-emphasis">
                ({{ item.loss.loss_rate }}%)
              </span>
            </td>
            <td class="text-center">
              <v-btn
                variant="text"
                size="small"
                color="primary"
                :to="`/responsibility-trace?target_type=flower&target_id=${item.user.id}`"
                @click.stop="openTraceForUser(item)"
              >
                <v-icon start>mdi-account-clock-outline</v-icon>责任追踪
              </v-btn>
            </td>
          </tr>
          <tr v-if="rankingList.length === 0 && !loading">
            <td colspan="16" class="text-center text-medium-emphasis py-8">
              <v-icon size="32" class="mb-2">mdi-clipboard-text-search-outline</v-icon>
              <div>暂无绩效数据</div>
            </td>
          </tr>
        </tbody>
      </v-table>
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

    <v-dialog v-model="traceDialog.show" max-width="1200">
      <v-card rounded="lg">
        <v-card-item>
          <v-card-title>
            <v-icon start color="primary">mdi-account-clock-outline</v-icon>
            责任流转追踪 - {{ traceDialog.userName }}
          </v-card-title>
          <v-card-subtitle>
            该员工参与处理的花桶、花材、预警和批次的完整责任人流转过程
          </v-card-subtitle>
        </v-card-item>
        <v-divider />
        <v-card-text>
          <v-row>
            <v-col cols="12" md="3">
              <v-card variant="outlined" class="pa-2" style="max-height: 480px; overflow-y: auto">
                <v-list density="compact" lines="two">
                  <v-list-subheader>花材列表</v-list-subheader>
                  <v-list-item
                    v-for="f in traceDialog.relatedFlowers"
                    :key="f.id"
                    :active="traceDialog.selectedTarget === `flower-${f.id}`"
                    @click="loadTrace('flower', f.id)"
                  >
                    <template #prepend><v-icon color="success">mdi-flower-outline</v-icon></template>
                    <v-list-item-title>{{ f.flower_name }}</v-list-item-title>
                    <v-list-item-subtitle>{{ f.flower_code }} · {{ f.current_quantity }}枝</v-list-item-subtitle>
                  </v-list-item>
                  <v-divider class="my-2" />
                  <v-list-subheader>批次列表</v-list-subheader>
                  <v-list-item
                    v-for="b in traceDialog.relatedBatches"
                    :key="b"
                    :active="traceDialog.selectedTarget === `batch-${b}`"
                    @click="loadTrace('batch', b)"
                  >
                    <template #prepend><v-icon color="info">mdi-package-variant-closed</v-icon></template>
                    <v-list-item-title>{{ b }}</v-list-item-title>
                    <v-list-item-subtitle>批次号</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-card>
            </v-col>
            <v-col cols="12" md="9">
              <div v-if="traceData.traces.length === 0" class="text-center text-medium-emphasis py-8">
                <v-icon size="32" class="mb-2">mdi-clipboard-text-search-outline</v-icon>
                <div>请选择左侧目标查看责任流转过程</div>
              </div>
              <div v-else style="position: relative">
                <v-alert type="info" variant="tonal" density="comfortable" class="mb-3">
                  <v-icon start>mdi-information-outline</v-icon>
                  <strong>{{ traceData.target_type_label }}</strong> - 
                  {{ traceData.target_info.flower_name || traceData.target_info.bucket_code || traceData.target_info.message || traceData.target_info.batch_no || traceData.target_id }}
                  <span v-if="traceData.target_info.batch_no" class="ms-2">
                    <v-chip size="small" variant="flat" color="info" theme="dark">
                      批次: {{ traceData.target_info.batch_no }}
                    </v-chip>
                  </span>
                </v-alert>
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
                    <v-card-item style="padding: 12px 16px">
                      <div class="d-flex align-start justify-space-between w-100 flex-wrap" style="gap: 8px">
                        <div>
                          <div class="d-flex align-center" style="gap: 8px">
                            <v-chip size="small" variant="flat" :color="actionColor[t.action]" theme="dark">
                              {{ t.action_label }}
                            </v-chip>
                            <span class="text-caption text-medium-emphasis">
                              {{ formatDate(t.created_at) }}
                            </span>
                            <span v-if="t.batch_no">
                              <v-chip size="small" variant="tonal" color="info">
                                批次: {{ t.batch_no }}
                              </v-chip>
                            </span>
                          </div>
                          <div class="font-weight-medium mt-2">{{ t.remark || t.action_label }}</div>
                          <div class="text-caption text-medium-emphasis mt-1" style="display: flex; gap: 12px; flex-wrap: wrap">
                            <span v-if="t.store?.store_name">
                              <v-icon size="12">mdi-store</v-icon> {{ t.store.store_name }}
                            </span>
                            <span v-if="t.bucket?.bucket_code">
                              <v-icon size="12">mdi-bucket-outline</v-icon> {{ t.bucket.bucket_code }}
                            </span>
                            <span v-if="t.flower?.flower_name">
                              <v-icon size="12">mdi-flower-outline</v-icon> {{ t.flower.flower_name }} ({{ t.flower.flower_code }})
                            </span>
                            <span>
                              <v-icon size="12">mdi-account</v-icon>
                              {{ t.operator?.full_name || t.operator_name || '-' }}
                              <span class="text-medium-emphasis">({{ t.operator?.position_label || t.operator_position_label || '-' }})</span>
                            </span>
                          </div>
                        </div>
                      </div>
                    </v-card-item>
                  </v-card>
                </div>
              </div>
            </v-col>
          </v-row>
        </v-card-text>
        <v-divider />
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="traceDialog.show = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { performanceApi, type RankingQuery } from '@/api/performance'
import { storeApi } from '@/api/store'
import type {
  PositionInfo,
  Store,
  EmployeePerformance,
  PerformanceSummary,
  ResponsibilityTraceResponse,
} from '@/types'
import dayjs from 'dayjs'

const loading = ref(false)
const rankingList = ref<EmployeePerformance[]>([])
const total = ref(0)
const storeOptions = ref<Store[]>([])
const positionOptions = ref<PositionInfo[]>([])

const sortOptions = [
  { label: '综合评分', value: 'score' },
  { label: '总操作量', value: 'total_operations' },
  { label: '操作及时率', value: 'on_time_rate' },
  { label: '损耗率(升序)', value: 'loss_rate' },
]

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

const summary = reactive<PerformanceSummary>({
  period_start: '',
  period_end: '',
  total_employees: 0,
  total_operations: 0,
  avg_on_time_rate: 0,
  total_loss_quantity: 0,
})

const query = reactive<RankingQuery>({
  page: 1,
  page_size: 20,
  start_date: '',
  end_date: '',
  store_id: '',
  position: '',
  sort_by: 'score',
})

const traceDialog = reactive<{
  show: boolean
  userName: string
  userId: string
  relatedFlowers: any[]
  relatedBatches: string[]
  selectedTarget: string
}>({
  show: false,
  userName: '',
  userId: '',
  relatedFlowers: [],
  relatedBatches: [],
  selectedTarget: '',
})

const traceData = reactive<ResponsibilityTraceResponse>({
  target_type: '',
  target_type_label: '',
  target_id: '',
  target_info: {},
  traces: [],
  total: 0,
})

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / (query.page_size || 20))))

function formatDate(d: string) {
  return dayjs(d).format('YYYY-MM-DD HH:mm:ss')
}

function resetQuery() {
  query.page = 1
  query.start_date = ''
  query.end_date = ''
  query.store_id = ''
  query.position = ''
  query.sort_by = 'score'
  loadData()
}

async function loadOptions() {
  try {
    const [s, p] = await Promise.all([storeApi.listAll(), performanceApi.positions()])
    storeOptions.value = s as any
    positionOptions.value = p
  } catch {}
}

async function loadData() {
  loading.value = true
  try {
    const params: RankingQuery = { page: query.page, page_size: query.page_size, sort_by: query.sort_by }
    if (query.start_date) params.start_date = query.start_date
    if (query.end_date) params.end_date = query.end_date
    if (query.store_id) params.store_id = query.store_id
    if (query.position) params.position = query.position

    const [rank, sum] = await Promise.all([
      performanceApi.ranking(params),
      performanceApi.summary({
        start_date: query.start_date || undefined,
        end_date: query.end_date || undefined,
        store_id: query.store_id || undefined,
      }),
    ])
    rankingList.value = rank.items
    total.value = rank.total
    Object.assign(summary, sum)
  } finally {
    loading.value = false
  }
}

async function openTraceForUser(item: EmployeePerformance) {
  traceDialog.show = true
  traceDialog.userName = item.user.full_name || item.user.username
  traceDialog.userId = item.user.id
  traceDialog.relatedFlowers = []
  traceDialog.relatedBatches = []
  traceDialog.selectedTarget = ''
  traceData.traces = []
  traceData.target_info = {}
}

async function loadTrace(targetType: string, targetId: string) {
  try {
    traceDialog.selectedTarget = `${targetType}-${targetId}`
    const res = await performanceApi.trace({
      target_type: targetType as any,
      target_id: targetId,
    })
    Object.assign(traceData, res)
  } catch {}
}

onMounted(async () => {
  await loadOptions()
  await loadData()
})
</script>
