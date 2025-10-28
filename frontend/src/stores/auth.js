import { defineStore } from "pinia";
import axios from "axios";
import { startBlockEvents, stopBlockEvents } from "../services/blockEvents";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    token: localStorage.getItem("token"),
    isAuthenticated: false,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token && state.isAuthenticated,
  },

  actions: {
    async login(username, password) {
      try {
        const response = await axios.post("http://localhost:5000/api/auth/login", {
          username,
          password,
        });

        this.token = response.data.token;
        this.user = response.data.user;
        this.isAuthenticated = true;

        localStorage.setItem("token", this.token);

        // Start SSE stream once authenticated
        startBlockEvents(this.user?.id || this.user?._id || this.user?.user_id || this.user);

        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.message || "Login failed",
        };
      }
    },

    async register(username, password) {
      try {
        const response = await axios.post("http://localhost:5000/api/auth/register", {
          username,
          password,
        });

        this.token = response.data.token;
        this.user = response.data.user;
        this.isAuthenticated = true;

        localStorage.setItem("token", this.token);

        // Start SSE after register
        startBlockEvents(this.user?.id || this.user?._id || this.user?.user_id || this.user);

        return { success: true, data: response.data };
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.message || "Registration failed",
        };
      }
    },

    async verifyToken() {
      if (!this.token) return false;

      try {
        const response = await axios.get("http://localhost:5000/api/auth/verify", {
          headers: {
            Authorization: `Bearer ${this.token}`,
          },
        });

        this.user = response.data.user;
        this.isAuthenticated = true;

        // Ensure SSE is started after token verification as well
        startBlockEvents(this.user?.id || this.user?._id || this.user?.user_id || this.user);

        return true;
      } catch (error) {
        this.logout();
        return false;
      }
    },

    logout() {
      this.user = null;
      this.token = null;
      this.isAuthenticated = false;
      localStorage.removeItem("token");
      // Stop SSE when logging out
      stopBlockEvents();
    },
  },
});
