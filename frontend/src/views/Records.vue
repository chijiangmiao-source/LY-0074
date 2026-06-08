<template>
  <div>
    <v-card elevation="2" class="mb-4" rounded="lg">
      <v-card-item>
        <v-card-title class="text-h6">业务记录</v-card-title>
        <v-card-subtitle>入桶、回桶、保鲜液补充、损耗记录管理</v-card-subtitle>
      </v-card-item>

      <v-divider />

      <v-card-text>
        <v-tabs v-model="activeTab" color="primary" align-tabs="start" density="comfortable">
          <v-tab value="in-bucket" prepend-icon="mdi-arrow-down-bold-box-outline">
            入桶登记
          </v-tab>
          <v-tab value="out-bucket" prepend-icon="mdi-arrow-up-bold-box-outline">
            回桶登记
          </v-tab>
          <v-tab value="preservation" prepend-icon="mdi-water-plus-outline">
            保鲜液补充
          </v-tab>
          <v-tab value="loss" prepend-icon="mdi-alert-circle-outline">
            损耗记录
          </v-tab>
        </v-tabs>
      </v-card-text>
    </v-card>

    <!-- 入桶登记 -->
    <div v-show="activeTab === 'in-bucket'">
      <v-card elevation="2" class="mb-4" rounded="lg">
        <v-card-item>
          <div class="d-flex align-center justify-space-between">
            <v-card-title class="text-subtitle-1">入桶登记</v-card-title>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openInDialog">
              新增入桶
            </v-btn>
          </div>
        </v-card-item>
        <v-divider />
        <v-card-text>
          <v-row align="center">
            <v-col cols="12" md="3">
              <v-date-picker v-model="filter.start_date" label="开始日期" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" md="3">
              <v-date-picker v-model="filter.end_date" label="结束日期" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" md="6">
              <v-btn color="primary" variant="flat" class="me-2" @click="loadInRecords">
                <v-icon start>mdi-magnify</v-icon>查询
              </v-btn>
              <v-btn variant="outlined" @click="resetFilter">
                <v-icon start>mdi-refresh</v-icon>重置
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
        <v-table>
          <thead>
            <tr>
              <th>花桶编号</th>
              <th>花材名称</th>
              <th>数量</th>
              <th>操作人</th>
              <th>备注</th>
              <th>登记时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in inRecords" :key="item._id">
              <td class="font-weight-medium">{{ item.bucket?.bucket_code }}</td>
              <td>{{ item.flower?.flower_name }} ({{ item.flower?.flower_code }})</td>
              <td>{{ item.quantity }} 枝</td>
              <td>{{ item.operator || '-' }}</td>
              <td>{{ item.remark || '-' }}</td>
              <td>{{ formatDate(item.created_at) }}</td>
            </tr>
            <tr v-if="!loading.in && inRecords.length === 0">
              <td colspan="6" class="text-center text-medium-emphasis py-6">暂无数据</td>
            </tr>
          </tbody>
        </v-table>
      </v-card>
    </div>

    <!-- 回桶登记 -->
    <div v-show="activeTab === 'out-bucket'">
      <v-card elevation="2" class="mb-4" rounded="lg">
        <v-card-item>
          <div class="d-flex align-center justify-space-between">
            <v-card-title class="text-subtitle-1">回桶登记</v-card-title>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openOutDialog">
              新增回桶
            </v-btn>
          </div>
        </v-card-item>
        <v-divider />
        <v-card-text>
          <v-row align="center">
            <v-col cols="12" md="3">
              <v-date-picker v-model="filter.start_date" label="开始日期" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" md="3">
              <v-date-picker v-model="filter.end_date" label="结束日期" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" md="6">
              <v-btn color="primary" variant="flat" class="me-2" @click="loadOutRecords">
                <v-icon start>mdi-magnify</v-icon>查询
              </v-btn>
              <v-btn variant="outlined" @click="resetFilter">
                <v-icon start>mdi-refresh</v-icon>重置
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
        <v-table>
          <thead>
            <tr>
              <th>花桶编号</th>
              <th>花材名称</th>
              <th>数量</th>
              <th>操作人</th>
              <th>备注</th>
              <th>登记时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in outRecords" :key="item._id">
              <td class="font-weight-medium">{{ item.bucket?.bucket_code }}</td>
              <td>{{ item.flower?.flower_name }} ({{ item.flower?.flower_code }})</td>
              <td>{{ item.quantity }} 枝</td>
              <td>{{ item.operator || '-' }}</td>
              <td>{{ item.remark || '-' }}</td>
              <td>{{ formatDate(item.created_at) }}</td>
            </tr>
            <tr v-if="!loading.out && outRecords.length === 0">
              <td colspan="6" class="text-center text-medium-emphasis py-6">暂无数据</td>
            </tr>
          </tbody>
        </v-table>
      </v-card>
    </div>

    <!-- 保鲜液补充 -->
    <div v-show="activeTab === 'preservation'">
      <v-card elevation="2" class="mb-4" rounded="lg">
        <v-card-item>
          <div class="d-flex align-center justify-space-between">
            <v-card-title class="text-subtitle-1">保鲜液补充记录</v-card-title>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openPreservationDialog">
              新增补充
            </v-btn>
          </div>
        </v-card-item>
        <v-divider />
        <v-card-text>
          <v-row align="center">
            <v-col cols="12" md="3">
              <v-select
                v-model="filter.store_id"
                :items="storeOptions"
                item-title="store_name"
                item-value="_id"
                label="门店"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-date-picker v-model="filter.start_date" label="开始日期" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" md="3">
              <v-date-picker v-model="filter.end_date" label="结束日期" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" md="3">
              <v-btn color="primary" variant="flat" class="me-2" @click="loadPreservationRecords">查询</v-btn>
              <v-btn variant="outlined" @click="resetFilter">重置</v-btn>
            </v-col>
          </v-row>
        </v-card-text>
        <v-table>
          <thead>
            <tr>
              <th>花桶编号</th>
              <th>所属门店</th>
              <th>补充前液位</th>
              <th>补充量</th>
              <th>补充后液位</th>
              <th>操作人</th>
              <th>登记时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in preservationRecords" :key="item._id">
              <td class="font-weight-medium">{{ item.bucket?.bucket_code }}</td>
              <td>{{ item.store?.store_name || '-' }}</td>
              <td>{{ item.previous_quantity }} L</td>
              <td class="text-success font-weight-medium">+ {{ item.supplement_quantity }} L</td>
              <td>{{ item.after_quantity }} L</td>
              <td>{{ item.operator || '-' }}</td>
              <td>{{ formatDate(item.created_at) }}</td>
            </tr>
            <tr v-if="!loading.preservation && preservationRecords.length === 0">
              <td colspan="7" class="text-center text-medium-emphasis py-6">暂无数据</td>
            </tr>
          </tbody>
        </v-table>
      </v-card>
    </div>

    <!-- 损耗记录 -->
    <div v-show="activeTab === 'loss'">
      <v-card elevation="2" class="mb-4" rounded="lg">
        <v-card-item>
          <div class="d-flex align-center justify-space-between">
            <v-card-title class="text-subtitle-1">损耗记录</v-card-title>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openLossDialog">
              新增损耗
            </v-btn>
          </div>
        </v-card-item>
        <v-divider />
        <v-card-text>
          <v-row align="center">
            <v-col cols="12" md="3">
              <v-select
                v-model="filter.store_id"
                :items="storeOptions"
                item-title="store_name"
                item-value="_id"
                label="门店"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-date-picker v-model="filter.start_date" label="开始日期" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" md="3">
              <v-date-picker v-model="filter.end_date" label="结束日期" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" md="3">
              <v-btn color="primary" variant="flat" class="me-2" @click="loadLossRecords">查询</v-btn>
              <v-btn variant="outlined" @click="resetFilter">重置</v-btn>
            </v-col>
          </v-row>
        </v-card-text>
        <v-table>
          <thead>
            <tr>
              <th>花材名称</th>
              <th>所属门店</th>
              <th>损耗数量</th>
              <th>损耗原因</th>
              <th>操作人</th>
              <th>登记时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in lossRecords" :key="item._id">
              <td class="font-weight-medium">{{ item.flower?.flower_name }} ({{ item.flower?.flower_code }})</td>
              <td>{{ item.store?.store_name || '-' }}</td>
              <td class="text-error font-weight-medium">- {{ item.quantity }} 枝</td>
              <td>{{ item.reason || '-' }}</td>
              <td>{{ item.operator || '-' }}</td>
              <td>{{ formatDate(item.created_at) }}</td>
            </tr>
            <tr v-if="!loading.loss && lossRecords.length === 0">
              <td colspan="6" class="text-center text-medium-emphasis py-6">暂无数据</td>
            </tr>
          </tbody>
        </v-table>
      </v-card>
    </div>

    <!-- 入桶对话框 -->
    <v-dialog v-model="dialog.in" max-width="500" persistent>
      <v-card rounded="lg">
        <v-card-item><v-card-title>入桶登记</v-card-title></v-card-item>
        <v-divider />
        <v-form @submit.prevent="submitInBucket">
          <v-card-text>
            <v-select
              v-model="inForm.bucket_id"
              :items="activeBuckets"
              item-title="bucket_code"
              item-value="_id"
              label="选择花桶 *"
              variant="outlined"
              :rules="[(v: string) => !!v || '请选择花桶']"
              class="mb-3"
            />
            <v-select
              v-model="inForm.flower_id"
              :items="flowerOptions"
              item-title="flower_name"
              item-value="_id"
              label="选择花材 *"
              variant="outlined"
              :rules="[(v: string) => !!v || '请选择花材']"
              class="mb-3"
            />
            <v-text-field
              v-model.number="inForm.quantity"
              type="number"
              label="入桶数量(枝) *"
              variant="outlined"
              min="1"
              max="100000"
              :rules="[
                (v: number) => (v && v > 0) || '数量必须大于0',
                (v: number) => !v || v <= 100000 || '数量不能超过100000',
              ]"
              class="mb-3"
            />
            <v-text-field
              v-model="inForm.operator"
              label="操作人"
              variant="outlined"
              counter
              maxlength="20"
              :rules="[(v: string) => !v || v.length <= 20 || '操作人姓名不能超过20个字符']"
              class="mb-3"
            />
            <v-textarea
              v-model="inForm.remark"
              label="备注"
              variant="outlined"
              rows="2"
              counter
              maxlength="200"
              :rules="[(v: string) => !v || v.length <= 200 || '备注不能超过200个字符']"
            />
          </v-card-text>
          <v-divider />
          <v-card-actions class="justify-end">
            <v-btn variant="text" @click="dialog.in = false">取消</v-btn>
            <v-btn color="primary" type="submit" :loading="submitting.in">确定</v-btn>
          </v-card-actions>
        </v-form>
      </v-card>
    </v-dialog>

    <!-- 回桶对话框 -->
    <v-dialog v-model="dialog.out" max-width="500" persistent>
      <v-card rounded="lg">
        <v-card-item><v-card-title>回桶登记</v-card-title></v-card-item>
        <v-divider />
        <v-form @submit.prevent="submitOutBucket">
          <v-card-text>
            <v-select
              v-model="outForm.bucket_id"
              :items="bucketOptions"
              item-title="bucket_code"
              item-value="_id"
              label="选择花桶 *"
              variant="outlined"
              :rules="[(v: string) => !!v || '请选择花桶']"
              class="mb-3"
            />
            <v-select
              v-model="outForm.flower_id"
              :items="flowerOptions"
              item-title="flower_name"
              item-value="_id"
              label="选择花材 *"
              variant="outlined"
              :rules="[(v: string) => !!v || '请选择花材']"
              class="mb-3"
            />
            <v-text-field
              v-model.number="outForm.quantity"
              type="number"
              label="回桶数量(枝) *"
              variant="outlined"
              min="1"
              max="100000"
              :rules="[
                (v: number) => (v && v > 0) || '数量必须大于0',
                (v: number) => !v || v <= 100000 || '数量不能超过100000',
              ]"
              class="mb-3"
            />
            <v-text-field
              v-model="outForm.operator"
              label="操作人"
              variant="outlined"
              counter
              maxlength="20"
              :rules="[(v: string) => !v || v.length <= 20 || '操作人姓名不能超过20个字符']"
              class="mb-3"
            />
            <v-textarea
              v-model="outForm.remark"
              label="备注"
              variant="outlined"
              rows="2"
              counter
              maxlength="200"
              :rules="[(v: string) => !v || v.length <= 200 || '备注不能超过200个字符']"
            />
          </v-card-text>
          <v-divider />
          <v-card-actions class="justify-end">
            <v-btn variant="text" @click="dialog.out = false">取消</v-btn>
            <v-btn color="primary" type="submit" :loading="submitting.out">确定</v-btn>
          </v-card-actions>
        </v-form>
      </v-card>
    </v-dialog>

    <!-- 保鲜液补充对话框 -->
    <v-dialog v-model="dialog.preservation" max-width="500" persistent>
      <v-card rounded="lg">
        <v-card-item><v-card-title>保鲜液补充</v-card-title></v-card-item>
        <v-divider />
        <v-form @submit.prevent="submitPreservation">
          <v-card-text>
            <v-select
              v-model="preservationForm.bucket_id"
              :items="bucketOptions"
              item-title="bucket_code"
              item-value="_id"
              label="选择花桶 *"
              variant="outlined"
              :rules="[(v: string) => !!v || '请选择花桶']"
              class="mb-3"
            />
            <v-text-field
              v-model.number="preservationForm.supplement_quantity"
              type="number"
              label="补充量(L) *"
              variant="outlined"
              min="0.1"
              max="1000"
              step="0.1"
              :rules="[
                (v: number) => (v && v > 0) || '补充量必须大于0',
                (v: number) => !v || v <= 1000 || '补充量不能超过1000L',
              ]"
              class="mb-3"
            />
            <v-text-field
              v-model="preservationForm.operator"
              label="操作人"
              variant="outlined"
              counter
              maxlength="20"
              :rules="[(v: string) => !v || v.length <= 20 || '操作人姓名不能超过20个字符']"
              class="mb-3"
            />
            <v-textarea
              v-model="preservationForm.remark"
              label="备注"
              variant="outlined"
              rows="2"
              counter
              maxlength="200"
              :rules="[(v: string) => !v || v.length <= 200 || '备注不能超过200个字符']"
            />
          </v-card-text>
          <v-divider />
          <v-card-actions class="justify-end">
            <v-btn variant="text" @click="dialog.preservation = false">取消</v-btn>
            <v-btn color="primary" type="submit" :loading="submitting.preservation">确定</v-btn>
          </v-card-actions>
        </v-form>
      </v-card>
    </v-dialog>

    <!-- 损耗对话框 -->
    <v-dialog v-model="dialog.loss" max-width="500" persistent>
      <v-card rounded="lg">
        <v-card-item><v-card-title>损耗登记</v-card-title></v-card-item>
        <v-divider />
        <v-form @submit.prevent="submitLoss">
          <v-card-text>
            <v-select
              v-model="lossForm.flower_id"
              :items="flowerOptions"
              item-title="flower_name"
              item-value="_id"
              label="选择花材 *"
              variant="outlined"
              :rules="[(v: string) => !!v || '请选择花材']"
              class="mb-3"
            />
            <v-text-field
              v-model.number="lossForm.quantity"
              type="number"
              label="损耗数量(枝) *"
              variant="outlined"
              min="1"
              max="100000"
              :rules="[
                (v: number) => (v && v > 0) || '数量必须大于0',
                (v: number) => !v || v <= 100000 || '数量不能超过100000',
              ]"
              class="mb-3"
            />
            <v-text-field
              v-model="lossForm.reason"
              label="损耗原因"
              variant="outlined"
              counter
              maxlength="100"
              :rules="[(v: string) => !v || v.length <= 100 || '损耗原因不能超过100个字符']"
              class="mb-3"
            />
            <v-text-field
              v-model="lossForm.operator"
              label="操作人"
              variant="outlined"
              counter
              maxlength="20"
              :rules="[(v: string) => !v || v.length <= 20 || '操作人姓名不能超过20个字符']"
              class="mb-3"
            />
            <v-textarea
              v-model="lossForm.remark"
              label="备注"
              variant="outlined"
              rows="2"
              counter
              maxlength="200"
              :rules="[(v: string) => !v || v.length <= 200 || '备注不能超过200个字符']"
            />
          </v-card-text>
          <v-divider />
          <v-card-actions class="justify-end">
            <v-btn variant="text" @click="dialog.loss = false">取消</v-btn>
            <v-btn color="primary" type="submit" :loading="submitting.loss">确定</v-btn>
          </v-card-actions>
        </v-form>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { recordApi, type BucketInCreate, type BucketOutCreate, type PreservationCreate, type LossCreate } from '@/api/record'
