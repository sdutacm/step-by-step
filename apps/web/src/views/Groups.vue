<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import {
  ElCard,
  ElTable,
  ElTableColumn,
  ElPagination,
  ElButton,
  ElEmpty,
  ElMessage,
  ElMessageBox,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
} from "element-plus";
import {
  getGroups,
  deleteGroup,
  createGroup,
  type GroupListItem,
  type GroupListResponse,
  type CreateGroupData,
} from "../api/group";
import { useUserStore } from "../stores/user";

const router = useRouter();
const userStore = useUserStore();

const groups = ref<GroupListItem[]>([]);
const isLoading = ref(false);
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
});

const createDialogVisible = ref(false);
const createForm = ref<CreateGroupData>({
  name: "",
  description: "",
});
const isCreating = ref(false);

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

function isSuperAdmin() {
  return userStore.isSuperAdmin;
}

async function fetchGroups() {
  isLoading.value = true;
  try {
    const data: GroupListResponse = await getGroups(
      pagination.value.page,
      pagination.value.page_size
    );
    groups.value = data.items;
    pagination.value.total = data.total;
  } catch {
    ElMessage.error("获取组织列表失败");
  } finally {
    isLoading.value = false;
  }
}

function handlePageChange(page: number) {
  pagination.value.page = page;
  void fetchGroups();
}

function handleSizeChange(size: number) {
  pagination.value.page_size = size;
  pagination.value.page = 1;
  void fetchGroups();
}

function goToGroupDetail(id: number) {
  void router.push(`/groups/${String(id)}`);
}

async function handleCreate() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning("请输入组织名称");
    return;
  }
  isCreating.value = true;
  try {
    await createGroup(createForm.value);
    ElMessage.success("创建成功");
    createDialogVisible.value = false;
    createForm.value = { name: "", description: "" };
    await fetchGroups();
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || "创建失败");
  } finally {
    isCreating.value = false;
  }
}

async function handleDelete(id: number, name: string) {
  try {
    await ElMessageBox.confirm(`确定要删除组织「${name}」吗？`, "删除确认", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await deleteGroup(id);
    ElMessage.success("删除成功");
    await fetchGroups();
  } catch (e: unknown) {
    if ((e as Error).message !== "cancel") {
      ElMessage.error((e as Error).message || "删除失败");
    }
  }
}

onMounted(() => {
  void fetchGroups();
});

watch(
  () => userStore.user,
  () => {
    // userStore.isSuperAdmin will update reactively
  }
);
</script>

<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto">
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>组织</span>
          <el-button v-if="isSuperAdmin()" type="primary" @click="createDialogVisible = true">
            创建组织
          </el-button>
        </div>
      </template>
      <el-table
        v-loading="isLoading"
        :data="groups"
        style="width: 100%"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
        @row-click="(row: GroupListItem) => goToGroupDetail(row.id)"
      >
        <el-table-column prop="name" label="名称" min-width="150">
          <template #default="{ row }">
            <span style="color: #409eff; cursor: pointer">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            {{ row.description || "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="member_count" label="成员数" width="100" align="center" />
        <el-table-column prop="step_count" label="计划数" width="100" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column v-if="isSuperAdmin()" label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click.stop="handleDelete(row.id, row.name)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!isLoading && !groups.length" description="暂无组织" />
      <div style="margin-top: 20px; display: flex; justify-content: flex-end">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="createDialogVisible" title="创建组织" width="500px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="请输入组织名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            placeholder="请输入组织描述（可选）"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="isCreating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>
