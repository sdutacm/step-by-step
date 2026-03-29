<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import {
  ElButton,
  ElTag,
  ElEmpty,
  ElMessage,
  ElLink,
  ElTable,
  ElTableColumn,
  ElDialog,
} from "element-plus";
import {
  getBoard,
  getBoardProgress,
  type Board,
  type BoardProgressResponse,
  type ProblemProgress,
  type SubmissionRecord,
} from "../api/board";
import { getCurrentUser } from "../api/auth";
import { useUserStore } from "../stores/user";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const board = ref<Board | null>(null);
const progress = ref<BoardProgressResponse | null>(null);
const progressLoading = ref(false);
const currentUser = ref<{ id: number } | null>(null);

const boardId = computed(() => Number(route.params.id));

interface TableUser {
  user_id: number;
  username: string;
  nickname: string | null;
}

interface CellData {
  solved: boolean;
  ac_time: string | null;
  failed_time: string | null;
  result: number | null;
  submissions: SubmissionRecord[];
}

const submissionsDialogVisible = ref(false);
const submissionsDialogData = ref<{
  problem: ProblemProgress | null;
  user: TableUser | null;
  submissions: SubmissionRecord[];
}>({
  problem: null,
  user: null,
  submissions: [],
});

const users = computed<TableUser[]>(() => {
  if (!progress.value) return [];
  return progress.value.users.map(u => ({
    user_id: u.user_id,
    username: u.username,
    nickname: u.nickname,
  }));
});

const problems = computed<ProblemProgress[]>(() => {
  if (!progress.value || progress.value.users.length === 0) return [];
  return [...progress.value.users[0].problems].sort((a, b) => a.order - b.order);
});

const cellMap = computed(() => {
  const map = new Map<number, Map<number, CellData>>();
  if (!progress.value) return map;

  for (const user of progress.value.users) {
    const userMap = new Map<number, CellData>();
    for (const problem of user.problems) {
      userMap.set(problem.problem_id, {
        solved: problem.ac_time !== null,
        ac_time: problem.ac_time,
        failed_time: problem.failed_time,
        result: problem.result,
        submissions: problem.submissions,
      });
    }
    map.set(user.user_id, userMap);
  }
  return map;
});

const tableHeight = ref(window.innerHeight - 80);

function updateTableHeight() {
  tableHeight.value = window.innerHeight - 80;
}

function getCellData(problemId: number, userId: number): CellData | null {
  const userMap = cellMap.value.get(userId);
  if (!userMap) return null;
  return userMap.get(problemId) || null;
}

function isWithin7Days(dateStr: string | null): boolean {
  if (!dateStr) return false;
  const date = new Date(dateStr);
  const now = new Date();
  const diffTime = now.getTime() - date.getTime();
  const diffDays = diffTime / (1000 * 60 * 60 * 24);
  return diffDays <= 7;
}

function getCellStyle(problemId: number, userId: number): string {
  const cell = getCellData(problemId, userId);
  if (!cell || cell.result === null) return "";
  const timeToCheck = cell.result === 1 ? cell.ac_time : cell.failed_time;
  const within7Days = isWithin7Days(timeToCheck);
  if (cell.result === 1) {
    return within7Days
      ? "background-color: #67c23a; color: #fff;"
      : "background-color: #e1f3d8; color: #67c23a;";
  } else {
    return within7Days
      ? "background-color: #f56c6c; color: #fff;"
      : "background-color: #fde2e2; color: #f56c6c;";
  }
}

function getCellTimeText(problemId: number, userId: number): string {
  const cell = getCellData(problemId, userId);
  if (!cell || cell.result === null) return "";
  const time = cell.result === 1 ? cell.ac_time : cell.failed_time;
  return formatTime(time || "");
}

function openSubmissionsDialog(problemId: number, userId: number) {
  const problem = problems.value.find(p => p.problem_id === problemId);
  const user = users.value.find(u => u.user_id === userId);
  const cell = getCellData(problemId, userId);

  submissionsDialogData.value = {
    problem: problem || null,
    user: user || null,
    submissions: cell?.submissions || [],
  };
  submissionsDialogVisible.value = true;
}