import { bucketApi } from '@/api/bucket'
import { flowerApi } from '@/api/flower'
import { storeApi } from '@/api/store'
import type { BucketInRecord, BucketOutRecord, PreservationRecord, LossRecord, Bucket, Flower, Store } from '@/types'
import dayjs from 'dayjs'

const activeTab = ref('in-bucket')
const loading = reactive({ in: false, out: false, preservation: false, loss: false })
const submitting = reactive({ in: false, out: false, preservation: false, loss: false })

const inRecords = ref<BucketInRecord[]>([])
const outRecords = ref<BucketOutRecord[]>([])
const preservationRecords = ref<PreservationRecord[]>([])
const lossRecords = ref<LossRecord[]>([])

const bucketOptions = ref<Bucket[]>([])
const activeBuckets = ref<Bucket[]>([])
const flowerOptions = ref<Flower[]>([])
const storeOptions = ref<Store[]>([])

const filter = reactive({
  start_date: '',
  end_date: '',
  store_id: '',
})

const dialog = reactive({ in: false, out: false, preservation: false, loss: false })
const inForm = reactive<BucketInCreate>({ bucket_id: '', flower_id: '', quantity: 0, operator: '', remark: '' })
const outForm = reactive<BucketOutCreate>({ bucket_id: '', flower_id: '', quantity: 0, operator: '', remark: '' })
const preservationForm = reactive<PreservationCreate>({ bucket_id: '', supplement_quantity: 0, operator: '', remark: '' })
const lossForm = reactive<LossCreate>({ flower_id: '', quantity: 0, reason: '', operator: '', remark: '' })

