<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import type { TripPlan } from '../types'

const router = useRouter()

const tripPlan = ref<TripPlan | null>(null)
const activeSection = ref('overview')
const activeDayKeys = ref<string[]>([])

const selectedKeys = computed({
  get: () => [activeSection.value],
  set: (val: string[]) => { activeSection.value = val[0] || 'overview' },
})

const editMode = ref(false)
const originalPlan = ref<TripPlan | null>(null)

let mapInstance: any = null
const AMAP_WEB_KEY = import.meta.env.VITE_AMAP_WEB_KEY || ''

onMounted(async () => {
  const state = history.state as { tripPlan?: TripPlan } | null
  if (state?.tripPlan) {
    tripPlan.value = state.tripPlan
    activeDayKeys.value = tripPlan.value.days.map((_, i) => String(i))
    await nextTick()
    initMap()
  } else {
    router.replace({ name: 'home' })
  }
})

const initMap = async () => {
  if (!tripPlan.value || !AMAP_WEB_KEY) return
  try {
    const AMapLoader = (await import('@amap/amap-jsapi-loader')).default
    const AMap = await AMapLoader.load({ key: AMAP_WEB_KEY, version: '2.0' })
    let centerLng = 116.397; let centerLat = 39.916
    const allPoints: [number, number][] = []
    tripPlan.value.days.forEach((day) => {
      day.attractions.forEach((attr) => {
        allPoints.push([attr.location.longitude, attr.location.latitude])
      })
    })
    if (allPoints.length > 0) {
      centerLng = allPoints.reduce((s, p) => s + p[0], 0) / allPoints.length
      centerLat = allPoints.reduce((s, p) => s + p[1], 0) / allPoints.length
    }
    mapInstance = new AMap.Map('amap-container', {
      zoom: 12,
      center: [centerLng, centerLat],
    })
    const markers: any[] = []
    tripPlan.value.days.forEach((day, dayIdx) => {
      day.attractions.forEach((attr, attrIdx) => {
        const marker = new AMap.Marker({
          position: [attr.location.longitude, attr.location.latitude],
          title: attr.name,
          label: {
            content: `<div style="background:#1a2942;color:#fff;padding:2px 7px;border-radius:10px;font-size:11px;font-weight:600">${dayIdx + 1}-${attrIdx + 1}</div>`,
            offset: new AMap.Pixel(0, -30),
          },
        })
        marker.setMap(mapInstance)
        markers.push(marker)
      })
    })
    if (markers.length > 0) mapInstance.setFitView(markers)
  } catch (e) {
    console.warn('地图加载失败:', e)
  }
}

const toggleEditMode = () => {
  if (!editMode.value) originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
  editMode.value = !editMode.value
}

const saveChanges = () => {
  editMode.value = false
  originalPlan.value = null
  message.success('修改已保存')
  nextTick(() => initMap())
}

const cancelEdit = () => {
  if (originalPlan.value) tripPlan.value = originalPlan.value
  editMode.value = false
  originalPlan.value = null
}

const moveAttraction = (dayIndex: number, attrIndex: number, direction: 'up' | 'down') => {
  if (!tripPlan.value) return
  const attractions = tripPlan.value.days[dayIndex].attractions
  const newIndex = direction === 'up' ? attrIndex - 1 : attrIndex + 1
  if (newIndex >= 0 && newIndex < attractions.length) {
    ;[attractions[attrIndex], attractions[newIndex]] = [attractions[newIndex], attractions[attrIndex]]
  }
}

const deleteAttraction = (dayIndex: number, attrIndex: number) => {
  if (!tripPlan.value) return
  tripPlan.value.days[dayIndex].attractions.splice(attrIndex, 1)
}

