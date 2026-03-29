<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElAvatar,
  ElMessage,
  ElMessageBox,
  ElButton,
  ElInput,
  ElDialog,
  ElForm,
  ElFormItem,
  ElSelect,
  ElOption,
  ElTable,
  ElTableColumn,
  ElTag,
} from "element-plus";
import {
  getCurrentUser,
  updateCurrentUser,
  getSources,
  bindSource,
  unbindSource,
  claimGhostAccount,
  getGhostAccounts,
  type User,
  type Source,
  type GhostAccount,
} from "../api/auth";
import { useUserStore } from "../stores/user";

const userStore = useUserStore();
const user = ref<User | null>(null);
const editDialogVisible = ref(false);
const bindDialogVisible = ref(false);
const claimDialogVisible = ref(false);
const isBinding = ref(false);
const isClaiming = ref(false);
const sources = ref<Source[]>([]);
const ghostAccounts = ref<GhostAccount[]>([]);
const isLoadingGhosts = ref(false);

const editForm = ref({
  nickname: "",
  avatar_url: "",
});

const bindForm = ref({
  source: "",
  username: "",
  password: "",
});

const claimForm = ref({
  source: "",
  username: "",
  password: "",
});

async function refreshUser() {
  try {
    user.value = await getCurrentUser();
    userStore.setUser(user.value);
  } catch {
    ElMessage.error("获取用户信息失败");
  }
}

async function refreshSources() {
  try {
    sources.value = await getSources();
  } catch {
    ElMessage.error("获取平台列表失败");
  }
}

function openEditDialog() {
  editForm.value = {
    nickname: user.value?.nickname ?? "",
    avatar_url: user.value?.avatar_url ?? "",
  };
  editDialogVisible.value = true;
}

async function handleUpdate() {
  try {
    await updateCurrentUser({
      nickname: editForm.value.nickname || undefined,
      avatar_url: editForm.value.avatar_url || undefined,
    });
    ElMessage.success("更新成功");
    editDialogVisible.value = false;
    await refreshUser();
  } catch {
    ElMessage.error("更新失败");
  }
}

function openBindDialog() {
  bindForm.value = {
    source: "",
    username: "",
    password: "",
  };
  bindDialogVisible.value = true;
}

async function handleBind() {
  if (!bindForm.value.source || !bindForm.value.username || !bindForm.value.password) {
    ElMessage.error("请填写所有字段");
    return;
  }
  isBinding.value = true;
  try {
    await bindSource({
      source: bindForm.value.source,
      username: bindForm.value.username,
      password: bindForm.value.password,
    });
    ElMessage.success("绑定成功");
    bindDialogVisible.value = false;
    await refreshUser();
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || "绑定失败");
  } finally {
    isBinding.value = false;
  }
}

async function handleUnbind(bindingId: number, source: string, username: string) {
  try {
    await ElMessageBox.confirm(
      `确定要解绑平台 ${source.toUpperCase()} (用户名: ${username}) 吗？`,
      "解绑确认",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }
    );
    await unbindSource(bindingId);
    ElMessage.success("解绑成功");
    await refreshUser();
  } catch (e: unknown) {
    if ((e as Error).message !== "cancel") {
      ElMessage.error((e as Error).message || "解绑失败");
    }
  }
}

async function fetchGhostAccounts() {
  isLoadingGhosts.value = true;
  try {
    const data = await getGhostAccounts();
    ghostAccounts.value = data.ghosts;
  } catch {
    ElMessage.error("获取幽灵账号失败");
  } finally {
    isLoadingGhosts.value = false;
  }
}

function openClaimDialog() {
  claimForm.value = {
    source: "",
    username: "",
    password: "",
  };
  claimDialogVisible.value = true;
  void fetchGhostAccounts();
}

async function handleClaimGhost() {
  if (!claimForm.value.source || !claimForm.value.username || !claimForm.value.password) {
    ElMessage.error("请填写所有字段");
    return;
  }
  isClaiming.value = true;
  try {
    const result = await claimGhostAccount({
      source: claimForm.value.source,
      username: claimForm.value.username,
      password: claimForm.value.password,
    });
    ElMessage.success(result.message);
    claimDialogVisible.value = false;
    await refreshUser();
    await fetchGhostAccounts();
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || "认领失败");
  } finally {
    isClaiming.value = false;
  }
}

onMounted(async () => {
  await Promise.all([refreshUser(), refreshSources()]);
});
</script>