function formatDate(d: string) {
  return dayjs(d).format('YYYY-MM-DD HH:mm')
}

function resetFilter() {
  filter.start_date = ''
  filter.end_date = ''
  filter.store_id = ''
  loadAll()
}

function resetForms() {
  Object.assign(inForm, { bucket_id: '', flower_id: '', quantity: 0, operator: '', remark: '' })
  Object.assign(outForm, { bucket_id: '', flower_id: '', quantity: 0, operator: '', remark: '' })
  Object.assign(preservationForm, { bucket_id: '', supplement_quantity: 0, operator: '', remark: '' })
  Object.assign(lossForm, { flower_id: '', quantity: 0, reason: '', operator: '', remark: '' })
}

async function openInDialog() {
  resetForms()
  if (activeBuckets.value.length === 0) {
    activeBuckets.value = await bucketApi.listAll({ status: 'active' })
  }
  if (flowerOptions.value.length === 0) {
    flowerOptions.value = await flowerApi.listAll()
  }
  dialog.in = true
}
async function openOutDialog() {
  resetForms()
  if (bucketOptions.value.length === 0) {
    bucketOptions.value = await bucketApi.listAll()
  }
  if (flowerOptions.value.length === 0) {
    flowerOptions.value = await flowerApi.listAll()
  }
  dialog.out = true
}
async function openPreservationDialog() {
  resetForms()
  if (bucketOptions.value.length === 0) {
    bucketOptions.value = await bucketApi.listAll()
  }
  dialog.preservation = true
}
async function openLossDialog() {
  resetForms()
  if (flowerOptions.value.length === 0) {
    flowerOptions.value = await flowerApi.listAll()
  }
  dialog.loss = true
}

