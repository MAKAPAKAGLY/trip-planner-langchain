<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateTripPlan } from '../services/api'
import type { TripPlanRequest } from '../types'

const router = useRouter()

const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')

const formData = reactive<TripPlanRequest>({
  city: '',
  start_date: '',
  end_date: '',
  days: 3,
  preferences: '综合体验',
  budget: '中等',
  transportation: '公共交通',
  accommodation: '舒适型酒店',
  notes: '',
})

const formRef = ref()

const preferenceOptions = [
  { label: '综合体验', value: '综合体验' },
  { label: '历史文化', value: '历史文化' },
  { label: '自然风光', value: '自然风光' },
  { label: '美食之旅', value: '美食之旅' },
  { label: '亲子游乐', value: '亲子游乐' },
  { label: '购物休闲', value: '购物休闲' },
]

const budgetOptions = [
  { label: '经济实惠', value: '经济' },
  { label: '中等预算', value: '中等' },
  { label: '舒适享受', value: '舒适' },
  { label: '豪华体验', value: '豪华' },
]

const transportOptions = [
  { label: '公共交通', value: '公共交通' },
  { label: '自驾', value: '自驾' },
  { label: '出租车/网约车', value: '出租车' },
  { label: '租车', value: '租车' },
]

const accommodationOptions = [
  { label: '舒适型酒店', value: '舒适型酒店' },
  { label: '经济型酒店', value: '经济型酒店' },
  { label: '豪华型酒店', value: '豪华型酒店' },
  { label: '民宿/客栈', value: '民宿' },
]

const rules = {
  city: [{ required: true, message: '请输入目的地城市', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择出发日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
}

watch(
  [() => formData.start_date, () => formData.end_date],
  ([start, end]) => {
    if (start && end) {
      const startDate = new Date(start)
      const endDate = new Date(end)
      if (!isNaN(startDate.getTime()) && !isNaN(endDate.getTime()) && endDate >= startDate) {
        const diffTime = Date.UTC(
          endDate.getFullYear(), endDate.getMonth(), endDate.getDate()
        ) - Date.UTC(
          startDate.getFullYear(), startDate.getMonth(), startDate.getDate()
        )
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1
        formData.days = Math.max(1, Math.min(30, diffDays))
      }
    }
  }
)

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  if (formData.start_date && formData.end_date) {
    const start = new Date(formData.start_date)
    const end = new Date(formData.end_date)
    if (end < start) {
      message.error('结束日期不能早于开始日期')
      return
    }
  }

  loading.value = true
  loadingProgress.value = 0
  loadingStatus.value = ''

  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += Math.random() * 8 + 2
      if (loadingProgress.value > 90) loadingProgress.value = 90
      if (loadingProgress.value <= 30) {
        loadingStatus.value = '🔍 正在搜索景点…'
      } else if (loadingProgress.value <= 55) {
        loadingStatus.value = '🌤️ 正在查询天气…'
      } else if (loadingProgress.value <= 75) {
        loadingStatus.value = '🏨 正在搜索酒店…'
      } else {
        loadingStatus.value = '📋 正在生成行程计划…'
      }
    }
  }, 600)

  try {
    const response = await generateTripPlan(formData)
    clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '✅ 完成！'
    setTimeout(() => {
      router.push({
        name: 'result',
        state: { tripPlan: response as any },
      })
    }, 500)
  } catch (error: any) {
    clearInterval(progressInterval)
    message.error(error.message || '生成计划失败，请重试')
    loading.value = false
  }
}
</script>

