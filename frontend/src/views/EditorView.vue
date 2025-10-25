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
.editor-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
}

.app-header {
  background: #2d2d2d;
  border-bottom: 1px solid #3e3e3e;
  padding: 0 1rem;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  max-width: 1200px;
  margin: 0 auto;
}

.app-header h1 {
  margin: 0;
  color: #ffffff;
  font-size: 1.5rem;
  font-weight: 600;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: #d4d4d4;
}

.logout-button {
  background: #ef4444;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.logout-button:hover {
  background: #dc2626;
}

.app-main {
  flex: 1;
  overflow: hidden;
}
</style>
