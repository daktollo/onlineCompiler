<template>
  <div
    v-if="display"
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
.matrix {
  display: grid;
  pointer-events: none; /* matrix itself shouldn't capture drag */
}
.matrix.empty {
  width: 1px;
  height: 1px;
}
.pixel {
  border-radius: 2px;
}
</style>


