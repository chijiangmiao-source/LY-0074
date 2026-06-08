<template>
  <div>
    <v-card elevation="2" class="mb-4" rounded="lg">
      <v-card-item>
        <v-card-title class="text-h6">数据看板</v-card-title>
        <v-card-subtitle>系统运营数据概览与智能预警</v-card-subtitle>
      </v-card-item>
    </v-card>

    <!-- 统计卡片 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card elevation="2" rounded="lg" color="primary" theme="dark" class="stat-card">
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-caption text-opacity-75">门店总数</div>
                <div class="text-h4 font-weight-bold mt-2">{{ summary.total_stores }}</div>
              </div>
              <v-icon size="48" class="text-white text-opacity-50">mdi-store</v-icon>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card elevation="2" rounded="lg" color="success" theme="dark" class="stat-card">
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-caption text-opacity-75">启用花桶</div>
                <div class="text-h4 font-weight-bold mt-2">
                  {{ summary.active_buckets }} / {{ summary.total_buckets }}
                </div>
              </div>
              <v-icon size="48" class="text-white text-opacity-50">mdi-bucket-outline</v-icon>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card elevation="2" rounded="lg" color="info" theme="dark" class="stat-card">
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-caption text-opacity-75">在桶花材</div>
                <div class="text-h4 font-weight-bold mt-2">
                  {{ summary.in_bucket_flowers }} / {{ summary.total_flowers }}
                </div>
              </div>
              <v-icon size="48" class="text-white text-opacity-50">mdi-flower-outline</v-icon>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card
          elevation="2"
          rounded="lg"
          :color="warningStats.total > 0 ? 'error' : 'warning'"
          theme="dark"
          class="stat-card"
          @click="scrollToWarnings"
          style="cursor: pointer"
        >
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-caption text-opacity-75">待处理预警</div>
                <div class="text-h4 font-weight-bold mt-2">
                  {{ warningStats.total }}
                </div>
              </div>
              <v-badge color="white" :content="warningStats.high" offset-x="-4" offset-y="4">
                <v-icon size="48" class="text-white text-opacity-50">mdi-alert</v-icon>
              </v-badge>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 预警区域 -->
    <v-card elevation="2" class="mb-4" rounded="lg" ref="warningsCard">
      <v-card-item>
        <div class="d-flex align-center justify-space-between flex-wrap" style="gap: 12px">
          <div>
            <v-card-title class="text-subtitle-1">
              <v-icon start color="error">mdi-alert-circle</v-icon>
              待处理预警列表
            </v-card-title>
            <v-card-subtitle>
              液位过低、花材萎蔫、入桶超时、损耗过高自动预警
            </v-card-subtitle>
          </div>
          <div class="d-flex align-center" style="gap: 8px">
            <v-chip
              v-for="stat in [
                { key: 'total', label: '全部', color: 'primary' },
                { key: 'low_liquid', label: '液位低', color: 'info' },
                { key: 'wilted', label: '萎蔫', color: 'error' },
                { key: 'long_in_bucket', label: '超时', color: 'warning' },
                { key: 'high_loss', label: '高损耗', color: 'deep-orange' },
              ]"
              :key="stat.key"
              size="small"
              variant="tonal"
              :color="warningFilter === stat.key ? stat.color : 'default'"
              @click="warningFilter = warningFilter === stat.key ? '' : stat.key"
              style="cursor: pointer"
            >
              {{ stat.label }}
              <span class="ms-1 font-weight-bold">({{ warningStats[stat.key] || 0 }})</span>
            </v-chip>
            <v-btn variant="text" size="small" @click="loadWarnings">
              <v-icon start>mdi-refresh</v-icon>刷新
            </v-btn>
            <router-link to="/trace">
              <v-btn variant="outlined" size="small" color="primary">
                <v-icon start>mdi-history</v-icon>轨迹追踪
              </v-btn>
            </router-link>
          </div>
        </div>
      </v-card-item>
      <v-divider />
      <v-table>
        <thead>
          <tr>
            <th>级别</th>
            <th>类型</th>
            <th>门店</th>
            <th>花桶</th>
            <th>花材</th>
            <th>预警信息</th>
            <th>当前值 / 阈值</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="w in filteredWarnings" :key="w.warning_id">
            <td>
              <v-chip
                size="small"
                :color="w.severity === 'high' ? 'error' : w.severity === 'medium' ? 'warning' : 'info'"
                variant="flat"
                theme="dark"
              >
                {{ w.severity === 'high' ? '严重' : w.severity === 'medium' ? '中等' : '提示' }}
              </v-chip>
            </td>
            <td>
              <v-chip
                size="small"
                variant="tonal"
                :color="warningTypeColor[w.warning_type]"
              >
                <v-icon start size="14">
                  {{ warningTypeIcon[w.warning_type] }}
                </v-icon>
                {{ w.warning_type_label }}
              </v-chip>
            </td>
            <td>{{ w.store_name || '-' }}</td>
            <td>{{ w.bucket_code || '-' }}</td>
            <td>
              <span v-if="w.flower_name">
                {{ w.flower_name }}
                <span class="text-caption text-medium-emphasis">({{ w.flower_code }})</span>
              </span>
              <span v-else>-</span>
            </td>
            <td class="font-weight-medium">{{ w.message }}</td>
            <td>
              <span :class="w.severity === 'high' ? 'text-error' : 'text-warning'">
                {{ w.current_value }}{{ w.unit }}
              </span>
              <span class="text-medium-emphasis"> / {{ w.threshold }}{{ w.unit }}</span>
            </td>
            <td class="text-center">
              <v-btn
                v-if="w.warning_type === 'low_liquid'"
                variant="text"
                size="small"
                color="primary"
                :to="`/records?bucket_id=${w.bucket_id}&tab=preservation`"
              >
                去补液
              </v-btn>
              <v-btn
                v-else-if="w.warning_type === 'wilted' || w.warning_type === 'long_in_bucket'"
                variant="text"
                size="small"
                color="primary"
                :to="`/flowers?flower_id=${w.flower_id}`"
              >
                查看花材
              </v-btn>
              <v-btn
                v-else-if="w.warning_type === 'high_loss'"
                variant="text"
                size="small"
                color="primary"
                :to="`/trace?store_id=${w.store_id}`"
              >
                查看损耗
              </v-btn>
            </td>
          </tr>
          <tr v-if="filteredWarnings.length === 0">
            <td colspan="8" class="text-center text-medium-emphasis py-8">
              <v-icon size="32" class="mb-2">mdi-check-circle</v-icon>
              <div>暂无待处理预警</div>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <!-- 图表区域 -->
    <v-row>
      <!-- 花桶周转率 -->
      <v-col cols="12" lg="6">
        <v-card elevation="2" rounded="lg" height="100%">
          <v-card-item>
            <v-card-title class="text-subtitle-1">花桶周转率 TOP 10</v-card-title>
            <v-card-subtitle>按周转次数排序</v-card-subtitle>
          </v-card-item>
          <v-divider />
          <v-card-text>
            <div v-if="turnoverData.length === 0" class="text-center text-medium-emphasis py-8">
              暂无数据
            </div>
            <div v-else>
              <div v-for="(item, idx) in topTurnover" :key="item.bucket_id" class="mb-3">
                <div class="d-flex align-center mb-1">
                  <v-chip size="small" :color="idx < 3 ? 'primary' : 'secondary'" class="me-2" theme="dark">
                    {{ idx + 1 }}
                  </v-chip>
                  <span class="font-weight-medium">{{ item.bucket_code }}</span>
                  <span class="text-medium-emphasis ms-2">({{ item.store_name }})</span>
                  <v-spacer />
                  <span class="text-caption text-medium-emphasis">{{ item.turnover_count }} 次</span>
                </div>
                <v-progress-linear
                  :model-value="Math.min(item.utilization_rate, 100)"
                  :color="item.utilization_rate > 80 ? 'error' : item.utilization_rate > 50 ? 'warning' : 'success'"
                  height="6"
                  rounded
                />
                <div class="d-flex justify-space-between mt-1">
                  <span class="text-caption text-medium-emphasis">
                    液位: {{ item.current_quantity }}/{{ item.capacity }} L
                  </span>
                  <span class="text-caption font-weight-medium">
                    利用率 {{ item.utilization_rate }}%
                  </span>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 花材分类分布 -->
      <v-col cols="12" lg="6">
        <v-card elevation="2" rounded="lg" height="100%">
          <v-card-item>
            <v-card-title class="text-subtitle-1">花材分类分布</v-card-title>
            <v-card-subtitle>按数量统计</v-card-subtitle>
          </v-card-item>
          <v-divider />
          <v-card-text>
            <div v-if="categoryData.length === 0" class="text-center text-medium-emphasis py-8">
              暂无数据
            </div>
            <div v-else style="position: relative; height: 360px">
              <Doughnut :data="categoryChartData" :options="doughnutOptions" />
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 门店损耗排行 -->
      <v-col cols="12" lg="6">
        <v-card elevation="2" rounded="lg">
          <v-card-item>
            <v-card-title class="text-subtitle-1">门店损耗排行</v-card-title>
            <v-card-subtitle>按损耗数量排序</v-card-subtitle>
          </v-card-item>
          <v-divider />
          <v-table>
            <thead>
              <tr>
                <th>排名</th>
                <th>门店</th>
                <th>负责人</th>
                <th>损耗数量</th>
                <th>损耗次数</th>
                <th>当前库存</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in lossRanking" :key="item.store_id">
                <td>
                  <v-chip
                    size="small"
                    :color="item.rank === 1 ? 'error' : item.rank === 2 ? 'warning' : item.rank === 3 ? 'info' : 'default'"
                    variant="flat"
                  >
                    {{ item.rank }}
                  </v-chip>
                </td>
                <td class="font-weight-medium">{{ item.store_name }}</td>
                <td>{{ item.manager || '-' }}</td>
                <td class="text-error font-weight-medium">{{ item.total_loss_quantity }} 枝</td>
                <td>{{ item.total_loss_count }}</td>
                <td>{{ item.current_flower_quantity }} 枝</td>
              </tr>
              <tr v-if="lossRanking.length === 0">
                <td colspan="6" class="text-center text-medium-emphasis py-6">暂无数据</td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>

      <!-- 最近操作记录 -->
      <v-col cols="12" lg="6">
        <v-card elevation="2" rounded="lg">
          <v-card-item>
            <div class="d-flex align-center justify-space-between">
              <div>
                <v-card-title class="text-subtitle-1">最近操作记录</v-card-title>
                <v-card-subtitle>最新动态</v-card-subtitle>
              </div>
              <router-link to="/trace">
                <v-btn variant="text" size="small" color="primary">
                  查看全部 <v-icon end>mdi-arrow-right</v-icon>
                </v-btn>
              </router-link>
            </div>
          </v-card-item>
          <v-divider />
          <v-table>
            <thead>
              <tr>
                <th>类型</th>
                <th>花桶</th>
                <th>花材</th>
                <th>数量</th>
                <th>操作人</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recentRecords" :key="`${item.type_key}-${item.created_at}`">
                <td>
                  <v-chip
                    size="small"
                    :color="recordColor[item.type_key]"
                    variant="flat"
                  >
                    {{ item.type }}
                  </v-chip>
                </td>
                <td>{{ item.bucket_code || '-' }}</td>
                <td>{{ item.flower_name || '-' }}</td>
                <td>
                  <span :class="item.type_key === 'loss' ? 'text-error' : item.type_key === 'preservation' ? 'text-success' : ''">
                    {{ item.type_key === 'loss' ? '-' : item.type_key === 'preservation' ? '+' : '' }}{{ item.quantity }}
                  </span>
                </td>
                <td>{{ item.operator || '-' }}</td>
                <td class="text-caption">{{ formatDate(item.created_at) }}</td>
              </tr>
              <tr v-if="recentRecords.length === 0">
                <td colspan="6" class="text-center text-medium-emphasis py-6">暂无数据</td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, Title } from 'chart.js'
