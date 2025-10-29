<template>
  <div v-if="display" class="display-panel">
    <div class="panel-header">DisplayBlock: {{ display.displayId }}</div>
    <div
      class="matrix"
      :style="{
        gridTemplateColumns: `repeat(${display.width}, ${pixelSize}px)`,
        gridTemplateRows: `repeat(${display.height}, ${pixelSize}px)`,
        gap: `${gap}px`,
      }"
    >
      <div
        v-for="(row, y) in display.blocks"
        :key="`row-${y}`"
      >
        <div
          v-for="(cell, x) in row"
          :key="`${x}-${y}`"
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
  border: 1px solid #000;
  border-radius: 6px;
  background: #fff;
  width: max-content;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.panel-header {
  text-align: center;
  font-weight: 600;
  padding: 6px 12px;
  border-bottom: 1px solid #000;
  border-top: 4px solid #000;
  cursor: move;
  user-select: none;
}
.matrix {
  display: grid;
}
.matrix.empty {
  width: 1px;
  height: 1px;
}
.pixel {
  border-radius: 2px;
  border: 1px solid #000;
}
</style>


