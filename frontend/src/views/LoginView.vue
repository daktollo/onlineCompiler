<template>
  <div class="login-container">
    <div class="login-card">
      <h2>Online Compiler</h2>
      <p>Sign in to your account</p>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            placeholder="Enter your username"
          />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            placeholder="Enter your password"
          />
        </div>
        
        <button type="submit" :disabled="isLoading" class="login-button">
          {{ isLoading ? 'Signing in...' : 'Sign In' }}
        </button>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </form>
      
      <div class="register-link">
        <p>Don't have an account? <router-link to="/register">Sign up</router-link></p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'LoginView',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const username = ref('')
    const password = ref('')
    const isLoading = ref(false)
    const error = ref('')

    const handleLogin = async () => {
      isLoading.value = true
      error.value = ''
      
      const result = await authStore.login(username.value, password.value)
      
      if (result.success) {
        router.push('/editor')
      } else {
        error.value = result.error
      }
      
      isLoading.value = false
    }

    return {
      username,
      password,
      isLoading,
      error,
      handleLogin
    }
  }
}
</script>

<style scoped>
/* Minimal styling - basic form layout only */
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.login-card {
  background: white;
  border: 1px solid #ccc;
  padding: 2rem;
  width: 100%;
  max-width: 400px;
}

.login-card h2 {
  text-align: center;
  margin-bottom: 1rem;
}

.login-card p {
  text-align: center;
  margin-bottom: 2rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group input {
  padding: 0.5rem;
  border: 1px solid #ccc;
}

.login-button {
  padding: 0.5rem;
  border: 1px solid #ccc;
  background: #f5f5f5;
  cursor: pointer;
}

.login-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 0.5rem;
  border: 1px solid #fcc;
  text-align: center;
}

.register-link {
  text-align: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #ccc;
}

.register-link a {
  color: #0066cc;
  text-decoration: none;
}
</style>