import { Doughnut } from 'vue-chartjs'
import { dashboardApi, type DashboardSummary, type BucketTurnover, type CategoryDistribution, type StoreLossRanking, type RecentRecord } from '@/api/dashboard'
import type { Warning, WarningType, WarningSeverity } from '@/types'
import dayjs from 'dayjs'

ChartJS.register(ArcElement, Tooltip, Legend, Title)

const summary = reactive<DashboardSummary>({
  total_stores: 0,
  total_buckets: 0,
  active_buckets: 0,
  total_flowers: 0,
  in_bucket_flowers: 0,
  total_flower_quantity: 0,
  total_preservation_records: 0,
  total_loss_records: 0,
})

const turnoverData = ref<BucketTurnover[]>([])
const categoryData = ref<CategoryDistribution[]>([])
const lossRanking = ref<StoreLossRanking[]>([])
const recentRecords = ref<RecentRecord[]>([])

const warnings = ref<Warning[]>([])
const warningFilter = ref('')
const warningsCard = ref()

const warningStats = computed(() => {
  const stats: Record<string, number> = {
    total: warnings.value.length,
    high: 0,
    medium: 0,
    low: 0,
    low_liquid: 0,
    wilted: 0,
    long_in_bucket: 0,
    high_loss: 0,
  }
  for (const w of warnings.value) {
    stats[w.severity] = (stats[w.severity] || 0) + 1
    stats[w.warning_type] = (stats[w.warning_type] || 0) + 1
  }
  return stats
})

