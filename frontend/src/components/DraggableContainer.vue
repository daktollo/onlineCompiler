<template>
  <div
    class="drag-wrap"
    :style="{ transform: `translate(${x}px, ${y}px)` }"
    @pointerdown="onPointerDown"
  >
    <slot />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  id: { type: String, required: true },
  initialX: { type: Number, default: 40 },
  initialY: { type: Number, default: 40 },
  handleSelector: { type: String, default: '' },
})

const x = ref(0)
const y = ref(0)
let dragging = false
let startX = 0
let startY = 0
let baseX = 0
let baseY = 0

onMounted(() => {
  const key = `dragpos:${props.id}`
  try {
    const saved = JSON.parse(localStorage.getItem(key))
    if (saved && typeof saved.x === 'number' && typeof saved.y === 'number') {
      x.value = saved.x
      y.value = saved.y
    } else {
      x.value = props.initialX
      y.value = props.initialY
    }
  } catch {
    x.value = props.initialX
    y.value = props.initialY
  }
})

watch([x, y], () => {
  const key = `dragpos:${props.id}`
  localStorage.setItem(key, JSON.stringify({ x: x.value, y: y.value }))
})

function onPointerDown(e) {
  if (props.handleSelector && !e.target.closest(props.handleSelector)) return
  dragging = true
  startX = e.clientX
  startY = e.clientY
  baseX = x.value
  baseY = y.value
  document.addEventListener('pointermove', onPointerMove)
  document.addEventListener('pointerup', onPointerUp, { once: true })
}

function onPointerMove(e) {
  if (!dragging) return
  const dx = e.clientX - startX
  const dy = e.clientY - startY
  x.value = baseX + dx
  y.value = baseY + dy
}

function onPointerUp() {
  dragging = false
  document.removeEventListener('pointermove', onPointerMove)
}
</script>

<style scoped>
.drag-wrap {
  position: absolute;
  top: 0;
  left: 0;
  will-change: transform;
  cursor: default;
  user-select: none;
  -webkit-user-drag: none;
  pointer-events: auto; /* re-enable events even if parent layer has pointer-events: none */
}
</style>


