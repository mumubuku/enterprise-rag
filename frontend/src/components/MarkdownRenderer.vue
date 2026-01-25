<template>
  <div class="markdown-content" v-html="renderedContent"></div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

const props = defineProps({
  content: {
    type: String,
    default: ''
  }
})

marked.setOptions({
  highlight: function(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  },
  langPrefix: 'hljs language-',
  breaks: true,
  gfm: true
})

const renderedContent = computed(() => {
  if (!props.content) return ''
  return marked(props.content)
})
</script>

<style scoped>
.markdown-content {
  line-height: 1.6;
  color: #303133;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
  color: #1a1a1a;
}

.markdown-content :deep(h1) {
  font-size: 2em;
  border-bottom: 2px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-content :deep(h2) {
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-content :deep(h3) {
  font-size: 1.25em;
}

.markdown-content :deep(p) {
  margin: 1em 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 1em 0;
  padding-left: 2em;
}

.markdown-content :deep(li) {
  margin: 0.5em 0;
}

.markdown-content :deep(code) {
  background-color: #f6f8fa;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background-color: #1e1e1e;
  padding: 1em;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1em 0;
}

.markdown-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  color: #d4d4d4;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #dfe2e5;
  padding-left: 1em;
  margin: 1em 0;
  color: #6a737d;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #dfe2e5;
  padding: 0.5em 1em;
  text-align: left;
}

.markdown-content :deep(th) {
  background-color: #f6f8fa;
  font-weight: 600;
}

.markdown-content :deep(a) {
  color: #0366d6;
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 2px solid #eaecef;
  margin: 2em 0;
}

.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
}
</style>