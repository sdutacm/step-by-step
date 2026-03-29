<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import Sortable from "sortablejs";
import {
  ElCard,
  ElButton,
  ElTable,
  ElTableColumn,
  ElTag,
  ElEmpty,
  ElMessage,
  ElMessageBox,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElSelect,
  ElOption,
  ElPagination,
  ElSkeleton,
} from "element-plus";

import {
  getStep,
  updateStep,
  addProblemsToStep,
  removeProblemFromStep,
  reorderStepProblems,
  getProblems,
  type Step,
  type StepProblemItem,
  type ProblemSimple,
} from "../api/step";
import { getCurrentUser } from "../api/auth";
import { useUserStore } from "../stores/user";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const step = ref<Step | null>(null);
const isLoading = ref(false);
const isEditing = ref(false);
const isAddingProblems = ref(false);
const isSubmitting = ref(false);
const problemsLoading = ref(false);
const availableProblems = ref<ProblemSimple[]>([]);
const selectedProblems = ref<StepProblemItem[]>([]);
const problemsPagination = ref({ page: 1, page_size: 20, total: 0 });
const problemsSearch = ref({ title: "", source: "" });
const currentUserId = ref<number | null>(null);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const problemsTableRef = ref<any>(null);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let sortableInstance: any = null;

const stepId = computed(() => Number(route.params.id));

const editForm = ref({
  title: "",
  description: "",
});

async function fetchCurrentUser() {
  try {
    const user = await getCurrentUser();
    currentUserId.value = user.id;
  } catch {
    currentUserId.value = null;
  }
}

function isCreator() {
  return step.value?.creator_id === currentUserId.value;
}

function formatTime(time: string) {
  const d = new Date(time);
  const pad = (n: string): string => n.padStart(2, "0");
  const year = d.getFullYear().toString();
  const month = pad((d.getMonth() + 1).toString());
  const day = pad(d.getDate().toString());
  const hour = pad(d.getHours().toString());
  const minute = pad(d.getMinutes().toString());
  const second = pad(d.getSeconds().toString());
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

function getProblemUrl(source: string, problemId: string): string {
  switch (source.toLowerCase()) {
    case "vj":
      return `https://vjudge.net/problem/${problemId}`;
    case "sdut":
      return `https://oj.sdutacm.cn/onlinejudge3/problems/${problemId}`;
    default:
      return "#";
  }
}

async function fetchStep() {
  isLoading.value = true;
  try {
    step.value = await getStep(stepId.value);
    editForm.value.title = step.value.title;
    editForm.value.description = step.value.description ?? "";
  } catch {
    ElMessage.error("获取训练计划详情失败");
    void router.push("/steps");
  } finally {
    isLoading.value = false;
  }
}

async function fetchAvailableProblems() {
  problemsLoading.value = true;
  try {
    const data = await getProblems(
      problemsPagination.value.page,
      problemsPagination.value.page_size,
      problemsSearch.value.title || undefined,
      problemsSearch.value.source || undefined
    );
    availableProblems.value = data.items.filter(
      p => !step.value?.problems.some(sp => sp.id === p.id)
    );
    problemsPagination.value.total = data.total;
  } catch {
    ElMessage.error("获取题目列表失败");
  } finally {
    problemsLoading.value = false;
  }
}

async function handleProblemsSearch() {
  problemsPagination.value.page = 1;
  await fetchAvailableProblems();
}

async function handleProblemsPageChange(page: number) {
  problemsPagination.value.page = page;
  await fetchAvailableProblems();
}

async function handleUpdate() {
  if (!editForm.value.title.trim()) {
    ElMessage.error("请输入标题");
    return;
  }
  isSubmitting.value = true;
  try {
    await updateStep(stepId.value, {
      title: editForm.value.title,
      description: editForm.value.description || undefined,
    });
    ElMessage.success("更新成功");
    isEditing.value = false;
    await fetchStep();
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || "更新失败");
  } finally {
    isSubmitting.value = false;
  }
}

async function openAddProblemsDialog() {
  problemsSearch.value = { title: "", source: "" };
  problemsPagination.value = { page: 1, page_size: 20, total: 0 };
  selectedProblems.value = [];
  await fetchAvailableProblems();
  isAddingProblems.value = true;
}

async function handleAddProblems() {
  if (selectedProblems.value.length === 0) {
    ElMessage.error("请选择至少一道题目");
    return;
  }
  isSubmitting.value = true;
  try {
    await addProblemsToStep(stepId.value, { problems: selectedProblems.value });
    ElMessage.success("添加成功");
    isAddingProblems.value = false;
    await fetchStep();
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || "添加失败");
  } finally {
    isSubmitting.value = false;
  }
}

