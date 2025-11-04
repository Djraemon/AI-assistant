<template>
  <div class="result">
    <h2>测试题</h2>
    <div v-for="(question, index) in questions" :key="index" class="question-block">
      <h3  style="white-space: pre-line;">{{ index + 1 }}. {{ question.text }}</h3>
      <div class="options">
        <button
          v-for="(option, idx) in question.options"
          :key="idx"
          :class="['option-btn', selectedAnswers[index] === idx ? (option.correct ? 'correct' : 'wrong') : '']"
          :disabled="selectedAnswers[index] !== null"
          @click="selectAnswer(index, idx)"
        >
          {{ option.text }}
        </button>
      </div>
    </div>

    <div v-if="allAnswered" class="score">
      <h3>测试完成！您的得分：{{ score }} / {{ questions.length }}</h3>
      <button @click="saveScore">保存成绩</button>
      <button @click="resetTest">重新开始</button>
      <p v-if="submitMessage" :class="submitSuccess ? 'success-message' : 'error-message'">
        {{ submitMessage }}
      </p>
    </div>
  </div>
</template>

<script lang="ts" setup name="TestQuiz">
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8000/api'

const studentId = ref('student_001') // 使用 ref 定义
const testId = ref('1') // 使用 ref 定义
const submitData = ref<any>(null)

interface Option {
  text: string,
  correct: boolean
}

interface Question {
  type: 'single' | 'judge',
  text: string,
  options: Option[]
}

