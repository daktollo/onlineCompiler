import { defineStore } from "pinia";
import axios from "axios";
import { useAuthStore } from "./auth";
import { nextTick } from "vue";

export const useCodeStore = defineStore("code", {
  state: () => ({
    code: "",
    output: "",
    error: "",
    isExecuting: false,
    aiResponse: "",
    outputLines: [], // For streaming output
    isStreaming: false,
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
          "http://localhost:6600/api/code/execute",
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
        const response = await fetch("http://localhost:6600/api/ai/error-handler", {
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

    async executeCodeStreaming(code) {
      const authStore = useAuthStore();
      if (!authStore.token) {
        throw new Error("Not authenticated");
      }

      this.isExecuting = true;
      this.isStreaming = true;
      this.error = "";
      this.output = "";
      this.outputLines = []; // Clear previous output lines

      // Flags must be defined outside try so finally can access them
      let completed = false;
      let hadNetworkError = false;
      let gotDone = false;

      try {
        // Step 1: Get redirect information from backend
        console.log("🔄 Getting redirect information from backend...");
        const redirectResponse = await fetch("http://localhost:6600/api/code/execute_streaming", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authStore.token}`,
          },
          body: JSON.stringify({ code }),
        });

        if (!redirectResponse.ok) {
          throw new Error(`Backend error! status: ${redirectResponse.status}`);
        }

        const redirectInfo = await redirectResponse.json();
        console.log("📋 Redirect info received:", redirectInfo);

        // Step 2: Make direct call to CodeManager
        console.log("🚀 Making direct call to CodeManager...");
        const directResponse = await fetch(redirectInfo.redirect_url, {
          method: redirectInfo.method,
          headers: redirectInfo.headers,
          body: JSON.stringify(redirectInfo.payload),
        });

        if (!directResponse.ok) {
          throw new Error(`CodeManager error! status: ${directResponse.status}`);
        }

        console.log("✅ Direct connection established, starting stream...");

        // Step 3: Process streaming response
        const reader = directResponse.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        const processStream = async () => {
          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              console.log("Stream completed");
              break;
            }

            // Decode chunk and add to buffer
            const chunk = decoder.decode(value, { stream: true });
            console.log("Received chunk:", chunk);
            buffer += chunk;

            // Process line by line for better performance
            const lines = buffer.split("\n");
            buffer = lines.pop() || ""; // Keep incomplete line in buffer

            for (const line of lines) {
              if (line.trim() && line.startsWith("data: ")) {
                try {
                  const data = JSON.parse(line.slice(6));
                  console.log("Streaming data received:", data);

                  // Handle different output types
                  if (data.type === "stdout" && data.line !== "") {
                    this.addOutputLine("stdout", data.line);
                  } else if (data.type === "stderr") {
                    this.addOutputLine("stderr", data.line);
                  } else if (data.type === "error") {
                    this.addOutputLine("error", data.line);
                  } else if (data.type === "done") {
                    // Immediate completion signal
                    gotDone = true;
                    return; // stop processing further
                  }

                  // Force immediate UI update
                  await nextTick();
                } catch (e) {
                  console.warn("Failed to parse streaming data:", line, e);
                }
              }
            }
          }
        };

        await processStream();
        completed = true;

        // Process any remaining data in buffer
        if (buffer.trim() && buffer.startsWith("data: ")) {
          try {
            const data = JSON.parse(buffer.slice(6));
            this.addOutputLine(data.type, data.line);
          } catch (e) {
            console.warn("Failed to parse final streaming data:", buffer);
          }
        }

        return { success: true };
      } catch (error) {
        const msg = error && error.message ? String(error.message) : String(error);
        // Suppress noisy fetch/network errors; keep Stop enabled
        if (/NetworkError|Failed to fetch|The user aborted a request/i.test(msg)) {
          console.warn("Streaming fetch warning:", msg);
          hadNetworkError = true;
          return { success: false, transient: true };
        } else {
          this.addOutputLine("error", msg);
          throw error;
        }
      } finally {
        if (completed || gotDone) {
          this.isExecuting = false;
          this.isStreaming = false;
        } else if (hadNetworkError) {
          // Keep flags true so user can press Stop to kill the container
          this.isExecuting = true;
          this.isStreaming = true;
        } else {
          this.isExecuting = false;
          this.isStreaming = false;
        }
      }
    },

    async stopExecution(options = {}) {
      const authStore = useAuthStore();
      if (!authStore.token) {
        return { success: false, error: "Not authenticated" };
      }
      try {
        const fetchOptions = {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authStore.token}`,
          },
          body: JSON.stringify({}),
        };
        if (options.keepalive) {
          fetchOptions.keepalive = true;
        }
        const resp = await fetch("http://localhost:6600/api/code/stop", fetchOptions);
        const data = await resp.json().catch(() => ({}));
        this.isExecuting = false;
        this.isStreaming = false;
        return { success: resp.ok, data };
      } catch (e) {
        this.isExecuting = false;
        this.isStreaming = false;
        return { success: false, error: e?.message || String(e) };
      }
    },

    addOutputLine(type, content) {
      const line = {
        type: type,
        content: content,
        timestamp: new Date(),
        id: Date.now() + Math.random(), // Unique ID for Vue key
      };

      this.outputLines.push(line);

      // Also update the legacy output field for compatibility
      if (type === "stdout") {
        this.output += content + "\n";
      } else if (type === "stderr" || type === "error") {
        this.error += content + "\n";
      }

      // Force UI update and scroll to bottom
      nextTick(() => {
        const outputContainer = document.querySelector(".output-container");
        if (outputContainer) {
          outputContainer.scrollTop = outputContainer.scrollHeight;
        }
      });
    },

    clearOutput() {
      this.output = "";
      this.error = "";
      this.aiResponse = "";
      this.outputLines = [];
    },
  },
});