async function loadOptions() {
  bucketOptions.value = await bucketApi.listAll()
  activeBuckets.value = await bucketApi.listAll({ status: 'active' })
  flowerOptions.value = await flowerApi.listAll()
  storeOptions.value = await storeApi.listAll()
}

async function loadInRecords() {
  loading.in = true
  try {
    const p: any = { page: 1, page_size: 100 }
    if (filter.start_date) p.start_date = filter.start_date
    if (filter.end_date) p.end_date = filter.end_date
    const res = await recordApi.listInBucket(p)
    inRecords.value = res.items as any
  } finally { loading.in = false }
}

async function loadOutRecords() {
  loading.out = true
  try {
    const p: any = { page: 1, page_size: 100 }
    if (filter.start_date) p.start_date = filter.start_date
    if (filter.end_date) p.end_date = filter.end_date
    const res = await recordApi.listOutBucket(p)
    outRecords.value = res.items as any
  } finally { loading.out = false }
}

async function loadPreservationRecords() {
  loading.preservation = true
  try {
    const p: any = { page: 1, page_size: 100 }
    if (filter.store_id) p.store_id = filter.store_id
    if (filter.start_date) p.start_date = filter.start_date
    if (filter.end_date) p.end_date = filter.end_date
    const res = await recordApi.listPreservation(p)
    preservationRecords.value = res.items as any
  } finally { loading.preservation = false }
}

