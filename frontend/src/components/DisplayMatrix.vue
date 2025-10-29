<template>
  <div v-if="display" class="display-panel">
    <div class="panel-header">DisplayBlock: {{ display.displayId }}</div>
    <div class="matrix-surface">
      <div
        class="matrix"
        :style="{
          gridTemplateColumns: `repeat(${display.width}, ${pixelSize}px)`,
          gridTemplateRows: `repeat(${display.height}, ${pixelSize}px)`,
          gap: `${gap}px`,
        }"
      >
        <div
          v-for="(cell, idx) in flatBlocks"
          :key="idx"
          class="pixel"
          :style="pixelStyle(cell)"
        />
      </div>
    </div>
  </div>
  <div v-else class="matrix empty"></div>
  
</template>

<script setup>
import { computed } from 'vue'
import { useBlockDisplaysStore } from '../stores/blockDisplays'

const props = defineProps({
  displayId: { type: String, required: true },
  pixelSize: { type: Number, default: 16 },
  gap: { type: Number, default: 2 },
})

const store = useBlockDisplaysStore()
const display = computed(() => store.byId[props.displayId])

// Flatten rows so pixels themselves are grid items; enables proper CSS grid gap
const flatBlocks = computed(() => {
  const d = display.value
  if (!d) return []
  return d.blocks.flat()
})

function pixelStyle(cell) {
  const [r, g, b] = cell.color || [255, 255, 255]
  return {
    width: props.pixelSize + 'px',
    height: props.pixelSize + 'px',
    backgroundColor: `rgb(${r}, ${g}, ${b})`,
    opacity: cell.brightness ?? 1.0,
    visibility: cell.on ? 'visible' : 'hidden',
  }
}
</script>

<style scoped>
.display-panel {
  border: 2px solid #111827; /* dark bezel */
  border-radius: 10px;
  background: #0f172a; /* slate-900 */
  width: max-content;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255,255,255,0.03);
}
.panel-header {
  text-align: center;
  font-weight: 700;
  padding: 10px 14px;
  background: linear-gradient(#f8fafc, #e5e7eb); /* subtle modern header */
  color: #111827;
  border-bottom: 1px solid #cbd5e1;
  border-top: 6px solid #111827; /* thicker top */
  cursor: move;
  user-select: none;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}
.matrix-surface {
  padding: 12px; /* inner bezel padding around the grid */
  background: radial-gradient(120% 100% at 50% 0%, #0b0f14 0%, #0a0e12 60%, #090c10 100%);
  border-bottom-left-radius: 10px;
  border-bottom-right-radius: 10px;
}
.matrix {
  display: grid;
}
.matrix.empty {
  width: 1px;
  height: 1px;
}
.pixel {
  border-radius: 3px;
  border: 1px solid #ffffff; /* white separators between black pixels */
  box-shadow: 0 0 0 1px rgba(255,255,255,0.05) inset;
}
</style>


