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
    
    <main class="app-main">
      <CodeEditor />
    </main>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import CodeEditor from '../components/CodeEditor.vue'

export default {
  name: 'EditorView',
  components: {
    CodeEditor
  },
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const user = computed(() => authStore.user)

    const handleLogout = () => {
      authStore.logout()
      router.push('/login')
    }

    return {
      user,
      handleLogout
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
}

.app-main {
  flex: 1;
}
</style>