const questions = ref<Question[]>([
  {
    type: 'single',
    text: '为什么我们说数据像未加工的原油？ 以下哪一个不是合理的原因？',
    options: [
      { text: '数据有价值', correct: false },
      { text: '需要被加工才能使用', correct: false },
      { text: '一个数据集可以应用到不同的分析目的', correct: false },
      { text: '可以被出售', correct: true }
    ]
  },
  {
    type: 'single',
    text: '产生和消费数据的模式已经转变为以下哪种情况？',
    options: [
      { text: '少数公司产生数据，其他公司消费数据', correct: false },
      { text: '我们所有人都在产生数据，同时我们所有人也在消费数据', correct: true },
      { text: '一些公司在产生数据，一些公司在消费数据', correct: false },
      { text: '我们中的一些人在产生数据，我们中的一些人在消费数据', correct: false }
    ]
  },
  {
    type: 'single',
    text: '关于大数据术语，哪个描述不合适？',
    options: [
      { text: '可以分析大数据以获得更好的决策和战略业务举措的见解', correct: false },
      { text: '只是规模大', correct: true },
      { text: '包括结构化和非结构化数据', correct: false },
      { text: '难以管理的数据量', correct: false }
    ]
  },
  {
    type: 'single',
    text: '关于数据生成阶段，哪个顺序是正确的？',
    options: [
      { text: '运营与业务系统、感知阶段、用户生成内容', correct: false },
      { text: '运营与业务系统, 用户生成内容, 感知阶段', correct: true },
      { text: '感知阶段, 运营与业务系统, 用户生成内容', correct: false },
      { text: '感知阶段, 用户生成内容, 运营与业务系统', correct: false }
    ]
  },
  {
    type: 'single',
    text: '以下哪个阶段是大数据的主要原因？',
    options: [
      { text: '运营与业务系统', correct: false },
      { text: '用户生成内容', correct: true },
      { text: '感知阶段', correct: false },
      { text: '社交媒体', correct: false }
    ]
  },
  {
    type: 'single',
    text: '据 Gartner 称，估计有 20% 的组织数据是 ( ) 数据, 其他多数是 ( ) 数据。',
    options: [
      { text: '结构化, 非结构化', correct: true },
      { text: '非结构, 结构化', correct: false },
      { text: '结构化, 半结构化', correct: false },
      { text: '非结构, 半结构化', correct: false }
    ]
  },
  {
    type: 'single',
    text: '关于结构化数据，与非结构化数据相比，哪个描述不对？',
    options: [
      { text: '它通常采用行和列的表格形式', correct: false },
      { text: '它以预定义的格式组织数据', correct: false },
      { text: '易于加工', correct: false },
      { text: '需要更多的存储空间', correct: true }
    ]
  },
  {
    type: 'single',
    text: '关于非结构化数据，与结构化数据相比，哪个描述不对？',
    options: [
      { text: '不能显示在行、列和关系数据库中', correct: false },
      { text: '它们通常是图像、音频、视频、文字处理文件、电子邮件、电子表格', correct: false },
      { text: '它们需要更多存储空间，因为它们数量庞大且组织不当', correct: false },
      { text: '可以轻松地使用传统方式用遗留解决方案管理和保护', correct: true }
    ]
  },
  {
    type: 'single',
    text: '对比数据库和大数据，哪个先有schema，再根据schema组织数据？',
    options: [
      { text: '数据库', correct: true },
      { text: '数据库和大数据', correct: false },
      { text: '大数据', correct: false },
      { text: '数据库和大数据都不是', correct: false }
    ]
  },
  {
    type: 'single',
    text: '数据规模递增的正确顺序是',
    options: [
      { text: 'KB MB GB PB TB EB', correct: false },
      { text: 'KB MB GB TB PB EB', correct: true },
      { text: 'KB MB TB GB PB EB', correct: false },
      { text: 'KB MB GB TB EB PB', correct: false }
    ]
  },
  {
    type: 'judge',
    text: '我们可以找到一种工具来处理大数据的所有数据管理问题。',
    options: [
      { text: '正确', correct: false },
      { text: '错误', correct: true }
    ]
  },
  {
    type: 'judge',
    text: '我们可以找到一种工具来处理数据库的所有数据管理问题。',
    options: [
      { text: '正确', correct: true },
      { text: '错误', correct: false }
    ]
  },
  {
    type: 'single',
    text: '哪个关于 Jim Gray的描述不能确定？',
    options: [
      { text: '关系型数据库创始人', correct: false },
      { text: '航海运动爱好者', correct: false },
      { text: '将科学研究分为四种范式', correct: false },
      { text: '大数据科学家', correct: true }
    ]
  },
  {
    type: 'single',
    text: '四个范式的正确时间顺序是？',
    options: [
      { text: '实证-理论-计算-数据探索', correct: true },
      { text: '理论-实证-计算-数据探索', correct: false },
      { text: '实证-计算-理论-数据探索', correct: false },
      { text: '实证-理论-数据探索-计算', correct: false }
    ]
  },
  {
    type: 'single',
    text: '在大数据的特征当中，哪一个是最重要的特征？',
    options: [
      { text: '规模 & 速度', correct: false },
      { text: '多样性', correct: false },
      { text: '真实性', correct: false },
      { text: '价值', correct: true }
    ]
  },
  {
    type: 'single',
    text: '下面哪一个大数据的特征最好的描述了 Data at Rest？',
    options: [
      { text: '规模', correct: true },
      { text: '速度', correct: false },
      { text: '真实性', correct: false },
      { text: '价值', correct: false }
    ]
  },
  {
    type: 'single',
    text: '下面哪一个大数据的特征最好的描述了Data in Motion？',
    options: [
      { text: '规模', correct: false },
      { text: '多样性', correct: false },
      { text: '真实性', correct: false },
      { text: '速度', correct: true }
    ]
  },
  {
    type: 'single',
    text: '下面哪一个大数据的特征最好的描述了 Data in Many Forms？',
    options: [
      { text: '规模', correct: false },
      { text: '多样性', correct: true },
      { text: '真实性', correct: false },
      { text: '速度', correct: false }
    ]
  },
  {
    type: 'single',
    text: '下面哪一个大数据的特征最好的描述了Data in Doubt (这意味着由于数据不一致和不完整、歧义、延迟、欺骗、模型近似而导致的不确定性)？',
    options: [
      { text: '规模', correct: false },
      { text: '多样性', correct: false },
      { text: '真实性', correct: true },
      { text: '速度', correct: false }
    ]
  },
  {
    type: 'single',
    text: '下面哪一个大数据的特征最好的描述了“沙中淘金”？',
    options: [
      { text: '价值', correct: true },
      { text: '多样性', correct: false },
      { text: '真实性', correct: false },
      { text: '速度', correct: false }
    ]
  },
  {
    type: 'single',
    text: '正确的大数据生命周期是？',
    options: [
      { text: '数据治理, 数据采集, 数据存储和数据分析', correct: false },
      { text: '数据采集, 数据治理, 数据存储和数据分析', correct: false },
      { text: '数据采集, 数据存储, 数据治理和数据分析', correct: false },
      { text: '数据采集, 数据存储, 数据分析和数据治理', correct: true }
    ]
  },
  {
    type: 'single',
    text: '提取信息时，支持制定决策的风险降低顺序是？',
    options: [
      { text: '数据, 信息, 智慧, 知识', correct: false },
      { text: '信息, 数据, 知识, 智慧', correct: false },
      { text: '数据, 信息, 知识, 智慧', correct: true },
      { text: '信息, 数据, 智慧, 知识', correct: false }
    ]
  },
  {
    type: 'single',
    text: '以下哪一个是关于个别事实、数字、信号、测量？',
    options: [
      { text: '数据', correct: true },
      { text: '信息', correct: false },
      { text: '智慧', correct: false },
      { text: '知识', correct: false }
    ]
  },
  {
    type: 'single',
    text: '以下哪一个是关于有组织的，结构化的分类的，有用的,凝练的，计算过的数据？',
    options: [
      { text: '数据', correct: false },
      { text: '信息', correct: true },
      { text: '智慧', correct: false },
      { text: '知识', correct: false }
    ]
  },
  {
    type: 'single',
    text: '以下哪一个是关于想法、学习、符号、概念、综合、比较、思考、讨论？',
    options: [
      { text: '数据', correct: false },
      { text: '信息', correct: false },
      { text: '智慧', correct: false },
      { text: '知识', correct: true }
    ]
  },
  {
    type: 'single',
    text: '以下哪一项是关于理解、整合、应用、反思、可操作、积累、原则、模式、决策过程？',
    options: [
      { text: '数据', correct: false },
      { text: '信息', correct: false },
      { text: '智慧', correct: true },
      { text: '知识', correct: false }
    ]
  },
  {
    type: 'single',
    text: '利用数据的历史技术发展顺序是\n1) (  ) 可以对历史数据进行报告和人工分析\n2) (  ) 可以分析当前数据以改善业务交易\n3) (  ) 实时分析处理以做出实时决策并改进实时业务响应',
    options: [
      { text: 'OLAP: 在线分析处理; OLTP: 在线交易处理; RTAP: 实时分析处理', correct: false },
      { text: 'OLTP: 在线交易处理; OLAP: 在线分析处理; RTAP: 实时分析处理', correct: true },
      { text: 'OLAP: 在线分析处理; RTAP: 实时分析处理; OLTP: 在线交易处理', correct: false },
      { text: 'OLTP: 在线交易处理; RTAP: 实时分析处理; OLAP: 在线分析处理', correct: false }
    ]
  },
  {
    type: 'single',
    text: '当数据量越来越大时，任何单一的传统高性能服务器都无法满足需求，需要更多的服务器. 这叫做 ( ) 扩展',
    options: [
      { text: '垂直', correct: false },
      { text: '水平', correct: true },
      { text: '集中式', correct: false },
      { text: '分布式', correct: false }
    ]
  },
  {
    type: 'single',
    text: '分布式计算的思想是使用 ( ) 来取得  ( )',
    options: [
      { text: '冗余性, 可靠性', correct: true },
      { text: '可靠性, 冗余性', correct: false },
      { text: '冗余性, 性能', correct: false },
      { text: '可靠性, 性能', correct: false }
    ]
  },
  {
    type: 'single',
    text: '大数据的两个主要的组件是( ) 和 ( )',
    options: [
      { text: '分布式存储, 分布式处理', correct: true },
      { text: '分布式采集, 分布式处理', correct: false },
      { text: '分布式采集, 分布式存储', correct: false },
      { text: '分布式采集, 分布式应用', correct: false }
    ]
  },
  {
    type: 'single',
    text: '在大数据通用架构中，从下到上，大数据计算系统的三个基本层是( )',
    options: [
      { text: '数据处理系统; 数据存储系统; 数据应用系统', correct: false },
      { text: '数据存储系统; 数据处理系统; 数据应用系统', correct: true },
      { text: '数据采集系统; 数据处理系统; 数据存储系统', correct: false },
      { text: '数据存储系统; 数据处理系统; 数据可视化系统', correct: false }
    ]
  },
  {
    type: 'single',
    text: '在大数据通用架构中，数据存储系统分为四个部分，哪一个最能描述数据存储系统的四个部分？',
    options: [
      { text: '数据采集, 数据建模, 数据存储（分布式文件系统和分布式数据库）, 统一数据访问接口', correct: true },
      { text: '数据采集, 数据预处理, 数据存储（分布式文件系统和分布式数据库）, 统一数据访问接口', correct: false },
      { text: '数据预处理, 数据建模, 数据存储（分布式文件系统和分布式数据库）, 统一数据访问接口', correct: false },
      { text: '数据预处理, 数据建模, 分布式文件系统，分布式数据库', correct: false }
    ]
  },
  {
    type: 'single',
    text: '在大数据通用架构中，数据处理系统分为三个部分，哪一个最恰当地描述了它们？',
    options: [
      { text: '数据存储, 数据处理算法, 计算引擎和计算平台', correct: false },
      { text: '数据存储, 计算模型, 计算引擎和计算平台', correct: false },
      { text: '数据处理算法, 计算模型, 计算引擎和计算平台', correct: true },
      { text: '数据处理算法, 计算引擎, 计算平台', correct: false }
    ]
  },
  {
    type: 'single',
    text: '在大数据通用架构中，UDAI-统一数据访问接口不能解决的问题是？',
    options: [
      { text: '跨平台问题', correct: false },
      { text: '异构问题 ', correct: false },
      { text: '分布式计算问题', correct: false },
      { text: '数据不一致问题', correct: true }
    ]
  },
  {
    type: 'judge',
    text: 'Hadoop是唯一的大数据架构。',
    options: [
      { text: '正确', correct: false },
      { text: '错误', correct: true }
    ]
  }
])

