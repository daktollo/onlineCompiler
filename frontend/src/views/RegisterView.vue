<template>
  <div class="register-container">
    <div class="register-card">
      <h2>Create Account</h2>
      <p>Sign up for Online Compiler</p>
      
      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            placeholder="Choose a username"
          />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            placeholder="Create a password"
          />
        </div>
        
        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            required
            placeholder="Confirm your password"
          />
        </div>
        
        <button type="submit" :disabled="isLoading || !passwordsMatch" class="register-button">
          {{ isLoading ? 'Creating Account...' : 'Create Account' }}
        </button>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div v-if="!passwordsMatch && confirmPassword" class="error-message">
          Passwords do not match
        </div>
      </form>
      
      <div class="login-link">
        <p>Already have an account? <router-link to="/login">Sign in</router-link></p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'RegisterView',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const username = ref('')
    const password = ref('')
    const confirmPassword = ref('')
    const isLoading = ref(false)
    const error = ref('')

    const passwordsMatch = computed(() => {
      return password.value === confirmPassword.value
    })

    const handleRegister = async () => {
      if (!passwordsMatch.value) {
        error.value = 'Passwords do not match'
        return
      }

      isLoading.value = true
      error.value = ''
      
      const result = await authStore.register(username.value, password.value)
      
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
      confirmPassword,
      isLoading,
      error,
      passwordsMatch,
      handleRegister
    }
  }
}
</script>

<style scoped>
/* Minimal styling - basic form layout only */
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.register-card {
  background: white;
  border: 1px solid #ccc;
  padding: 2rem;
  width: 100%;
  max-width: 400px;
}

.register-card h2 {
  text-align: center;
  margin-bottom: 1rem;
}

.register-card p {
  text-align: center;
  margin-bottom: 2rem;
}

.register-form {
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

.register-button {
  padding: 0.5rem;
  border: 1px solid #ccc;
  background: #f5f5f5;
  cursor: pointer;
}

.register-button:disabled {
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

.login-link {
  text-align: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #ccc;
}

.login-link a {
  color: #0066cc;
  text-decoration: none;
}
</style>
