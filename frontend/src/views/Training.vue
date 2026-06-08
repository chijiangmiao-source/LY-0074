<template>
  <div>
    <v-card elevation="2" class="mb-4" rounded="lg">
      <v-card-item>
        <div class="d-flex align-center justify-space-between flex-wrap" style="gap: 12px">
          <div>
            <v-card-title class="text-h6">
              <v-icon start color="primary">mdi-school-outline</v-icon>
              培训与能力改进
            </v-card-title>
            <v-card-subtitle>
              自动识别员工薄弱能力项，生成个性化培训建议，支持培训完成率、复训通过率、问题复发率等多维度统计分析
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
          <v-col cols="12" md="12">
            <v-btn color="primary" variant="flat" class="me-2" @click="loadAllData">
              <v-icon start>mdi-magnify</v-icon>查询
            </v-btn>
            <v-btn variant="outlined" @click="resetQuery">
              <v-icon start>mdi-refresh</v-icon>重置
            </v-btn>
            <v-btn color="success" variant="flat" class="ms-2" @click="showAssignDialog = true">
              <v-icon start>mdi-plus</v-icon>指派培训任务
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-tabs v-model="activeTab" color="primary" density="comfortable" class="mb-4">
      <v-tab value="stats">
        <v-icon start>mdi-chart-box-outline</v-icon>培训统计概览
      </v-tab>
      <v-tab value="assessment">
        <v-icon start>mdi-clipboard-check-outline</v-icon>员工能力评估
      </v-tab>
      <v-tab value="tasks">
        <v-icon start>mdi-clipboard-list-outline</v-icon>培训任务管理
      </v-tab>
      <v-tab value="errors">
        <v-icon start>mdi-alert-circle-outline</v-icon>高频错误与责任关联
      </v-tab>
    </v-tabs>

    <v-window v-model="activeTab">
      <v-window-item value="stats">
        <v-row class="mb-4">
          <v-col cols="6" sm="3">
            <v-card elevation="2" rounded="lg" color="primary" theme="dark">
              <v-card-text>
                <div class="text-caption text-opacity-75">培训完成率</div>
                <div class="text-h4 font-weight-bold mt-1">{{ stats.training_completion_rate }}%</div>
                <div class="text-caption text-opacity-75 mt-1">
                  已完成 {{ stats.completed_tasks }} / 共 {{ stats.total_tasks }} 个任务
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card elevation="2" rounded="lg" color="success" theme="dark">
              <v-card-text>
                <div class="text-caption text-opacity-75">复训通过率</div>
                <div class="text-h4 font-weight-bold mt-1">{{ stats.refresher_pass_rate }}%</div>
                <div class="text-caption text-opacity-75 mt-1">
                  通过 {{ stats.refresher_passed }} / 共 {{ stats.refresher_tasks }} 个复训
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card elevation="2" rounded="lg" color="warning" theme="dark">
              <v-card-text>
                <div class="text-caption text-opacity-75">问题复发率</div>
                <div class="text-h4 font-weight-bold mt-1">{{ stats.problem_recurrence_rate }}%</div>
                <div class="text-caption text-opacity-75 mt-1">
                  考核通过率 {{ stats.exam_pass_rate }}%
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card elevation="2" rounded="lg" color="info" theme="dark">
              <v-card-text>
                <div class="text-caption text-opacity-75">平均能力评分</div>
                <div class="text-h4 font-weight-bold mt-1">{{ stats.avg_overall_score }}</div>
                <div class="text-caption text-opacity-75 mt-1">
                  覆盖员工 {{ stats.total_employees }} 人
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="12" md="7">
            <v-card elevation="2" rounded="lg">
              <v-card-item>
                <v-card-title class="text-subtitle-1">能力提升趋势</v-card-title>
                <v-card-subtitle>近6周培训完成情况变化</v-card-subtitle>
              </v-card-item>
              <v-divider />
              <v-card-text>
                <div style="height: 300px">
                  <canvas ref="trendChartRef"></canvas>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="5">
            <v-card elevation="2" rounded="lg">
              <v-card-item>
                <v-card-title class="text-subtitle-1">各能力维度平均得分</v-card-title>
                <v-card-subtitle>全体员工能力分布</v-card-subtitle>
              </v-card-item>
              <v-divider />
              <v-card-text>
                <div style="height: 300px">
                  <canvas ref="radarChartRef"></canvas>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <v-card elevation="2" rounded="lg" class="mt-4">
          <v-card-item>
            <v-card-title class="text-subtitle-1">各维度能力得分详情</v-card-title>
          </v-card-item>
          <v-divider />
          <v-table>
            <thead>
              <tr>
                <th>能力维度</th>
                <th class="text-center">平均得分</th>
                <th class="text-center">覆盖员工数</th>
                <th class="text-center">得分分布</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="dim in stats.dimension_scores" :key="dim.dimension">
                <td>
                  <v-chip size="small" variant="tonal" color="primary">
                    {{ dim.dimension_label }}
                  </v-chip>
                </td>
                <td class="text-center">
                  <span class="font-weight-bold" :class="getScoreColor(dim.avg_score)">
                    {{ dim.avg_score }}
                  </span>
                </td>
                <td class="text-center">{{ dim.employee_count }}</td>
                <td>
                  <v-progress-linear
                    :model-value="dim.avg_score"
                    :color="dim.avg_score >= 75 ? 'success' : dim.avg_score >= 60 ? 'warning' : 'error'"
                    height="8"
                    rounded
                  />
                </td>
              </tr>
              <tr v-if="stats.dimension_scores.length === 0 && !loading">
                <td colspan="4" class="text-center text-medium-emphasis py-8">
                  <v-icon size="32" class="mb-2">mdi-chart-line</v-icon>
                  <div>暂无统计数据，请调整筛选条件</div>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-window-item>

      <v-window-item value="assessment">
        <v-row>
          <v-col cols="12" md="4">
            <v-card elevation="2" rounded="lg">
              <v-card-item>
                <v-card-title class="text-subtitle-1">选择员工</v-card-title>
              </v-card-item>
              <v-divider />
              <v-card-text>
                <v-select
                  v-model="selectedEmployeeId"
                  :items="employeeOptions"
                  item-title="label"
                  item-value="value"
                  label="选择员工查看能力评估"
                  variant="outlined"
                  density="comfortable"
                  :items-length="10"
                />
                <v-btn
                  color="primary"
                  variant="flat"
                  block
                  class="mt-3"
                  :disabled="!selectedEmployeeId"
                  @click="loadAssessment"
                >
                  <v-icon start>mdi-magnify</v-icon>查看能力评估
                </v-btn>
                <v-btn
                  variant="outlined"
                  block
                  class="mt-2"
                  :disabled="!selectedEmployeeId"
                  @click="refreshAssessment"
                >
                  <v-icon start>mdi-refresh</v-icon>刷新评估结果
                </v-btn>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="8">
            <div v-if="assessment">
              <v-card elevation="2" rounded="lg" class="mb-4">
                <v-card-item>
                  <div class="d-flex align-center justify-space-between w-100 flex-wrap" style="gap: 12px">
                    <div>
                      <v-card-title class="text-subtitle-1">
                        {{ assessment.user_name }} 的能力评估报告
                      </v-card-title>
                      <v-card-subtitle>
                        {{ assessment.position_label || '-' }} · {{ assessment.store_name || '-' }} · 
                        评估周期: {{ assessment.period_start }} ~ {{ assessment.period_end }}
                      </v-card-subtitle>
                    </div>
                    <div class="text-center">
                      <div class="text-caption text-medium-emphasis">综合评分</div>
                      <div class="text-h3 font-weight-bold" :class="getScoreColor(assessment.overall_score)">
                        {{ assessment.overall_score }}
                      </div>
                      <v-chip
                        size="small"
                        :color="getLevelColor(assessment.overall_level)"
                        variant="flat"
                        theme="dark"
                      >
                        {{ assessment.overall_level_label }}
                      </v-chip>
                    </div>
                  </div>
                </v-card-item>
              </v-card>

              <v-row>
                <v-col cols="12" md="6">
                  <v-card elevation="2" rounded="lg">
                    <v-card-item>
                      <v-card-title class="text-subtitle-1">各维度能力得分</v-card-title>
                    </v-card-item>
                    <v-divider />
                    <v-card-text>
                      <div style="height: 280px">
                        <canvas ref="employeeRadarRef"></canvas>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
                <v-col cols="12" md="6">
                  <v-card elevation="2" rounded="lg">
                    <v-card-item>
                      <v-card-title class="text-subtitle-1">培训建议</v-card-title>
                    </v-card-item>
                    <v-divider />
                    <v-card-text style="max-height: 320px; overflow-y: auto">
                      <v-list density="compact">
                        <v-list-item
                          v-for="(sug, idx) in assessment.training_suggestions"
                          :key="idx"
                        >
                          <template #prepend>
                            <v-icon
                              :color="sug.includes('紧急') ? 'error' : sug.includes('注意') ? 'warning' : 'info'"
                            >
                              {{ sug.includes('紧急') ? 'mdi-alert-octagon' : sug.includes('注意') ? 'mdi-alert' : 'mdi-lightbulb' }}
                            </v-icon>
                          </template>
                          <v-list-item-title>{{ sug }}</v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <v-card elevation="2" rounded="lg" class="mt-4">
                <v-card-item>
                  <v-card-title class="text-subtitle-1">能力维度详情</v-card-title>
                </v-card-item>
                <v-divider />
                <v-table>
                  <thead>
                    <tr>
                      <th>能力维度</th>
                      <th class="text-center">得分</th>
                      <th class="text-center">等级</th>
                      <th class="text-center">操作次数</th>
                      <th class="text-center">问题次数</th>
                      <th>详情</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="s in assessment.competency_scores" :key="s.dimension">
                      <td>
                        <v-chip size="small" variant="tonal" color="primary">
                          {{ s.dimension_label }}
                        </v-chip>
                      </td>
                      <td class="text-center">
                        <span class="font-weight-bold" :class="getScoreColor(s.score)">
                          {{ s.score }}
                        </span>
                      </td>
                      <td class="text-center">
                        <v-chip
                          size="small"
                          variant="flat"
                          :color="getLevelColor(s.level)"
                          theme="dark"
                        >
                          {{ s.level_label }}
                        </v-chip>
                      </td>
                      <td class="text-center">{{ s.operations_count }}</td>
                      <td class="text-center">
                        <span v-if="s.error_count > 0" class="text-error font-weight-medium">
                          {{ s.error_count }}
                        </span>
                        <span v-else class="text-success">-</span>
                      </td>
                      <td class="text-caption text-medium-emphasis">
                        <span v-for="(val, key) in s.details" :key="key" class="me-3">
                          {{ key }}: {{ val }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </v-card>
            </div>
            <v-card v-else elevation="2" rounded="lg">
              <v-card-text class="text-center text-medium-emphasis py-12">
                <v-icon size="48" class="mb-3">mdi-account-search-outline</v-icon>
                <div>请选择员工查看能力评估报告</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>

      <v-window-item value="tasks">
        <v-card elevation="2" rounded="lg">
          <v-card-item>
            <div class="d-flex align-center justify-space-between flex-wrap" style="gap: 12px">
              <div>
                <v-card-title class="text-subtitle-1">培训任务列表</v-card-title>
                <v-card-subtitle>共 {{ taskTotal }} 条记录</v-card-subtitle>
              </div>
              <div class="d-flex" style="gap: 8px">
                <v-select
                  v-model="taskFilter.status"
                  :items="statusOptions"
                  item-title="label"
                  item-value="value"
                  label="状态"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                  style="width: 140px"
                />
                <v-select
                  v-model="taskFilter.task_type"
                  :items="taskTypeOptions"
                  item-title="label"
                  item-value="value"
                  label="类型"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                  style="width: 140px"
                />
                <v-select
                  v-model="taskFilter.competency_dimension"
                  :items="dimensionOptions"
                  item-title="label"
                  item-value="code"
                  label="能力维度"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                  style="width: 160px"
                />
              </div>
            </div>
          </v-card-item>
          <v-divider />
          <v-table>
            <thead>
              <tr>
                <th>员工</th>
                <th>门店</th>
                <th>培训内容</th>
                <th class="text-center">能力维度</th>
                <th class="text-center">类型</th>
                <th class="text-center">状态</th>
                <th class="text-center">指派时间</th>
                <th class="text-center">得分</th>
                <th class="text-center">是否通过</th>
                <th class="text-center">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="task in taskList" :key="task._id">
                <td>
                  <div class="font-weight-medium">{{ task.user_name }}</div>
                  <div class="text-caption text-medium-emphasis">{{ task.position_label || '-' }}</div>
                </td>
                <td>{{ task.store_name || '-' }}</td>
                <td>
                  <div class="font-weight-medium">{{ task.course_name }}</div>
                  <div v-if="task.remark" class="text-caption text-medium-emphasis">{{ task.remark }}</div>
                </td>
                <td class="text-center">
                  <v-chip size="small" variant="tonal" color="info">
                    {{ task.competency_dimension_label }}
                  </v-chip>
                </td>
                <td class="text-center">
                  <v-chip
                    size="small"
                    variant="flat"
                    :color="task.task_type === 'exam' ? 'secondary' : task.task_type === 'refresher' ? 'warning' : 'primary'"
                    theme="dark"
                  >
                    {{ task.task_type_label }}
                  </v-chip>
                </td>
                <td class="text-center">
                  <v-chip
                    size="small"
                    variant="flat"
                    :color="getTaskStatusColor(task.status)"
                    theme="dark"
                  >
                    {{ task.status_label }}
                  </v-chip>
                </td>
                <td class="text-center text-caption">{{ formatDate(task.assigned_at) }}</td>
                <td class="text-center">
                  <span v-if="task.score !== undefined && task.score !== null" class="font-weight-bold">
                    {{ task.score }}
                  </span>
                  <span v-else class="text-medium-emphasis">-</span>
                </td>
                <td class="text-center">
                  <v-chip
                    v-if="task.passed !== undefined && task.passed !== null"
                    size="small"
                    variant="flat"
                    :color="task.passed ? 'success' : 'error'"
                    theme="dark"
                  >
                    {{ task.passed ? '通过' : '未通过' }}
                  </v-chip>
                  <span v-else class="text-medium-emphasis">-</span>
                </td>
                <td class="text-center">
                  <v-btn
                    variant="text"
                    size="small"
                    color="primary"
                    @click="openUpdateTaskDialog(task)"
                  >
                    更新进度
                  </v-btn>
                </td>
              </tr>
              <tr v-if="taskList.length === 0 && !loading">
                <td colspan="10" class="text-center text-medium-emphasis py-8">
                  <v-icon size="32" class="mb-2">mdi-clipboard-text-search-outline</v-icon>
                  <div>暂无培训任务</div>
                </td>
              </tr>
            </tbody>
          </v-table>
          <v-divider />
          <v-card-actions class="justify-space-between px-4">
            <span class="text-medium-emphasis text-caption">
              共 {{ taskTotal }} 条记录 · 第 {{ taskQuery.page }}/{{ totalTaskPages }} 页
            </span>
            <v-pagination
              v-model="taskQuery.page"
              :length="totalTaskPages"
              :total-visible="7"
              @update:model-value="loadTasks"
              size="small"
            />
          </v-card-actions>
        </v-card>
      </v-window-item>

      <v-window-item value="errors">
        <v-card elevation="2" rounded="lg" class="mb-4">
          <v-card-item>
            <div class="d-flex align-center justify-space-between flex-wrap" style="gap: 12px">
              <div>
                <v-card-title class="text-subtitle-1">高频错误分析</v-card-title>
                <v-card-subtitle>
                  自动识别责任追踪记录中的高频错误，可直接关联到责任追踪详情
                </v-card-subtitle>
              </div>
              <v-btn color="primary" variant="flat" @click="loadHighFreqErrors">
                <v-icon start>mdi-refresh</v-icon>刷新分析
              </v-btn>
            </div>
          </v-card-item>
        </v-card>

        <v-row>
          <v-col v-for="err in highFreqErrors" :key="err._id" cols="12" md="6">
            <v-card elevation="2" rounded="lg">
              <v-card-item>
                <div class="d-flex align-start justify-space-between w-100">
                  <div>
                    <v-card-title class="text-subtitle-1" style="color: rgb(var(--v-theme-error))">
                      <v-icon start>mdi-alert-circle</v-icon>
                      {{ err.error_type_label }}
                    </v-card-title>
                    <v-card-subtitle>{{ err.description }}</v-card-subtitle>
                  </div>
                  <v-chip
                    color="error"
                    variant="flat"
                    theme="dark"
                    size="large"
                  >
                    {{ err.occurrence_count }} 次
                  </v-chip>
                </div>
              </v-card-item>
              <v-divider />
              <v-card-text>
                <v-row>
                  <v-col cols="6">
                    <div class="text-caption text-medium-emphasis">关联能力维度</div>
                    <v-chip size="small" variant="tonal" color="warning" class="mt-1">
                      {{ err.competency_dimension_label }}
                    </v-chip>
                  </v-col>
                  <v-col cols="6">
                    <div class="text-caption text-medium-emphasis">影响范围</div>
                    <div class="mt-1">
                      <span class="font-weight-medium">{{ err.affected_employee_count }}</span> 名员工 · 
                      <span class="font-weight-medium">{{ err.affected_store_count }}</span> 家门店
                    </div>
                  </v-col>
                </v-row>
                <v-divider class="my-3" />
                <div class="text-caption text-medium-emphasis mb-2">典型案例（点击查看责任追踪）:</div>
                <v-list density="compact">
                  <v-list-item
                    v-for="sample in err.sample_traces"
                    :key="sample.trace_id"
                    :to="`/responsibility-trace?target_type=warning&target_id=${sample.trace_id}`"
                  >
                    <template #prepend>
                      <v-icon color="error">mdi-link-variant</v-icon>
                    </template>
                    <v-list-item-title>
                      {{ sample.operator_name }} · {{ formatDate(sample.created_at) }}
                    </v-list-item-title>
                    <v-list-item-subtitle v-if="sample.remark">
                      {{ sample.remark }}
                    </v-list-item-subtitle>
                    <v-list-item-subtitle v-if="sample.batch_no">
                      批次: {{ sample.batch_no }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
                <div class="mt-3 d-flex" style="gap: 8px">
                  <v-btn
                    size="small"
                    variant="outlined"
                    color="primary"
                    @click="openAssignDialogFromError(err)"
                  >
                    <v-icon start>mdi-account-plus-outline</v-icon>为相关员工指派培训
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col v-if="highFreqErrors.length === 0 && !loading" cols="12">
            <v-card elevation="2" rounded="lg">
              <v-card-text class="text-center text-medium-emphasis py-12">
                <v-icon size="48" class="mb-3">mdi-check-circle-outline</v-icon>
                <div>暂未发现高频错误，员工操作表现良好</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>
    </v-window>

    <v-dialog v-model="showAssignDialog" max-width="600">
      <v-card rounded="lg">
        <v-card-item>
          <v-card-title>
            <v-icon start color="primary">mdi-plus-circle-outline</v-icon>
            指派培训任务
          </v-card-title>
        </v-card-item>
        <v-divider />
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <v-select
                v-model="assignForm.user_id"
                :items="employeeOptions"
                item-title="label"
                item-value="value"
                label="选择员工"
                variant="outlined"
                density="comfortable"
                :items-length="10"
              />
            </v-col>
            <v-col cols="12">
              <v-text-field
                v-model="assignForm.course_name"
                label="培训内容/课程名称"
                variant="outlined"
                density="comfortable"
                placeholder="如：损耗处理规范培训"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-select
                v-model="assignForm.competency_dimension"
                :items="dimensionOptions"
                item-title="label"
                item-value="code"
                label="对应能力维度"
                variant="outlined"
                density="comfortable"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-select
                v-model="assignForm.task_type"
                :items="taskTypeOptions"
                item-title="label"
                item-value="value"
                label="任务类型"
                variant="outlined"
                density="comfortable"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-date-picker
                v-model="assignForm.deadline"
                label="截止日期"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
              />
            </v-col>
            <v-col cols="12">
              <v-textarea
                v-model="assignForm.remark"
                label="备注说明"
                variant="outlined"
                density="comfortable"
                rows="2"
                auto-grow
              />
            </v-col>
          </v-row>
        </v-card-text>
        <v-divider />
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="showAssignDialog = false">取消</v-btn>
          <v-btn color="primary" variant="flat" @click="submitAssignTask">
            <v-icon start>mdi-check</v-icon>确认指派
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showUpdateDialog" max-width="500">
      <v-card rounded="lg">
        <v-card-item>
          <v-card-title>
            <v-icon start color="primary">mdi-pencil-outline</v-icon>
            更新培训任务进度
          </v-card-title>
          <v-card-subtitle v-if="updateTask">
            {{ updateTask.course_name }} - {{ updateTask.user_name }}
          </v-card-subtitle>
        </v-card-item>
        <v-divider />
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <v-select
                v-model="updateForm.status"
                :items="statusOptions"
                item-title="label"
                item-value="value"
                label="任务状态"
                variant="outlined"
                density="comfortable"
              />
            </v-col>
            <v-col cols="12">
              <v-text-field
                v-model.number="updateForm.score"
                label="考核得分（0-100）"
                type="number"
                variant="outlined"
                density="comfortable"
                min="0"
                max="100"
              />
            </v-col>
            <v-col cols="12">
              <v-select
                v-model="updateForm.passed"
                :items="[
                  { label: '通过', value: true },
                  { label: '未通过', value: false },
                ]"
                label="是否通过"
                variant="outlined"
                density="comfortable"
                clearable
              />
            </v-col>
            <v-col cols="12">
              <v-textarea
                v-model="updateForm.remark"
                label="备注"
                variant="outlined"
                density="comfortable"
                rows="2"
                auto-grow
              />
            </v-col>
          </v-row>
        </v-card-text>
        <v-divider />
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="showUpdateDialog = false">取消</v-btn>
          <v-btn color="primary" variant="flat" @click="submitUpdateTask">
            <v-icon start>mdi-check</v-icon>保存更新
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { trainingApi, type TaskListQuery } from '@/api/training'
import { performanceApi } from '@/api/performance'
import { storeApi } from '@/api/store'
import type {
  PositionInfo,
  Store,
  EmployeePerformance,
  TrainingStats,
  EmployeeCompetencyAssessment,
  TrainingTask,
  HighFrequencyError,
  CreateTrainingTaskRequest,
  UpdateTrainingTaskRequest,
} from '@/types'
import dayjs from 'dayjs'
import {
  Chart,
  RadarController,
  LineController,
  BarController,
  RadialLinearScale,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'

Chart.register(
  RadarController,
  LineController,
  BarController,
  RadialLinearScale,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler,
  Tooltip,
  Legend,
)

const loading = ref(false)
const activeTab = ref('stats')

const storeOptions = ref<Store[]>([])
const positionOptions = ref<PositionInfo[]>([])
const dimensionOptions = ref<{ code: string; label: string }[]>([])
const employeeOptions = ref<{ value: string; label: string }[]>([])

const statusOptions = [
  { label: '待开始', value: 'pending' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
  { label: '未通过', value: 'failed' },
  { label: '已过期', value: 'expired' },
]

const taskTypeOptions = [
  { label: '初次培训', value: 'initial' },
  { label: '复训任务', value: 'refresher' },
  { label: '考核任务', value: 'exam' },
]

const query = reactive({
  start_date: '',
  end_date: '',
  store_id: '',
  position: '',
})

const stats = reactive<TrainingStats>({
  period_start: '',
  period_end: '',
  total_employees: 0,
  total_tasks: 0,
  pending_tasks: 0,
  in_progress_tasks: 0,
  completed_tasks: 0,
  failed_tasks: 0,
  training_completion_rate: 0,
  refresher_tasks: 0,
  refresher_passed: 0,
  refresher_pass_rate: 0,
  exam_tasks: 0,
  exam_passed: 0,
  exam_pass_rate: 0,
  problem_recurrence_rate: 0,
  avg_overall_score: 0,
  dimension_scores: [],
  trend_data: [],
})

const selectedEmployeeId = ref('')
const assessment = ref<EmployeeCompetencyAssessment | null>(null)

const taskFilter = reactive({
  status: '',
  task_type: '',
  competency_dimension: '',
})

const taskQuery = reactive<TaskListQuery>({
  page: 1,
  page_size: 10,
})

const taskList = ref<TrainingTask[]>([])
const taskTotal = ref(0)

const totalTaskPages = computed(() =>
  Math.max(1, Math.ceil(taskTotal.value / (taskQuery.page_size || 10)))
)

const highFreqErrors = ref<HighFrequencyError[]>([])

const showAssignDialog = ref(false)
const assignForm = reactive<CreateTrainingTaskRequest>({
  user_id: '',
  course_name: '',
  competency_dimension: '',
  task_type: 'refresher',
  deadline: '',
  remark: '',
  related_error_ids: [],
  related_trace_ids: [],
})

const showUpdateDialog = ref(false)
const updateTask = ref<TrainingTask | null>(null)
const updateForm = reactive<UpdateTrainingTaskRequest>({
  status: '',
  score: undefined,
  passed: undefined,
  remark: '',
})

const trendChartRef = ref<HTMLCanvasElement | null>(null)
const radarChartRef = ref<HTMLCanvasElement | null>(null)
const employeeRadarRef = ref<HTMLCanvasElement | null>(null)

let trendChart: Chart | null = null
let radarChart: Chart | null = null
let employeeRadarChart: Chart | null = null

function formatDate(d: string) {
  return dayjs(d).format('YYYY-MM-DD HH:mm')
}

function getScoreColor(score: number) {
  if (score >= 90) return 'text-success'
  if (score >= 75) return 'text-primary'
  if (score >= 60) return 'text-warning'
  return 'text-error'
}

function getLevelColor(level: string) {
  const map: Record<string, string> = {
    excellent: 'success',
    good: 'primary',
    normal: 'info',
    weak: 'warning',
    poor: 'error',
  }
  return map[level] || 'default'
}

function getTaskStatusColor(status: string) {
  const map: Record<string, string> = {
    pending: 'secondary',
    in_progress: 'primary',
    completed: 'success',
    failed: 'error',
    expired: 'warning',
  }
  return map[status] || 'default'
}

function resetQuery() {
  query.start_date = ''
  query.end_date = ''
  query.store_id = ''
  query.position = ''
  loadAllData()
}

async function loadOptions() {
  try {
    const [s, p, d, rank] = await Promise.all([
      storeApi.listAll(),
      performanceApi.positions(),
      trainingApi.dimensions(),
      performanceApi.ranking({ page: 1, page_size: 100 }),
    ])
    storeOptions.value = s as any
    positionOptions.value = p
    dimensionOptions.value = d
    employeeOptions.value = (rank.items as EmployeePerformance[]).map((item) => ({
      value: item.user.id,
      label: `${item.user.full_name || item.user.username} (${item.user.position_label || ''})`,
    }))
  } catch (e) {}
}

async function loadStats() {
  try {
    const params: any = {}
    if (query.start_date) params.start_date = query.start_date
    if (query.end_date) params.end_date = query.end_date
    if (query.store_id) params.store_id = query.store_id
    if (query.position) params.position = query.position
    const res = await trainingApi.getStats(params)
    Object.assign(stats, res)
    await nextTick()
    renderTrendChart()
    renderRadarChart()
  } catch (e) {}
}

async function loadAssessment() {
  if (!selectedEmployeeId.value) return
  loading.value = true
  try {
    const params: any = {}
    if (query.start_date) params.start_date = query.start_date
    if (query.end_date) params.end_date = query.end_date
    if (query.store_id) params.store_id = query.store_id
    const res = await trainingApi.getAssessment(selectedEmployeeId.value, params)
    assessment.value = res
    await nextTick()
    renderEmployeeRadar()
  } finally {
    loading.value = false
  }
}

async function refreshAssessment() {
  if (!selectedEmployeeId.value) return
  loading.value = true
  try {
    const params: any = {}
    if (query.start_date) params.start_date = query.start_date
    if (query.end_date) params.end_date = query.end_date
    if (query.store_id) params.store_id = query.store_id
    const res = await trainingApi.refreshAssessment(selectedEmployeeId.value, params)
    assessment.value = res
    await nextTick()
    renderEmployeeRadar()
  } finally {
    loading.value = false
  }
}

async function loadTasks() {
  try {
    const params: TaskListQuery = {
      page: taskQuery.page,
      page_size: taskQuery.page_size,
    }
    if (query.start_date) params.start_date = query.start_date
    if (query.end_date) params.end_date = query.end_date
    if (query.store_id) params.store_id = query.store_id
    if (query.position) params.position = query.position
    if (taskFilter.status) params.status = taskFilter.status
    if (taskFilter.task_type) params.task_type = taskFilter.task_type
    if (taskFilter.competency_dimension) params.competency_dimension = taskFilter.competency_dimension
    const res = await trainingApi.listTasks(params)
    taskList.value = res.items
    taskTotal.value = res.total
  } catch (e) {}
}

async function loadHighFreqErrors() {
  try {
    const params: any = { min_occurrences: 2 }
    if (query.start_date) params.start_date = query.start_date
    if (query.end_date) params.end_date = query.end_date
    if (query.store_id) params.store_id = query.store_id
    highFreqErrors.value = await trainingApi.getHighFrequencyErrors(params)
  } catch (e) {}
}

async function loadAllData() {
  loading.value = true
  try {
    await Promise.all([loadStats(), loadTasks(), loadHighFreqErrors()])
  } finally {
    loading.value = false
  }
}

function renderTrendChart() {
  if (!trendChartRef.value) return
  if (trendChart) trendChart.destroy()
  const ctx = trendChartRef.value.getContext('2d')
  if (!ctx) return

  const labels = stats.trend_data.map((d) => d.period)
  const completionData = stats.trend_data.map((d) => d.completion_rate)

  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: '培训完成率 (%)',
          data: completionData,
          borderColor: 'rgb(var(--v-theme-primary))',
          backgroundColor: 'rgba(var(--v-theme-primary), 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointBackgroundColor: 'rgb(var(--v-theme-primary))',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
        },
      },
    },
  })
}