<template>
  <div class="home-container">
    <!-- Hero Section -->
    <header class="hero">
      <div class="hero-accent"></div>
      <p class="hero-eyebrow">AI 多智能体协作规划</p>
      <h1 class="hero-title">
        智能旅行助手
      </h1>
      <p class="hero-subtitle">
        告诉我们你的梦想目的地，AI 将为你自动搜索景点、天气、酒店，生成一份完整的个性化旅行计划。
      </p>
    </header>

    <!-- Form Card -->
    <a-card class="form-card" :bordered="false">
      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
        @finish="handleSubmit"
        :disabled="loading"
      >
        <!-- Row 1: City + Days -->
        <a-row :gutter="20">
          <a-col :span="16">
            <a-form-item label="目的地城市" name="city">
              <a-input
                v-model:value="formData.city"
                placeholder="你想去哪里？如：北京、杭州、成都…"
                size="large"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="旅行天数" name="days">
              <a-input-number
                v-model:value="formData.days"
                :min="1"
                :max="30"
                style="width: 100%"
                size="large"
                :disabled="!!(formData.start_date && formData.end_date)"
              />
              <div v-if="formData.start_date && formData.end_date" class="days-hint">
                已根据日期范围自动计算
              </div>
            </a-form-item>
          </a-col>
        </a-row>

        <!-- Row 2: Dates -->
        <a-row :gutter="20">
          <a-col :span="12">
            <a-form-item label="出发日期" name="start_date">
              <a-date-picker
                v-model:value="formData.start_date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                size="large"
                placeholder="选择出发日期"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束日期" name="end_date">
              <a-date-picker
                v-model:value="formData.end_date"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                size="large"
                placeholder="选择结束日期"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- Row 3: Preferences + Budget -->
        <a-row :gutter="20">
          <a-col :span="12">
            <a-form-item label="旅行偏好" name="preferences">
              <a-select
                v-model:value="formData.preferences"
                :options="preferenceOptions"
                size="large"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="预算水平" name="budget">
              <a-select
                v-model:value="formData.budget"
                :options="budgetOptions"
                size="large"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- Row 4: Transport + Accommodation -->
        <a-row :gutter="20">
          <a-col :span="12">
            <a-form-item label="交通方式" name="transportation">
              <a-select
                v-model:value="formData.transportation"
                :options="transportOptions"
                size="large"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="住宿类型" name="accommodation">
              <a-select
                v-model:value="formData.accommodation"
                :options="accommodationOptions"
                size="large"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- Row 5: Notes -->
        <a-row :gutter="20">
          <a-col :span="24">
            <a-form-item label="补充说明" name="notes">
              <a-textarea
                v-model:value="formData.notes"
                placeholder="还有什么想告诉我们的？比如必去的景点、饮食偏好、行动便利性、行程节奏…"
                :rows="3"
                :auto-size="{ minRows: 3, maxRows: 6 }"
              />
              <div class="notes-hint">
                选填 — 补充下拉选项之外的特殊需求
              </div>
            </a-form-item>
          </a-col>
        </a-row>

        <!-- Submit -->
        <a-form-item style="margin-bottom: 0">
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            :loading="loading"
            block
            class="submit-btn"
          >
            <template v-if="!loading">🚀 开始规划</template>
            <template v-else>正在生成旅行计划…</template>
          </a-button>
        </a-form-item>

        <!-- Loading indicator -->
        <div v-if="loading" class="loading-section">
          <a-progress
            :percent="Math.round(loadingProgress)"
            :status="loadingProgress >= 100 ? 'success' : 'active'"
            :stroke-color="{ from: '#c8963e', to: '#1a2942' }"
            :show-info="false"
          />
          <p class="loading-status">{{ loadingStatus }}</p>
        </div>
      </a-form>
    </a-card>

    <!-- Feature Highlights -->
    <div class="feature-row">
      <div class="feature-item">
        <span class="feature-icon">&#9670;</span>
        <div>
          <h4>多智能体协作</h4>
          <p>四个专门 Agent 并行搜索景点、天气、酒店，自动生成个性化行程</p>
        </div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">&#9670;</span>
        <div>
          <h4>地图可视化</h4>
          <p>所有景点标注在交互地图上，路线一目了然</p>
        </div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">&#9670;</span>
        <div>
          <h4>预算明细</h4>
          <p>自动计算门票、住宿、餐饮、交通费用，消费透明</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Container ── */
.home-container {
  max-width: 820px;
  margin: 0 auto;
  padding: 56px 24px 80px;
}

/* ── Hero ── */
.hero {
  text-align: center;
  margin-bottom: 40px;
  position: relative;
}

.hero-accent {
  width: 48px;
  height: 3px;
  background: #c8963e;
  margin: 0 auto 20px;
  border-radius: 2px;
}

.hero-eyebrow {
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #8b7e74;
  margin-bottom: 12px;
}

.hero-title {
  font-family: 'Playfair Display', 'Noto Sans SC', serif;
  font-size: 48px;
  font-weight: 900;
  color: #1a2942;
  line-height: 1.15;
  margin-bottom: 16px;
  letter-spacing: -0.02em;
}

.hero-title-accent {
  color: #c8963e;
  font-style: italic;
}

.hero-subtitle {
  font-size: 16px;
  color: #8b7e74;
  max-width: 540px;
  margin: 0 auto;
  line-height: 1.7;
  font-weight: 400;
}

/* ── Form Card ── */
.form-card {
  border-radius: 20px;
  box-shadow:
    0 1px 0 rgba(0,0,0,0.02),
    0 4px 32px rgba(26, 41, 66, 0.06),
    0 12px 64px rgba(26, 41, 66, 0.03);
  background: #ffffff;
  border: 1px solid #e8e2d8;
  margin-bottom: 48px;
  padding: 4px;
}

.form-card :deep(.ant-card-body) {
  padding: 36px 40px;
}

/* ── Form items ── */
.form-card :deep(.ant-form-item-label > label) {
  font-size: 13px;
  font-weight: 600;
  color: #5c5040;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.days-hint {
  margin-top: 4px;
  font-size: 11px;
  color: #8b7e74;
  font-style: italic;
}

.notes-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #b8afa0;
  font-style: italic;
}

/* ── Submit Button ── */
.submit-btn {
  height: 52px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em;
  border-radius: 12px !important;
  margin-top: 8px;
  font-family: 'DM Sans', 'Noto Sans SC', sans-serif !important;
}

/* ── Loading ── */
.loading-section {
  text-align: center;
  padding: 24px 0 8px;
}

.loading-status {
  margin-top: 14px;
  font-size: 14px;
  color: #8b7e74;
  font-style: italic;
}

/* ── Feature Row ── */
.feature-row {
  display: flex;
  gap: 28px;
}

.feature-item {
  flex: 1;
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.feature-icon {
  font-size: 18px;
  color: #c8963e;
  margin-top: 2px;
  flex-shrink: 0;
}

.feature-item h4 {
  font-family: 'DM Sans', 'Noto Sans SC', sans-serif;
  font-size: 14px;
  font-weight: 700;
  color: #1a2942;
  margin: 0 0 4px;
}

.feature-item p {
  font-size: 13px;
  color: #8b7e74;
  margin: 0;
  line-height: 1.6;
}

/* ── Responsive ── */
@media (max-width: 640px) {
  .home-container {
    padding: 32px 16px 60px;
  }

  .hero-title {
    font-size: 32px;
  }

  .hero-subtitle {
    font-size: 14px;
  }

  .form-card :deep(.ant-card-body) {
    padding: 24px 20px;
  }

  .feature-row {
    flex-direction: column;
    gap: 20px;
  }
}
</style>
