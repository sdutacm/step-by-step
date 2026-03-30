<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElCard, ElForm, ElFormItem, ElInput, ElButton, ElMessage } from "element-plus";
import {
  createStep,
  updateStep,
  getStep,
  type CreateStepData,
  type UpdateStepData,
} from "../api/step";

const router = useRouter();
const route = useRoute();

const isEdit = ref(false);
const stepId = ref<number | null>(null);
const isSubmitting = ref(false);

const form = ref({
  title: "",
  description: "",
});

async function handleSubmit() {
  if (!form.value.title.trim()) {
    ElMessage.error("请输入标题");
    return;
  }

  isSubmitting.value = true;
  try {
    if (isEdit.value && stepId.value) {
      const data: UpdateStepData = {
        title: form.value.title,
        description: form.value.description || undefined,
      };
      await updateStep(stepId.value, data);
      ElMessage.success("更新成功");
    } else {
      const data: CreateStepData = {
        title: form.value.title,
        description: form.value.description || undefined,
      };
      await createStep(data);
      ElMessage.success("创建成功");
    }
    void router.push("/steps");
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || "操作失败");
  } finally {
    isSubmitting.value = false;
  }
}

onMounted(async () => {
  if (route.path === "/steps/create") {
    isEdit.value = false;
  } else if (route.path.startsWith("/steps/") && route.params.id) {
    isEdit.value = true;
    stepId.value = Number(route.params.id);
    try {
      const step = await getStep(stepId.value);
      form.value.title = step.title;
      form.value.description = step.description ?? "";
    } catch {
      ElMessage.error("获取训练计划信息失败");
      void router.push("/steps");
    }
  }
});
</script>

<template>
  <div style="padding: 20px; max-width: 800px; margin: 0 auto">
    <el-card>
      <template #header>
        <span>{{ isEdit ? "编辑训练计划" : "创建训练计划" }}</span>
      </template>
      <el-form label-position="top" :model="form">
        <el-form-item label="标题" required>
          <el-input
            v-model="form.title"
            placeholder="请输入训练计划标题"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="请输入训练计划描述（可选）"
            :rows="4"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="isSubmitting" @click="handleSubmit">
            {{ isEdit ? "保存" : "创建" }}
          </el-button>
          <el-button @click="router.push('/steps')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