function renderRadarChart() {
  if (!radarChartRef.value) return
  if (radarChart) radarChart.destroy()
  const ctx = radarChartRef.value.getContext('2d')
  if (!ctx) return

  const labels = stats.dimension_scores.map((d) => d.dimension_label)
  const data = stats.dimension_scores.map((d) => d.avg_score)

  radarChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels,
      datasets: [
        {
          label: '平均得分',
          data,
          borderColor: 'rgb(var(--v-theme-success))',
          backgroundColor: 'rgba(var(--v-theme-success), 0.2)',
          pointBackgroundColor: 'rgb(var(--v-theme-success))',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
        },
      },
    },
  })
}

function renderEmployeeRadar() {
  if (!employeeRadarRef.value || !assessment.value) return
  if (employeeRadarChart) employeeRadarChart.destroy()
  const ctx = employeeRadarRef.value.getContext('2d')
  if (!ctx) return

  const labels = assessment.value.competency_scores.map((s) => s.dimension_label)
  const data = assessment.value.competency_scores.map((s) => s.score)

  employeeRadarChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels,
      datasets: [
        {
          label: '能力得分',
          data,
          borderColor: 'rgb(var(--v-theme-primary))',
          backgroundColor: 'rgba(var(--v-theme-primary), 0.2)',
          pointBackgroundColor: 'rgb(var(--v-theme-primary))',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
        },
      },
    },
  })
}