async function handleRemoveProblem(problemId: number, title: string) {
  try {
    await ElMessageBox.confirm(`确定要从训练计划中移除「${title}」吗？`, "移除确认", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await removeProblemFromStep(stepId.value, problemId);
    ElMessage.success("移除成功");
    await fetchStep();
  } catch (e: unknown) {
    if ((e as Error).message !== "cancel") {
      ElMessage.error((e as Error).message || "移除失败");
    }
  }
}

onMounted(async () => {
  await fetchCurrentUser();
  void fetchStep();
});

function initTableDrag() {
  if (!isCreator()) return;

  const table = problemsTableRef.value?.$el;
  if (!table) {
    setTimeout(initTableDrag, 100);
    return;
  }

  const tbody = table.querySelector(".el-table__body-wrapper tbody");
  if (!tbody) {
    return;
  }
  if (sortableInstance) {
    sortableInstance.destroy();
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  sortableInstance = (Sortable as any).create(tbody as HTMLElement, {
    animation: 150,
    handle: ".el-table__row",

    onEnd: async ({
      oldIndex,
      newIndex,
    }: {
      oldIndex: number | undefined;
      newIndex: number | undefined;
    }) => {
      if (
        oldIndex === undefined ||
        newIndex === undefined ||
        !step.value ||
        oldIndex === newIndex
      ) {
        return;
      }
      const problems = [...step.value.problems];
      const [removed] = problems.splice(oldIndex, 1);
      problems.splice(newIndex, 0, removed);
      step.value.problems = problems;
      const problemIds = problems.map(p => p.id);
      try {
        await reorderStepProblems(stepId.value, problemIds);
        ElMessage.success("排序已保存");
      } catch (e: unknown) {
        ElMessage.error((e as Error).message || "保存排序失败");
        await fetchStep();
      }
    },
  });
}

watch(
  () => userStore.user,
  async (newUser, oldUser) => {
    if (!oldUser && newUser) {
      await fetchCurrentUser();
    }
  }
);

watch(
  () => step.value?.problems.length,
  newLen => {
    if (newLen && newLen > 0) {
      setTimeout(initTableDrag, 100);
    }
  }
);
</script>

<template>
  <div
    style="
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 20px;
    "
  >
    <el-card v-if="!isLoading && step">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>{{ step.title }}</span>
          <div style="display: flex; gap: 8px">
            <el-button @click="router.push('/steps')">返回列表</el-button>
            <el-button v-if="isCreator() && !isEditing" type="primary" @click="isEditing = true">
              编辑信息
            </el-button>
          </div>
        </div>
      </template>

      <template v-if="isEditing">
        <el-form label-position="top" :model="editForm">
          <el-form-item label="标题" required>
            <el-input
              v-model="editForm.title"
              placeholder="请输入标题"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="描述">
            <el-input
              v-model="editForm.description"
              type="textarea"
              placeholder="请输入描述"
              :rows="3"
              maxlength="1000"
              show-word-limit
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="isSubmitting" @click="handleUpdate">保存</el-button>
            <el-button @click="isEditing = false">取消</el-button>
          </el-form-item>
        </el-form>
      </template>

      <template v-else>
        <div style="display: flex; flex-direction: column; gap: 16px">
          <div>
            <strong>描述：</strong>
            <span>{{ step.description || "暂无描述" }}</span>
          </div>
          <div>
            <strong>创建者：</strong>
            <span>{{ step.creator_username }}</span>
          </div>
          <div>
            <strong>创建时间：</strong>
            <span>{{ formatTime(step.created_at) }}</span>
          </div>
          <div>
            <strong>更新时间：</strong>
            <span>{{ formatTime(step.updated_at) }}</span>
          </div>
        </div>
      </template>
    </el-card>
    <el-card v-else>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>训练计划详情</span>
        </div>
      </template>
      <el-skeleton :rows="4" animated />
    </el-card>

    <el-card v-if="!isLoading && step">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>题目列表 ({{ step.problem_count }})</span>
          <el-button v-if="isCreator()" type="primary" @click="openAddProblemsDialog"
            >添加题目</el-button
          >
        </div>
      </template>
      <el-table
        v-if="step.problems.length"
        ref="problemsTableRef"
        :data="step.problems"
        style="width: 100%"
        row-key="id"
      >
        <el-table-column prop="order" label="顺序" width="80" align="center" />
        <el-table-column prop="problem_id" label="题目ID" width="120" />
        <el-table-column prop="source" label="平台" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.source.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200">
          <template #default="{ row }">
            <a
              :href="getProblemUrl(row.source, row.problem_id)"
              target="_blank"
              rel="noopener noreferrer"
              style="color: #409eff; text-decoration: none"
            >
              {{ row.title }}
            </a>
          </template>
        </el-table-column>
        <el-table-column v-if="isCreator()" label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="handleRemoveProblem(row.id, row.title)">
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无题目" />
    </el-card>
  </div>

  <el-dialog v-model="isAddingProblems" title="添加题目" width="800px">
    <div style="margin-bottom: 16px; display: flex; gap: 12px">
      <el-input
        v-model="problemsSearch.title"
        placeholder="搜索题目标题"
        style="width: 300px"
        clearable
        @keyup.enter="handleProblemsSearch"
      />
      <el-select
        v-model="problemsSearch.source"
        placeholder="选择平台"
        style="width: 150px"
        clearable
        @change="handleProblemsSearch"
      >
        <el-option label="VJ" value="vj" />
        <el-option label="SDUT" value="sdut" />
      </el-select>
      <el-button type="primary" @click="handleProblemsSearch">搜索</el-button>
    </div>
    <el-table
      v-loading="problemsLoading"
      :data="availableProblems"
      max-height="400"
      @selection-change="
        (rows: ProblemSimple[]) =>
          (selectedProblems = rows.map(p => ({ problem_id: p.id, order: 0 })))
      "
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="problem_id" label="题目ID" width="100" />
      <el-table-column prop="source" label="平台" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.source.toUpperCase() }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" />
    </el-table>
    <div style="margin-top: 16px; display: flex; justify-content: flex-end">
      <el-pagination
        v-model:current-page="problemsPagination.page"
        :page-size="problemsPagination.page_size"
        :total="problemsPagination.total"
        layout="prev, pager, next, jumper"
        @current-change="handleProblemsPageChange"
      />
    </div>
    <template #footer>
      <el-button @click="isAddingProblems = false">取消</el-button>
      <el-button type="primary" :loading="isSubmitting" @click="handleAddProblems">
        添加 ({{ selectedProblems.length }})
      </el-button>
    </template>
  </el-dialog>
</template>