const filteredWarnings = computed(() => {
  if (!warningFilter.value || warningFilter.value === 'total') {
    return warnings.value
  }
  return warnings.value.filter(w => w.warning_type === warningFilter.value)
})

const topTurnover = computed(() => turnoverData.value.slice(0, 10))

const warningTypeColor: Record<WarningType, string> = {
  low_liquid: 'info',
  wilted: 'error',
  long_in_bucket: 'warning',
  high_loss: 'deep-orange',
}

const warningTypeIcon: Record<WarningType, string> = {
  low_liquid: 'mdi-water-off',
  wilted: 'mdi-flower-tulip',
  long_in_bucket: 'mdi-clock-alert',
  high_loss: 'mdi-trending-down',
}

const recordColor: Record<string, string> = {
  in_bucket: 'primary',
  out_bucket: 'info',
  preservation: 'success',
  loss: 'error',
}

const palette = [
  '#1976D2', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0',
  '#00BCD4', '#8BC34A', '#FFC107', '#F44336', '#3F51B5',
  '#009688', '#CDDC39', '#FF5722', '#673AB7', '#2196F3',
]

const categoryChartData = computed(() => ({
  labels: categoryData.value.map(c => c.category_name),
  datasets: [
    {
      data: categoryData.value.map(c => c.total_quantity),
      backgroundColor: palette.slice(0, categoryData.value.length),
      borderWidth: 2,
      borderColor: '#ffffff',
    },
  ],
}))

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right' as const,
      labels: {
        padding: 16,
        usePointStyle: true,
      },
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
          const value = context.parsed
          const pct = total > 0 ? ((value / total) * 100).toFixed(1) : 0
          return `${context.label}: ${value} 枝 (${pct}%)`
        },
      },
    },
  },
}

function formatDate(d: string) {
  return dayjs(d).format('MM-DD HH:mm')
}

function scrollToWarnings() {
  warningsCard.value?.scrollIntoView({ behavior: 'smooth' })
}

async function loadWarnings() {
  try {
    warnings.value = await dashboardApi.warnings()
  } catch {}
}

async function loadAll() {
  try {
    const [s, t, c, l, r] = await Promise.all([
      dashboardApi.summary(),
      dashboardApi.bucketTurnover(),
      dashboardApi.categoryDistribution(),
      dashboardApi.storeLossRanking(),
      dashboardApi.recentRecords(15),
    ])
    Object.assign(summary, s)
    turnoverData.value = t
    categoryData.value = c
    lossRanking.value = l
    recentRecords.value = r
  } catch {}
}

onMounted(async () => {
  await loadAll()
  await loadWarnings()
})
</script>

<style lang="scss" scoped>
.stat-card {
  transition: transform 0.2s;
  &:hover {
    transform: translateY(-2px);
  }
}
</style>
