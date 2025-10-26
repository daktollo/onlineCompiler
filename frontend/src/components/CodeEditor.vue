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

.run-button, .clear-button {
  padding: 0.5rem 1rem;
  border: 1px solid #ccc;
  background: #f5f5f5;
  cursor: pointer;
}

.run-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.editor-container {
  flex: 1;
  overflow: hidden;
}

.editor {
  height: 100%;
  font-family: monospace;
}

.output-section {
  height: 300px;
  border-top: 1px solid #ccc;
  display: flex;
  flex-direction: column;
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #ccc;
}

.clear-output-button {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ccc;
  background: #f5f5f5;
  cursor: pointer;
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
</style>