const scrollToSection = (key: string) => {
  activeSection.value = key
  const element = document.getElementById(key)
  if (element) element.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const goBack = () => router.push({ name: 'home' })

const exportAsImage = async () => {
  const element = document.getElementById('trip-plan-content')
  if (!element) return
  try {
    const canvas = await html2canvas(element, { backgroundColor: '#faf8f4', scale: 2, useCORS: true })
    const link = document.createElement('a')
    link.download = `${tripPlan.value?.city || 'trip'}-plan.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    message.success('图片导出成功！')
  } catch { message.error('导出失败') }
}

const exportAsPDF = async () => {
  const element = document.getElementById('trip-plan-content')
  if (!element) return
  try {
    const canvas = await html2canvas(element, { backgroundColor: '#faf8f4', scale: 2, useCORS: true, allowTaint: true })
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const imgWidth = 210; const imgHeight = (canvas.height * imgWidth) / canvas.width
    let heightLeft = imgHeight; let position = 0
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= 297
    while (heightLeft > 0) {
      position = -(imgHeight - heightLeft)
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= 297
    }
    pdf.save(`${tripPlan.value?.city || 'trip'}-plan.pdf`)
    message.success('PDF 导出成功！')
  } catch { message.error('导出失败') }
}

const imageLoadFailed = reactive<Record<string, boolean>>({})

const getMealIcon = (type: string) => {
  const icons: Record<string, string> = { breakfast: '🌅', lunch: '☀️', dinner: '🌙', snack: '🍿' }
  return icons[type] || '🍽️'
}

const getMealLabel = (type: string) => {
  const labels: Record<string, string> = { breakfast: '早餐', lunch: '午餐', dinner: '晚餐', snack: '小食' }
  return labels[type] || type
}
</script>

<template>
  <div class="result-layout" v-if="tripPlan">
    <div class="layout-inner">
      <!-- Sidebar -->
      <aside class="sidebar">
        <a-affix :offset-top="24">
          <nav class="sidebar-nav">
            <a class="nav-item" :class="{ active: activeSection === 'overview' }" @click="scrollToSection('overview')">行程概览</a>
            <a v-if="tripPlan.budget" class="nav-item" :class="{ active: activeSection === 'budget' }" @click="scrollToSection('budget')">预算明细</a>
            <a class="nav-item" :class="{ active: activeSection === 'map' }" @click="scrollToSection('map')">景点地图</a>
            <a class="nav-item" :class="{ active: activeSection === 'days' }" @click="scrollToSection('days')">每日行程</a>
            <a v-if="tripPlan.weather_info.length" class="nav-item" :class="{ active: activeSection === 'weather' }" @click="scrollToSection('weather')">天气预报</a>
            <a class="nav-item" :class="{ active: activeSection === 'suggestions' }" @click="scrollToSection('suggestions')">出行建议</a>
          </nav>

          <div class="sidebar-actions">
            <a-button :type="editMode ? 'primary' : 'default'" block @click="toggleEditMode" style="margin-bottom:8px">
              {{ editMode ? '退出编辑' : '✏️ 编辑行程' }}
            </a-button>
            <template v-if="editMode">
              <a-button type="primary" block @click="saveChanges" style="margin-bottom:8px">✅ 保存修改</a-button>
              <a-button block @click="cancelEdit" style="margin-bottom:8px">↩️ 取消编辑</a-button>
            </template>
            <a-dropdown>
              <a-button block>📥 导出行程</a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item key="image" @click="exportAsImage">🖼️ 导出为图片</a-menu-item>
                  <a-menu-item key="pdf" @click="exportAsPDF">📄 导出为 PDF</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
            <a-button block style="margin-top:8px" @click="goBack">🏠 重新规划</a-button>
          </div>
        </a-affix>
      </aside>

      <!-- Main -->
      <main class="main-content" id="trip-plan-content">
        <!-- Header -->
        <header class="result-header">
          <div class="header-accent"></div>
          <p class="header-eyebrow">{{ tripPlan.start_date }} &mdash; {{ tripPlan.end_date }} &middot; {{ tripPlan.days.length }} 天</p>
          <h1 class="header-title">{{ tripPlan.city }}</h1>
        </header>

        <!-- Overview -->
        <section id="overview" class="content-section">
          <a-card :bordered="false" class="section-card">
            <h2 class="section-heading">行程概览</h2>
            <a-row :gutter="24">
              <a-col :span="8">
                <div class="stat-item">
                  <span class="stat-value">{{ tripPlan.days.length }}</span>
                  <span class="stat-label">旅行天数</span>
                </div>
              </a-col>
              <a-col :span="8">
                <div class="stat-item">
                  <span class="stat-value">{{ tripPlan.days.reduce((s, d) => s + d.attractions.length, 0) }}</span>
                  <span class="stat-label">景点数量</span>
                </div>
              </a-col>
              <a-col :span="8">
                <div class="stat-item">
                  <span class="stat-value" style="color:#c8963e">¥{{ tripPlan.budget?.total?.toLocaleString() || '—' }}</span>
                  <span class="stat-label">预估总费用</span>
                </div>
              </a-col>
            </a-row>
          </a-card>
        </section>

        <!-- Budget -->
        <section v-if="tripPlan.budget" id="budget" class="content-section">
          <a-card :bordered="false" class="section-card">
            <h2 class="section-heading">预算明细</h2>
            <div class="budget-grid">
              <div class="budget-item">
                <span class="budget-amount">¥{{ tripPlan.budget.total_attractions.toLocaleString() }}</span>
                <span class="budget-category">景点门票</span>
              </div>
              <div class="budget-item">
                <span class="budget-amount">¥{{ tripPlan.budget.total_hotels.toLocaleString() }}</span>
                <span class="budget-category">酒店住宿</span>
              </div>
              <div class="budget-item">
                <span class="budget-amount">¥{{ tripPlan.budget.total_meals.toLocaleString() }}</span>
                <span class="budget-category">餐饮费用</span>
              </div>
              <div class="budget-item">
                <span class="budget-amount">¥{{ tripPlan.budget.total_transportation.toLocaleString() }}</span>
                <span class="budget-category">交通费用</span>
              </div>
            </div>
            <div class="budget-total-bar">
              <span class="budget-total-label">预估总费用</span>
              <span class="budget-total-value">¥{{ tripPlan.budget.total.toLocaleString() }}</span>
            </div>
          </a-card>
        </section>

        <!-- Map -->
        <section id="map" class="content-section">
          <a-card :bordered="false" class="section-card">
            <h2 class="section-heading">景点地图</h2>
            <div id="amap-container" class="map-container">
              <div v-if="!AMAP_WEB_KEY" class="map-placeholder">请配置高德地图 Web JS Key 后查看地图</div>
            </div>
          </a-card>
        </section>

        <!-- Itinerary -->
        <section id="days" class="content-section">
          <a-card :bordered="false" class="section-card">
            <h2 class="section-heading">每日行程</h2>
            <a-collapse v-model:activeKey="activeDayKeys" :bordered="false" ghost expand-icon-position="end">
              <a-collapse-panel v-for="(day, dayIndex) in tripPlan.days" :key="String(dayIndex)">
                <template #header>
                  <div class="day-header">
                    <span class="day-label">第 {{ day.day_index + 1 }} 天</span>
                    <span class="day-date">{{ day.date }}</span>
                    <span class="day-summary">{{ day.attractions.length }} 个景点 &middot; {{ day.hotel?.name || '待定' }}</span>
                  </div>
                </template>

                <p class="day-desc">{{ day.description }}</p>

                <!-- Hotel -->
                <div v-if="day.hotel" class="hotel-card">
                  <div class="hotel-meta">
                    <span class="hotel-name">{{ day.hotel.name }}</span>
                    <span class="hotel-type">{{ day.hotel.type }}</span>
                  </div>
                  <div class="hotel-details">
                    <span>{{ day.hotel.address }}</span>
                    <span v-if="day.hotel.rating"> &middot; {{ day.hotel.rating }}</span>
                    <span> &middot; {{ day.hotel.price_range }}</span>
                  </div>
                </div>

                <!-- Attractions -->
                <div class="attractions-list">
                  <div v-for="(item, index) in day.attractions" :key="index" class="attraction-card">
                    <div class="attr-image-wrap">
                      <img
                        v-if="item.image_url && !imageLoadFailed[`${dayIndex}-${index}`]"
                        :src="item.image_url" :alt="item.name" class="attr-image"
                        @error="imageLoadFailed[`${dayIndex}-${index}`] = true"
                      />
                      <div v-else class="attr-image-fallback">
                        <span class="fallback-num">{{ index + 1 }}</span>
                      </div>
                    </div>
                    <div class="attr-content">
                      <div class="attr-header">
                        <span class="attr-name">{{ item.name }}</span>
                        <div class="attr-tags">
                          <a-tag v-if="item.category" color="gold">{{ item.category }}</a-tag>
                          <a-tag v-if="item.ticket_price > 0">¥{{ item.ticket_price }}</a-tag>
                        </div>
                      </div>
                      <p class="attr-desc">{{ item.description }}</p>
                      <div class="attr-meta">
                        <span>{{ item.address }}</span>
                        <span>{{ item.visit_duration }} min</span>
                        <span v-if="item.rating">{{ item.rating }}/5</span>
                      </div>
                    </div>
                    <div v-if="editMode" class="attr-actions">
                      <a-button size="small" :disabled="index === 0" @click="moveAttraction(dayIndex, index, 'up')">&#8593;</a-button>
                      <a-button size="small" :disabled="index === day.attractions.length - 1" @click="moveAttraction(dayIndex, index, 'down')">&#8595;</a-button>
                      <a-button size="small" danger @click="deleteAttraction(dayIndex, index)">&times;</a-button>
                    </div>
                  </div>
                </div>

                <!-- Meals -->
                <div v-if="day.meals.length > 0" class="meals-list">
                  <h4 class="meals-heading">餐饮安排</h4>
                  <div class="meal-row" v-for="meal in day.meals" :key="meal.type + meal.name">
                    <span class="meal-icon">{{ getMealIcon(meal.type) }}</span>
                    <span class="meal-type">{{ getMealLabel(meal.type) }}</span>
                    <span class="meal-name">{{ meal.name }}</span>
                    <span v-if="meal.estimated_cost > 0" class="meal-cost">¥{{ meal.estimated_cost }}</span>
                    <span v-if="meal.description" class="meal-desc">&mdash; {{ meal.description }}</span>
                  </div>
                </div>
              </a-collapse-panel>
            </a-collapse>
          </a-card>
        </section>

        <!-- Weather -->
        <section v-if="tripPlan.weather_info.length > 0" id="weather" class="content-section">
          <a-card :bordered="false" class="section-card">
            <h2 class="section-heading">天气预报</h2>
            <div class="weather-grid">
              <div v-for="w in tripPlan.weather_info" :key="w.date" class="weather-card">
                <p class="weather-date">{{ w.date }}</p>
                <div class="weather-temps">
                  <span class="temp-high">{{ w.day_temp }}&deg;</span>
                  <span class="temp-divider">/</span>
                  <span class="temp-low">{{ w.night_temp }}&deg;</span>
                </div>
                <p class="weather-desc">白天: {{ w.day_weather }}</p>
                <p class="weather-desc night-desc">夜间: {{ w.night_weather }}</p>
                <p class="weather-wind">{{ w.wind_direction }} {{ w.wind_power }}</p>
              </div>
            </div>
          </a-card>
        </section>

        <!-- Suggestions -->
        <section id="suggestions" class="content-section">
          <a-card :bordered="false" class="section-card">
            <h2 class="section-heading">出行建议</h2>
            <p class="suggestions-text">{{ tripPlan.overall_suggestions }}</p>
          </a-card>
        </section>

        <div class="bottom-spacer"></div>
      </main>
    </div>
  </div>

  <div v-else class="no-data">
    <a-result status="warning" title="暂无行程数据" sub-title="请先在首页填写旅行需求并生成计划">
      <template #extra>
        <a-button type="primary" @click="goBack">返回首页</a-button>
      </template>
    </a-result>
  </div>
</template>

<style scoped>
/* ── Layout ── */
.result-layout {
  min-height: 100vh;
  background: #faf8f4;
}

.layout-inner {
  display: flex;
  max-width: 1150px;
  margin: 0 auto;
}

/* ── Sidebar ── */
.sidebar {
  width: 200px;
  flex-shrink: 0;
  background: #1a2942;
  padding: 28px 20px;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: block;
  padding: 10px 14px;
  color: rgba(255,255,255,0.55);
  font-size: 13px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  letter-spacing: 0.02em;
}

.nav-item:hover {
  color: rgba(255,255,255,0.85);
  background: rgba(255,255,255,0.06);
}

.nav-item.active {
  color: #fff;
  background: rgba(200,150,62,0.2);
}

.sidebar-actions {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.sidebar-actions :deep(.ant-btn) {
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}

.sidebar-actions :deep(.ant-btn-default) {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.15);
  color: rgba(255,255,255,0.7);
}

.sidebar-actions :deep(.ant-btn-default:hover) {
  background: rgba(255,255,255,0.14);
  color: #fff;
  border-color: rgba(255,255,255,0.25);
}

/* ── Main ── */
.main-content {
  flex: 1;
  padding: 32px 36px 0;
  min-width: 0;
}

/* ── Header ── */
.result-header {
  margin-bottom: 36px;
}

.header-accent {
  width: 40px;
  height: 3px;
  background: #c8963e;
  border-radius: 2px;
  margin-bottom: 12px;
}

.header-eyebrow {
  font-size: 13px;
  color: #8b7e74;
  letter-spacing: 0.04em;
  margin-bottom: 6px;
  text-transform: uppercase;
}

.header-title {
  font-family: 'Playfair Display', 'Noto Sans SC', serif;
  font-size: 52px;
  font-weight: 900;
  color: #1a2942;
  letter-spacing: -0.02em;
}

/* ── Content Sections ── */
.content-section {
  margin-bottom: 20px;
}

.section-card {
  border-radius: 16px;
  border: 1px solid #e8e2d8 !important;
  box-shadow: 0 2px 16px rgba(26,41,66,0.04);
}

.section-heading {
  font-family: 'Playfair Display', 'Noto Sans SC', serif;
  font-size: 22px;
  font-weight: 700;
  color: #1a2942;
  margin: 0 0 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f0ebe0;
}

/* ── Stats ── */
.stat-item {
  text-align: center;
  padding: 12px 0;
}

.stat-value {
  display: block;
  font-family: 'Playfair Display', serif;
  font-size: 36px;
  font-weight: 900;
  color: #1a2942;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #8b7e74;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 500;
}

/* ── Budget ── */
.budget-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.budget-item {
  text-align: center;
  padding: 16px 8px;
  background: #faf8f4;
  border-radius: 12px;
}

.budget-amount {
  display: block;
  font-family: 'DM Sans', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: #1a2942;
}

.budget-category {
  font-size: 12px;
  color: #8b7e74;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 4px;
  display: block;
}

.budget-total-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #1a2942, #243556);
  border-radius: 12px;
}

.budget-total-label {
  color: rgba(255,255,255,0.7);
  font-size: 14px;
  font-weight: 500;
}

.budget-total-value {
  font-family: 'Playfair Display', serif;
  font-size: 28px;
  font-weight: 900;
  color: #c8963e;
}

/* ── Map ── */
.map-container {
  width: 100%;
  height: 420px;
  border-radius: 12px;
  background: #f0ebe0;
  overflow: hidden;
}

.map-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #8b7e74;
  font-size: 14px;
}

/* ── Day Header ── */
.day-header {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding-right: 16px;
}

.day-label {
  font-family: 'Playfair Display', serif;
  font-size: 18px;
  font-weight: 700;
  color: #1a2942;
}

.day-date {
  font-size: 13px;
  color: #8b7e74;
}

.day-summary {
  font-size: 12px;
  color: #b8afa0;
  margin-left: auto;
}

/* ── Day Desc ── */
.day-desc {
  color: #5c5040;
  font-size: 14px;
  line-height: 1.7;
  margin-bottom: 16px;
}

/* ── Hotel ── */
.hotel-card {
  background: #faf8f0;
  border: 1px solid #e8e2d8;
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 18px;
}

.hotel-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.hotel-name {
  font-size: 15px;
  font-weight: 700;
  color: #1a2942;
}

.hotel-type {
  font-size: 11px;
  background: #1a2942;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.03em;
}

.hotel-details {
  font-size: 12px;
  color: #8b7e74;
}

/* ── Attractions ── */
.attractions-list {
  margin-bottom: 20px;
}

.attraction-card {
  display: flex;
  gap: 16px;
  padding: 14px;
  margin-bottom: 10px;
  background: #fff;
  border: 1px solid #f0ebe0;
  border-radius: 12px;
  transition: box-shadow 0.2s;
}

.attraction-card:hover {
  box-shadow: 0 2px 12px rgba(26,41,66,0.06);
}

.attr-image-wrap {
  width: 160px;
  height: 120px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
}

.attr-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.attr-image-fallback {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #1a2942, #2d4a6f);
  display: flex;
  align-items: center;
  justify-content: center;
}

.fallback-num {
  font-family: 'Playfair Display', serif;
  font-size: 36px;
  color: rgba(200,150,62,0.5);
  font-weight: 900;
}

.attr-content {
  flex: 1;
  min-width: 0;
}

.attr-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.attr-name {
  font-size: 15px;
  font-weight: 700;
  color: #1a2942;
}

.attr-tags {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.attr-desc {
  margin: 0 0 8px;
  color: #5c5040;
  font-size: 13px;
  line-height: 1.6;
}

.attr-meta {
  display: flex;
  gap: 14px;
  color: #8b7e74;
  font-size: 12px;
}

.attr-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}

.attr-actions :deep(.ant-btn) {
  width: 32px;
  height: 32px;
  padding: 0;
  border-radius: 8px;
}

/* ── Meals ── */
.meals-heading {
  font-size: 14px;
  font-weight: 700;
  color: #1a2942;
  margin: 0 0 10px;
}

.meal-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #f5f0e8;
  font-size: 13px;
}

.meal-row:last-child { border-bottom: none; }

.meal-icon { flex-shrink: 0; }
.meal-type {
  color: #8b7e74;
  font-size: 11px;
  text-transform: uppercase;
  min-width: 60px;
  font-weight: 500;
}

.meal-name {
  font-weight: 600;
  color: #1a2942;
}

.meal-cost { color: #c8963e; font-weight: 600; margin-left: auto; }
.meal-desc { color: #b8afa0; font-size: 12px; }

/* ── Weather ── */
.weather-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.weather-card {
  text-align: center;
  padding: 18px 12px;
  border-radius: 12px;
  background: linear-gradient(135deg, #faf8f0 0%, #f0ebe0 100%);
  border: 1px solid #e8e2d8;
}

.weather-date {
  font-size: 12px;
  color: #8b7e74;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 10px;
  font-weight: 500;
}

.weather-temps {
  margin-bottom: 8px;
}

.temp-high {
  font-family: 'DM Sans', sans-serif;
  font-size: 26px;
  font-weight: 700;
  color: #c05a4a;
}

.temp-divider {
  font-size: 20px;
  color: #b8afa0;
  margin: 0 4px;
}

.temp-low {
  font-family: 'DM Sans', sans-serif;
  font-size: 20px;
  font-weight: 600;
  color: #4a7c96;
}

.weather-desc {
  font-size: 13px;
  color: #5c5040;
  margin: 2px 0;
}

.night-desc { color: #8b7e74; font-size: 12px; }

.weather-wind {
  font-size: 11px;
  color: #b8afa0;
  margin-top: 6px;
}

/* ── Suggestions ── */
.suggestions-text {
  font-size: 14px;
  line-height: 1.9;
  color: #5c5040;
  white-space: pre-wrap;
}

/* ── Bottom ── */
.bottom-spacer { height: 80px; }

/* ── No Data ── */
.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #faf8f4;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .layout-inner { flex-direction: column; }
  .sidebar {
    width: 100%; height: auto; position: static;
    padding: 16px;
  }
  .sidebar-nav {
    flex-direction: row; flex-wrap: wrap; gap: 6px;
  }
  .nav-item { font-size: 12px; padding: 6px 12px; }
  .main-content { padding: 20px; }
  .header-title { font-size: 36px; }
  .budget-grid { grid-template-columns: repeat(2, 1fr); }
  .attraction-card { flex-direction: column; }
  .attr-image-wrap { width: 100%; height: 180px; }
  .weather-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