// 用来记录用户选择的答案：索引或null未选
const selectedAnswers = ref<(number | null)[]>(Array(questions.value.length).fill(null))

// 提交状态
const isSubmitting = ref(false)
const submitMessage = ref('')
const submitSuccess = ref(false)

// 选择答案
function selectAnswer(qIndex: number, optionIndex: number) {
  selectedAnswers.value[qIndex] = optionIndex
  updateSubmitData()
}

// 判断是否所有题目都已作答
const allAnswered = computed(() => selectedAnswers.value.every(ans => ans !== null))

// 计算得分（每题选中一个正确答案计1分，单选题只取一个选项，判断题同理）
const score = computed(() =>
  questions.value.reduce((sum, question, i) => {
    const selectedIdx = selectedAnswers.value[i]
    if (selectedIdx === null) return sum

    if(question.type === 'single' || question.type === 'judge') {
      if (question.options[selectedIdx].correct) return sum + 1
    }
    return sum
  }, 0)
)

function updateSubmitData() {
  submitData.value = {
    student_id: studentId.value, // 修正：使用 .value
    test_id: testId.value,       // 修正：使用 .value
    score: score.value,
    total_questions: questions.value.length,
    correct_answers: score.value,
    percentage: (score.value / questions.value.length * 100).toFixed(2),
    answers: selectedAnswers.value.map((answer, index) => ({
      question_id: index,
      question_text: questions.value[index].text,
      selected_answer: answer,
      correct: answer !== null ? questions.value[index].options[answer]?.correct : false
    })),
    submitted_at: new Date().toISOString()
  }
}