function openAssignDialogFromError(err: HighFrequencyError) {
  assignForm.competency_dimension = err.competency_dimension
  assignForm.course_name = `${err.error_type_label}专项培训`
  assignForm.remark = `关联高频错误: ${err.description}`
  assignForm.related_error_ids = [err._id]
  assignForm.related_trace_ids = err.related_trace_ids.slice(0, 5)
  showAssignDialog.value = true
}

async function submitAssignTask() {
  if (!assignForm.user_id || !assignForm.course_name || !assignForm.competency_dimension) {
    alert('请填写必要信息')
    return
  }
  try {
    await trainingApi.createTask({ ...assignForm })
    showAssignDialog.value = false
    Object.assign(assignForm, {
      user_id: '',
      course_name: '',
      competency_dimension: '',
      task_type: 'refresher',
      deadline: '',
      remark: '',
      related_error_ids: [],
      related_trace_ids: [],
    })
    await loadTasks()
    await loadStats()
  } catch (e: any) {
    alert(typeof e === 'string' ? e : '指派失败')
  }
}

function openUpdateTaskDialog(task: TrainingTask) {
  updateTask.value = task
  updateForm.status = task.status
  updateForm.score = task.score
  updateForm.passed = task.passed
  updateForm.remark = task.remark || ''
  showUpdateDialog.value = true
}

async function submitUpdateTask() {
  if (!updateTask.value) return
  try {
    await trainingApi.updateTask(updateTask.value._id, { ...updateForm })
    showUpdateDialog.value = false
    await loadTasks()
    await loadStats()
  } catch (e: any) {
    alert(typeof e === 'string' ? e : '更新失败')
  }
}

watch(
  () => [taskFilter.status, taskFilter.task_type, taskFilter.competency_dimension],
  () => {
    taskQuery.page = 1
    loadTasks()
  }
)

onMounted(async () => {
  await loadOptions()
  await loadAllData()
})
</script>
