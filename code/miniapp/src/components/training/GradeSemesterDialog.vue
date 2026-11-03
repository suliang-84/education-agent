<script setup lang="ts">
/**
 * 补充 / 修改年级学期弹窗（按知识点、按单元、随机训练共用）
 * 选好后直接保存到学生资料（PATCH /profile/me），保存成功触发 saved；required 为 true 时「返回」触发 cancel。
 */
import { ref, watch } from 'vue'
import { profileApi } from '@/api'
import { useAuthStore } from '@/store'

const props = defineProps<{
  show: boolean
  required?: boolean
  gradeOptions: Array<{ code: string; name: string }>
  semesterOptions: Array<{ code: string; name: string }>
  grade?: string
  semester?: string
}>()
const emit = defineEmits<{ (e: 'saved'): void; (e: 'cancel'): void }>()

const authStore = useAuthStore()
const pickGrade = ref('')
const pickSemester = ref('')
const error = ref('')
const saving = ref(false)

watch(() => props.show, (v) => {
  if (v) {
    pickGrade.value = props.grade ?? ''
    pickSemester.value = props.semester ?? ''
    error.value = ''
  }
}, { immediate: true })

async function save() {
  if (saving.value) return
  if (!pickGrade.value || !pickSemester.value) {
    error.value = !pickGrade.value ? '请选择年级' : '请选择学期'
    return
  }
  saving.value = true
  try {
    await profileApi.updateMe({ grade: pickGrade.value, semester: pickSemester.value })
    authStore.updateUserInfo({ grade: pickGrade.value, semester: pickSemester.value } as never)
    emit('saved')
  } catch {
    error.value = '保存失败，请重试'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <view v-if="show" class="mask">
    <view class="dialog">
      <text class="dialog__title">{{ required ? '请先补充年级和学期' : '修改年级和学期' }}</text>
      <text class="dialog__desc">按你当前所在的年级和学期，为你选取对应的题目</text>

      <text class="dialog__label">年级</text>
      <view class="chips">
        <view
          v-for="g in gradeOptions"
          :key="g.code"
          class="chip"
          :class="{ 'chip--active': pickGrade === g.code }"
          @tap="pickGrade = g.code; error = ''"
        ><text class="chip__text">{{ g.name }}</text></view>
      </view>

      <text class="dialog__label">学期</text>
      <view class="chips">
        <view
          v-for="s in semesterOptions"
          :key="s.code"
          class="chip chip--half"
          :class="{ 'chip--active': pickSemester === s.code }"
          @tap="pickSemester = s.code; error = ''"
        ><text class="chip__text">{{ s.name }}</text></view>
      </view>

      <text v-if="error" class="dialog__error">{{ error }}</text>

      <view class="dialog__btns">
        <button class="dlg-btn dlg-btn--cancel" @tap="emit('cancel')">{{ required ? '返回' : '取消' }}</button>
        <button class="dlg-btn dlg-btn--ok" @tap="save">确定</button>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.mask {
  position: fixed;
  inset: 0;
  background: $mask;
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: $space-6;
}

.dialog {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-5;
  width: 100%;
  border: 1rpx solid $border;
  box-shadow: $shadow-md;
  display: flex;
  flex-direction: column;
  gap: $space-2;

  &__title { font-size: $font-size-lg; color: $text-1; font-weight: 700; text-align: center; }
  &__desc { font-size: $font-size-sm; color: $text-3; text-align: center; margin-bottom: $space-2; }
  &__label { font-size: $font-size-sm; color: $text-2; font-weight: 600; margin-top: $space-2; }
  &__error { font-size: $font-size-sm; color: $danger; margin-top: $space-1; }
  &__btns { display: flex; gap: $space-2; margin-top: $space-3; }
}

.chips { display: flex; flex-wrap: wrap; gap: $space-2; }
.chip {
  height: 68rpx;
  padding: 0 $space-4;
  border-radius: $r-pill;
  background: $bg-muted;
  border: 1rpx solid transparent;
  display: flex;
  align-items: center;
  justify-content: center;

  &--half { flex: 1; }
  &--active { background: $primary-light; border-color: $primary-border; }
  &__text { font-size: $font-size-sm; color: $text-2; font-weight: 500; }
  &--active &__text { color: $primary; font-weight: 600; }
}

.dlg-btn {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: $r-pill;
  font-size: $font-size-base;
  font-weight: 600;
  border: none;
  padding: 0;
  &::after { border: none; }

  &--cancel { background: $bg-muted; color: $text-2; }
  &--ok { background: $cta-gradient; color: $on-primary; box-shadow: $shadow-cta; }
}
</style>
