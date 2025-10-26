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
        <button @click="clearEditor" class="clear-button">
          Clear
        </button>
      </div>
    </div>
    
    <div class="editor-container">
      <div ref="editorElement" class="editor"></div>
    </div>
    
    <div class="output-section">
      <div class="output-header">
        <h4>Output</h4>
        <button @click="clearOutput" class="clear-output-button">
          Clear Output
        </button>
      </div>
      
      <div class="output-container">
        <div v-if="output" class="output success">
          <pre>{{ output }}</pre>
        </div>
        <div v-if="error" class="output error">
          <pre>{{ error }}</pre>
          <button @click="getAIHelp" class="ai-help-button">
            Get AI Help
          </button>
        </div>
        <div v-if="aiResponse" class="ai-response">
          <h5>AI Assistant:</h5>
          <p>{{ aiResponse }}</p>
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
    
    // Use storeToRefs to make store properties reactive
    const { code, output, error, isExecuting, aiResponse } = storeToRefs(codeStore)

    onMounted(() => {
      if (editorElement.value) {
        editorView.value = new EditorView({
          doc: 'print("Hello, World!")\n',
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
        const result = await codeStore.executeCode(codeStore.code);
        console.log('Execution result:', result);
        console.log('Current output:', codeStore.output);
        console.log('Current error:', codeStore.error);
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

    return {
      editorElement,
      code,
      output,
      error,
      isExecuting,
      aiResponse,
      executeCode,
      clearEditor,
      clearOutput,
      getAIHelp
    }
  }
}
</script>

<style scoped>
.code-editor {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #1e1e1e;
  color: #d4d4d4;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #2d2d2d;
  border-bottom: 1px solid #3e3e3e;
}

.editor-header h3 {
  margin: 0;
  color: #ffffff;
}

.editor-actions {
  display: flex;
  gap: 0.5rem;
}

.run-button, .clear-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.run-button {
  background: #007acc;
  color: white;
}

.run-button:hover:not(:disabled) {
  background: #005a9e;
}

.run-button:disabled {
  background: #666;
  cursor: not-allowed;
}

.clear-button {
  background: #666;
  color: white;
}

.clear-button:hover {
  background: #888;
}

.editor-container {
  flex: 1;
  overflow: hidden;
}

.editor {
  height: 100%;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
}

.output-section {
  height: 300px;
  background: #1e1e1e;
  border-top: 1px solid #3e3e3e;
  display: flex;
  flex-direction: column;
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #2d2d2d;
  border-bottom: 1px solid #3e3e3e;
}

.output-header h4 {
  margin: 0;
  color: #ffffff;
}

.clear-output-button {
  padding: 0.25rem 0.5rem;
  background: #666;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.clear-output-button:hover {
  background: #888;
}

.output-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.output {
  margin-bottom: 1rem;
}

.output pre {
  margin: 0;
  padding: 0.5rem;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.output.success pre {
  background: #1e3a1e;
  color: #4ade80;
  border: 1px solid #22c55e;
}

.output.error pre {
  background: #3a1e1e;
  color: #f87171;
  border: 1px solid #ef4444;
}

.ai-help-button {
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  background: #7c3aed;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.ai-help-button:hover {
  background: #8b5cf6;
}

.ai-response {
  background: #2a1e3a;
  border: 1px solid #7c3aed;
  border-radius: 4px;
  padding: 1rem;
  margin-top: 1rem;
}

.ai-response h5 {
  margin: 0 0 0.5rem 0;
  color: #a78bfa;
}

.ai-response p {
  margin: 0;
  color: #d4d4d4;
}
</style>