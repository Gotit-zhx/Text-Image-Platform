<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import BaseButton from '../ui/BaseButton.vue'
const props = defineProps<{ images: string[]; start: number; open: boolean }>()
const emit = defineEmits<{ close: [] }>()
const viewerElement=ref<HTMLElement|null>(null)
const focusViewer=async()=>{await nextTick();viewerElement.value?.focus()}
const retry = () => {
  viewerElement.value?.focus()
  failed.value = false
}
const index = ref(0),
  scale = ref(1),
  failed = ref(false),
  touchX = ref(0),
  pinch = ref<{ distance: number; scale: number }>()
watch(
  () => [props.start, props.open],
  () => {
    index.value = Math.max(0,Math.min(props.start,props.images.length-1))
    scale.value = 1
    failed.value = false
  }
)
const move = (delta: number) => {
  if(!props.images.length)return
  index.value = (index.value + delta + props.images.length) % props.images.length
  scale.value = 1
  failed.value = false
}
const touchStart = (e: TouchEvent) => {
  touchX.value = e.changedTouches[0]?.clientX || 0
  if (e.touches.length === 2) {
    const [a, b] = [e.touches[0]!, e.touches[1]!]
    pinch.value = {
      distance: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY),
      scale: scale.value
    }
  }
}
const touchMove = (e: TouchEvent) => {
  if (pinch.value && e.touches.length === 2) {
    e.preventDefault()
    const [a, b] = [e.touches[0]!, e.touches[1]!]
    scale.value = Math.max(
      1,
      Math.min(
        3,
        (pinch.value.scale * Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY)) /
          pinch.value.distance
      )
    )
  }
}
const touchEnd = (e: TouchEvent) => {
  if (pinch.value) {
    pinch.value = undefined
    return
  }
  const delta = (e.changedTouches[0]?.clientX || 0) - touchX.value
  if (scale.value === 1 && Math.abs(delta) > 60) move(delta > 0 ? -1 : 1)
}
const key = (e: KeyboardEvent) => {
  if(e.isComposing||e.target instanceof HTMLInputElement||e.target instanceof HTMLTextAreaElement||(e.target instanceof HTMLElement&&e.target.isContentEditable))return
  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    move(-1)
  }
  if(e.key==='+'||e.key==='='){e.preventDefault();scale.value=Math.min(3,scale.value+.5)}
  if(e.key==='-'){e.preventDefault();scale.value=Math.max(1,scale.value-.5)}
  if (e.key === 'ArrowRight') {
    e.preventDefault()
    move(1)
  }
}
</script>
<template>
  <el-dialog
    :model-value="open"
    title="图片查看器"
    width="min(1200px,96vw)"
    append-to-body
    class="image-viewer"
    @opened="focusViewer"
    @close="emit('close')"
    ><div
      ref="viewerElement" class="viewer" role="group" aria-label="图片查看区域，左右键切图，加减键缩放"
      tabindex="0"
      @keydown="key"
      @touchstart="touchStart"
      @touchmove="touchMove"
      @touchend="touchEnd"
    >
      <div class="image-stage">
        <img
          v-if="!failed"
          :key="images[index]"
          :src="images[index]"
          :style="{ transform: `scale(${scale})` }"
          alt="作品大图"
          @error="failed = true"
        />
        <p v-else role="alert">图片加载失败 <button @click="retry">重试</button></p>
      </div>
      <div class="viewer-tools">
        <BaseButton :disabled="images.length < 2" @click="move(-1)">上一张</BaseButton
        ><span aria-live="polite">{{ images.length?index + 1:0 }} / {{ images.length }} · {{Math.round(scale*100)}}%</span
        ><BaseButton :disabled="images.length < 2" @click="move(1)">下一张</BaseButton
        ><BaseButton
          :disabled="scale <= 1"
          @click="scale = Math.max(1, scale - 0.5)"
          aria-label="缩小图片"
          >−</BaseButton
        ><BaseButton
          :disabled="scale >= 3"
          @click="scale = Math.min(3, scale + 0.5)"
          aria-label="放大图片"
          >＋</BaseButton
        >
      </div>
    </div></el-dialog
  >
</template>
<style scoped>
.image-stage {
  touch-action: none;
  height: min(65dvh, 760px);
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
}
.image-stage img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transform-origin: center;
}
.viewer-tools {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}
.viewer-tools span {
  font-size: 12px;
}
</style>
