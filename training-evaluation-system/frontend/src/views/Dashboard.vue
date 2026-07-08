<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="item in statCards" :key="item.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: item.color }">
              <el-icon :size="28"><component :is="item.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ item.value }}</div>
              <div class="stat-label">{{ item.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>分数分布</span></template>
          <v-chart :option="distributionOption" style="height: 300px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>最近提交</span></template>
          <el-table :data="recentSubmissions" size="small" style="width: 100%">
            <el-table-column prop="student_name" label="学生" width="80" />
            <el-table-column prop="training_title" label="实训项目" show-overflow-tooltip />
            <el-table-column prop="final_score" label="得分" width="70">
              <template #default="{ row }">
                <el-tag v-if="row.final_score" :type="scoreType(row.final_score)" size="small">
                  {{ row.final_score }}
                </el-tag>
                <el-tag v-else type="info" size="small">待评</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'evaluated' ? 'success' : 'warning'" size="small">
                  {{ row.status === 'evaluated' ? '已评价' : '待评价' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { reportAPI } from '../api'
import { use } from 'echarts/core'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, TitleComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([BarChart, PieChart, GridComponent, TooltipComponent, TitleComponent, LegendComponent, CanvasRenderer])

const stats = ref({
  total_trainings: 0, total_submissions: 0, evaluated_count: 0,
  avg_score: 0, score_distribution: {}, recent_submissions: []
})

const statCards = computed(() => [
  { label: '实训项目', value: stats.value.total_trainings, icon: 'Notebook', color: '#409EFF' },
  { label: '学生提交', value: stats.value.total_submissions, icon: 'UserFilled', color: '#67C23A' },
  { label: '已评价', value: stats.value.evaluated_count, icon: 'Finished', color: '#E6A23C' },
  { label: '平均分', value: stats.value.avg_score, icon: 'TrendCharts', color: '#F56C6C' },
])

const distributionOption = computed(() => {
  const dist = stats.value.score_distribution
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: Object.keys(dist) },
    yAxis: { type: 'value', name: '人数' },
    series: [{
      type: 'bar', data: Object.values(dist),
      itemStyle: {
        color: ({ dataIndex }) => ['#F56C6C', '#E6A23C', '#409EFF', '#67C23A', '#909399'][dataIndex]
      }
    }]
  }
})

const recentSubmissions = computed(() => stats.value.recent_submissions || [])

const scoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'warning'
  return 'danger'
}

onMounted(async () => {
  try {
    const { data } = await reportAPI.stats()
    stats.value = data
  } catch (e) { /* handled by interceptor */ }
})
</script>

<style scoped>
.stats-row { margin-bottom: 20px; }
.stat-card .stat-content { display: flex; align-items: center; gap: 16px; }
.stat-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #fff; }
.stat-value { font-size: 28px; font-weight: bold; color: #303133; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.chart-row { margin-top: 0; }
</style>