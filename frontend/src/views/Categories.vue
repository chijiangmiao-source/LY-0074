<template>
  <div>
    <v-card elevation="2" class="mb-4" rounded="lg">
      <v-card-item>
        <div class="d-flex align-center justify-space-between">
          <div>
            <v-card-title class="text-h6">花材分类</v-card-title>
            <v-card-subtitle>管理花材分类信息</v-card-subtitle>
          </div>
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()">
            新增分类
          </v-btn>
        </div>
      </v-card-item>

      <v-divider />

      <v-card-text>
        <v-text-field
          v-model="query.keyword"
          label="搜索分类编号/名称"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          prepend-inner-icon="mdi-magnify"
          @keyup.enter="loadData"
          class="mb-2"
          style="max-width: 360px"
        />
        <v-btn color="primary" variant="flat" class="me-2" @click="loadData">
          查询
        </v-btn>
        <v-btn variant="outlined" @click="resetQuery">重置</v-btn>
      </v-card-text>
    </v-card>

    <v-card elevation="2" rounded="lg">
      <v-table>
        <thead>
          <tr>
            <th>分类编号</th>
            <th>分类名称</th>
            <th>描述</th>
            <th>创建时间</th>
            <th class="text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in data" :key="item._id">
            <td class="font-weight-medium">{{ item.category_code }}</td>
            <td>{{ item.category_name }}</td>
            <td>{{ item.description || '-' }}</td>
            <td>{{ formatDate(item.created_at) }}</td>
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
            <td colspan="5" class="text-center text-medium-emphasis py-8">暂无数据</td>
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

    <v-dialog v-model="dialogVisible" max-width="500" persistent>
      <v-card rounded="lg">
        <v-card-item>
          <v-card-title>{{ editing ? '编辑分类' : '新增分类' }}</v-card-title>
        </v-card-item>
        <v-divider />
        <v-form ref="formRef" @submit.prevent="submitForm">
          <v-card-text>
            <v-text-field
              v-model="form.category_code"
              label="分类编号 *"
              variant="outlined"
              counter
              maxlength="20"
              :rules="[
                (v: string) => !!v || '请输入分类编号',
                (v: string) => (v && v.length <= 20) || '分类编号不能超过20个字符',
                (v: string) => /^[A-Za-z0-9_-]+$/.test(v) || '分类编号只能包含字母、数字、下划线和短横线',
              ]"
              :disabled="editing"
              class="mb-3"
            />
            <v-text-field
              v-model="form.category_name"
              label="分类名称 *"
              variant="outlined"
              counter
              maxlength="30"
              :rules="[
                (v: string) => !!v || '请输入分类名称',
                (v: string) => (v && v.length <= 30) || '分类名称不能超过30个字符',
              ]"
              class="mb-3"
            />
            <v-textarea
              v-model="form.description"
              label="描述"
              variant="outlined"
              rows="3"
              counter
              maxlength="200"
              :rules="[(v: string) => !v || v.length <= 200 || '描述不能超过200个字符']"
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
import { categoryApi } from '@/api/category'
import type { FlowerCategory, CategoryCreate, CategoryUpdate } from '@/types'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const data = ref<FlowerCategory[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
})

const totalPages = computed(() => Math.ceil(total.value / query.page_size))

const dialogVisible = ref(false)
const editing = ref(false)
const editId = ref<string | null>(null)
const formRef = ref()
const form = reactive<CategoryCreate>({
  category_code: '',
  category_name: '',
  description: '',
})

function formatDate(d: string) {
  return dayjs(d).format('YYYY-MM-DD HH:mm')
}

function resetForm() {
  form.category_code = ''
  form.category_name = ''
  form.description = ''
  editing.value = false
  editId.value = null
}

function openDialog(item?: FlowerCategory) {
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
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const res = await categoryApi.list(query)
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
      const d: CategoryUpdate = { ...form }
      await categoryApi.update(editId.value, d)
    } else {
      await categoryApi.create({ ...form })
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

async function deleteItem(item: FlowerCategory) {
  if (!confirm(`确定删除分类「${item.category_name}」吗？`)) return
  try {
    await categoryApi.delete(item._id)
    query.page = 1
    loadData()
  } catch (err: any) {
    alert(typeof err === 'string' ? err : '删除失败')
  }
}

onMounted(loadData)
</script>
