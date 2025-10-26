import { defineStore } from "pinia";
import axios from "axios";
import { useAuthStore } from "./auth";

export const useCodeStore = defineStore("code", {
  state: () => ({
    code: "",
    output: "",
    error: "",
    isExecuting: false,
    aiResponse: "",
  }),

  actions: {
    async executeCode(code) {
      const authStore = useAuthStore();
      if (!authStore.token) {
        throw new Error("Not authenticated");
      }

      this.isExecuting = true;
      this.error = null; // Clear previous errors
      this.output = "";

      try {
        const response = await axios.post(
          "http://localhost:5000/api/code/execute",
          {
            code,
          },
          {
            headers: {
              Authorization: `Bearer ${authStore.token}`,
            },
          }
        );

        console.log("Response data:", response.data);

        if (response.data.error) {
          this.error = response.data.error;
          console.log("Error set:", this.error);
        } else {
          this.output = response.data.output;
          console.log("Output set:", this.output);
        }

        return response.data;
      } catch (error) {
        if (error.response?.status === 429) {
          this.error = "Too many requests. Please wait a moment before trying again.";
        } else {
          this.error = error.response?.data?.error || "Code execution failed";
        }
        throw error;
      } finally {
        this.isExecuting = false;
      }
    },

    async getAIErrorHelp(code, output) {
      const authStore = useAuthStore();
      if (!authStore.token) {
        throw new Error("Not authenticated");
      }

      try {
        const response = await fetch("http://localhost:5000/api/ai/error-handler", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authStore.token}`,
          },
          body: JSON.stringify({ code, output }),
        });

        if (!response.ok) {
          throw new Error("AI service error");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let aiResponse = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.response) {
                  aiResponse += data.response;
                  this.aiResponse = aiResponse;
                }
              } catch (e) {
                // Ignore parsing errors
              }
            }
          }
        }

        return aiResponse;
      } catch (error) {
        this.aiResponse = "AI service is not available";
        throw error;
      }
    },

    setCode(code) {
      this.code = code;
    },

    clearOutput() {
      this.output = "";
      this.error = "";
      this.aiResponse = "";
    },
  },
});