<template>
  <div
    style="
      padding: 20px;
      max-width: 800px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 20px;
    "
  >
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <div style="display: flex; align-items: center; gap: 16px">
            <el-avatar v-if="user?.avatar_url" :size="64" :src="user.avatar_url" />
            <el-avatar v-else :size="64">
              {{ user?.username?.charAt(0).toUpperCase() }}
            </el-avatar>
            <div>
              <div style="display: flex; align-items: center; gap: 8px">
                <h2 style="margin: 0">{{ user?.nickname || user?.username }}</h2>
                <el-tag v-if="user?.is_super_admin" type="danger" size="small">超级管理员</el-tag>
              </div>
              <span style="color: #999">个人信息</span>
            </div>
          </div>
          <el-button @click="openEditDialog">编辑资料</el-button>
        </div>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ user?.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ user?.nickname || "未设置" }}</el-descriptions-item>
        <el-descriptions-item label="头像">
          <el-image
            v-if="user?.avatar_url"
            style="width: 80px; height: 80px"
            :src="user.avatar_url"
            fit="cover"
          />
          <span v-else>未设置</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>已绑定平台</span>
          <el-button type="primary" size="small" @click="openBindDialog">绑定新平台</el-button>
        </div>
      </template>
      <el-table :data="user?.source_users || []" style="width: 100%">
        <el-table-column prop="source" label="平台" width="120">
          <template #default="{ row }">
            <el-tag>{{ row.source.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              @click="handleUnbind(row.id, row.source, row.username)"
            >
              解绑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!user?.source_users?.length" description="暂未绑定任何平台" />
    </el-card>

    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>幽灵账号</span>
          <el-button type="warning" size="small" @click="openClaimDialog">认领幽灵账号</el-button>
        </div>
      </template>
      <el-table v-loading="isLoadingGhosts" :data="ghostAccounts" style="width: 100%">
        <el-table-column prop="source" label="平台" width="120">
          <template #default="{ row }">
            <el-tag>{{ row.source.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="nickname" label="昵称">
          <template #default="{ row }">
            {{ row.nickname || "-" }}
          </template>
        </el-table-column>
        <el-table-column prop="bound" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.bound" type="success">已认领</el-tag>
            <el-tag v-else type="warning">未认领</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty
        v-if="!isLoadingGhosts && !ghostAccounts.length"
        description="暂无非本人的幽灵账号"
      />
    </el-card>
  </div>

  <el-dialog v-model="editDialogVisible" title="编辑资料" width="400px">
    <el-form label-position="top" :model="editForm">
      <el-form-item label="昵称">
        <el-input v-model="editForm.nickname" placeholder="请输入昵称" />
      </el-form-item>
      <el-form-item label="头像URL">
        <el-input v-model="editForm.avatar_url" placeholder="请输入头像URL" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="editDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleUpdate">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="bindDialogVisible" title="绑定平台" width="400px">
    <el-form label-position="top" :model="bindForm">
      <el-form-item label="平台">
        <el-select v-model="bindForm.source" placeholder="请选择平台" style="width: 100%">
          <el-option
            v-for="s in sources"
            :key="s.source"
            :label="s.source.toUpperCase()"
            :value="s.source"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="用户名">
        <el-input v-model="bindForm.username" placeholder="请输入平台用户名" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input
          v-model="bindForm.password"
          type="password"
          placeholder="请输入平台密码"
          show-password
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="bindDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="isBinding" @click="handleBind">绑定</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="claimDialogVisible" title="认领幽灵账号" width="500px">
    <el-alert title="认领说明" type="info" :closable="false" style="margin-bottom: 16px">
      <template #default>
        认领幽灵账号需要验证您在OJ平台的密码。验证成功后，该OJ账号将绑定到您的账户。
        幽灵账号是指由组织管理员批量导入但未被任何真实用户认领的OJ账号。
      </template>
    </el-alert>
    <el-form label-position="top" :model="claimForm">
      <el-form-item label="平台">
        <el-select v-model="claimForm.source" placeholder="请选择平台" style="width: 100%">
          <el-option
            v-for="s in sources"
            :key="s.source"
            :label="s.source.toUpperCase()"
            :value="s.source"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="用户名">
        <el-input v-model="claimForm.username" placeholder="请输入OJ平台用户名" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input
          v-model="claimForm.password"
          type="password"
          placeholder="请输入OJ平台密码"
          show-password
        />
      </el-form-item>
    </el-form>
    <el-divider />
    <div v-if="ghostAccounts.length">
      <div style="font-weight: bold; margin-bottom: 8px">可认领的幽灵账号：</div>
      <el-table :data="ghostAccounts.filter(g => !g.bound)" size="small" max-height="200">
        <el-table-column prop="source" label="平台" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.source.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="nickname" label="昵称">
          <template #default="{ row }">
            {{ row.nickname || "-" }}
          </template>
        </el-table-column>
      </el-table>
    </div>
    <template #footer>
      <el-button @click="claimDialogVisible = false">取消</el-button>
      <el-button type="warning" :loading="isClaiming" @click="handleClaimGhost">认领</el-button>
    </template>
  </el-dialog>
</template>