// 提交分数到后端
async function saveScore() {
  console.log('准备提交')
  if (isSubmitting.value) return
  
  isSubmitting.value = true
  submitMessage.value = ''
  submitSuccess.value = false

  try {
    updateSubmitData()

    console.log('🎯 准备提交数据:', JSON.stringify(submitData.value, null, 2))
    console.log('📡 请求URL:', `${API_BASE}/api/test/scores/`)
    console.log('🔧 请求方法: POST')

    const response = await axios.post(`${API_BASE}/test/scores/`, submitData.value, {
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      }
    })
    
    console.log('✅ 服务器响应:', response.data)

    if (response.data.success) {
      submitSuccess.value = true
      submitMessage.value = `成绩提交成功！得分：${score.value}/${questions.value.length}`
    } else {
      throw new Error(response.data.error || '提交失败')
    }
  } catch (error: any) {
    console.error('提交成绩失败:', error)
    submitSuccess.value = false
    submitMessage.value = `提交失败：${error.response?.data?.error || error.message || '网络错误'}`
  } finally {
    isSubmitting.value = false
  }
}

// 自动提交功能（可选）：当所有题目回答完成后自动提交
watch(allAnswered, (newVal) => {
  if (newVal) {
    // 可以选择自动提交，或者让用户手动点击提交
    saveScore() // 取消注释启用自动提交
  }
})

// 重置测试
function resetTest() {
  selectedAnswers.value = Array(questions.value.length).fill(null)
}
</script>

<style scoped>
.result {
  background-color: #e8f5e9;
  color: #2e7d32;
  border: 2px solid #81c784;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  padding: 20px;
  max-width: 600px;
  margin: 50px auto;
  text-align: center;
}

h2 {
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 20px;
}

h3 {
  font-size: 18px;
  margin-bottom: 10px;
  text-align: left;
}

.question-block {
  margin-bottom: 25px;
  text-align: left;
}

.options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.option-btn {
  flex: 1 1 45%;
  padding: 10px 15px;
  font-size: 16px;
  border: 2px solid #81c784;
  border-radius: 8px;
  background-color: #f1f8f4;
  color: #2e7d32;
  cursor: pointer;
  transition: background-color 0.3s ease;
  user-select: none;
}

.option-btn:hover:not(:disabled) {
  background-color: #c8e6c9;
}

.option-btn.correct {
  background-color: #4caf50;
  color: white;
  border-color: #388e3c;
}

.option-btn.wrong {
  background-color: #e57373;
  color: white;
  border-color: #d32f2f;
}

.option-btn:disabled {
  cursor: default;
  opacity: 0.7;
}

.score {
  margin-top: 30px;
}

.score button {
  margin-top: 15px;
  padding: 8px 16px;
  background-color: #81c784;
  border: none;
  border-radius: 6px;
  color: white;
  font-weight: bold;
  cursor: pointer;
}

.score button:hover {
  background-color: #66bb6a;
}
</style>
