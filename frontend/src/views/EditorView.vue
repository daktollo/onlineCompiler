<template>
  <div class="editor-view">
    <header class="app-header">
      <div class="header-content">
        <h1>Online Compiler</h1>
        <div class="user-info">
          <span>Welcome, {{ user?.username }}</span>
          <button @click="handleLogout" class="logout-button">
            Logout
          </button>
        </div>
      </div>
    </header>
    
    <!-- Full screen overlay container -->
    <div class="full-screen-container">
      <div class="draggable-window" ref="draggableWindow">
        <div class="window-header" @mousedown="startDrag">
          <h3>Code Editor</h3>
          <div class="window-controls">
            <button @click="minimizeWindow" class="control-btn minimize">−</button>
            <button @click="closeWindow" class="control-btn close">×</button>
          </div>
        </div>
        <div class="window-content">
          <CodeEditor />
        </div>
      </div>

      <!-- Frameless draggable DisplayBlock panels -->
      <div class="matrix-layer">
        <DraggableContainer
          v-for="(id, idx) in displayIds"
          :key="id"
          :id="`display-${id}`"
          :initialX="60 + idx * 40"
          :initialY="200 + idx * 40"
        >
          <DisplayMatrix :displayId="id" :pixelSize="16" :gap="2" />
        </DraggableContainer>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useBlockDisplaysStore } from '../stores/blockDisplays'
import CodeEditor from '../components/CodeEditor.vue'
import DraggableContainer from '../components/DraggableContainer.vue'
import DisplayMatrix from '../components/DisplayMatrix.vue'

export default {
  name: 'EditorView',
  components: {
    CodeEditor,
    DraggableContainer,
    DisplayMatrix
  },
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const blockStore = useBlockDisplaysStore()
    const draggableWindow = ref(null)
    
    const user = computed(() => authStore.user)
    const displayIds = computed(() => Object.keys(blockStore.byId))
    
    // Drag functionality
    let isDragging = false
    let dragOffset = { x: 0, y: 0 }
    let isMinimized = false

    const startDrag = (e) => {
      if (e.target.closest('.window-controls')) return
      
      isDragging = true
      const rect = draggableWindow.value.getBoundingClientRect()
      dragOffset.x = e.clientX - rect.left
      dragOffset.y = e.clientY - rect.top
      
      document.addEventListener('mousemove', onDrag)
      document.addEventListener('mouseup', stopDrag)
      e.preventDefault()
    }

    const onDrag = (e) => {
      if (!isDragging) return
      
      const x = e.clientX - dragOffset.x
      const y = e.clientY - dragOffset.y
      
      // Keep window within viewport bounds
      const maxX = window.innerWidth - draggableWindow.value.offsetWidth
      const maxY = window.innerHeight - draggableWindow.value.offsetHeight
      
      const constrainedX = Math.max(0, Math.min(x, maxX))
      const constrainedY = Math.max(0, Math.min(y, maxY))
      
      draggableWindow.value.style.left = `${constrainedX}px`
      draggableWindow.value.style.top = `${constrainedY}px`
    }

    const stopDrag = () => {
      isDragging = false
      document.removeEventListener('mousemove', onDrag)
      document.removeEventListener('mouseup', stopDrag)
    }

    const minimizeWindow = () => {
      isMinimized = !isMinimized
      if (isMinimized) {
        draggableWindow.value.style.height = '40px'
        draggableWindow.value.querySelector('.window-content').style.display = 'none'
      } else {
        draggableWindow.value.style.height = '80vh'
        draggableWindow.value.querySelector('.window-content').style.display = 'block'
      }
    }

    const closeWindow = () => {
      // For now, just minimize instead of closing
      minimizeWindow()
    }

    onMounted(() => {
      // Set initial position
      if (draggableWindow.value) {
        draggableWindow.value.style.left = '50px'
        draggableWindow.value.style.top = '100px'
      }
    })

    onUnmounted(() => {
      document.removeEventListener('mousemove', onDrag)
      document.removeEventListener('mouseup', stopDrag)
    })

    const handleLogout = () => {
      authStore.logout()
      router.push('/login')
    }

    return {
      user,
      displayIds,
      draggableWindow,
      handleLogout,
      startDrag,
      minimizeWindow,
      closeWindow
    }
  }
}
</script>

<style scoped>
/* Minimal styling - basic layout only */
.editor-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  padding: 1rem;
  border-bottom: 1px solid #ccc;
  background: #f8f9fa;
  z-index: 1000;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logout-button {
  padding: 0.5rem 1rem;
  border: 1px solid #ccc;
  background: #f5f5f5;
  cursor: pointer;
  border-radius: 4px;
}

.logout-button:hover {
  background: #e9ecef;
}

/* Full screen container */
.full-screen-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.matrix-layer {
  position: fixed;
  inset: 0;
  z-index: 110;
  pointer-events: none; /* allow drag via container while matrix pixels ignore pointer */
}

/* Draggable window */
.draggable-window {
  position: absolute;
  width: 45vw;
  height: 40vh;
  background: white;
  border: 2px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  resize: both;
  min-width: 400px;
  min-height: 300px;
}

/* Window header */
.window-header {
  background: #f8f9fa;
  border-bottom: 1px solid #ddd;
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: move;
  user-select: none;
}

.window-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #333;
}

.window-controls {
  display: flex;
  gap: 0.5rem;
}

.control-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  transition: background-color 0.2s;
}

.control-btn.minimize {
  background: #ffc107;
  color: #000;
}

.control-btn.minimize:hover {
  background: #e0a800;
}

.control-btn.close {
  background: #dc3545;
  color: white;
}

.control-btn.close:hover {
  background: #c82333;
}

/* Window content */
.window-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Make sure CodeEditor fills the window content */
.window-content .code-editor {
  height: 100%;
}
</style>