async function loadLossRecords() {
  loading.loss = true
  try {
    const p: any = { page: 1, page_size: 100 }
    if (filter.store_id) p.store_id = filter.store_id
    if (filter.start_date) p.start_date = filter.start_date
    if (filter.end_date) p.end_date = filter.end_date
    const res = await recordApi.listLoss(p)
    lossRecords.value = res.items as any
  } finally { loading.loss = false }
}

function loadAll() {
  loadInRecords()
  loadOutRecords()
  loadPreservationRecords()
  loadLossRecords()
}

async function submitInBucket() {
  submitting.in = true
  try {
    await recordApi.createInBucket({ ...inForm })
    dialog.in = false
    loadInRecords()
    await loadOptions()
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '操作失败')
  } finally { submitting.in = false }
}

async function submitOutBucket() {
  submitting.out = true
  try {
    await recordApi.createOutBucket({ ...outForm })
    dialog.out = false
    loadOutRecords()
    await loadOptions()
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '操作失败')
  } finally { submitting.out = false }
}

async function submitPreservation() {
  submitting.preservation = true
  try {
    await recordApi.createPreservation({ ...preservationForm })
    dialog.preservation = false
    loadPreservationRecords()
    await loadOptions()
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '操作失败')
  } finally { submitting.preservation = false }
}

async function submitLoss() {
  submitting.loss = true
  try {
    await recordApi.createLoss({ ...lossForm })
    dialog.loss = false
    loadLossRecords()
    await loadOptions()
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '操作失败')
  } finally { submitting.loss = false }
}

watch(activeTab, (t) => {
  if (t === 'in-bucket') loadInRecords()
  else if (t === 'out-bucket') loadOutRecords()
  else if (t === 'preservation') loadPreservationRecords()
  else if (t === 'loss') loadLossRecords()
})

onMounted(async () => {
  await loadOptions()
  loadAll()
})
</script>
