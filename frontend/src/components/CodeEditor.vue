<template>
  <div class="code-editor">
    <div class="editor-header">
      <h3>Python Code Editor</h3>
      <div class="editor-actions">
        <button 
          @click="executeCode" 
          :disabled="isExecuting"
          class="run-button"
        >
          {{ isExecuting ? 'Running...' : 'Run Code' }}
        </button>
        <button 
          @click="stopExecution"
          :disabled="!isExecuting && !isStreaming"
          class="stop-button"
        >
          Stop
        </button>
        <button @click="clearEditor" class="clear-button">
          Clear
        </button>
      </div>
    </div>
    
    <div class="editor-container">
      <div ref="editorElement" class="editor"></div>
    </div>
    
    <div class="output-section">
      <div class="output-header" @click="toggleOutput">
        <h4>Output</h4>
        <div class="output-controls">
          <button @click.stop="clearOutput" class="clear-output-button">
            Clear Output
          </button>
          <button class="toggle-output-button" :class="{ 'collapsed': !isOutputExpanded }">
            {{ isOutputExpanded ? '▼' : '▶' }}
          </button>
        </div>
      </div>
      
      <div class="output-container" :class="{ 'collapsed': !isOutputExpanded }">
        <!-- Streaming Output Lines -->
        <div v-if="outputLines.length > 0" class="streaming-output">
          <div 
            v-for="line in outputLines" 
            :key="line.id"
            class="output-line"
            :class="line.type"
          >
            <pre>{{ line.content }}</pre>
          </div>
        </div>
        
        <!-- Legacy Output (for compatibility) -->
        <div v-if="output && outputLines.length === 0" class="output success">
          <pre>{{ output }}</pre>
        </div>
        <div v-if="error && outputLines.length === 0" class="output error">
          <pre>{{ error }}</pre>
          <button @click="getAIHelp" class="ai-help-button">
            Get AI Help
          </button>
        </div>
        
        <!-- AI Response -->
        <div v-if="aiResponse" class="ai-response">
          <h5>AI Assistant:</h5>
          <p>{{ aiResponse }}</p>
        </div>
        
        <!-- Streaming Indicator -->
        <div v-if="isStreaming" class="streaming-indicator">
          <div class="spinner"></div>
          <span>Executing...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { EditorView, basicSetup } from 'codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { useCodeStore } from '../stores/code'

export default {
  name: 'CodeEditor',
  setup() {
    const editorElement = ref(null)
    const editorView = ref(null)
    const codeStore = useCodeStore()
    const isOutputExpanded = ref(true)
    
    // Use storeToRefs to make store properties reactive
    const { code, output, error, isExecuting, aiResponse, outputLines, isStreaming } = storeToRefs(codeStore)

    onMounted(() => {
      if (editorElement.value) {
        editorView.value = new EditorView({
          doc: '# Test streaming output\nimport time\n\nprint("Starting...")\nfor i in range(5):\n    print(f"Count: {i}")\n    time.sleep(1)\nprint("Done!")\n\n# Test infinite loop (uncomment to test)\n# while True:\n#     print("Infinite loop")\n#     time.sleep(1)',
          extensions: [
            basicSetup,
            python(),
            oneDark,
            EditorView.updateListener.of((update) => {
              if (update.docChanged) {
                codeStore.setCode(update.state.doc.toString())
              }
            })
          ],
          parent: editorElement.value
        })
        
        // Set initial code
        codeStore.setCode(editorView.value.state.doc.toString())
      }
    })

    onUnmounted(() => {
      if (editorView.value) {
        editorView.value.destroy()
      }
    })

    const executeCode = async () => {
      try {
        console.log('Executing code:', codeStore.code);
        const result = await codeStore.executeCodeStreaming(codeStore.code);
        console.log('Execution result:', result);
      } catch (error) {
        console.error('Code execution error:', error)
      }
    }

    const clearEditor = () => {
      if (editorView.value) {
        editorView.value.dispatch({
          changes: {
            from: 0,
            to: editorView.value.state.doc.length,
            insert: ''
          }
        })
        codeStore.setCode('')
      }
    }

    const clearOutput = () => {
      codeStore.clearOutput()
    }

    const getAIHelp = async () => {
      try {
        await codeStore.getAIErrorHelp(codeStore.code, codeStore.error)
      } catch (error) {
        console.error('AI help error:', error)
      }
    }

    const toggleOutput = () => {
      isOutputExpanded.value = !isOutputExpanded.value
    }

    const stopExecution = async () => {
      try {
        await codeStore.stopExecution()
      } catch (error) {
        console.error('Stop error:', error)
      }
    }

    return {
      editorElement,
      code,
      output,
      error,
      isExecuting,
      aiResponse,
      outputLines,
      isStreaming,
      isOutputExpanded,
      executeCode,
      clearEditor,
      clearOutput,
      getAIHelp,
      toggleOutput,
      stopExecution
    }
  }
}
</script>

<style scoped>
/* Minimal styling - basic layout only */
.code-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #ccc;
}

.editor-actions {
  display: flex;
  gap: 0.5rem;
}

.run-button, .clear-button, .stop-button {
  padding: 0.5rem 1rem;
  border: 1px solid #ccc;
  background: #f5f5f5;
  cursor: pointer;
}

.stop-button {
  background: #ffecec;
}

.run-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.editor-container {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

.editor {
  height: 100%;
  font-family: monospace;
  overflow: auto;
}

.output-section {
  border-top: 1px solid #ccc;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  max-height: 300px;
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #ccc;
  cursor: pointer;
  user-select: none;
  background: #f8f9fa;
  transition: background-color 0.2s;
}

.output-header:hover {
  background: #e9ecef;
}

.output-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.clear-output-button {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ccc;
  background: #f5f5f5;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.8rem;
}

.clear-output-button:hover {
  background: #e9ecef;
}

.toggle-output-button {
  width: 24px;
  height: 24px;
  border: 1px solid #ccc;
  background: #f5f5f5;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.2s;
}

.toggle-output-button:hover {
  background: #e9ecef;
}

.toggle-output-button.collapsed {
  transform: rotate(-90deg);
}

.output-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  transition: all 0.3s ease;
  min-height: 0;
}

.output-container.collapsed {
  max-height: 0;
  padding: 0 1rem;
  overflow: hidden;
  flex: 0;
}

.output {
  margin-bottom: 1rem;
}

.output pre {
  margin: 0;
  padding: 0.5rem;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.output.success pre {
  background: #f0f8f0;
  border: 1px solid #90ee90;
}

.output.error pre {
  background: #fff0f0;
  border: 1px solid #ffb6c1;
}

.ai-help-button {
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid #ccc;
  background: #f5f5f5;
  cursor: pointer;
}

.ai-response {
  border: 1px solid #ccc;
  padding: 1rem;
  margin-top: 1rem;
  background: #f9f9f9;
}

/* Streaming Output Styles */
.streaming-output {
  margin-bottom: 1rem;
}

.output-line {
  margin-bottom: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9rem;
}

.output-line.stdout {
  background: #f0f8f0;
  border-left: 3px solid #90ee90;
  color: #2d5a2d;
}

.output-line.stderr {
  background: #fff0f0;
  border-left: 3px solid #ffb6c1;
  color: #8b0000;
}

.output-line.error {
  background: #ffe6e6;
  border-left: 3px solid #ff6b6b;
  color: #cc0000;
  font-weight: bold;
}

.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #e3f2fd;
  border: 1px solid #2196f3;
  border-radius: 4px;
  color: #1976d2;
  font-size: 0.9rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e3f2fd;
  border-top: 2px solid #2196f3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>