function formatTime(time: string) {
  const d = new Date(time);
  const pad = (n: number) => n.toString().padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function getResultLabel(result: number | null): string {
  if (result === null) return "未提交";
  const results: Record<number, string> = {
    1: "Accepted",
    2: "Wrong Answer",
    3: "Time Limit Exceeded",
    4: "Memory Limit Exceeded",
    5: "Runtime Error",
    6: "Output Limit Exceeded",
    7: "Compile Error",
    8: "Presentation Error",
    9: "System Error",
    999: "Unknown",
  };
  return results[result] || "Unknown";
}

function getResultType(result: number | null): string {
  if (result === 1) return "success";
  if (result === null) return "info";
  return "danger";
}

function getLanguageLabel(language: number): string {
  const languages: Record<number, string> = {
    1: "C",
    2: "C++",
    3: "Python",
    4: "Java",
    5: "Go",
    6: "Rust",
    7: "JavaScript",
    8: "TypeScript",
    9: "C#",
    10: "Pascal",
    11: "Fortran",
    999: "Unknown",
  };
  return languages[language] || "Unknown";
}

function getProblemUrl(source: string, problemId: string): string {
  if (source === "vj") return `https://vjudge.net/problem/${problemId}`;
  if (source === "sdut") return `https://oj.sdutacm.cn/onlinejudge3/problems/${problemId}`;
  return "#";
}

async function fetchCurrentUser() {
  try {
    const user = await getCurrentUser();
    currentUser.value = user;
    userStore.setUser(user);
  } catch {
    currentUser.value = null;
    userStore.clearUser();
  }
}

async function fetchBoard() {
  try {
    board.value = await getBoard(boardId.value);
  } catch {
    ElMessage.error("获取看板详情失败");
    router.push("/groups");
  }
}

async function fetchProgress() {
  progressLoading.value = true;
  try {
    progress.value = await getBoardProgress(boardId.value);
  } catch {
    ElMessage.error("获取学习进度失败");
  } finally {
    progressLoading.value = false;
  }
}

onMounted(async () => {
  window.addEventListener("resize", updateTableHeight);
  await fetchCurrentUser();
  await Promise.all([fetchBoard(), fetchProgress()]);
});

onUnmounted(() => {
  window.removeEventListener("resize", updateTableHeight);
});
</script>

<template>
  <div v-loading="progressLoading" style="height: 100%">
    <el-table
      v-if="problems.length"
      :data="problems"
      border
      :scrollbar-always-on="true"
      :height="tableHeight"
      class="board-table"
    >
      <el-table-column
        prop="specialty"
        label="专项"
        width="120"
        align="center"
        fixed
        show-overflow-tooltip
      />
      <el-table-column
        prop="topic"
        label="专题"
        width="120"
        align="center"
        fixed
        show-overflow-tooltip
      />
      <el-table-column prop="title" label="题目" width="180" fixed show-overflow-tooltip>
        <template #default="{ row }">
          <el-link
            type="primary"
            :href="getProblemUrl(row.source, row.oj_problem_id)"
            target="_blank"
            >{{ row.title }}</el-link
          >
        </template>
      </el-table-column>
      <el-table-column
        v-for="user in users"
        :key="user.user_id"
        :label="user.nickname ? `${user.username} (${user.nickname})` : user.username"
        width="200"
        align="center"
      >
        <template #default="{ row }">
          <div
            v-if="getCellData(row.problem_id, user.user_id)?.result !== null"
            :style="getCellStyle(row.problem_id, user.user_id)"
            class="cell-bg"
            @click="openSubmissionsDialog(row.problem_id, user.user_id)"
          >
            {{ getCellTimeText(row.problem_id, user.user_id) }}
          </div>
        </template>
      </el-table-column>
    </el-table>
    <div v-else style="padding: 100px 0">
      <el-empty description="暂无数据" />
    </div>

    <el-dialog
      v-model="submissionsDialogVisible"
      :title="`${submissionsDialogData.user?.nickname || submissionsDialogData.user?.username} - ${submissionsDialogData.problem?.title} 提交记录`"
      width="600px"
    >
      <el-table :data="submissionsDialogData.submissions" max-height="400">
        <el-table-column prop="submitted_at" label="提交时间" width="220">
          <template #default="{ row }">
            {{ formatTime(row.submitted_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="result" label="结果" width="150">
          <template #default="{ row }">
            <el-tag :type="getResultType(row.result)" size="small">
              {{ getResultLabel(row.result) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="language" label="语言" width="100">
          <template #default="{ row }">
            {{ getLanguageLabel(row.language) }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<style scoped>
.board-table :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

.board-table :deep(.el-table__body .el-table-cell) {
  position: relative;
}

.cell-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
